"""FastAPI + SSE 服务器（契约 §6 HTTP API + §5 事件流）。

一期范围：
- /api/runs* 五个端点（runs 创建/SSE/gate/state/autonomy）——完整可用
- /api/projects 两个只读 + 手动 publish —— 从 workspace/runs/<id>/project.json 扫描重建，空则 []
- /api/workflows* 五个端点（list/create/delete/toggle/run）—— workflows_store 持久化，run 立即触发一条 auto run
- /api/chat —— 对话意图路由（workflow_intent.classify，失败降级 kind=run）
- /api/monitor/videos —— 读 workspace/ 下持久化 JSON，无数据返回 []

SSE 断线重连：重连后先补发该 run 的完整事件历史（事件即快照翻译结果），再继续直播。
"""
from __future__ import annotations

import asyncio
import json
import os
import re
import shutil
import uuid
from typing import Any

from fastapi import Body, FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, StreamingResponse
from langgraph.types import Command

from agent import config, logx
from agent.graph import aiter_run, build_graph, finalize_project
from agent.state import dump_jsonable, initial_state
from agent import workflow_intent, workflows_store

_log = logx.setup()
_log.info("server 启动：MPT_MODE=%s，日志文件 → %s", config.mpt_mode(), config.LOG_FILE)

app = FastAPI(title="MediaAgent-X Agent Server", version="0.1.0")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# ---------------------------------------------------------------- 运行时单例
_GRAPH = None


def get_graph():
    """惰性编译一次：checkpointer（MemorySaver）随图复用，thread_id=run_id 隔离。"""
    global _GRAPH
    if _GRAPH is None:
        config.ensure_dirs()
        _GRAPH = build_graph()
    return _GRAPH


class RunHandle:
    """一个 run 的 SSE 广播句柄：history 重放 + Condition 订阅，不丢不重。"""

    def __init__(self, run_id: str):
        self.run_id = run_id
        self.history: list[dict] = []
        self.cond = asyncio.Condition()
        self.inbox: asyncio.Queue = asyncio.Queue()  # /gate 注入的 Command
        self.closed = False
        self.task: asyncio.Task | None = None

    async def broadcast(self, ev: dict) -> None:
        async with self.cond:
            self.history.append(ev)
            self.cond.notify_all()

    async def close(self) -> None:
        async with self.cond:
            self.closed = True
            self.cond.notify_all()


RUNS: dict[str, RunHandle] = {}


# ---------------------------------------------------------------- 驱动
async def _drive(handle: RunHandle, initial: dict) -> None:
    g = get_graph()
    cfg = {"configurable": {"thread_id": handle.run_id}}
    input_: Any = initial
    first = True
    try:
        while True:
            async for ev in aiter_run(g, input_, cfg, started=first):
                await handle.broadcast(ev)
            first = False
            st = await g.aget_state(cfg)
            if st.next:
                # 图停在闸门 interrupt：等 /gate 端点注入 Command(resume=...)
                input_ = await handle.inbox.get()
                continue
            final = st.values
            project = finalize_project(final)
            data: dict[str, Any] = {"status": final.get("status", "failed")}
            if project is not None:
                data["project"] = project
            await handle.broadcast({"event": "run_finished", "data": data})
            _log.info("run %s 收官 status=%s", handle.run_id, data["status"])
            break
    except Exception as e:  # 驱动兜底：任何异常都以 error + failed 收场
        _log.warning("run %s 驱动异常：%r", handle.run_id, e)
        await handle.broadcast({"event": "error", "data": {"stage": "driver", "message": str(e)}})
        await handle.broadcast({"event": "run_finished", "data": {"status": "failed"}})
    finally:
        await handle.close()


# ---------------------------------------------------------------- /api/runs*
def _start_run(text: str, account: str, autonomy: dict | None, auto_mode: bool) -> str:
    """创建并驱动一个 run（/api/runs 与 /api/workflows/{id}/run 共用）。
    必须在事件循环线程上调用（内部 asyncio.create_task）——sync 端点禁用。"""
    run_id = f"r-{uuid.uuid4().hex[:8]}"
    state = initial_state(run_id, text, account=account, autonomy=autonomy, auto_mode=auto_mode)
    handle = RunHandle(run_id)
    RUNS[run_id] = handle
    get_graph()  # 确保已编译（尽早暴露编译错误）
    handle.task = asyncio.create_task(_drive(handle, state))
    _log.info("run %s 创建 account=%s auto=%s in=%d字", run_id, account, auto_mode, len(text))
    return run_id


