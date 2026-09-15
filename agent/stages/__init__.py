"""STAGE_REGISTRY：12 节点注册表 —— 增删改节点只动这一个列表（契约 §7.2 第 1 条）。

顺序即拓扑（与前端 buildStages() 一一对应）：
trend_scan ⇄ gate_topic → script_draft ⇄ gate_script → storyboard
→ mpt_pipeline ⇄ gate_preview → packaging ⇄ gate_publish → publish → monitoring → review
"""
from __future__ import annotations

from agent.gates import make_gate
from agent.stages import (
    monitoring,
    mpt_pipeline,
    packaging,
    publish,
    review,
    script_draft,
    storyboard,
    trend_scan,
)
from agent.stages.base import StageSpec

# ---- 四闸门：同一工厂生成，参数只有 (key, title, autonomyKey, view_fn, rerun_to) ----
GATE_TOPIC = make_gate(
    key="gate_topic",
    title="选题确认",
    autonomyKey="topic",
    view_fn=lambda s: {"candidates": s.get("trend_candidates", [])},
    rerun_to="trend_scan",
)
GATE_SCRIPT = make_gate(
    key="gate_script",
    title="脚本确认",
    autonomyKey="script",
    view_fn=lambda s: {"excerpt": s.get("script_excerpt", "")},
    rerun_to="script_draft",
)
GATE_PREVIEW = make_gate(
    key="gate_preview",
    title="成片预览",
    autonomyKey="preview",
    view_fn=lambda s: {"video": s.get("artifacts", {}).get("final", "")},
    rerun_to="mpt_pipeline",
)
GATE_PUBLISH = make_gate(
    key="gate_publish",
    title="发布确认",
    autonomyKey="publish",
    view_fn=lambda s: {"pack": s.get("pack", {})},
    rerun_to="packaging",
)

STAGE_REGISTRY: list[StageSpec] = [
    trend_scan.STAGE,
    GATE_TOPIC,
    script_draft.STAGE,
    GATE_SCRIPT,
    storyboard.STAGE,
    mpt_pipeline.STAGE,
    GATE_PREVIEW,
    packaging.STAGE,
    GATE_PUBLISH,
    publish.STAGE,
    monitoring.STAGE,
    review.STAGE,
]

__all__ = ["STAGE_REGISTRY", "StageSpec"]
