"""Merge two transcript markdown files (loopback + mic) by chunk timestamp.

Each ## H:M:S section header from each input is tagged with [loopback] or
[mic] and the merged result is written ordered by timestamp. The merged
transcript inherits frontmatter from the first input (loopback by default)
with `source: merged` and start/end_time spanning both.

Usage:
    python3 merge-transcripts.py \
        --loopback /tmp/meeting-transcript.md \
        --mic /tmp/meeting-transcript-mic.md \
        --output /tmp/meeting-transcript-merged.md
"""
from __future__ import annotations

import argparse
import re
import sys
from dataclasses import dataclass
from pathlib import Path


@dataclass
class Section:
    timestamp: str  # HH:MM:SS
    header: str    # full header line "## HH:MM:SS (lang=zh, 2.3s)"
    body: str      # content after header up to next header or EOF
    source: str    # "loopback" or "mic"


SECTION_RE = re.compile(r"^## (\d{2}:\d{2}:\d{2})", re.MULTILINE)
FRONTMATTER_RE = re.compile(r"^---\n(.*?)\n---\n", re.DOTALL)


def parse_frontmatter(text: str) -> tuple[dict, str]:
    """Return (frontmatter dict, body without frontmatter)."""
    m = FRONTMATTER_RE.match(text)
    if not m:
        return {}, text
    fm = {}
    for line in m.group(1).splitlines():
        if ":" in line:
            k, _, v = line.partition(":")
            fm[k.strip()] = v.strip()
    return fm, text[m.end():]


def parse_sections(body: str, source: str) -> list[Section]:
    """Split body into sections by ## HH:MM:SS headers."""
    matches = list(SECTION_RE.finditer(body))
    sections: list[Section] = []
    for i, m in enumerate(matches):
        ts = m.group(1)
        header_end = body.find("\n", m.start())
        if header_end == -1:
            header_end = len(body)
        header_line = body[m.start():header_end]
        body_end = matches[i + 1].start() if i + 1 < len(matches) else len(body)
        section_body = body[header_end + 1:body_end].rstrip()
        sections.append(Section(timestamp=ts, header=header_line, body=section_body, source=source))
    return sections


def build_frontmatter(loopback_fm: dict, mic_fm: dict) -> str:
    """Merge: take loopback's basics, set source=merged, span start/end times."""
    merged = dict(loopback_fm)
    merged["source"] = "merged"

    def _min(a: str | None, b: str | None) -> str | None:
        if not a or a == "TBD":
            return b
        if not b or b == "TBD":
            return a
        return min(a, b)

    def _max(a: str | None, b: str | None) -> str | None:
        if not a or a == "TBD":
            return b
        if not b or b == "TBD":
            return a
        return max(a, b)

    merged["start_time"] = _min(loopback_fm.get("start_time"), mic_fm.get("start_time")) or "TBD"
    merged["end_time"] = _max(loopback_fm.get("end_time"), mic_fm.get("end_time")) or "TBD"

    lines = ["---"]
    for k in ("date", "start_time", "end_time", "timezone", "source", "model"):
        if k in merged:
            lines.append(f"{k}: {merged[k]}")
    lines.append("---")
    return "\n".join(lines) + "\n"


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--loopback", required=True, help="Loopback transcript path")
    ap.add_argument("--mic", required=True, help="Mic transcript path")
    ap.add_argument("--output", default="/tmp/meeting-transcript-merged.md",
                    help="Merged transcript output path")
    args = ap.parse_args()

    lp_text = Path(args.loopback).read_text()
    mc_text = Path(args.mic).read_text()

    lp_fm, lp_body = parse_frontmatter(lp_text)
    mc_fm, mc_body = parse_frontmatter(mc_text)

    lp_sections = parse_sections(lp_body, "loopback")
    mc_sections = parse_sections(mc_body, "mic")

    all_sections = sorted(lp_sections + mc_sections, key=lambda s: s.timestamp)
    if not all_sections:
        sys.exit("no sections found in either transcript")

    merged_fm = build_frontmatter(lp_fm, mc_fm)

    out = [merged_fm, "", f"# Meeting transcript (merged: loopback + mic)", ""]
    for sec in all_sections:
        # Inject [source] tag into header right after timestamp
        new_header = sec.header.replace(
            f"## {sec.timestamp}",
            f"## {sec.timestamp} [{sec.source}]",
            1,
        )
        out.append(new_header)
        out.append(sec.body)
        out.append("")

    Path(args.output).write_text("\n".join(out) + "\n")
    print(f"merged {len(lp_sections)} loopback + {len(mc_sections)} mic sections → {args.output}")


if __name__ == "__main__":
    main()
