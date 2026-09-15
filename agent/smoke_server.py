"""服务器冒烟（契约 §9.4 / 验收 4）：TestClient 验证 POST /api/runs + SSE 流完一个 auto run。

断言：
- from agent.server import app 可导入（本文件 import 即证）
- POST /api/runs 返回 run_id
- GET /api/runs/{id}/events SSE 首帧即 run_started，且 auto run 能流到 run_finished
- GET /api/runs/{id}/state 返回 MediaState 快照
- GET /api/projects 能扫到刚完成的 run
全程 mock，无 API key / mpt / 网络依赖。

运行：python -m agent.smoke_server
"""
from __future__ import annotations

import json
import sys

from fastapi.testclient import TestClient

from agent.server import app  # noqa: F401  —— 可导入性即验收点之一

PASS, FAIL = "\033[32m[PASS]\033[0m", "\033[31m[FAIL]\033[0m"
_failures: list[str] = []


def check(cond: bool, label: str) -> None:
    print((PASS if cond else FAIL), label)
    if not cond:
        _failures.append(label)


def main() -> int:
    with TestClient(app) as client:
        r = client.post("/api/runs", json={
            "text": "做一条数码赛道的短视频",
            "account": "dy-shuma",
            "autoMode": True,
        })
        check(r.status_code == 200, f"POST /api/runs → 200（实际 {r.status_code}）")
        run_id = r.json().get("run_id", "")
        check(bool(run_id), f"返回 run_id={run_id}")

        # SSE：auto run 一次性流到 run_finished（首帧必须是 run_started）
        events_seen: list[tuple[str, dict]] = []
        with client.stream("GET", f"/api/runs/{run_id}/events") as s:
            check(s.status_code == 200, f"GET /events → 200（实际 {s.status_code}）")
            cur_event = None
            for line in s.iter_lines():
                if line.startswith("event: "):
                    cur_event = line[7:]
                elif line.startswith("data: ") and cur_event:
                    events_seen.append((cur_event, json.loads(line[6:])))
                    cur_event = None
                if events_seen and events_seen[-1][0] == "run_finished":
                    break
        names = [e for e, _ in events_seen]
        check(bool(names) and names[0] == "run_started", f"SSE 首帧 run_started（实际 {names[:1]}）")
        check("run_finished" in names, "SSE 流到 run_finished")
        check(events_seen and events_seen[-1][1].get("status") == "published",
              f"run_finished status=published（实际 {events_seen and events_seen[-1][1].get('status')}）")
        done_stages = {d["key"] for e, d in events_seen
                       if e == "stage_update" and d.get("status") == "done"}
        check(len(done_stages) == 12, f"12 节点全 done（实际 {len(done_stages)}: {sorted(done_stages)}）")
        check("review_ready" in names, "review_ready 已发")

        st = client.get(f"/api/runs/{run_id}/state")
        check(st.status_code == 200 and st.json().get("status") == "published",
              "GET /state 快照 status=published")

        projects = client.get("/api/projects")
        check(projects.status_code == 200, "GET /api/projects → 200")
        check(any(p.get("id") == run_id for p in projects.json()),
              f"/api/projects 扫到 {run_id}")

        # 闸门端点存在性（auto run 已结束，应得到业务层拒绝而非 404/500）
        g = client.post(f"/api/runs/{run_id}/gate", json={"nonce": 1, "action": "confirm"})
        check(g.status_code == 200, "POST /gate 端点可用")

        # ---- 工作流端点（spec §3.2）----
        wf = client.post("/api/workflows", json={
            "name": "冒烟日更", "schedule": "40 7 * * *",
            "account": "dy-shuma", "brief": "做一条数码赛道的短视频",
        })
        check(wf.status_code == 200
              and wf.json().get("workflow", {}).get("id", "").startswith("wf-"),
              "POST /api/workflows 创建成功")
        wf_id = wf.json()["workflow"]["id"]
        bad = client.post("/api/workflows", json={"name": "坏cron", "schedule": "每天早上"})
        check(bad.status_code == 400, f"非法 cron → 400（实际 {bad.status_code}）")
        tg = client.post(f"/api/workflows/{wf_id}/toggle")
        check(tg.status_code == 200 and tg.json().get("enabled") is False,
              "工作流 toggle 翻转为 False")
        rr = client.post(f"/api/workflows/{wf_id}/run")
        check(rr.status_code == 200 and rr.json().get("run_id", "").startswith("r-"),
              "工作流立即运行 → run_id")
        ch = client.post("/api/chat", json={"text": "做一条数码赛道的短视频", "account": "dy-shuma"})
        check(ch.status_code == 200 and ch.json().get("kind") == "run",
              "MockChat 下 /api/chat 降级 kind=run")
        dl = client.delete(f"/api/workflows/{wf_id}")
        check(dl.status_code == 200 and dl.json().get("ok") is True, "DELETE 工作流")
        lst = client.get("/api/workflows")
        check(all(w.get("id") != wf_id for w in lst.json()), "删除后列表已移除")

    print()
    if _failures:
        print(f"{FAIL} {len(_failures)} 项未过：{_failures}")
        return 1
    print(f"{PASS} smoke_server 全部断言通过")
    return 0


if __name__ == "__main__":
    sys.exit(main())
