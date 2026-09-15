"""图构建与驱动（契约 §7.1）：build_graph(registry) 纯粹由 STAGE_REGISTRY 驱动。

- 拓扑：registry 顺序线性串联；闸门 reject 回边由节点内 Command(goto=rerun_to) 完成，
  静态图上不画回边 —— 因此删尾部节点不影响编译（可拆解性第 1 条）。
- checkpointer：默认 MemorySaver；AGENT_SQLITE=1 时尝试 SqliteSaver，
  缺包自动回退 MemorySaver（不因为缺包崩）。
- 驱动：iter_run_sync / aiter_run 把 astream(stream_mode=["custom","updates"])
  的 chunk 翻译成 §5 SSE 事件；interrupt 值翻译成 gate_request。
"""
from __future__ import annotations

import json
import time
from datetime import datetime
from typing import Any, AsyncIterator, Iterator

from langgraph.checkpoint.memory import MemorySaver
from langgraph.errors import GraphInterrupt
from langgraph.graph import END, START, StateGraph
from langgraph.types import Command

from agent import config, events
from agent.stages import STAGE_REGISTRY
from agent.stages.base import StageSpec, summary
from agent.state import MediaState


# ---------------------------------------------------------------- checkpointer
def make_checkpointer():
    if config.use_sqlite():
        try:
            import sqlite3

            from langgraph.checkpoint.sqlite import SqliteSaver

            config.ensure_dirs()
            conn = sqlite3.connect(str(config.SQLITE_PATH), check_same_thread=False)
            return SqliteSaver(conn)
        except Exception as e:  # 缺包或初始化失败都不许崩，回退内存
            print(f"[warn] SqliteSaver 不可用（{e}），回退 MemorySaver")
    return MemorySaver()


# ---------------------------------------------------------------- 节点包装
def _wrap(spec: StageSpec):
    """统一包装：进节点报 active、出节点报 done、计时、异常收敛为 failed。

    失败语义（契约 §2）：节点抛错 → stage failed + error 事件 + error 写入 state，
    普通返回 dict（不用 Command(goto=END)——langgraph 1.2.x 中 Command 不抑制静态边，
    是否终止由 task 节点后的条件边根据 state.status 裁决）。
    """

    def wrapped(state: MediaState):
        events.stage_update(spec.key, "active")
        t0 = time.perf_counter()
        try:
            result = spec.node(state)
        except GraphInterrupt:
            raise  # 闸门 interrupt 的暂停信号，必须透传给 Pregel，不能当异常吞掉
        except Exception as e:
            dur = f"{time.perf_counter() - t0:.1f}s"
            events.stage_update(spec.key, "failed", duration=dur)
            events.error(spec.key, str(e))
            return {"status": "failed", "error": f"{spec.key}: {e}", "stage": spec.key}
        dur = f"{time.perf_counter() - t0:.1f}s"
        if isinstance(result, Command):
            # 闸门路由（confirm→next / reject→rerun_to）：reject 不标 done
            gotos = result.goto if isinstance(result.goto, (list, tuple)) else [result.goto]
            if spec.rerun_to and spec.rerun_to in gotos:
                events.stage_update(spec.key, "active", status_text="已驳回，重做中")
            else:
                events.stage_update(spec.key, "done", duration=dur)
            return result
        events.stage_update(spec.key, "done", duration=dur)
        return {**(result or {}), "stage": spec.key}

    wrapped.__name__ = spec.key
    return wrapped


def _route_unless_failed(next_key: str):
    """task 节点的出边裁决：failed → END（图终止于该节点），否则 → 下一节点。"""
    def route(state: MediaState) -> str:
        return END if state.get("status") == "failed" else next_key
    return route


