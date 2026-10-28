#!/usr/bin/env python3
"""校对 CLI——任何 ASR 文本(文件或 stdin)过 Galileo LLM 纠错,输出干净文本 + 变更日志。

后端无关:bilibili/xhs/meeting/微信语音的转写都能喂进来。

Usage:
    correct_transcript.py <file>                          # 校对文件
    cat asr.txt | correct_transcript.py                   # 读 stdin
    correct_transcript.py <file> --domain "长征/近代军事史" \\
        --glossary "遵义,滇军,黔军,湘军,薛岳,上官云相,陈赓,叙永"
    correct_transcript.py <file> -o clean.txt             # 校对稿落盘(默认 stdout)
    correct_transcript.py <file> --log changes.md         # 变更日志单独落盘
    correct_transcript.py <file> --model gpt-4o-2024-11-20 # 指定校对模型

stdout:校对后的文本。变更日志默认打到 stderr(或 --log 落盘)。
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from lib.correct import DEFAULT_CHAT_MODEL, correct_transcript
from lib.galileo import GalileoError


def main() -> int:
    p = argparse.ArgumentParser(description="ASR 文本 LLM 校对(Galileo)")
    p.add_argument("file", nargs="?", help="待校对文件;省略则读 stdin")
    p.add_argument("--title", help="内容标题(给模型上下文)")
    p.add_argument("--domain", help="领域/主题,如 '长征/近代军事史'")
    p.add_argument("--glossary", help="术语表,逗号分隔的正确写法")
    p.add_argument("--model", default=DEFAULT_CHAT_MODEL, help="校对模型")
    p.add_argument("--chunk-chars", type=int, default=2500, help="分块大小")
    p.add_argument("-o", "--output", help="校对稿落盘路径(默认 stdout)")
    p.add_argument("--log", help="变更日志落盘路径(markdown 表;默认打 stderr)")
    args = p.parse_args()

    if args.file:
        text = Path(args.file).read_text(encoding="utf-8")
    else:
        text = sys.stdin.read()
    if not text.strip():
        print("ERROR: 输入为空", file=sys.stderr)
        return 2

    try:
        result = correct_transcript(
            text,
            title=args.title,
            domain=args.domain,
            glossary=args.glossary,
            model=args.model,
            chunk_chars=args.chunk_chars,
        )
    except GalileoError as e:
        print(f"ERROR: Galileo 校对失败: {e}", file=sys.stderr)
        return 1

    if args.output:
        Path(args.output).write_text(result.corrected + "\n", encoding="utf-8")
        print(f"[INFO] 校对稿 → {args.output}", file=sys.stderr)
    else:
        print(result.corrected)

    log_md = f"# 校对变更日志({len(result.changes)} 处)\n\n{result.change_log_md()}\n"
    if args.log:
        Path(args.log).write_text(log_md, encoding="utf-8")
        print(f"[INFO] 变更日志 → {args.log}（{len(result.changes)} 处）", file=sys.stderr)
    else:
        print(f"\n[INFO] 共 {len(result.changes)} 处变更:", file=sys.stderr)
        print(result.change_log_md(), file=sys.stderr)

    return 0


if __name__ == "__main__":
    sys.exit(main())
