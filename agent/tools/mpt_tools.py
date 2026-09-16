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

import json
import os
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
_CLI_RESULTS: dict[str, dict] = {}  # str(run_dir) → mpt 结果 JSON（单次出片，后续子任务复用）


def _cli_env() -> dict:
    """子进程环境：imageio-ffmpeg 的 ffmpeg 目录前置进 PATH（mpt 按名字调 ffmpeg）。"""
    env = os.environ.copy()
    exe = _ffmpeg_exe()
    if exe:
        env["PATH"] = str(Path(exe).parent) + os.pathsep + env.get("PATH", "")
    env["PYTHONUTF8"] = "1"
    return env


def _cli_stop_at(stop_at: str, extra_args: list[str] | None = None) -> dict:
    """子进程跑 mpt 官方 cli.py 的 stop_at 分段（01 拆解 §2 六级出口）。

    成功返回 stdout 末尾的结果 JSON {"task_id", "result"}；失败抛 MPTCliError。
    """
    cli_py = config.MPT_ROOT / "cli.py"
    if not cli_py.exists():
        raise MPTCliError(f"cli 模式不可用：未找到 mpt 入口 {cli_py}（检查 MPT_ROOT）")
    if shutil.which("uv") is None:
        raise MPTCliError("cli 模式不可用：PATH 中未找到 uv（mpt 官方封装依赖 uv run）")
    cmd = ["uv", "run", "python", "cli.py", "--stop-at", stop_at] + list(extra_args or [])
    try:
        proc = subprocess.run(
            cmd, cwd=str(config.MPT_ROOT), capture_output=True, text=True,
            timeout=3600, env=_cli_env(),
        )
    except subprocess.TimeoutExpired as e:
        raise MPTCliError(f"mpt cli 超时（stop_at={stop_at}）") from e
    except OSError as e:
        raise MPTCliError(f"mpt cli 启动失败（stop_at={stop_at}）：{e}") from e
    if proc.returncode != 0:
        tail = (proc.stderr or proc.stdout or "")[-800:]
        raise MPTCliError(f"mpt cli 失败（stop_at={stop_at}，exit={proc.returncode}）：{tail}")
    # runtime 日志在 stderr；stdout 末尾一行是结果 JSON（01 拆解 §7 B 类契约）
    for line in reversed((proc.stdout or "").strip().splitlines()):
        line = line.strip()
        if line.startswith("{"):
            try:
                return json.loads(line)
            except json.JSONDecodeError:
                continue
    raise MPTCliError(f"mpt cli 未返回结果 JSON（stop_at={stop_at}）：{(proc.stdout or '')[-300:]}")


def _task_dir(run_dir: Path) -> Path:
    """mpt 产物目录：storage/tasks/<uuid>。cli.py 要求 task-id 为合法 UUID，
    用 run_id 确定性派生（uuid5），无需额外映射状态。"""
    return config.MPT_ROOT / "storage" / "tasks" / _task_uuid(run_dir.name)


def _task_uuid(run_id: str) -> str:
    import uuid

    return str(uuid.uuid5(uuid.NAMESPACE_URL, f"mediaagent-x:{run_id}"))


def _plain_narration(text: str) -> str:
    """注入 mpt 的文本必须是纯口播：剥掉 markdown 符号与括号/书名号标注
    （对齐 mpt 自己的脚本后处理语义，01 拆解 §3.1）。分镜 narration 本身
    不含这些符号，此层是 script 兜底路径的防御。"""
    import re as _re

def _plain_narration(text: str) -> str:
    """注入 mpt 的文本必须是纯口播：剥掉 markdown 符号、括号/书名号/引号标注，
    并按 \n\n 分段（对齐 mpt 自己脚本的纯文本段落格式，01 拆解 §3.1——
    edge 字幕匹配器按「段落/句子 vs TTS 词边界」对齐，碎词标签行会导致整段匹配失败）。
    分镜 narration 本身不含这些符号，此层是 script 兜底路径的防御。"""
    import re as _re

    t = _re.sub(r"[#*`|→「」]", "", text)
    t = _re.sub(r"[【\[\(（][^】\]\)）]*[】\]\)）]", "", t)
    t = _re.sub(r"^(画面|台词|镜头|字幕)\s*[:：]\s*", "", t, flags=_re.M)
    lines = []
    for ln in (l.strip() for l in t.splitlines()):
        if not ln or ln in ("画面 台词", "画面  台词"):
            continue
        lines.append(ln)
    return "\n\n".join(lines)


def _cli_full_run(subject: str, script: str, terms: list[str], run_dir: Path) -> dict:
    """单次 stop_at=video 全量出片；结果 JSON 按 run_dir 缓存，后续子任务直接读产物。"""
    key = str(run_dir)
    if key not in _CLI_RESULTS:
        args = ["--video-script", _plain_narration(script), "--video-source", "pexels",
                "--video-aspect", "9:16", "--bgm-type", "none",
                "--task-id", _task_uuid(run_dir.name)]
        if subject:
            args += ["--video-subject", subject]
        if terms:
            args += ["--video-terms", ",".join(t for t in terms if t)]
        out = _cli_stop_at("video", args)
        result = dict(out.get("result") or {})
        result["_task_dir"] = str(_task_dir(run_dir))
        _CLI_RESULTS[key] = result
    return _CLI_RESULTS[key]


