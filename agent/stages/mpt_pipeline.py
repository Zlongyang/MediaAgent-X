"""mpt_pipeline · 制片流水线（制片，复合节点）：shots → artifacts 路径（audio/subtitle/final）。

5 个子任务（契约 §2）：terms → audio → subtitle → materials → video，
每个对应 mpt stop_at 的一段。失败语义：子任务失败 → 抛 SubTaskError，
父节点 failed，图终止于该节点，error 写入 state（对齐 mpt failed_stage 语义）。
"""
from __future__ import annotations

import sys
import time

from agent import config, events
from agent.llm import load_prompt
from agent.state import MediaState, mark_todo
from agent.stages.base import StageSpec
from agent.tools import mpt_tools

# 子任务定义：(key, 成本类别, 成本, runner)；runner(state, run_dir) -> 产物 dict
SUBS = [
    {"key": "terms", "name": "terms · 提示词生成"},
    {"key": "audio", "name": "audio · 配音合成"},
    {"key": "subtitle", "name": "subtitle · 字幕生成"},
    {"key": "materials", "name": "materials · 素材拉取"},
    {"key": "video", "name": "video · 视频合成"},
]

SUB_COSTS = {
    "terms": ("llm", 0.006),
    "audio": ("tts", 0.05),
    "subtitle": ("llm", 0.004),
    "materials": ("material", 0.12),
    "video": ("material", 0.08),
}


class SubTaskError(mpt_tools.MPTError):
    def __init__(self, sub_key: str, cause: Exception):
        super().__init__(f"子任务 {sub_key} 失败：{cause}")
        self.sub_key = sub_key


def _run_sub(sub_key: str, state: MediaState, run_dir) -> dict:
    """按子任务分发到 mpt_tools（模式差异在 mpt_tools 内部屏蔽）。"""
    script = state.get("script", "")
    subject = state.get("topic") or state.get("brief", "")
    terms = state.get("_terms_cache") or [s.get("search", "") for s in state.get("shots", [])]
    if sub_key == "terms":
        return {"terms": mpt_tools.generate_terms(subject, script)}
    if sub_key == "audio":
        # cli 模式注入 mpt 的「脚本」必须是纯口播文本：mpt 自己的脚本后处理会删
        # markdown/标题/标注（01 拆解 §3.1），但 --video-script 注入不经过那层。
        # 分镜的 narration 字段生来就是逐镜口播稿，直接拼接即最佳 TTS 文本。
        vo = "\n\n".join(s.get("narration", "").strip()
                         for s in state.get("shots", []) if s.get("narration", "").strip())
        return mpt_tools.synthesize_audio(vo or script, run_dir, subject=subject, terms=terms)
    if sub_key == "subtitle":
        return mpt_tools.make_subtitle(script, run_dir)
    if sub_key == "materials":
        return mpt_tools.fetch_materials(terms, run_dir)
    if sub_key == "video":
        return mpt_tools.compose_video(run_dir)
    raise SubTaskError(sub_key, ValueError("未知子任务"))


def node(state: MediaState) -> dict:
    _ = load_prompt("subagents/producer.md")  # 人设即文件；mock 期仅校验可读
    run_dir = config.run_dir(state["run_id"])

    if config.mpt_mode() == "cli":
        events.message("note", "mpt 真实出片：全流程由 mpt 一次跑完（通常 2-5 分钟），各子任务在产物回读时统一补齐。")

    artifacts_update: dict = {}
    cost_update: dict = {"llm": 0.0, "material": 0.0, "tts": 0.0}
    terms: list[str] = []

    for sub in SUBS:
        key = sub["key"]
        events.sub_update("mpt_pipeline", key, "active")
        t0 = time.perf_counter()
        try:
            result = _run_sub(key, {**state, "_terms_cache": terms}, run_dir)
        except Exception as e:
            events.sub_update("mpt_pipeline", key, "failed", duration=f"{time.perf_counter() - t0:.1f}s")
            err = e if isinstance(e, SubTaskError) else SubTaskError(key, e)
            raise err
        dur = f"{time.perf_counter() - t0:.1f}s"
        events.sub_update("mpt_pipeline", key, "done", duration=dur)

        # 成本与产物回填（契约 §2 完成时回填表）
        cat, amount = SUB_COSTS[key]
        cost_update[cat] += amount
        events.cost_add(**{cat: amount})
        if key == "terms":
            terms = result.get("terms", [])
        for art_key in ("audio", "subtitle", "final"):
            if art_key in result:
                artifacts_update[art_key] = result[art_key]
                events.artifact_set(art_key, result[art_key])

    events.todo_update(4, True)
    events.message("assistant", "制片流水线完成：配音/字幕/素材/成片全部就绪。")
    return {
        "artifacts": artifacts_update,
        "cost": {k: v for k, v in cost_update.items() if v},
        "todos": mark_todo(state.get("todos", []), 4),
        "messages": [{"type": "assistant", "text": "制片流水线完成，成片已出。"}],
    }


STAGE = StageSpec(
    key="mpt_pipeline",
    name="mpt_pipeline · 制片流水线",
    worker="制片",
    icon="factory",
    kind="composite",
    node=node,
    subs=SUBS,
)


if __name__ == "__main__":
    from agent.state import initial_state

    s = initial_state("selftest", "做一条数码赛道的短视频")
    s["script"] = "自测脚本"
    t0 = time.perf_counter()
    out = node(s)
    print("artifacts:", out["artifacts"])
    print(f"[ok] mpt_pipeline 自测通过（MPT_MODE={config.mpt_mode()}），耗时 {time.perf_counter() - t0:.2f}s", file=sys.stderr)
