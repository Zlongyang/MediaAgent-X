"""mpt 接入层（契约 §8）：mock / cli / inproc 三模式，MPT_MODE 一键切换。

- mock（默认）：确定性 fixture，秒回；占位工件写到 workspace/runs/<run_id>/。
  有 imageio-ffmpeg 时 final.mp4/voiceover.mp3 用内置 ffmpeg 合成为**真实可播**文件
  （镜头色卡 + SHOT i/n 字幕卡），否则回退占位字节并 warn。
- cli：子进程 `uv run python cli.py --stop-at X`（参考 01 拆解 §7 B 类 / mpt 官方
  docs/skill/mpt_agent.py 的封装）。环境不通时明确报 MPTCliError，绝不静默降级 mock。
- inproc：import app.services（sys.path 注入 mpt 根，MemoryState 隔离），一期预留接口。

stage 代码只调下面 5 个函数，不感知模式差异（契约 §7.2 可拆解性第 4 条）。
"""
from __future__ import annotations

import shutil
import subprocess
import sys
import warnings
from pathlib import Path

from agent import config
from agent.tools import mock_content


class MPTError(RuntimeError):
    """mpt 接入层统一错误。"""


class MPTCliError(MPTError):
    """cli 模式环境不通 / 执行失败（明确报错，不降级）。"""


class MPTInprocError(MPTError):
    """inproc 模式不可用（一期预留）。"""


# ---------------------------------------------------------------- cli 模式
def _cli_stop_at(stop_at: str, extra_args: list[str] | None = None) -> None:
    """子进程跑 mpt 官方 cli.py 的 stop_at 分段（01 拆解 §2 六级出口）。"""
    cli_py = config.MPT_ROOT / "cli.py"
    if not cli_py.exists():
        raise MPTCliError(f"cli 模式不可用：未找到 mpt 入口 {cli_py}（检查 MPT_ROOT）")
    if shutil.which("uv") is None:
        raise MPTCliError("cli 模式不可用：PATH 中未找到 uv（mpt 官方封装依赖 uv run）")
    cmd = ["uv", "run", "python", "cli.py", "--stop-at", stop_at] + list(extra_args or [])
    try:
        proc = subprocess.run(
            cmd, cwd=str(config.MPT_ROOT), capture_output=True, text=True, timeout=1800
        )
    except subprocess.TimeoutExpired as e:
        raise MPTCliError(f"mpt cli 超时（stop_at={stop_at}）") from e
    except OSError as e:
        raise MPTCliError(f"mpt cli 启动失败（stop_at={stop_at}）：{e}") from e
    if proc.returncode != 0:
        tail = (proc.stderr or proc.stdout or "")[-500:]
        raise MPTCliError(f"mpt cli 失败（stop_at={stop_at}，exit={proc.returncode}）：{tail}")


# ---------------------------------------------------------------- inproc 模式
def _inproc_run(stop_at: str) -> None:
    """一期预留：sys.path 注入 mpt 根后 import app.services，MemoryState 隔离。"""
    try:
        if str(config.MPT_ROOT) not in sys.path:
            sys.path.insert(0, str(config.MPT_ROOT))
        import app.services.task  # noqa: F401
    except ImportError as e:
        raise MPTInprocError(f"inproc 模式不可用：无法 import app.services（{e}）") from e
    raise MPTInprocError("inproc 模式为一期预留接口，暂未实现编排调用；请用 mock 或 cli。")


# ---------------------------------------------------------------- mock 模式
def _write(path: Path, data: bytes) -> str:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(data)
    return str(path)


def _ffmpeg_exe() -> str | None:
    """imageio-ffmpeg 的内置静态 ffmpeg（免系统安装）；缺包返回 None。"""
    try:
        import imageio_ffmpeg

        return imageio_ffmpeg.get_ffmpeg_exe()
    except Exception:
        return None


def _sec(d) -> float:
    try:
        return max(0.5, float(str(d).rstrip("s").strip()))
    except (TypeError, ValueError):
        return 3.0


_SLATE_COLORS = ["0x1f6feb", "0x8957e5", "0x1a7f37", "0xbf8700", "0xcf222e", "0x0a7ea4", "0x6e7781", "0x8250df"]


def _render_mock_video(shots: list[dict], out: Path) -> bool:
    """用 ffmpeg 把分镜表渲染成镜头色卡视频（真实可播 mp4）。失败返回 False。"""
    exe = _ffmpeg_exe()
    if not exe:
        return False
    out.parent.mkdir(parents=True, exist_ok=True)
    n = len(shots)
    inputs: list[str] = []
    filters: list[str] = []
    font = "fontfile='C\\:/Windows/Fonts/arial.ttf':"
    for i, s in enumerate(shots):
        dur = _sec(s.get("duration"))
        color = _SLATE_COLORS[i % len(_SLATE_COLORS)]
        inputs += ["-f", "lavfi", "-i", f"color=c={color}:s=1080x1920:d={dur}"]
        text = f"MOCK SHOT {i + 1}/{n}  ·  {dur:g}s"
        filters.append(f"[{i}]drawtext={font}text='{text}':fontcolor=white:fontsize=64:"
                       f"x=(w-text_w)/2:y=(h-text_h)/2[v{i}]")
    concat = "".join(f"[v{i}]" for i in range(n)) + f"concat=n={n}:v=1:a=0[out]"
    cmd = [exe, "-y", *inputs, "-filter_complex", ";".join(filters) + ";" + concat,
           "-map", "[out]", "-c:v", "libx264", "-preset", "ultrafast",
           "-pix_fmt", "yuv420p", "-movflags", "+faststart", str(out)]
    try:
        proc = subprocess.run(cmd, capture_output=True, text=True, timeout=300)
    except (OSError, subprocess.TimeoutExpired):
        return False
    if proc.returncode != 0:
        # 字体/drawtext 兼容性兜底：去掉 drawtext 纯上色卡
        if "drawtext" in "".join(filters):
            plain = "".join(f"[{i}]" for i in range(n)) + f"concat=n={n}:v=1:a=0[out]"
            cmd2 = [exe, "-y", *inputs, "-filter_complex", plain,
                    "-map", "[out]", "-c:v", "libx264", "-preset", "ultrafast",
                    "-pix_fmt", "yuv420p", str(out)]
            try:
                proc = subprocess.run(cmd2, capture_output=True, text=True, timeout=300)
            except (OSError, subprocess.TimeoutExpired):
                return False
            if proc.returncode != 0:
                return False
        else:
            return False
    # 校验产物真的是 mp4（ftyp box）
    try:
        return out.is_file() and b"ftyp" in out.read_bytes()[:16]
    except OSError:
        return False


