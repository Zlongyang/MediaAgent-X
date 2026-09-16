"""冒烟入口（契约 §9）：python -m agent.cli --mock --auto "做一条数码赛道的短视频"

- --auto（默认开）：四闸门 autonomy=false，全流程自动跑通，退出码 0
- --no-auto：图在 gate_topic interrupt，打印 interrupt 信息与 resume 提示后退出
- --mock：强制 MPT_MODE=mock（默认就是 mock；cli/inproc 需真实 mpt 环境）

resume 提示：跨进程恢复需要 AGENT_SQLITE=1（可选包 langgraph-checkpoint-sqlite）；
同进程恢复范例见 agent/smoke_gates.py。
"""
from __future__ import annotations

import argparse
import os
import sys
import uuid

# --mock 必须在导入 agent 模块前生效（mpt_tools 运行时读 env，双保险）
if "--mock" in sys.argv:
    os.environ["MPT_MODE"] = "mock"
    os.environ.setdefault("AGENT_TEST_DOUBLE", "1")

from agent import config, graph as graph_mod
from agent.state import initial_state

GREEN, RED, YELLOW, DIM, RESET = "\033[32m", "\033[31m", "\033[33m", "\033[2m", "\033[0m"


def _fmt_event(ev: dict, cost_box: dict) -> str | None:
    e, d = ev.get("event"), ev.get("data", {})
    if e == "run_started":
        return f"{DIM}run {d['run_id']} started，{len(d['stages'])} 个节点{RESET}"
    if e == "stage_update":
        icon = {"active": "▶", "done": "✓", "failed": "✗"}.get(d["status"], "·")
        color = {"active": YELLOW, "done": GREEN, "failed": RED}.get(d["status"], DIM)
        tail = f" ({d['duration']})" if d.get("duration") else ""
        note = f" — {d['statusText']}" if d.get("statusText") else ""
        return f"{color}{icon} {d['key']}{tail}{note}{RESET}"
    if e == "sub_update":
        icon = {"active": "▸", "done": "✓", "failed": "✗"}.get(d["status"], "·")
        tail = f" ({d['duration']})" if d.get("duration") else ""
        return f"  {DIM}{icon} {d['parent']}/{d['key']}{tail}{RESET}"
    if e == "gate_request":
        v = d.get("view", {})
        hint = "候选 " + str(len(v.get("candidates", []))) if "candidates" in v else \
               "节选 " + str(len(v.get("excerpt", ""))) + "字" if "excerpt" in v else \
               ("video=" + v.get("video", "")) if "video" in v else \
               ("title=" + v.get("pack", {}).get("title", "")) if "pack" in v else ""
        return f"{YELLOW}⏸ GATE {d['key']}「{d['title']}」nonce={d['nonce']}（{hint}）等待人工决议{RESET}"
    if e == "gate_resolved":
        tag = "自动" if d.get("auto") else "人工"
        return f"{GREEN}✓ GATE {d['key']} nonce={d['nonce']} {d['action']}（{tag}）{RESET}"
    if e == "cost_add":
        for k, v in d.items():
            cost_box[k] = round(cost_box.get(k, 0.0) + v, 4)
        return None
    if e == "artifact_set":
        return f"{DIM}  artifact {d['key']} → {d['path']}{RESET}"
    if e == "message":
        return f"{DIM}[{d['type']}] {d['text']}{RESET}"
    if e == "review_ready":
        return f"{GREEN}★ 复盘就绪：tips {len(d.get('tips', []))} 条，metrics {len(d.get('metrics', []))} 期{RESET}"
    if e == "error":
        return f"{RED}✗ ERROR stage={d.get('stage')}: {d.get('message')}{RESET}"
    return None


def main() -> int:
    p = argparse.ArgumentParser(prog="agent.cli", description="MediaAgent-X LangGraph 冒烟入口")
    p.add_argument("text", help="任务描述，如：做一条数码赛道的短视频")
    p.add_argument("--mock", action="store_true", help="强制 MPT_MODE=mock（默认即 mock）")
    p.add_argument("--account", default="dy-shuma", help="发布账号；传 none 则转手动发布")
    g = p.add_mutually_exclusive_group()
    g.add_argument("--auto", dest="auto", action="store_true", default=True, help="闸门全自动（默认）")
    g.add_argument("--no-auto", dest="auto", action="store_false", help="闸门等人工：interrupt 后打印并退出")
    args = p.parse_args()

    config.ensure_dirs()
    run_id = f"r-{uuid.uuid4().hex[:8]}"
    gph = graph_mod.build_graph()
    cfg = {"configurable": {"thread_id": run_id}}
    state = initial_state(run_id, args.text, account=args.account, auto_mode=args.auto)

    print(f"{DIM}mode: MPT_MODE={config.mpt_mode()}, auto={args.auto}, run_id={run_id}{RESET}")
    cost_box: dict = {}
    input_ = state
    first = True
    exit_code = 0

    while True:
        for ev in graph_mod.iter_run_sync(gph, input_, cfg, started=first):
            line = _fmt_event(ev, cost_box)
            if line:
                print(line)
            if ev.get("event") == "gate_request" and not args.auto:
                d = ev["data"]
                print(f"\n{YELLOW}已暂停在闸门 {d['key']}（nonce={d['nonce']}）。{RESET}")
                print("同进程 resume 范例见 agent/smoke_gates.py；跨进程恢复请置 AGENT_SQLITE=1 后：")
                print(f'  Command(resume={{"action":"confirm","payload":{{...}}}}), '
                      f'config={{"configurable":{{"thread_id": "{run_id}"}}}}')
                return 0  # --no-auto：打印 interrupt 信息后退出
        first = False
        st = gph.get_state(cfg)
        if st.next:
            # auto 模式下不应走到这里（闸门不 interrupt）；防御性退出
            print(f"{RED}意外中断于 {st.next}（auto 模式不应出现）{RESET}")
            return 1
        break

    final = gph.get_state(cfg).values
    status = final.get("status", "unknown")
    if status != "failed":
        project = graph_mod.finalize_project(final)
        print(f"\n{GREEN}■ run_finished status={status}{RESET} "
              f"cost_total={final.get('cost', {}).get('total', 0)}")
        rd = config.run_dir(run_id)
        print(f"工件目录 {rd}：")
        for f in sorted(rd.rglob("*")):
            if f.is_file():
                print(f"  {DIM}{f.relative_to(rd)}{RESET}")
        if project:
            print(f"{DIM}project.json 已落盘（/api/projects 可见）{RESET}")
    else:
        print(f"\n{RED}■ run_finished status=failed error={final.get('error')}{RESET}")
        exit_code = 1
    return exit_code


if __name__ == "__main__":
    sys.exit(main())
