"""packaging · 发布打包（包装师）：script+artifacts → pack {platform,title,caption,tags[],titleLen,descLen} + cover。"""
from __future__ import annotations

import json
import sys
import time

from agent import config, events
from agent.llm import chat, load_prompt
from agent.state import MediaState
from agent.stages.base import StageSpec
from agent.tools import mock_content

COST_LLM = 0.01


def node(state: MediaState) -> dict:
    topic = state.get("topic") or state.get("brief", "")
    script = state.get("script", "")
    system = load_prompt("SYSTEM.md") + "\n\n" + load_prompt("subagents/packager.md")
    raw = chat(
        system=system,
        user=f"为视频打包：选题「{topic}」。输出 minified JSON，恰好三键 "
             '{"title","caption","hashtags"}；title≤30 字，caption≤80 字，hashtags 3-8 个。\n\n'
             + script[:800],
    )
    try:
        meta = json.loads(raw)
        title = meta["title"]
        caption = meta["caption"]
        tags = list(meta["hashtags"])
    except Exception:
        title = mock_content.PACK_RESULT["title"]
        caption = mock_content.PACK_RESULT["caption"]
        tags = list(mock_content.PACK_RESULT["tags"])

    pack = {
        "platform": "抖音",
        "title": title,
        "caption": caption,
        "tags": tags,
        "titleLen": len(title),
        "descLen": len(caption),
    }

    # 封面工件落盘，state 只放指针
    cover = config.run_dir(state["run_id"]) / "cover" / "cover.jpg"
    cover.parent.mkdir(parents=True, exist_ok=True)
    cover.write_bytes(mock_content.MOCK_COVER_BYTES)
    events.artifact_set("cover", str(cover))

    events.cost_add(llm=COST_LLM)
    events.message("assistant", f"打包完成：标题 {pack['titleLen']}/30 字，{len(tags)} 个标签，封面已出。")
    return {
        "pack": pack,
        "artifacts": {"cover": str(cover)},
        "cost": {"llm": COST_LLM},
        "messages": [{"type": "assistant", "text": "打包完成，等待发布确认。"}],
    }


STAGE = StageSpec(
    key="packaging",
    name="packaging · 发布打包",
    worker="包装师",
    icon="package",
    kind="task",
    node=node,
)


if __name__ == "__main__":
    from agent.state import initial_state

    s = initial_state("selftest", "做一条数码赛道的短视频")
    s["topic"] = mock_content.TOPIC_CANDIDATES[0]["title"]
    s["script"] = mock_content.SCRIPT_FULL
    t0 = time.perf_counter()
    out = node(s)
    print(json.dumps(out["pack"], ensure_ascii=False, indent=2))
    print(f"[ok] packaging 自测通过，耗时 {time.perf_counter() - t0:.2f}s", file=sys.stderr)