def _render_mock_audio(seconds: float, out: Path) -> bool:
    """生成与片长一致的静音 mp3（真实可播）。失败返回 False。"""
    exe = _ffmpeg_exe()
    if not exe:
        return False
    out.parent.mkdir(parents=True, exist_ok=True)
    cmd = [exe, "-y", "-f", "lavfi", "-i", "anullsrc=r=44100:cl=stereo",
           "-t", f"{max(1.0, seconds):g}", "-q:a", "9", str(out)]
    try:
        proc = subprocess.run(cmd, capture_output=True, text=True, timeout=120)
    except (OSError, subprocess.TimeoutExpired):
        return False
    return proc.returncode == 0 and out.is_file() and out.stat().st_size > 200


def _mock_audio(run_dir: Path) -> str:
    out = run_dir / "audio" / "voiceover.mp3"
    total = sum(_sec(s.get("duration")) for s in mock_content.SHOTS)
    if _render_mock_audio(total, out):
        return str(out)
    warnings.warn("mock audio: ffmpeg 不可用，回退占位字节")
    return _write(out, mock_content.MOCK_AUDIO_BYTES)


def _mock_subtitle(run_dir: Path) -> str:
    return _write(run_dir / "subtitle" / "final.srt", mock_content.MOCK_SRT.encode("utf-8"))


def _mock_materials(run_dir: Path) -> list[str]:
    return [
        _write(run_dir / "materials" / f"clip-{s['idx']}.mp4", f"MOCK-MATERIAL {s['search']}\n".encode())
        for s in mock_content.SHOTS
    ]


def _mock_video(run_dir: Path) -> str:
    out = run_dir / "video" / "final.mp4"
    if _render_mock_video(list(mock_content.SHOTS), out):
        return str(out)
    warnings.warn("mock video: ffmpeg 不可用，回退占位字节")
    return _write(out, mock_content.MOCK_VIDEO_BYTES)


# ---------------------------------------------------------------- 对外 API
def generate_terms(subject: str, script: str) -> list[str]:
    """子任务 terms：llm.generate_terms 有序模式（01 拆解 §3.2）。"""
    mode = config.mpt_mode()
    if mode == "mock":
        return list(mock_content.SEARCH_TERMS)
    if mode == "cli":
        _cli_stop_at("terms", ["--video-subject", subject])
        raise MPTCliError("cli 模式 terms 结果需从 mpt storage 回读，一期未接；请用 mock。")
    if mode == "inproc":
        _inproc_run("terms")
    raise MPTError(f"未知 MPT_MODE: {mode}")


def synthesize_audio(script: str, run_dir: Path) -> dict:
    """子任务 audio：stop_at='audio'（TTS）→ artifacts.audio。"""
    mode = config.mpt_mode()
    if mode == "mock":
        return {"audio": _mock_audio(run_dir)}
    if mode == "cli":
        _cli_stop_at("audio")
        raise MPTCliError("cli 模式 audio 产物需从 mpt storage 回读，一期未接；请用 mock。")
    if mode == "inproc":
        _inproc_run("audio")
    raise MPTError(f"未知 MPT_MODE: {mode}")


def make_subtitle(script: str, run_dir: Path) -> dict:
    """子任务 subtitle：stop_at='subtitle' → artifacts.subtitle。"""
    mode = config.mpt_mode()
    if mode == "mock":
        return {"subtitle": _mock_subtitle(run_dir)}
    if mode == "cli":
        _cli_stop_at("subtitle")
        raise MPTCliError("cli 模式 subtitle 产物需从 mpt storage 回读，一期未接；请用 mock。")
    if mode == "inproc":
        _inproc_run("subtitle")
    raise MPTError(f"未知 MPT_MODE: {mode}")


def fetch_materials(terms: list[str], run_dir: Path) -> dict:
    """子任务 materials：stop_at='materials' → 素材路径列表。"""
    mode = config.mpt_mode()
    if mode == "mock":
        return {"materials": _mock_materials(run_dir)}
    if mode == "cli":
        _cli_stop_at("materials")
        raise MPTCliError("cli 模式 materials 产物需从 mpt storage 回读，一期未接；请用 mock。")
    if mode == "inproc":
        _inproc_run("materials")
    raise MPTError(f"未知 MPT_MODE: {mode}")


def compose_video(run_dir: Path) -> dict:
    """子任务 video：stop_at='video'（合成）→ artifacts.final。"""
    mode = config.mpt_mode()
    if mode == "mock":
        return {"final": _mock_video(run_dir)}
    if mode == "cli":
        _cli_stop_at("video")
        raise MPTCliError("cli 模式 video 产物需从 mpt storage 回读，一期未接；请用 mock。")
    if mode == "inproc":
        _inproc_run("video")
    raise MPTError(f"未知 MPT_MODE: {mode}")
