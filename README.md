# MediaAgent-X · 运行指南

> 「AI 总编」自媒体流水线：选题猎手 → 编剧 → 分镜师 → 制片 → 包装师 → 发行人 → 分析师，
> 关键节点由人工闸门（Gate）确认。本文件回答一个问题：**把这个项目跑起来需要干什么。**

## 0. 这个项目由什么组成

| 目录 | 角色 | 技术栈 |
|---|---|---|
| `web/` | 前端工作台（对话 + 流水线可视化 + 闸门卡片 + 项目归档） | Vue 3.5 + Vite 6 |
| `agent/` | 后端智能体（12 节点流水线 + 4 闸门 + SSE 服务） | Python + LangGraph + FastAPI |
| `MoneyPrinterTurbo/` | 视频生成引擎（被 agent 当 SDK 调，**不改其源码**） | Python + uv（它自己的环境） |
| `prompts/` | 可编辑人设：总编 SYSTEM.md + 7 个子代理 md | 纯文本，直接改 |
| `docs/` | 设计文档（01 mpt 拆解 / 02 选型 / 03 方案 / 04 业务契约 / FRONTEND.md） | — |
| `workspace/` | 运行产物（每次 run 的脚本/分镜/视频/复盘落盘于此） | 自动生成 |

## 1. 前置要求

| 必需性 | 依赖 | 说明 |
|---|---|---|
| ✅ 必需 | Node.js + npm | 跑前端（`web/` 依赖已装好，可 `npm i` 重建） |
| ✅ 必需 | Python 3.12（项目 `.venv`，`uv venv` 重建） | `langgraph / langchain_core / fastapi / uvicorn / langchain-openai / imageio-ffmpeg` |
| ✅ 必需 | `DEEPSEEK_API_KEY` | **mock 模式已移除**：无 key 时后端明确报错（`missing-key`）。可配 `DEEPSEEK_BASE_URL`/`DEEPSEEK_MODEL` 换任意 OpenAI 兼容端点 |
| ✅ 出片必需 | mpt 的 API Key | Pexels 素材 key 等，填进 `MoneyPrinterTurbo/config.toml`（`video_source=pexels`）；TTS 用 edge-tts 免费无需 key |
| ⬜ 可选 | uv | mpt 子进程调用链（`uv run python cli.py`）依赖它 |
| ⬜ 可选 | `AGENT_TEST_DOUBLE=1` | 离线测试替身（MockChat + MPT 占位视频），仅供冒烟/e2e/无网演示，**不属于产品运行形态** |

## 2. 两种运行形态

### 形态 A：离线冒烟（测试替身，零配置）

后端 CLI 全流程冒烟，不需要任何 key、不需要真 mpt：

```bash
# --mock = 开启测试替身（AGENT_TEST_DOUBLE + MPT_MODE=mock），确定性假数据
python -m agent.cli --mock --auto "做一条数码赛道的短视频"
```

跑完后看产物：`workspace/runs/<run_id>/` 下有 `script.md`、`shots.json`、`video/final.mp4`（内置 ffmpeg 合成的色卡占位片）、`review.md` 等。

### 形态 B：前端 + 后端（真实运行，日常形态）

```bash
# ① mpt 首次准备（在 MoneyPrinterTurbo/ 下）：uv sync --frozen，
#    并把 Pexels key 填进 config.toml（llm_provider=deepseek 时填 deepseek_api_key）
# ② 配 agent 的 LLM
export DEEPSEEK_API_KEY=sk-...

# 终端 1：后端 API + SSE 服务（默认 8000 端口；MPT_MODE 默认 cli=真实出片）
PYTHONUTF8=1 .venv/Scripts/python.exe -m uvicorn agent.server:app --host 127.0.0.1 --port 8000

# 终端 2：前端（Vite dev server，已配 /api → 127.0.0.1:8000 代理，可用 VITE_API_TARGET 改）
cd web && npm run dev
```

前端只有真实模式：对话框发起真实 run（真 LLM 写选题/脚本/分镜，mpt 真出片——60s 视频约 10-20 分钟），SSE 驱动流水线/闸门/成本；后端不可达时**诚实报错**（不再降级假数据）。

对话框除了发起单次任务，还能建工作流（如「每天早上 8 点做一条数码视频」→ LLM 意图路由自动建成 cron 工作流；判不准降级为普通 run）。工作流管理在「已安排工作流」页：新建/删除/启停/立即运行（立即运行 = 真实触发一条 run）。

视频：成片闸门与项目页「视频产出」是**真播放器**（工件经 `GET /api/runs/{id}/artifacts/` 提供）。侧栏项目行悬停出垃圾桶，两步确认删除（进行中 run 拒删）。

后端 API 一览（契约见 docs/04 §6）：

