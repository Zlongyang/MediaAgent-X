"""统一日志（设计目标：一眼看清「真 LLM 还是 Mock、每次调用、每次降级、run 生命周期」）。

- logger 名 "mediaagent"：INFO 级，stderr + 文件双写（workspace/logs/server.log）
- 仅 server（uvicorn）启动时调 setup()；CLI/自测不挂 handler ——
  INFO 静默丢弃、WARNING 走 lastResort 仍可见，不污染 CLI 排版输出
- warnings.captureWarnings(True)：各 stage 的 warnings.warn（降级 fixture 等）并入同一日志

日志里永远不写 API key、不写 prompt 正文（只记字数与耗时）。
"""
from __future__ import annotations

import logging

from agent import config

LOGGER_NAME = "mediaagent"


def get_logger() -> logging.Logger:
    return logging.getLogger(LOGGER_NAME)


def setup() -> logging.Logger:
    """挂 stderr + 文件 handler（幂等）。只在服务进程入口调一次。"""
    log = get_logger()
    if log.handlers:
        return log
    log.setLevel(logging.INFO)
    fmt = logging.Formatter("%(asctime)s %(levelname)-7s %(message)s", datefmt="%H:%M:%S")

    sh = logging.StreamHandler()
    sh.setFormatter(fmt)
    log.addHandler(sh)

    config.LOGS_DIR.mkdir(parents=True, exist_ok=True)
    fh = logging.FileHandler(config.LOG_FILE, encoding="utf-8")
    fh.setFormatter(fmt)
    log.addHandler(fh)

    # warnings.warn（llm 降级 / stage 解析失败降级）统一入日志
    logging.captureWarnings(True)
    pyw = logging.getLogger("py.warnings")
    for h in (sh, fh):
        pyw.addHandler(h)

    return log


if __name__ == "__main__":
    import tempfile
    from pathlib import Path

    config.LOGS_DIR = Path(tempfile.mkdtemp())
    config.LOG_FILE = config.LOGS_DIR / "server.log"
    log = setup()
    assert setup() is log and len(log.handlers) == 2  # 幂等
    log.info("自测消息 in=%d字", 12)
    import warnings

    warnings.warn("自测警告：降级 fixture")
    content = config.LOG_FILE.read_text(encoding="utf-8")
    assert "自测消息" in content and "自测警告" in content
    print("[PASS] logx 自测通过（文件与 stderr 双写、warnings 捕获、幂等）")
