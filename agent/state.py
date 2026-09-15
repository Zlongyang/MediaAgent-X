"""MediaState 状态模型（契约 §4）+ reducers + 初始状态工厂。

铁律：工件进文件系统，state 里只放指针（artifacts / review_report 存路径）。
脚本正文进 state 是因为闸门要展示，但不重复进 LLM 对话历史。
"""
from __future__ import annotations

import operator
from typing import Annotated, Any, TypedDict


def _merge_dict(old: dict | None, new: dict | None) -> dict:
    """浅合并 reducer：autonomy / artifacts / gate_nonces 用。"""
    merged = dict(old or {})
    if new:
        merged.update(new)
    return merged


def _sum_cost(old: dict | None, new: dict | None) -> dict:
    """cost 累加 reducer：节点只上报增量 {llm?, material?, tts?}，total 自动重算。"""
    old = old or {}
    new = new or {}
    merged = {}
    for k in ("llm", "material", "tts"):
        merged[k] = round(float(old.get(k, 0.0)) + float(new.get(k, 0.0)), 4)
    merged["total"] = round(sum(merged.values()), 4)
    return merged


class Shot(TypedDict, total=False):
    idx: int
    narration: str
    visual: str
    search: str
    duration: str


class Todo(TypedDict):
    id: int
    text: str
    done: bool


# 固定 6 项待办（对齐前端 ms.todos，App.vue:183-190）
DEFAULT_TODOS: list[Todo] = [
    {"id": 1, "text": "扫描赛道热点", "done": False},
    {"id": 2, "text": "确认选题", "done": False},
    {"id": 3, "text": "输出脚本草稿", "done": False},
    {"id": 4, "text": "分镜与制片", "done": False},
    {"id": 5, "text": "打包与发布", "done": False},
    {"id": 6, "text": "数据监控与复盘", "done": False},
]

DEFAULT_AUTONOMY = {"topic": True, "script": True, "preview": True, "publish": True}


class MediaState(TypedDict, total=False):
    # --- 契约 §4 字段 ---
    run_id: str
    stage: str                      # 当前 stage key
    topic: str
    autonomy: Annotated[dict, _merge_dict]           # {topic,script,preview,publish: bool}
    trend_candidates: list[dict]    # [{title,source,heat,reason}]
    script: str
    script_excerpt: str
    shots: list[Shot]
    cost: Annotated[dict, _sum_cost]                 # {llm,material,tts,total}
    artifacts: Annotated[dict, _merge_dict]          # {audio,subtitle,cover,final} 路径指针
    pack: dict                      # {platform,title,caption,tags[],titleLen,descLen}
    publish_records: Annotated[list[dict], operator.add]
    review_report: str              # 路径
    todos: list[Todo]               # 整表替换
    messages: Annotated[list[dict], operator.add]    # [{type: user/assistant/note, text}]
    status: str                     # running / published / unpublished / failed
    error: str
    # --- 后端内部字段 ---
    brief: str                      # 用户原始需求
    account: str                    # 发布账号（"none" → 不发布）
    gate_nonces: Annotated[dict, _merge_dict]  # 每个闸门已弹次数（nonce 递增）
    metrics_schedule: list[str]     # ["T+1h","T+6h","T+24h","T+7d"]
    metrics_snapshots: list[dict]   # 监控回拉快照（mock）


def mark_todo(todos: list[Todo], todo_id: int) -> list[Todo]:
    """返回勾选了指定 id 的新列表（reducer 是整表替换）。"""
    return [{**t, "done": True if t["id"] == todo_id else t["done"]} for t in todos]


def initial_state(
    run_id: str,
    brief: str,
    account: str = "none",
    autonomy: dict | None = None,
    auto_mode: bool = False,
) -> MediaState:
    """run 的初始状态。auto_mode=True → 四闸门全部自动放行。"""
    auto = dict(DEFAULT_AUTONOMY)
    if autonomy:
        auto.update({k: bool(v) for k, v in autonomy.items() if k in auto})
    if auto_mode:
        auto = {k: False for k in auto}
    return MediaState(
        run_id=run_id,
        stage="idle",
        topic="",
        autonomy=auto,
        trend_candidates=[],
        script="",
        script_excerpt="",
        shots=[],
        cost={"llm": 0.0, "material": 0.0, "tts": 0.0, "total": 0.0},
        artifacts={},
        pack={},
        publish_records=[],
        review_report="",
        todos=[dict(t) for t in DEFAULT_TODOS],
        messages=[{"type": "user", "text": brief}],
        status="running",
        error="",
        brief=brief,
        account=account,
        gate_nonces={},
        metrics_schedule=[],
        metrics_snapshots=[],
    )


def dump_jsonable(state: dict[str, Any]) -> dict[str, Any]:
    """get_state().values 已经是纯 dict；这里只做防御性拷贝。"""
    return dict(state)
