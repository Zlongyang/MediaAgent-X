"""对话意图路由（spec §3.2）：判断聊天文本是「单次视频任务」还是「周期工作流」。

有真 LLM 时输出严格 JSON 并直接落 workflows.json（agent 程序化创建入口）；
解析失败 / MockChat / 非法 cron 一律确定性降级 {"kind": "run"}（离线冒烟依赖）。
"""
from __future__ import annotations

import json
import re
import warnings

from agent import workflows_store
from agent.llm import chat

_PROMPT = """你是任务路由器，判断用户输入属于哪一类：
A) 单次视频任务（做一条/生成一个/来一条……）
B) 周期工作流（含「每天/每周/每隔/定时/cron」等周期语义）
只输出一行 JSON，不要输出任何其它文字：
A → {"kind":"run"}
B → {"kind":"workflow","name":"<工作流名，≤12字>","schedule":"<5段cron>","brief":"<周期执行的任务描述>"}
拿不准一律输出 {"kind":"run"}。
用户输入："""

_FENCE = re.compile(r"```(?:json)?")


def classify(text: str, account: str = "none") -> dict:
    """返回 {"kind":"run"} 或 {"kind":"workflow", "workflow": {...}}。永不抛异常。"""
    try:
        raw = chat(_PROMPT + text)
        data = json.loads(_FENCE.sub("", raw).strip())
        if data.get("kind") == "workflow":
            wf = workflows_store.create({
                "name": str(data.get("name") or text[:12]),
                "schedule": str(data.get("schedule") or ""),
                "desc": f"由对话创建：{text}",
                "account": str(data.get("account") or account or "none"),
                "brief": str(data.get("brief") or text),
                "enabled": True,
            })
            return {"kind": "workflow", "workflow": wf}
    except Exception as e:
        warnings.warn(f"workflow_intent 降级 run：{e!r}")
    return {"kind": "run"}


if __name__ == "__main__":
    # MockChat（无 DEEPSEEK_API_KEY）下必须确定性降级 run
    assert classify("做一条数码赛道的短视频") == {"kind": "run"}
    assert classify("每天早上 8 点做一条数码视频") == {"kind": "run"}  # mock 不会输出 JSON
    print("[PASS] workflow_intent 自测通过（MockChat 降级 kind=run）")
