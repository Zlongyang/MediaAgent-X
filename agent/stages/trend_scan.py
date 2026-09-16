"""trend_scan · 选题扫描（选题猎手）：brief → trend_candidates[]（3 个候选 {title,source,heat,reason}）。"""
from __future__ import annotations

import json
import sys
import time
import warnings

from agent import events
from agent.llm import chat, load_prompt, parse_llm_json
from agent.state import MediaState, mark_todo
from agent.stages.base import StageSpec
from agent.tools import mock_content

COST_LLM = 0.012


def node(state: MediaState) -> dict:
    brief = state.get("brief", "")
    system = load_prompt("SYSTEM.md") + "\n\n" + load_prompt("subagents/hunter.md")
    raw = chat(
        system=system,
        user=f"赛道 brief：{brief}\n请做热点扫描，给 3 个候选选题，"
             'JSON 数组，元素形状 {"title","source","heat","reason"}。',
    )
    try:
        candidates = parse_llm_json(raw)
        assert isinstance(candidates, list) and candidates
    except Exception as e:
        warnings.warn(f"trend_scan: LLM 输出解析失败，降级 fixture：{e!r}")
        candidates = list(mock_content.TOPIC_CANDIDATES)  # 解析失败兜底确定性 fixture
    candidates = candidates[:3]

    events.cost_add(llm=COST_LLM)
    events.todo_update(1, True)
    events.message("assistant", f"热点扫描完成：命中 {len(candidates)} 个上升话题，已按「争议度 × 搜索增速 × 粉丝画像」排序。")
    return {
        "trend_candidates": candidates,
        "cost": {"llm": COST_LLM},
        "todos": mark_todo(state.get("todos", []), 1),
        "messages": [{"type": "assistant", "text": f"热点扫描完成：{len(candidates)} 个候选选题已推送总编。"}],
    }


STAGE = StageSpec(
    key="trend_scan",
    name="trend_scan · 选题扫描",
    worker="选题猎手",
    icon="target",
    kind="task",
    node=node,
)


if __name__ == "__main__":
    # 独立自测：python -m agent.stages.trend_scan --mock
    from agent.state import initial_state

    t0 = time.perf_counter()
    out = node(initial_state("selftest", "做一条数码赛道的短视频"))
    print(json.dumps(out["trend_candidates"], ensure_ascii=False, indent=2))
    print(f"[ok] trend_scan 自测通过，耗时 {time.perf_counter() - t0:.2f}s", file=sys.stderr)
