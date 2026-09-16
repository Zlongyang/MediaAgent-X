"""review · 复盘报告（分析师）：全量 state → review_report（落盘 review.md，state 存指针）+ review_ready 事件。"""
from __future__ import annotations

import sys
import time

from agent import config, events
from agent.llm import chat, load_prompt
from agent.state import MediaState, mark_todo
from agent.stages.base import StageSpec
from agent.tools import mock_content

COST_LLM = 0.008

_TIP_MARKS = ("建议", "下一轮", "应该", "可以", "行动", "优化", "改进", "尝试")


def _derive_tips(text: str) -> list[str]:
    """从复盘文本提取行动向句子（≤3 条），无则空列表——真实产物，宁缺毋假。"""
    tips = []
    for ln in text.splitlines():
        ln = ln.strip().lstrip("-·*•0123456789.、）) ").strip()
        if ln and any(m in ln for m in _TIP_MARKS) and len(ln) >= 8:
            tips.append(ln)
        if len(tips) >= 3:
            break
    return tips


def node(state: MediaState) -> dict:
    run_id = state.get("run_id", "")
    topic = state.get("topic") or state.get("brief", "")
    system = load_prompt("SYSTEM.md") + "\n\n" + load_prompt("subagents/analyst.md")
    raw = chat(
        system=system,
        user=f"为 run {run_id}（选题「{topic}」）写复盘报告：数据结论 / 归因 / 下一轮行动。",
    )
    text = raw.strip()
    if not text:
        raise RuntimeError("review: LLM 返回空复盘")

    path = config.run_dir(run_id) / "review.md"
    path.write_text(text, encoding="utf-8")

    cost = state.get("cost", {"llm": 0, "material": 0, "tts": 0, "total": 0})
    # 反哺建议从真实复盘文本提取（行动向句子），不再使用 fixture
    tips = _derive_tips(text)
    metrics = state.get("metrics_snapshots", [])

    events.cost_add(llm=COST_LLM)
    events.todo_update(6, True)
    events.review_ready(run_id, metrics, cost, tips)
    events.message("assistant", "复盘报告已生成，本轮流水线收官。")
    return {
        "review_report": str(path),
        "cost": {"llm": COST_LLM},
        "todos": mark_todo(state.get("todos", []), 6),
        "messages": [{"type": "assistant", "text": "复盘报告已生成。"}],
    }


STAGE = StageSpec(
    key="review",
    name="review · 复盘报告",
    worker="分析师",
    icon="chart",
    kind="task",
    node=node,
)


if __name__ == "__main__":
    from agent.state import initial_state

    config.enable_test_double()
    s = initial_state("selftest", "做一条数码赛道的短视频")
    s["topic"] = mock_content.TOPIC_CANDIDATES[0]["title"]
    t0 = time.perf_counter()
    out = node(s)
    print("review.md ->", out["review_report"])
    print(f"[ok] review 自测通过，耗时 {time.perf_counter() - t0:.2f}s", file=sys.stderr)
