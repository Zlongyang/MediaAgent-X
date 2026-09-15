"""闸门工厂（契约 §3 闸门协议 + §7.2 可拆解性第 3 条：闸门即插拔）。

四个闸门全部由 make_gate(key, title, autonomyKey, view_fn, rerun_to) 生成：

- autonomy[key] === False → 不 interrupt，写 autoPayload 自动确认放行
- autonomy[key] === True  → interrupt(gate_payload) 挂出 GateCard；
  driver 把 interrupt 值翻译成 SSE gate_request
- 确认 = Command(resume={"action":"confirm","payload":{...}})；
  gate_topic 的 payload 是 {choice}，其余闸门是 {}
- 驳回 = Command(resume={"action":"reject"}) → 节点返回 Command(goto=rerun_to)
  回边到前一 stage，重跑后再进同一闸门，nonce 递增

nonce 语义：每次 interrupt 携带 nonce = 已确认次数 + 1；只有决议落定后才把
nonce 提交进 state.gate_nonces，因此 interrupt 抛出导致的节点重跑不会重复计数，
而 reject 重跑后的下一次弹出会拿到 nonce+1（对齐前端 gate.nonce 去重）。
"""
from __future__ import annotations

from typing import Any, Callable

from langgraph.graph import END
from langgraph.types import Command, interrupt

from agent import events
from agent.state import MediaState, mark_todo
from agent.stages.base import StageSpec


def _auto_payload(key: str, state: MediaState) -> dict:
    """autonomy=false 时的自动确认载荷：gate_topic 自动选第 1 个候选，其余为 {}。"""
    if key == "gate_topic":
        candidates = state.get("trend_candidates") or []
        return {"choice": candidates[0]} if candidates else {}
    return {}


def _apply_confirm(key: str, state: MediaState, payload: dict) -> dict:
    """确认载荷写入 state。gate_topic 收 {choice}；其余闸门只留确认痕迹（nonce）。"""
    update: dict[str, Any] = {}
    if key == "gate_topic":
        choice = (payload or {}).get("choice") or {}
        topic = choice.get("title") or state.get("topic") or ""
        if topic:
            update["topic"] = topic
            events.message("assistant", f"选题已锁定：「{topic}」。编剧开始起草脚本。")
            update["messages"] = [{"type": "assistant", "text": f"选题已锁定：「{topic}」。"}]
        update["todos"] = mark_todo(state.get("todos", []), 2)
        events.todo_update(2, True)
    return update


def make_gate(
    key: str,
    title: str,
    autonomyKey: str,
    view_fn: Callable[[MediaState], dict],
    rerun_to: str,
) -> StageSpec:
    """生成一个闸门 StageSpec。参数即全部差异，闸门逻辑零复制。"""

    def gate_node(state: MediaState):
        nonce = int(state.get("gate_nonces", {}).get(key, 0)) + 1
        wait_human = bool(state.get("autonomy", {}).get(autonomyKey, True))
        # confirm 去向由 build_graph 注入（无静态出边，Command 独占路由）
        next_key = spec.next_key or END

        if not wait_human:
            # autonomy=false：不 interrupt，自动确认放行（带 autoPayload）
            payload = _auto_payload(key, state)
            events.gate_resolved(key, nonce, "confirm", auto=True)
            update = {"gate_nonces": {key: nonce}}
            update.update(_apply_confirm(key, state, payload))
            return Command(goto=next_key, update=update)

        # autonomy=true：挂出 GateCard 等待人工。interrupt 值 = gate_request 载荷，
        # driver 负责翻译成 SSE gate_request 事件。
        view = view_fn(state) or {}
        decision = interrupt(events.gate_request_payload(key, title, autonomyKey, nonce, view))
        decision = decision or {}
        action = decision.get("action", "confirm")

        if action == "reject":
            # 驳回：无载荷，回边到 rerun_to 重跑，之后再弹同一闸门（nonce 已 +1）
            events.gate_resolved(key, nonce, "reject", auto=False)
            return Command(goto=rerun_to, update={"gate_nonces": {key: nonce}})

        events.gate_resolved(key, nonce, "confirm", auto=False)
        update = {"gate_nonces": {key: nonce}}
        update.update(_apply_confirm(key, state, decision.get("payload") or {}))
        return Command(goto=next_key, update=update)

    spec = StageSpec(
        key=key,
        name=title,
        worker="总编",
        icon="",
        kind="gate",
        node=gate_node,
        rerun_to=rerun_to,
    )
    return spec