# ---------------------------------------------------------------- 构图
def build_graph(registry: list[StageSpec] | None = None):
    """由 registry 驱动编译。registry 为空列表也能编译（START→END 直通）。

    布线规则（适配 langgraph 1.2.x：Command(goto) 不抑制静态出边）：
    - task/composite 节点：条件出边（failed→END，否则→后继）
    - gate 节点：无任何静态出边，confirm/reject 全部由节点内 Command(goto) 路由，
      confirm 去向（next_key）由这里注入
    """
    registry = list(STAGE_REGISTRY if registry is None else registry)
    for i, spec in enumerate(registry):
        if spec.kind == "gate":
            spec.next_key = registry[i + 1].key if i + 1 < len(registry) else END

    builder = StateGraph(MediaState)
    for spec in registry:
        builder.add_node(spec.key, _wrap(spec))
    if not registry:
        builder.add_edge(START, END)
        return builder.compile(checkpointer=make_checkpointer())

    builder.add_edge(START, registry[0].key)
    for i, spec in enumerate(registry):
        if spec.kind == "gate":
            continue  # gate 无静态出边
        nxt = registry[i + 1].key if i + 1 < len(registry) else END
        if nxt == END:
            builder.add_edge(spec.key, END)
        else:
            builder.add_conditional_edges(
                spec.key, _route_unless_failed(nxt), {nxt: nxt, END: END}
            )
    return builder.compile(checkpointer=make_checkpointer())


# ---------------------------------------------------------------- 驱动翻译
def _translate(mode: str, chunk: Any) -> list[dict]:
    """astream chunk → SSE 事件 dict 列表。interrupt 值 → gate_request。"""
    if mode == "custom":
        return [chunk]
    if mode == "updates" and isinstance(chunk, dict) and "__interrupt__" in chunk:
        out = []
        for intr in chunk["__interrupt__"]:
            out.append({"event": "gate_request", "data": intr.value})
        return out
    return []


def iter_run_sync(graph, input_, cfg: dict, registry: list[StageSpec] | None = None,
                  started: bool = True) -> Iterator[dict]:
    """同步驱动一轮（到 interrupt 或结束）。第一轮先发 run_started。"""
    if started:
        yield {"event": "run_started",
               "data": {"run_id": cfg["configurable"]["thread_id"],
                        "stages": [summary(s) for s in (registry or STAGE_REGISTRY)]}}
    for mode, chunk in graph.stream(input_, cfg, stream_mode=["custom", "updates"]):
        yield from _translate(mode, chunk)


async def aiter_run(graph, input_, cfg: dict, registry: list[StageSpec] | None = None,
                    started: bool = True) -> AsyncIterator[dict]:
    """异步驱动一轮（server 用）。"""
    if started:
        yield {"event": "run_started",
               "data": {"run_id": cfg["configurable"]["thread_id"],
                        "stages": [summary(s) for s in (registry or STAGE_REGISTRY)]}}
    async for mode, chunk in graph.astream(input_, cfg, stream_mode=["custom", "updates"]):
        for ev in _translate(mode, chunk):
            yield ev


# ---------------------------------------------------------------- 收尾
def finalize_project(final: dict) -> dict | None:
    """run 结束时把项目对象落盘 workspace/runs/<run_id>/project.json（供 /api/projects）。"""
    status = final.get("status", "")
    if status not in ("published", "unpublished"):
        return None
    run_id = final.get("run_id", "")
    if not run_id:
        return None
    project = {
        "id": run_id,
        "name": final.get("topic") or final.get("brief", ""),
        "account": final.get("account", "none"),
        "status": status,
        "createdAt": datetime.now().strftime("%Y-%m-%d %H:%M"),
        "detail": "full",
        "artifacts": dict(final.get("artifacts", {})),
        "pack": dict(final.get("pack", {})),
        "shots": list(final.get("shots", [])),
        "publish_records": list(final.get("publish_records", [])),
        "metrics_schedule": list(final.get("metrics_schedule", [])),
        "snapshots": list(final.get("metrics_snapshots", [])),
        "cost": dict(final.get("cost", {})),
        "review_report": final.get("review_report", ""),
        "chat": list(final.get("messages", [])),
        "logs": [
            f"[{datetime.now():%H:%M:%S}] run {run_id} finished, status={status}, "
            f"cost_total={final.get('cost', {}).get('total', 0)}"
        ],
    }
    path = config.run_dir(run_id) / "project.json"
    path.write_text(json.dumps(project, ensure_ascii=False, indent=2), encoding="utf-8")
    return project