@app.post("/api/runs")
async def create_run(body: dict = Body(...)):
    text = (body.get("text") or "").strip()
    if not text:
        raise HTTPException(400, "text 不能为空")
    run_id = _start_run(text, body.get("account") or "none",
                        body.get("autonomy"), bool(body.get("autoMode")))
    return {"run_id": run_id}


def _sse(ev: dict) -> str:
    return f"event: {ev['event']}\ndata: {json.dumps(ev['data'], ensure_ascii=False)}\n\n"


@app.get("/api/runs/{run_id}/events")
async def run_events(run_id: str):
    handle = RUNS.get(run_id)
    if handle is None:
        raise HTTPException(404, f"run {run_id} 不存在")

    async def gen():
        idx = 0
        while True:
            async with handle.cond:
                await handle.cond.wait_for(lambda: len(handle.history) > idx or handle.closed)
                batch = handle.history[idx:]
                idx = len(handle.history)
                drained = handle.closed and idx >= len(handle.history)
            for ev in batch:
                yield _sse(ev)
            if drained:
                break

    return StreamingResponse(
        gen(),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
    )


@app.post("/api/runs/{run_id}/gate")
async def resolve_gate(run_id: str, body: dict = Body(...)):
    handle = RUNS.get(run_id)
    if handle is None:
        raise HTTPException(404, f"run {run_id} 不存在")
    action = body.get("action")
    if action not in ("confirm", "reject"):
        raise HTTPException(400, "action 必须是 confirm 或 reject")
    st = await get_graph().aget_state({"configurable": {"thread_id": run_id}})
    if not st.next:
        return {"ok": False, "error": "run 未处于闸门等待"}
    resume = {"action": action, "payload": body.get("payload") or {}}
    handle.inbox.put_nowait(Command(resume=resume))
    _log.info("run %s gate 决议 action=%s nonce=%s", run_id, action, body.get("nonce"))
    return {"ok": True}


@app.get("/api/runs/{run_id}/state")
async def run_state(run_id: str):
    if run_id not in RUNS:
        raise HTTPException(404, f"run {run_id} 不存在")
    st = await get_graph().aget_state({"configurable": {"thread_id": run_id}})
    return dump_jsonable(st.values)


@app.post("/api/runs/{run_id}/autonomy")
async def set_autonomy(run_id: str, body: dict = Body(...)):
    if run_id not in RUNS:
        raise HTTPException(404, f"run {run_id} 不存在")
    key = body.get("key")
    if key not in ("topic", "script", "preview", "publish"):
        raise HTTPException(400, "key 必须是 topic/script/preview/publish")
    await get_graph().aupdate_state(
        {"configurable": {"thread_id": run_id}},
        {"autonomy": {key: bool(body.get("enabled"))}},
    )
    return {"ok": True}


# ---------------------------------------------------------------- /api/projects
def _scan_projects() -> list[dict]:
    out = []
    if config.RUNS_DIR.exists():
        for d in sorted(config.RUNS_DIR.iterdir()):
            pj = d / "project.json"
            if pj.is_file():
                try:
                    out.append(json.loads(pj.read_text(encoding="utf-8")))
                except (OSError, json.JSONDecodeError):
                    continue
    return out


@app.get("/api/projects")
async def list_projects():
    return _scan_projects()


@app.get("/api/projects/{project_id}")
async def get_project(project_id: str):
    for p in _scan_projects():
        if p.get("id") == project_id:
            return p
    raise HTTPException(404, f"project {project_id} 不存在")


@app.post("/api/projects/{project_id}/publish")
async def publish_project(project_id: str):
    pj = config.RUNS_DIR / project_id / "project.json"
    if not pj.is_file():
        raise HTTPException(404, f"project {project_id} 不存在")
    project = json.loads(pj.read_text(encoding="utf-8"))
    if project.get("status") == "unpublished":
        project["status"] = "published"
        project.setdefault("logs", []).append("manual publish via /api/projects/{id}/publish")
        pj.write_text(json.dumps(project, ensure_ascii=False, indent=2), encoding="utf-8")
    return {"ok": True, "status": project.get("status")}


