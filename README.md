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
| ✅ 必需 | Python 3.12（Kimi Work 管理版） | `langgraph / langchain_core / fastapi / uvicorn` **已安装**，无需再装 |
| ⬜ 可选 | `DEEPSEEK_API_KEY` | 不配也能跑：LLM 自动降级为确定性 Mock（离线演示模式） |
| ⬜ 可选 | uv + ffmpeg | 仅「真实出片」需要：给 mpt 配环境用 |
| ⬜ 可选 | mpt 的各 API Key | Pexels 素材 key、LLM key 等，填进 mpt 的 `config.toml`（首次启动自动从 `config.example.toml` 生成） |

## 2. 三种运行形态

### 形态 A：最快体验（零配置，1 分钟）

后端 CLI 全流程冒烟，不需要任何 key、不需要 mpt：

```bash
# 全自动模式：4 道闸门全部自动放行，12 节点跑到底
python -m agent.cli --mock --auto "做一条数码赛道的短视频"
```

跑完后看产物：`workspace/runs/<run_id>/` 下有 `script.md`、`shots.json`、`video/final.mp4`、`review.md` 等。

体验人工闸门：

```bash
python -m agent.cli --mock --no-auto "做一条数码赛道的短视频"
# 停在「选题确认」闸门，打印 resume 提示后退出
# 恢复方法见输出提示（Command(resume=...) + thread_id）
```

### 形态 B：前端 + 后端联调（日常开发）

开两个终端：

```bash
# 终端 1：后端 API + SSE 服务（默认 8000 端口）
uvicorn agent.server:app --host 127.0.0.1 --port 8000

# 终端 2：前端（Vite dev server）
cd web && npm run dev
```

> 注意：当前前端仍是 mock 数据演示（行为已验收），按 [docs/04](docs/04-业务逻辑梳理与后端契约.md) §11 接缝清单把 `App.vue startRun` 换成 SSE 消费即完成接真。

后端 API 一览（契约见 docs/04 §6）：

```
POST /api/runs                    创建并启动一次 run        → {run_id}
GET  /api/runs/{id}/events        SSE 事件流（阶段/闸门/成本/工件）
POST /api/runs/{id}/gate          闸门决议 {nonce, action: confirm|reject, payload?}
GET  /api/runs/{id}/state         MediaState 快照（运行状态面板数据源）
POST /api/runs/{id}/autonomy      切换闸门开关
GET  /api/projects[/{id}]         项目归档（扫描 workspace/runs 重建）
```

### 形态 C：真实出片（接 mpt + 真 LLM）

```bash
# ① 配 mpt 环境（在 MoneyPrinterTurbo/ 下，用它自己的 uv 环境）
cd MoneyPrinterTurbo && uv sync --frozen
#    首次运行自动生成 config.toml，填入 LLM key / Pexels key 等

# ② 配 agent 的 LLM（任选其一）
set DEEPSEEK_API_KEY=sk-...        :: Windows cmd
$env:DEEPSEEK_API_KEY="sk-..."     # PowerShell
export DEEPSEEK_API_KEY=sk-...     # bash

# ③ 切换 mpt 接入模式（默认 mock）
export MPT_MODE=cli                # 子进程调 mpt 的 cli.py --stop-at（推荐先做）
# export MPT_MODE=inproc           # 进程内 import（需 mpt 依赖可被 python 直接 import）

python -m agent.cli --auto "做一条数码赛道的短视频"
```

## 3. 环境变量总表

| 变量 | 默认 | 作用 |
|---|---|---|
| `MPT_MODE` | `mock` | mpt 接入模式：`mock`（确定性演示）/ `cli`（子进程）/ `inproc`（进程内，预留） |
| `DEEPSEEK_API_KEY` | 空 | 有了就走真 DeepSeek；没有自动 Mock，全流程照样跑通 |
| `DEEPSEEK_BASE_URL` | `https://api.deepseek.com` | 可换任意 OpenAI 兼容端点 |
| `DEEPSEEK_MODEL` | `deepseek-chat` | 模型名 |
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
| 演示数据（mock 选题/脚本/分镜） | `agent/tools/mock_content.py` |
| mpt 接入方式 | `agent/tools/mpt_tools.py`（stage 代码无感知） |
| 换 LLM provider | 只动 `agent/llm.py` 的 `chat()` |

## 6. 常见问题

- **`MPT_MODE=cli` 报 `MPTCliError`**：mpt 环境没配好（先做形态 C 的第①步）；报错是刻意的，不会静默降级成 mock。
- **`MPT_MODE=inproc` 报缺 `loguru` 等**：说明当前 Python 不是 mpt 的环境，用 cli 模式或配 mpt 的 venv。
- **断线续跑**：默认内存 checkpointer，重启丢 run；`AGENT_SQLITE=1` 后按 `thread_id` 恢复。
- **端口冲突**：后端换 `--port`，前端 vite 默认 5173，互不冲突。

---

更多设计细节：[docs/README.md](docs/README.md)（设计文档索引）
