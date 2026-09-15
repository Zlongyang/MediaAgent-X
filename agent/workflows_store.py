"""已安排工作流的 JSON 持久化（workspace/workflows.json）。

server.py 的 /api/workflows* 端点与 agent（程序化创建，如 workflow_intent）
共用这一层。cron 只校验 5 段格式，不验语义；调度执行器一期未接入，
`next` 字段固定占位 "未调度"。
"""
from __future__ import annotations

import json
import re
import uuid

from agent import config

_CRON_RE = re.compile(r"^\S+(\s+\S+){4}$")


def load() -> list[dict]:
    try:
        data = json.loads(config.WORKFLOWS_JSON.read_text(encoding="utf-8"))
        return data if isinstance(data, list) else []
    except (OSError, json.JSONDecodeError):
        return []


def save(items: list[dict]) -> None:
    config.ensure_dirs()
    config.WORKFLOWS_JSON.write_text(
        json.dumps(items, ensure_ascii=False, indent=2), encoding="utf-8"
    )


def create(data: dict) -> dict:
    name = str(data.get("name") or "").strip()
    schedule = str(data.get("schedule") or "").strip()
    if not name:
        raise ValueError("name 不能为空")
    if not _CRON_RE.match(schedule):
        raise ValueError("schedule 必须是 5 段 cron 表达式")
    wf = {
        "id": f"wf-{uuid.uuid4().hex[:8]}",
        "name": name,
        "desc": str(data.get("desc") or "").strip(),
        "schedule": schedule,
        "next": "未调度",
        "account": str(data.get("account") or "none").strip() or "none",
        "brief": str(data.get("brief") or data.get("desc") or name).strip(),
        "enabled": bool(data.get("enabled", True)),
    }
    items = load()
    items.append(wf)
    save(items)
    return wf


def get(wf_id: str) -> dict | None:
    return next((w for w in load() if w.get("id") == wf_id), None)


def delete(wf_id: str) -> bool:
    items = load()
    kept = [w for w in items if w.get("id") != wf_id]
    if len(kept) == len(items):
        return False
    save(kept)
    return True


def toggle(wf_id: str) -> dict | None:
    items = load()
    for w in items:
        if w.get("id") == wf_id:
            w["enabled"] = not w.get("enabled", False)
            save(items)
            return w
    return None


if __name__ == "__main__":
    wf = create({"name": "自测工作流", "schedule": "40 7 * * *",
                 "desc": "冒烟自测", "account": "dy-shuma"})
    assert wf["id"].startswith("wf-") and get(wf["id"])["name"] == "自测工作流"
    try:
        create({"name": "坏cron", "schedule": "每天早上"})
        raise SystemExit("非法 cron 未被拒绝")
    except ValueError:
        pass
    assert toggle(wf["id"])["enabled"] is False
    assert toggle(wf["id"])["enabled"] is True
    assert delete(wf["id"]) is True and get(wf["id"]) is None
    assert delete(wf["id"]) is False
    print("[PASS] workflows_store 自测通过")
