"""script_draft · 脚本草稿（编剧）：topic → script + script_excerpt，正文落盘 script.md。"""
from __future__ import annotations

import sys
import time

from agent import config, events
from agent.llm import chat, load_prompt
from agent.state import MediaState, mark_todo
from agent.stages.base import StageSpec
from agent.tools import mock_content

COST_LLM = 0.02


def node(state: MediaState) -> dict:
    topic = state.get("topic") or state.get("brief", "")
    system = load_prompt("SYSTEM.md") + "\n\n" + load_prompt("subagents/scriptwriter.md")
    raw = chat(
        system=system,
        user=f"定稿选题：「{topic}」。请写 60 秒短视频脚本：钩子/冲突/分段/收尾 CTA，"
             "含画面与台词标注。",
    )
    script = raw.strip() or mock_content.SCRIPT_FULL
    excerpt = mock_content.SCRIPT_EXCERPT  # 闸门展示用节选（节选由编剧工种产出，mock 期固定）

    # 铁律：工件进文件系统，上下文只放指针；脚本正文进 state 仅供闸门展示
    path = config.run_dir(state["run_id"]) / "script.md"
    path.write_text(script, encoding="utf-8")

    events.cost_add(llm=COST_LLM)
    events.todo_update(3, True)
    events.message("assistant", f"脚本草稿完成：「{topic}」，预计 58s，已提交总编审阅。")
    return {
        "script": script,
        "script_excerpt": excerpt,
        "cost": {"llm": COST_LLM},
        "todos": mark_todo(state.get("todos", []), 3),
        "messages": [{"type": "assistant", "text": "脚本草稿完成，已提交总编审阅。"}],
    }


STAGE = StageSpec(
    key="script_draft",
    name="script_draft · 脚本草稿",
    worker="编剧",
    icon="pen",
    kind="task",
    node=node,
)


if __name__ == "__main__":
    from agent.state import initial_state

    s = initial_state("selftest", "做一条数码赛道的短视频")
    s["topic"] = mock_content.TOPIC_CANDIDATES[0]["title"]
    t0 = time.perf_counter()
    out = node(s)
    print(out["script"][:200])
    print(f"[ok] script_draft 自测通过，耗时 {time.perf_counter() - t0:.2f}s", file=sys.stderr)
