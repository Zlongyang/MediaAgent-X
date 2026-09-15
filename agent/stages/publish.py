"""publish · 发布上线（发行人）：pack → publish_records[]；无账号 → unpublished 改手动。"""
from __future__ import annotations

import sys
import time
from datetime import datetime

from agent import events
from agent.llm import load_prompt
from agent.state import MediaState, mark_todo
from agent.stages.base import StageSpec
from agent.tools import mock_content

COST_LLM = 0.004


def node(state: MediaState) -> dict:
    _ = load_prompt("subagents/publisher.md")
    account = state.get("account", "none")
    pack = state.get("pack", {})
    final = state.get("artifacts", {}).get("final", "")

    events.cost_add(llm=COST_LLM)
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    if account and account != "none":
        # mock 发布：确定性回执（真实上传走 upload-post，一期不接）
        record = {**mock_content.PUBLISH_RECORD, "account": account, "ts": now, "video": final}
        events.todo_update(5, True)
        events.message("assistant", f"已发布：{record['platform']}（video_id={record['video_id']}）。分析师接管数据监控。")
        return {
            "publish_records": [record],
            "status": "published",
            "cost": {"llm": COST_LLM},
            "todos": mark_todo(state.get("todos", []), 5),
            "messages": [{"type": "assistant", "text": f"已发布：{record['platform']} video_id={record['video_id']}。"}],
        }

    # 无账号：不假装发布，标 unpublished 等人工（契约 §1 #10）
    record = {"platform": pack.get("platform", "抖音"), "account": "none", "ts": now,
              "video": final, "status": "unpublished", "reason": "未配置发布账号，转手动发布"}
    events.todo_update(5, True)
    events.message("assistant", "未配置发布账号：视频已就绪，状态 unpublished，可在项目页手动发布。")
    return {
        "publish_records": [record],
        "status": "unpublished",
        "cost": {"llm": COST_LLM},
        "todos": mark_todo(state.get("todos", []), 5),
        "messages": [{"type": "assistant", "text": "无账号，转手动发布（unpublished）。"}],
    }


STAGE = StageSpec(
    key="publish",
    name="publish · 发布上线",
    worker="发行人",
    icon="rocket",
    kind="task",
    node=node,
)


if __name__ == "__main__":
    from agent.state import initial_state

    s = initial_state("selftest", "做一条数码赛道的短视频", account="dy-shuma")
    s["pack"] = dict(mock_content.PACK_RESULT)
    t0 = time.perf_counter()
    out = node(s)
    print(out["status"], out["publish_records"][0]["video_id"])
    print(f"[ok] publish 自测通过，耗时 {time.perf_counter() - t0:.2f}s", file=sys.stderr)
