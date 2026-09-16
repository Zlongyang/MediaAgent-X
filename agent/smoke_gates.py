"""闸门人工流脚本化验证（契约 §9.2 / 验收 2）。

流程：
1. autoMode 关（四闸门 autonomy=true），跑到 gate_topic interrupt
2. resume confirm {choice: 候选#2} → 断言 topic 生效
3. gate_script interrupt(nonce=1) → reject → 断言 script_draft 重跑
   → gate_script 以 nonce+1=2 再次 interrupt → confirm {} 继续
4. 后续 gate_preview / gate_publish 直接 confirm，直到 run_finished
全程 mock，无需 API key / mpt / 网络。

运行：python -m agent.smoke_gates
"""
from __future__ import annotations

import os
import sys

os.environ.setdefault("AGENT_TEST_DOUBLE", "1")
os.environ.setdefault("MPT_MODE", "mock")

from langgraph.types import Command

from agent import config
from agent.graph import build_graph, iter_run_sync
from agent.state import initial_state
from agent.tools import mock_content

PASS = "\033[32m[PASS]\033[0m"
FAIL = "\033[31m[FAIL]\033[0m"
_failures: list[str] = []


def check(cond: bool, label: str) -> None:
    print((PASS if cond else FAIL), label)
    if not cond:
        _failures.append(label)


def collect(graph, input_, cfg, first: bool) -> tuple[list[dict], object]:
    """跑一轮 stream，返回（事件列表，中断 payload 或 None）。"""
    evs: list[dict] = []
    gate = None
    for ev in iter_run_sync(graph, input_, cfg, started=first):
        evs.append(ev)
        if ev["event"] == "gate_request":
            gate = ev["data"]
    return evs, gate


def main() -> int:
    config.ensure_dirs()
    run_id = "smoke-gates"
    graph = build_graph()
    cfg = {"configurable": {"thread_id": run_id}}
    state = initial_state(run_id, "做一条数码赛道的短视频",
                          account="dy-shuma", auto_mode=False)

    # ---- 1. 首轮：应在 gate_topic 停下 ----
    evs, gate = collect(graph, state, cfg, first=True)
    check(evs and evs[0]["event"] == "run_started", "run_started 首发")
    check(gate is not None and gate["key"] == "gate_topic", "autoMode 关：停在 gate_topic")
    check(gate and gate["nonce"] == 1, f"gate_topic nonce=1（实际 {gate and gate['nonce']}）")
    check(gate and len(gate["view"].get("candidates", [])) == 3, "gate_topic view 带 3 个候选")
    check(any(e["event"] == "stage_update" and e["data"]["key"] == "trend_scan"
              and e["data"]["status"] == "done" for e in evs), "trend_scan 已 done")

    # ---- 2. confirm {choice:#2} → topic 生效，继续到 gate_script ----
    choice = mock_content.TOPIC_CANDIDATES[1]
    evs, gate = collect(graph, Command(resume={"action": "confirm", "payload": {"choice": choice}}),
                        cfg, first=False)
    check(any(e["event"] == "gate_resolved" and e["data"]["key"] == "gate_topic"
              and e["data"]["action"] == "confirm" and not e["data"]["auto"] for e in evs),
          "gate_topic 人工 confirm 已广播 gate_resolved")
    topic_now = graph.get_state(cfg).values.get("topic", "")
    check(topic_now == choice["title"], f"confirm{{choice}} 生效：topic={topic_now!r}")
    check(gate is not None and gate["key"] == "gate_script" and gate["nonce"] == 1,
          "停在 gate_script nonce=1")
    check(gate and "excerpt" in gate["view"], "gate_script view 带脚本节选 excerpt")

    # ---- 3. gate_script reject → script_draft 重跑 → nonce=2 再弹 ----
    evs, gate = collect(graph, Command(resume={"action": "reject"}), cfg, first=False)
    check(any(e["event"] == "gate_resolved" and e["data"]["action"] == "reject" for e in evs),
          "gate_script reject 已广播")
    reruns = [e for e in evs if e["event"] == "stage_update"
              and e["data"]["key"] == "script_draft" and e["data"]["status"] == "active"]
    check(len(reruns) >= 1, "reject 回边：script_draft 重跑（rerun_to=script_draft）")
    check(gate is not None and gate["key"] == "gate_script" and gate["nonce"] == 2,
          f"gate_script 以 nonce+1=2 再次 interrupt（实际 {gate and gate['nonce']}）")

    # ---- 4. confirm 继续：依次过 gate_preview / gate_publish 到结束 ----
    evs, gate = collect(graph, Command(resume={"action": "confirm", "payload": {}}),
                        cfg, first=False)
    check(any(e["event"] == "stage_update" and e["data"]["key"] == "storyboard"
              and e["data"]["status"] == "done" for e in evs), "storyboard 完成")
    subs_done = {e["data"]["key"] for e in evs if e["event"] == "sub_update"
                 and e["data"]["status"] == "done"}
    check(subs_done == {"terms", "audio", "subtitle", "materials", "video"},
          f"mpt_pipeline 5 子任务全 done（实际 {sorted(subs_done)}）")
    check(gate is not None and gate["key"] == "gate_preview" and gate["nonce"] == 1,
          "停在 gate_preview")
    check(gate and gate["view"].get("video"), "gate_preview view 带成片路径")

    evs, gate = collect(graph, Command(resume={"action": "confirm", "payload": {}}),
                        cfg, first=False)
    check(gate is not None and gate["key"] == "gate_publish" and gate["nonce"] == 1,
          "停在 gate_publish")
    check(gate and gate["view"].get("pack", {}).get("title"), "gate_publish view 带 pack")

    evs, gate = collect(graph, Command(resume={"action": "confirm", "payload": {}}),
                        cfg, first=False)
    final = graph.get_state(cfg)
    check(not final.next, "图已正常 END")
    check(final.values.get("status") == "published",
          f"最终 status=published（实际 {final.values.get('status')}）")
    check(bool(final.values.get("review_report")), "review_report 已写入")

    print()
    if _failures:
        print(f"{FAIL} {len(_failures)} 项未过：{_failures}")
        return 1
    print(f"{PASS} smoke_gates 全部断言通过")
    return 0


if __name__ == "__main__":
    sys.exit(main())