```
POST /api/runs                    创建并启动一次 run        → {run_id}
GET  /api/runs/{id}/events        SSE 事件流（阶段/闸门/成本/工件）
POST /api/runs/{id}/gate          闸门决议 {nonce, action: confirm|reject, payload?}
GET  /api/runs/{id}/state         MediaState 快照（运行状态面板数据源）
POST /api/runs/{id}/autonomy      切换闸门开关
GET  /api/runs/{id}/artifacts/... 工件文件服务（前端播放器数据源）
POST /api/chat                    对话意图路由 → {kind:'run'} | {kind:'workflow', workflow}
GET  /api/projects[/{id}]         项目归档（扫描 workspace/runs 重建）
POST /api/projects/{id}/publish   手动发布（unpublished → published）
DELETE /api/projects/{id}         删除归档项目（进行中 run 拒删 409）
GET  /api/workflows               工作流列表（workspace/workflows.json）
POST /api/workflows               新建工作流 {name, desc, schedule, account, brief?, enabled?}
DELETE /api/workflows/{id}        删除工作流
POST /api/workflows/{id}/toggle   启停切换
POST /api/workflows/{id}/run      立即运行 → {ok, run_id}（真实触发）
GET  /api/monitor/videos          数据监控（读 workspace/monitor_videos.json，空则 []）
GET  /api/health                  健康检查（含 llm: 模型名|missing-key|test-double, mpt 模式）
```

## 3. 环境变量总表

| 变量 | 默认 | 作用 |
|---|---|---|
| `DEEPSEEK_API_KEY` | 空 | **必需**：缺失时 `chat()` 明确报错，health 报 `missing-key` |
| `DEEPSEEK_BASE_URL` | `https://api.deepseek.com` | 可换任意 OpenAI 兼容端点 |
| `DEEPSEEK_MODEL` | `deepseek-chat` | 模型名 |
| `MPT_MODE` | `cli` | mpt 接入模式：`cli`（子进程真实出片）/ `inproc`（进程内，预留）。`mock` 仅测试替身可用 |
| `AGENT_TEST_DOUBLE` | 关 | `=1` 时启用测试替身（MockChat + MPT 占位视频），供冒烟/e2e 离线确定性运行 |
| `AGENT_SQLITE` | 关 | `=1` 时用 SQLite 持久化运行状态（需 `pip install langgraph-checkpoint-sqlite`，缺包自动回退内存版） |

## 4. 常用命令速查

```bash
# 后端冒烟（验收用，全离线）
python -m agent.cli --mock --auto "任务描述"     # 全流程自动
python -m agent.smoke_gates                     # 闸门协议 21 项断言
python -m agent.smoke_server                    # API/SSE 12 项断言

# 单节点独立自测（可拆解性：每个 stage 都能单独跑）
python -m agent.stages.trend_scan --mock
python -m agent.stages.storyboard --mock

# 后端服务
uvicorn agent.server:app --host 127.0.0.1 --port 8000

# 前端
cd web && npm run dev          # 开发
cd web && npm run build        # 构建
```

## 5. 改行为去哪改（不动框架）

| 想改什么 | 改哪里 |
|---|---|
| 子代理人设/风格 | `prompts/subagents/*.md`、`prompts/SYSTEM.md`（运行时读取，改完即生效） |
| 增删流水线节点 | `agent/stages/` 加一个文件 + `agent/stages/__init__.py` 的 `STAGE_REGISTRY` 注册一行 |
| 测试夹具（替身输出/冒烟 fixture） | `agent/tools/mock_content.py`（仅 `AGENT_TEST_DOUBLE=1` 时使用） |
| mpt 接入方式 | `agent/tools/mpt_tools.py`（stage 代码无感知） |
| 换 LLM provider | 只动 `agent/llm.py` 的 `chat()` |

## 6. 常见问题

- **`RuntimeError: 未配置 DEEPSEEK_API_KEY`**：mock 模式已移除，先配 key（或离线测试置 `AGENT_TEST_DOUBLE=1`）。
- **`MPT_MODE=cli` 报 `MPTCliError`**：mpt 环境没配好（先做形态 B 的第①步）；报错是刻意的，不会静默降级。
- **出片很慢**：真实出片 = Pexels 下载 + TTS + 合成编码，60s 视频约 10-20 分钟，属正常。
- **`MPT_MODE=inproc` 报缺 `loguru` 等**：说明当前 Python 不是 mpt 的环境，用 cli 模式或配 mpt 的 venv。
- **断线续跑**：默认内存 checkpointer，重启丢 run；`AGENT_SQLITE=1` 后按 `thread_id` 恢复。
- **端口冲突**：后端换 `--port`，前端 vite 默认 5173，互不冲突。

---

更多设计细节：[docs/README.md](docs/README.md)（设计文档索引）
