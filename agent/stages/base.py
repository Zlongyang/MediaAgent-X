"""StageSpec：每个 stage 模块的静态描述（契约 §7.2 base.py）。

增删改节点只动 stages/__init__.py 的 STAGE_REGISTRY 列表；
graph.py 纯粹由 registry 驱动编译。
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Callable


@dataclass
class StageSpec:
    key: str                      # 与前端 buildStages() 的 key 一一对应
    name: str                     # 展示名
    worker: str                   # 工种（选题猎手/编剧/总编/…）
    icon: str                     # 前端图标名
    kind: str                     # "task" | "gate" | "composite"
    node: Callable[..., Any]      # 节点函数：(MediaState) -> dict | Command
    rerun_to: str | None = None   # 仅 gate：驳回后回到哪个 stage
    next_key: str | None = None   # 仅 gate：confirm 去向（由 build_graph 注入，缺省 END）
    subs: list[dict] = field(default_factory=list)  # 仅 composite：子任务描述


def summary(spec: StageSpec) -> dict:
    """run_started 事件里的 stages[] 元素形状（对齐前端 buildStages 行）。"""
    d: dict[str, Any] = {
        "key": spec.key,
        "name": spec.name,
        "agent": spec.worker,
        "icon": spec.icon,
        "kind": spec.kind,
    }
    if spec.kind == "gate":
        d["gate"] = True
    if spec.subs:
        d["subs"] = [dict(s) for s in spec.subs]
    return d
