#!/usr/bin/env python3
"""转写 CLI——本地音频文件 → 文本。可插拔后端 + 可选串联校对。

后端:
  local-whisper (默认)  faster-whisper,本地 CPU,现役唯一可用后端
  galileo-stt            Galileo /audio/transcriptions;当前未部署,会给出清晰指引
                         (开通后即用,见 README「Galileo STT 开通」)

Usage:
    transcribe.py audio.m4a                                # 本地 whisper
    transcribe.py audio.m4a --backend galileo-stt          # Galileo(未部署会明确报)
    transcribe.py audio.m4a --model large-v3 --no-timestamps
    transcribe.py audio.m4a --correct --domain "长征" \\
        --glossary "遵义,滇军,黔军"                          # 转写 + LLM 校对一条龙

注:平台视频抓取(bilibili BV / 小红书链接)走各自 demo 的 extract 脚本,本 CLI 只吃本地文件。
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from lib.asr_core import transcribe_media_file
from lib.correct import correct_transcript
from lib.galileo import GalileoError, GalileoSTTNotProvisioned, transcribe_audio


def main() -> int:
    p = argparse.ArgumentParser(description="音频转写(可插拔后端)+ 可选校对")
    p.add_argument("audio", help="本地音频/视频文件路径")
    p.add_argument(
        "--backend",
        default="local-whisper",
        choices=["local-whisper", "galileo-stt"],
        help="转写后端",
    )
    p.add_argument("--model", default=None, help="模型:local 用 small/medium/large-v3(默认 medium);galileo 用部署名(默认 gpt-4o-transcribe)")
    p.add_argument("--lang", default="zh", help="语言")
    p.add_argument("--no-timestamps", action="store_true", help="关时间戳(仅 local-whisper)")
    p.add_argument("--correct", action="store_true", help="转写后串联 Galileo LLM 校对")
    p.add_argument("--title", help="校对上下文:标题")
    p.add_argument("--domain", help="校对上下文:领域")
    p.add_argument("--glossary", help="校对上下文:术语表(逗号分隔)")
    args = p.parse_args()

    audio = Path(args.audio)
    if not audio.exists():
        print(f"ERROR: 文件不存在: {audio}", file=sys.stderr)
        return 2

    # Stage 1: 转写
    if args.backend == "local-whisper":
        text = transcribe_media_file(
            audio,
            model_name=args.model or "medium",
            language=args.lang,
            with_timestamps=not args.no_timestamps,
        )
    else:  # galileo-stt
        try:
            text = transcribe_audio(
                str(audio), model=args.model or "gpt-4o-transcribe", language=args.lang
            )
        except GalileoSTTNotProvisioned as e:
            print(f"ERROR: {e}", file=sys.stderr)
            return 4
        except GalileoError as e:
            print(f"ERROR: Galileo 转写失败: {e}", file=sys.stderr)
            return 1

    # Stage 2: 可选校对
    if args.correct:
        try:
            result = correct_transcript(
                text, title=args.title, domain=args.domain, glossary=args.glossary
            )
            text = result.corrected
            print(f"[INFO] 校对完成,{len(result.changes)} 处变更", file=sys.stderr)
        except GalileoError as e:
            print(f"WARN: 校对失败,输出未校对文本: {e}", file=sys.stderr)

    print(text)
    return 0


if __name__ == "__main__":
    sys.exit(main())
