"""共享 ASR 核心——bilibili / xiaohongshu / meeting-transcribe 三处复用的转写底座。

原先 demos/bilibili/lib/asr.py 与 demos/xiaohongshu/lib/asr.py 各有一份近乎重复的
`_fmt_ts / _find_yt_dlp / _transcribe`。抽到这里做 SSOT,各 demo 只保留平台专属的
下载逻辑,转写核心统一走本模块。

依赖剖面:仅需 PyAV(faster-whisper transitive 拉入)+ yt-dlp(下载在各 demo 里)。
不需要系统 ffmpeg。首次跑 medium 约 1.5 GB,large-v3 约 3 GB,缓存到 ~/.cache/huggingface/。

HF 模型下载(重要,2026-07-08 纠正):
    不再强制 HF_ENDPOINT=hf-mirror.com。留空 = 直连 huggingface.co(Ona/AWS 容器实测
    正常)。build-cli 中国网络若直连慢/不稳,再 `export HF_ENDPOINT=https://hf-mirror.com`。
    旧代码把 mirror 设成默认,反而是 Ona 上的坑(mirror 时通时不通)。
"""
from __future__ import annotations

import shutil
import subprocess
import sys
from pathlib import Path


def fmt_ts(seconds: float) -> str:
    """秒 → [MM:SS] 时间戳前缀。"""
    m, s = divmod(int(seconds), 60)
    return f"[{m:02d}:{s:02d}]"


def find_yt_dlp() -> str:
    """返回 yt-dlp 路径;找不到抛 FileNotFoundError。"""
    path = shutil.which("yt-dlp")
    if path:
        return path
    candidate = Path.home() / ".local" / "bin" / "yt-dlp"
    if candidate.exists():
        return str(candidate)
    raise FileNotFoundError(
        "yt-dlp 不在 PATH 中。装:pip install --user --break-system-packages yt-dlp"
    )


def run_yt_dlp(cmd: list[str]) -> subprocess.CompletedProcess:
    """跑 yt-dlp 并在非零退出时抛 RuntimeError(截断 stderr)。"""
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        raise RuntimeError(
            f"yt-dlp 失败 (rc={result.returncode}): {result.stderr.strip()[:500]}"
        )
    return result


def load_whisper_model(model_name: str = "medium", device: str = "cpu"):
    """加载 faster-whisper 模型(SSOT:device→compute_type 的选择在这里统一)。

    常驻场景(meeting-transcribe 的 watch-loop)加载一次跨调用复用;一次性转写用
    transcribe_media_file 即可。CPU→int8,GPU→float16。
    """
    from faster_whisper import WhisperModel

    compute_type = "int8" if device == "cpu" else "float16"
    print(f"  [INFO] faster-whisper 加载模型: {model_name} ({compute_type})", file=sys.stderr)
    return WhisperModel(model_name, device=device, compute_type=compute_type)


def transcribe_media_file(
    media_path: Path | str,
    model_name: str = "medium",
    *,
    language: str = "zh",
    with_timestamps: bool = True,
    vad_filter: bool = True,
) -> str:
    """faster-whisper 转写单个媒体文件(音频或含音轨的视频),返回文本。

    PyAV 直接解码 m4a/aac/mp4/webm 等,不依赖系统 ffmpeg。CPU int8。
    """
    model = load_whisper_model(model_name)
    segments, _info = model.transcribe(
        str(media_path),
        language=language,
        vad_filter=vad_filter,
    )
    lines = []
    for seg in segments:
        ts = fmt_ts(seg.start) + " " if with_timestamps else ""
        lines.append(f"{ts}{seg.text.strip()}")
    return "\n".join(lines)