# ---------------------------------------------------------------- workflows / chat / monitor
def _read_json_or_empty(path, default):
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return default


@app.get("/api/workflows")
async def list_workflows():
    return workflows_store.load()


@app.post("/api/workflows")
async def create_workflow(body: dict = Body(...)):
    try:
        wf = workflows_store.create(body)
    except ValueError as e:
        raise HTTPException(400, str(e))
    return {"ok": True, "workflow": wf}


@app.delete("/api/workflows/{workflow_id}")
async def delete_workflow(workflow_id: str):
    if not workflows_store.delete(workflow_id):
        raise HTTPException(404, f"workflow {workflow_id} 不存在")
    return {"ok": True}


@app.post("/api/workflows/{workflow_id}/toggle")
async def toggle_workflow(workflow_id: str):
    wf = workflows_store.toggle(workflow_id)
    if wf is None:
        raise HTTPException(404, f"workflow {workflow_id} 不存在")
    return {"ok": True, "enabled": wf["enabled"]}


@app.post("/api/workflows/{workflow_id}/run")
async def run_workflow(workflow_id: str):
    # 手动触发不看 enabled：启停只影响未来调度器（一期未接入），「立即运行」是显式人工动作。
    wf = workflows_store.get(workflow_id)
    if wf is None:
        raise HTTPException(404, f"workflow {workflow_id} 不存在")
    run_id = _start_run(wf.get("brief") or wf.get("desc") or wf["name"],
                        wf.get("account") or "none", None, True)
    return {"ok": True, "run_id": run_id}


@app.post("/api/chat")
def chat_route(body: dict = Body(...)):
    """对话意图路由。注意必须保持 sync def：classify() 含阻塞式 LLM 调用，
    async def 会冻结事件循环（FastAPI 对 sync 端点自动走 threadpool）。"""
    text = (body.get("text") or "").strip()
    if not text:
        raise HTTPException(400, "text 不能为空")
    return workflow_intent.classify(text, body.get("account") or "none")


@app.get("/api/monitor/videos")
async def monitor_videos(account: str | None = None):
    videos = _read_json_or_empty(config.MONITOR_VIDEOS_JSON, [])
    if account:
        videos = [v for v in videos if v.get("account") == account]
    return videos


# ---------------------------------------------------------------- 项目删除
_PROJECT_ID_RE = re.compile(r"^[\w-]+$")


@app.delete("/api/projects/{project_id}")
async def delete_project(project_id: str):
    """删除归档项目 = 移除 workspace/runs/<id>/ 整个目录。进行中的 run 拒绝（409）。"""
    if not _PROJECT_ID_RE.match(project_id):
        raise HTTPException(400, "非法 project_id")
    run_dir = (config.RUNS_DIR / project_id).resolve()
    if config.RUNS_DIR.resolve() not in run_dir.parents:
        raise HTTPException(400, "非法 project_id")
    if not run_dir.is_dir():
        raise HTTPException(404, f"project {project_id} 不存在")
    handle = RUNS.get(project_id)
    if handle is not None and not handle.closed:
        raise HTTPException(409, "run 进行中，不能删除")
    shutil.rmtree(run_dir)
    _log.info("project %s 已删除", project_id)
    return {"ok": True}


# ---------------------------------------------------------------- 工件服务
@app.get("/api/runs/{run_id}/artifacts/{rel_path:path}")
async def run_artifact(run_id: str, rel_path: str):
    """把 run 目录下的工件（final.mp4 等）通过 HTTP 提供给前端播放器。"""
    if not _PROJECT_ID_RE.match(run_id):
        raise HTTPException(400, "非法 run_id")
    base = (config.RUNS_DIR / run_id).resolve()
    if config.RUNS_DIR.resolve() not in base.parents:
        raise HTTPException(400, "非法 run_id")
    target = (base / rel_path).resolve()
    if target != base and base not in target.parents:
        raise HTTPException(400, "非法工件路径")
    if not target.is_file():
        raise HTTPException(404, "工件不存在")
    return FileResponse(target)


@app.get("/api/health")
async def health():
    if config.has_llm_key():
        llm = config.DEEPSEEK_MODEL
    elif config.test_double():
        llm = "test-double"
    else:
        llm = "missing-key"
    return {"ok": True, "llm": llm, "mpt": config.mpt_mode()}
