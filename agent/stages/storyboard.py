"""storyboard · 分镜设计（分镜师）：script → shots[]（[{idx,narration,visual,search,duration}]），落盘 shots.json。"""
from __future__ import annotations

import json
import sys
import time
import warnings

from agent import config, events
from agent.llm import chat, load_prompt, parse_llm_json
from agent.state import MediaState
from agent.stages.base import StageSpec
from agent.tools import mock_content

COST_LLM = 0.015


def _shot_seconds(d) -> float:
    """时长兼容：数值型（1.5）与字符串型（"3s"/"6"）都接受，不可解析按 0。"""
    try:
        return float(str(d).rstrip("s").strip())
    except (TypeError, ValueError):
        return 0.0


def node(state: MediaState) -> dict:
    script = state.get("script", "")
    system = load_prompt("SYSTEM.md") + "\n\n" + load_prompt("subagents/storyboarder.md")
    raw = chat(
        system=system,
        user="把下面脚本拆成镜头表，JSON 数组，元素形状 "
             '{"idx","narration","visual","search","duration"}；search 用英文 1-3 词。\n\n'
             + script[:1500],
    )
    try:
        shots = parse_llm_json(raw)
        assert isinstance(shots, list) and shots
    except Exception as e:
        warnings.warn(f"storyboard: LLM 输出解析失败，降级 fixture：{e!r}")
        shots = list(mock_content.SHOTS)
    # 规整 idx，保证递增
    for i, s in enumerate(shots, 1):
        s["idx"] = i

    path = config.run_dir(state["run_id"]) / "shots.json"
    path.write_text(json.dumps(shots, ensure_ascii=False, indent=2), encoding="utf-8")

    events.cost_add(llm=COST_LLM)
    total = sum(_shot_seconds(s.get("duration", 0)) for s in shots)
    events.message("assistant", f"分镜完成：{len(shots)} 个镜头，总时长约 {total:g}s。")
    return {
        "shots": shots,
        "cost": {"llm": COST_LLM},
        "messages": [{"type": "assistant", "text": f"分镜完成：{len(shots)} 个镜头。"}],
    }


STAGE = StageSpec(
    key="storyboard",
    name="storyboard · 分镜设计",
    worker="分镜师",
    icon="clapper",
    kind="task",
    node=node,
)


if __name__ == "__main__":
    from agent.state import initial_state

    assert _shot_seconds(1.5) == 1.5
    assert _shot_seconds("3s") == 3.0
    assert _shot_seconds("6") == 6.0
    assert _shot_seconds("abc") == 0.0
    assert _shot_seconds(None) == 0.0

    s = initial_state("selftest", "做一条数码赛道的短视频")
    s["script"] = mock_content.SCRIPT_FULL
    t0 = time.perf_counter()
    out = node(s)
    print(json.dumps(out["shots"], ensure_ascii=False, indent=2)[:400])
    print(f"[ok] storyboard 自测通过，耗时 {time.perf_counter() - t0:.2f}s", file=sys.stderr)