def _result_files(result: dict, key: str, glob_pat: str, what: str) -> list[Path]:
    """产物路径：结果 JSON 的字段优先，缺失时 glob 任务目录兜底。"""
    v = result.get(key)
    candidates = [Path(p) for p in (v if isinstance(v, list) else [v]) if p]
    files = [p for p in candidates if p.is_file()]
    if files:
        return files
    task_dir = Path(result["_task_dir"])
    files = sorted(task_dir.glob(glob_pat))
    if files:
        return files
    raise MPTCliError(f"mpt 产物缺失（{what}）：{task_dir}/{glob_pat}")


def _copy_artifact(src: Path, dst: Path, what: str) -> str:
    if not src.is_file():
        raise MPTCliError(f"mpt 产物缺失（{what}）：{src}")
    dst.parent.mkdir(parents=True, exist_ok=True)
    shutil.copyfile(src, dst)
    return str(dst)


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
    """子任务 terms：llm.generate_terms 有序模式（01 拆解 §3.2）。

    cli 模式下由我们自己的 LLM 生成（等价于 mpt 的 terms 生成，且 mpt 全流程
    在 audio 子任务一次跑完时通过 --video-terms 注入）；失败返回 []，
    由 stage 回退到分镜 search 字段。
    """
    mode = config.mpt_mode()
    if mode == "mock":
        return list(mock_content.SEARCH_TERMS)
    if mode == "cli":
        from agent.llm import chat, parse_llm_json

        try:
            raw = chat(user="为下面的短视频脚本生成 6 个 Pexels 素材搜索词，"
                           "JSON 数组，每个词 1-3 个英文单词：\n\n" + script[:1200])
            terms = parse_llm_json(raw)
            if isinstance(terms, list) and terms:
                return [str(t) for t in terms][:8]
        except Exception as e:
            warnings.warn(f"terms: LLM 生成搜索词失败，回退分镜 search：{e!r}")
        return []
    if mode == "inproc":
        _inproc_run("terms")
    raise MPTError(f"未知 MPT_MODE: {mode}")


def synthesize_audio(script: str, run_dir: Path, *, subject: str = "", terms: list[str] | None = None) -> dict:
    """子任务 audio：TTS → artifacts.audio。

    cli 模式：在此触发 mpt 全流程一次跑完（stop_at=video），后续子任务只回读产物。
    """
    mode = config.mpt_mode()
    if mode == "mock":
        return {"audio": _mock_audio(run_dir)}
    if mode == "cli":
        res = _cli_full_run(subject, script, terms or [], run_dir)
        src = _result_files(res, "audio_file", "audio.mp3", "audio")[0]
        return {"audio": _copy_artifact(src, run_dir / "audio" / "voiceover.mp3", "audio")}
    if mode == "inproc":
        _inproc_run("audio")
    raise MPTError(f"未知 MPT_MODE: {mode}")


def make_subtitle(script: str, run_dir: Path) -> dict:
    """子任务 subtitle：→ artifacts.subtitle。"""
    mode = config.mpt_mode()
    if mode == "mock":
        return {"subtitle": _mock_subtitle(run_dir)}
    if mode == "cli":
        res = _cli_full_run("", script, [], run_dir)  # 命中缓存，直接回读
        src = _result_files(res, "subtitle_path", "subtitle.srt", "subtitle")[0]
        return {"subtitle": _copy_artifact(src, run_dir / "subtitle" / "final.srt", "subtitle")}
    if mode == "inproc":
        _inproc_run("subtitle")
    raise MPTError(f"未知 MPT_MODE: {mode}")


def fetch_materials(terms: list[str], run_dir: Path) -> dict:
    """子任务 materials：→ 素材路径列表。"""
    mode = config.mpt_mode()
    if mode == "mock":
        return {"materials": _mock_materials(run_dir)}
    if mode == "cli":
        res = _cli_full_run("", "", [], run_dir)  # 命中缓存
        clips = _result_files(res, "combined_videos", "combined-*.mp4", "materials")
        return {"materials": [_copy_artifact(c, run_dir / "materials" / f"clip-{i}.mp4", "materials")
                              for i, c in enumerate(clips, 1)]}
    if mode == "inproc":
        _inproc_run("materials")
    raise MPTError(f"未知 MPT_MODE: {mode}")


def compose_video(run_dir: Path) -> dict:
    """子任务 video：合成 → artifacts.final。"""
    mode = config.mpt_mode()
    if mode == "mock":
        return {"final": _mock_video(run_dir)}
    if mode == "cli":
        res = _cli_full_run("", "", [], run_dir)  # 命中缓存
        src = _result_files(res, "videos", "final-*.mp4", "final")[0]
        return {"final": _copy_artifact(src, run_dir / "video" / "final.mp4", "final")}
    if mode == "inproc":
        _inproc_run("video")
    raise MPTError(f"未知 MPT_MODE: {mode}")
