"""monitoring · 数据回拉（分析师）：publish_records → metrics_schedule（T+1h/6h/24h/7d 四次排期）。"""
from __future__ import annotations

import sys
import time

from agent import events
from agent.llm import load_prompt
from agent.state import MediaState
from agent.stages.base import StageSpec
from agent.tools import mock_content

COST_LLM = 0.006


def node(state: MediaState) -> dict:
    _ = load_prompt("subagents/analyst.md")
    records = state.get("publish_records", [])
    published = any(r.get("status") == "published" for r in records)

    schedule = list(mock_content.METRICS_SCHEDULE)
    # 已发布才有真实回拉快照；未发布只排期（mock 期快照为确定性 fixture）
    snapshots = list(mock_content.METRICS_SNAPSHOTS) if published else []

    events.cost_add(llm=COST_LLM)
    events.message("assistant", f"监控排期已建：{'/'.join(schedule)} 四次回拉。")
    return {
        "metrics_schedule": schedule,
        "metrics_snapshots": snapshots,
        "cost": {"llm": COST_LLM},
        "messages": [{"type": "assistant", "text": f"监控排期：{'/'.join(schedule)}。"}],
    }


STAGE = StageSpec(
    key="monitoring",
    name="monitoring · 数据回拉",
    worker="分析师",
    icon="chart",
    kind="task",
    node=node,
)


if __name__ == "__main__":
    from agent.state import initial_state

    s = initial_state("selftest", "x", account="dy-shuma")
    s["publish_records"] = [dict(mock_content.PUBLISH_RECORD)]
    t0 = time.perf_counter()
    out = node(s)
    print(out["metrics_schedule"], len(out["metrics_snapshots"]))
    print(f"[ok] monitoring 自测通过，耗时 {time.perf_counter() - t0:.2f}s", file=sys.stderr)
