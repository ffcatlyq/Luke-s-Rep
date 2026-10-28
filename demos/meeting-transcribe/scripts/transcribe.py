"""WSL-side: watch a directory for new wav chunks, transcribe with
faster-whisper, append to a transcript markdown file with YAML frontmatter.

Usage:
    # Default: loopback (other people's voice)
    python3 transcribe.py

    # Mic (your own voice) — point at separate watch dir + output file
    python3 transcribe.py \
        --watch-dir /mnt/c/temp/meeting-audio-mic \
        --output /tmp/meeting-transcript-mic.md \
        --source local-mic

    # Larger model
    python3 transcribe.py --model medium --lang zh

Frontmatter is written on first chunk, with start_time / end_time / timezone /
source / model. end_time is updated in place after every chunk so a downstream
tool can compute the meeting window without parsing every section header.
"""
from __future__ import annotations

import argparse
import datetime
import re
import sys
import textwrap
import time
import zoneinfo
from pathlib import Path

# 复用跨 demo 的共享 ASR 核心(模型加载 SSOT + HF 下载策略说明)
sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))
from transcribe.lib.asr_core import load_whisper_model

POLL_SEC = 3


def load_processed(log: Path) -> set[str]:
    if not log.exists():
        return set()
    return set(log.read_text().splitlines())


def mark_processed(log: Path, name: str) -> None:
    with log.open("a") as f:
        f.write(name + "\n")


def parse_chunk_timestamp(stem: str, tz: zoneinfo.ZoneInfo) -> datetime.datetime | None:
    # Stem format: chunk_YYYYMMDD_HHMMSS
    m = re.match(r"chunk_(\d{8})_(\d{6})", stem)
    if not m:
        return None
    date_s, time_s = m.groups()
    try:
        dt = datetime.datetime.strptime(date_s + time_s, "%Y%m%d%H%M%S")
        return dt.replace(tzinfo=tz)
    except ValueError:
        return None


def write_initial_frontmatter(transcript: Path, tz_name: str, source: str, model: str, compute_type: str) -> None:
    today = datetime.date.today().isoformat()
    placeholder = "TBD"
    body = textwrap.dedent(f"""\
        ---
        date: {today}
        start_time: {placeholder}
        end_time: {placeholder}
        timezone: {tz_name}
        source: {source}
        model: {model}-{compute_type}
        ---

        # Meeting transcript ({datetime.datetime.now().isoformat(timespec='seconds')})

        """)
    transcript.write_text(body)


def update_frontmatter_times(transcript: Path, start_iso: str | None, end_iso: str) -> None:
    text = transcript.read_text()
    if start_iso is not None:
        text = re.sub(r"^start_time: .*$", f"start_time: {start_iso}", text, count=1, flags=re.MULTILINE)
    text = re.sub(r"^end_time: .*$", f"end_time: {end_iso}", text, count=1, flags=re.MULTILINE)
    transcript.write_text(text)


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--model", default="small",
                    choices=["tiny", "base", "small", "medium", "large-v3"])
    ap.add_argument("--lang", default="auto")
    ap.add_argument("--device", default="cpu", choices=["cpu", "cuda"])
    ap.add_argument("--watch-dir", default="/mnt/c/temp/meeting-audio",
                    help="Directory to watch for chunk_*.wav files")
    ap.add_argument("--output", default="/tmp/meeting-transcript.md",
                    help="Output transcript markdown path")
    ap.add_argument("--source", default="local-loopback",
                    choices=["local-loopback", "local-mic", "external-vtt"],
                    help="Audio source label (written to frontmatter)")
    ap.add_argument("--timezone", default="Asia/Shanghai",
                    help="IANA timezone for chunk timestamps (e.g. Asia/Shanghai)")
    ap.add_argument("--processed-log", default=None,
                    help="Path to processed-files log; defaults to <output>.processed")
    args = ap.parse_args()

    watch_dir = Path(args.watch_dir)
    transcript = Path(args.output)
    processed_log = Path(args.processed_log) if args.processed_log else Path(str(transcript) + ".processed")

    try:
        tz = zoneinfo.ZoneInfo(args.timezone)
    except zoneinfo.ZoneInfoNotFoundError:
        print(f"unknown timezone: {args.timezone}", file=sys.stderr)
        sys.exit(2)

    print(f"loading faster-whisper model={args.model} device={args.device} ...")
    compute_type = "int8" if args.device == "cpu" else "float16"
    model = load_whisper_model(args.model, device=args.device)
    print(f"model loaded.")
    print(f"watch:      {watch_dir}")
    print(f"transcript: {transcript}")
    print(f"source:     {args.source}")
    print(f"timezone:   {args.timezone}")
    print(f"poll:       every {POLL_SEC}s\n")

    if not transcript.exists():
        write_initial_frontmatter(transcript, args.timezone, args.source, args.model, compute_type)

    processed = load_processed(processed_log)
    start_set = bool(re.search(r"^start_time: (?!TBD$).+$", transcript.read_text(), re.MULTILINE))

    while True:
        try:
            chunks = sorted(watch_dir.glob("chunk_*.wav"))
        except FileNotFoundError:
            chunks = []

        new = [c for c in chunks if c.name not in processed]
        for c in new:
            # wait until file is fully written (size stable for >1s)
            try:
                s1 = c.stat().st_size
                time.sleep(0.5)
                s2 = c.stat().st_size
                if s1 != s2:
                    continue  # still being written; revisit next loop
            except FileNotFoundError:
                continue

            t0 = time.time()
            kwargs = {"beam_size": 1, "vad_filter": True}
            if args.lang != "auto":
                kwargs["language"] = args.lang

            segments, info = model.transcribe(str(c), **kwargs)

            chunk_dt = parse_chunk_timestamp(c.stem, tz)
            if chunk_dt:
                ts_pretty = chunk_dt.strftime("%H:%M:%S")
                ts_iso = chunk_dt.isoformat()
            else:
                ts_pretty = c.stem.replace("chunk_", "")
                ts_iso = ts_pretty

            lines = []
            for seg in segments:
                txt = seg.text.strip()
                if txt:
                    lines.append(txt)

            elapsed = time.time() - t0

            with transcript.open("a") as f:
                f.write(f"\n## {ts_pretty} (lang={info.language}, {elapsed:.1f}s)\n")
                if lines:
                    f.write("\n".join(lines) + "\n")
                else:
                    f.write("[no speech detected]\n")

            update_frontmatter_times(
                transcript,
                start_iso=None if start_set else ts_iso,
                end_iso=ts_iso,
            )
            start_set = True

            print(f"[{ts_pretty}] {c.name} → {len(lines)} segments ({elapsed:.1f}s, lang={info.language})")
            for line in lines[:3]:
                print(f"    {line[:80]}")

            mark_processed(processed_log, c.name)
            processed.add(c.name)

        time.sleep(POLL_SEC)


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\nstopped.")
        sys.exit(0)
