"""SSE 事件发射器（契约 §5）—— 全项目唯一允许写事件的地方。

节点内通过 get_stream_writer() 发 custom 事件；driver（cli/server）以
astream(stream_mode=["custom","updates"]) 接收并转发。事件形状与 §5 表一一对应。

注意：get_stream_writer() 在图外会抛 RuntimeError，这里静默降级为 no-op，
使每个 stage 文件可以在 __main__ 自测块里脱离图直接运行。
"""
from __future__ import annotations

from typing import Any

from langgraph.config import get_stream_writer


def _write(event: str, data: dict[str, Any]) -> None:
    payload = {"event": event, "data": data}
    try:
        writer = get_stream_writer()
    except Exception:
        return  # 图外（stage 独立自测）：不写事件
    try:
        writer(payload)
    except Exception:
        return


# ---- §5 事件表 ----

def run_started(run_id: str, stages: list[dict]) -> None:
    _write("run_started", {"run_id": run_id, "stages": stages})


def stage_update(key: str, status: str, duration: str | None = None, status_text: str | None = None) -> None:
    data: dict[str, Any] = {"key": key, "status": status}
    if duration is not None:
        data["duration"] = duration
    if status_text is not None:
        data["statusText"] = status_text
    _write("stage_update", data)


def sub_update(parent: str, key: str, status: str, duration: str | None = None, status_text: str | None = None) -> None:
    data: dict[str, Any] = {"parent": parent, "key": key, "status": status}
    if duration is not None:
        data["duration"] = duration
    if status_text is not None:
        data["statusText"] = status_text
    _write("sub_update", data)


def gate_resolved(key: str, nonce: int, action: str, auto: bool) -> None:
    _write("gate_resolved", {"key": key, "nonce": nonce, "action": action, "auto": auto})


def cost_add(llm: float = 0.0, material: float = 0.0, tts: float = 0.0) -> None:
    data: dict[str, float] = {}
    if llm:
        data["llm"] = llm
    if material:
        data["material"] = material
    if tts:
        data["tts"] = tts
    if data:
        _write("cost_add", data)


def artifact_set(key: str, path: str) -> None:
    _write("artifact_set", {"key": key, "path": path})


def todo_update(todo_id: int, done: bool) -> None:
    _write("todo_update", {"id": todo_id, "done": done})


def message(type_: str, text: str) -> None:
    _write("message", {"type": type_, "text": text})


def review_ready(run_id: str, metrics: list[dict], cost: dict, tips: list[str]) -> None:
    _write("review_ready", {"runId": run_id, "metrics": metrics, "cost": cost, "tips": tips})


def run_finished(status: str, project: dict | None = None) -> None:
    data: dict[str, Any] = {"status": status}
    if project is not None:
        data["project"] = project
    _write("run_finished", data)


def error(stage: str, message_: str) -> None:
    _write("error", {"stage": stage, "message": message_})


# gate_request 不走 writer：闸门节点把 payload 作为 interrupt() 的值抛出，
# 由 driver 翻译为 gate_request SSE（避免 resume 重跑节点时重复发卡片）。
def gate_request_payload(key: str, title: str, autonomy_key: str, nonce: int, view: dict) -> dict:
    return {"key": key, "title": title, "autonomyKey": autonomy_key, "nonce": nonce, "view": view}
