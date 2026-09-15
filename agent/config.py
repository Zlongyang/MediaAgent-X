"""环境开关与路径配置（对应契约 §7.2：LLM key / MPT_MODE / 路径）。

所有“可换”维度集中在这里：
- LLM：有 DEEPSEEK_API_KEY 走真实模型，否则 MockChat（见 llm.py）
- MPT：MPT_MODE = mock | cli | inproc（见 tools/mpt_tools.py）
- checkpointer：AGENT_SQLITE=1 时尝试 SqliteSaver，缺包自动回退 MemorySaver（见 graph.py）
"""
from __future__ import annotations

import os
from pathlib import Path

# ---- 路径（workspace 根 = agent 包的上一级） ----
AGENT_DIR = Path(__file__).resolve().parent
ROOT_DIR = AGENT_DIR.parent
WORKSPACE_DIR = ROOT_DIR / "workspace"
RUNS_DIR = WORKSPACE_DIR / "runs"
PROMPTS_DIR = ROOT_DIR / "prompts"
WORKFLOWS_JSON = WORKSPACE_DIR / "workflows.json"
MONITOR_VIDEOS_JSON = WORKSPACE_DIR / "monitor_videos.json"
# mpt 仓库（本工作区内嵌副本；cli/inproc 模式用，mock 模式不触碰）
MPT_ROOT = ROOT_DIR / "MoneyPrinterTurbo"


def ensure_dirs() -> None:
    RUNS_DIR.mkdir(parents=True, exist_ok=True)


def run_dir(run_id: str) -> Path:
    d = RUNS_DIR / run_id
    d.mkdir(parents=True, exist_ok=True)
    return d


# ---- LLM ----
DEEPSEEK_API_KEY = os.environ.get("DEEPSEEK_API_KEY", "").strip()
DEEPSEEK_BASE_URL = os.environ.get("DEEPSEEK_BASE_URL", "https://api.deepseek.com")
DEEPSEEK_MODEL = os.environ.get("DEEPSEEK_MODEL", "deepseek-chat")


def has_llm_key() -> bool:
    return bool(DEEPSEEK_API_KEY)


# ---- MPT 接入模式：mock（默认，确定性）/ cli（子进程）/ inproc（预留） ----
def mpt_mode() -> str:
    # 运行时读取，允许 cli.py 在启动时改写环境变量
    return os.environ.get("MPT_MODE", "mock").strip().lower() or "mock"


# ---- checkpointer ----
def use_sqlite() -> bool:
    return os.environ.get("AGENT_SQLITE", "").strip() == "1"


SQLITE_PATH = RUNS_DIR / "runs.sqlite"
