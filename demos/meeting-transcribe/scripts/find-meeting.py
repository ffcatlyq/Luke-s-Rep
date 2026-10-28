"""Find Calendar events overlapping a time window.

Given a [start, end] window (typically the meeting transcript's first chunk
to last chunk), query Calendar.events.list and return candidate events as
JSON to stdout.

Usage:
    python3 find-meeting.py --start 2026-05-25T11:00:00+08:00 --end 2026-05-25T11:18:00+08:00

    # Widen window by N minutes on each side (default 15)
    python3 find-meeting.py --start ... --end ... --pad-minutes 15

    # Limit to specific calendar (default: 'primary')
    python3 find-meeting.py --start ... --end ... --calendar primary

Output (JSON to stdout):
    [
      {
        "id": "abc123",
        "title": "IMP subsidy meeting",
        "start": "2026-05-25T11:00:00+08:00",
        "end": "2026-05-25T11:30:00+08:00",
        "organizer": "rong.fu@roche.com",
        "attendee_count": 5,
        "attendee_emails": [...],
        "location": "Meet link or room",
        "html_link": "https://calendar.google.com/..."
      },
      ...
    ]

Exit codes:
    0 — success (may be empty list if no candidates)
    1 — Calendar API error
    2 — bad arguments
"""
from __future__ import annotations

import argparse
import datetime
import json
import sys
from pathlib import Path

# Add gw_client to path
_HERE = Path(__file__).resolve().parent
_GW_SCRIPTS = _HERE.parent.parent / "google-workspace" / "scripts"
sys.path.insert(0, str(_GW_SCRIPTS))

from gw_client import get_calendar_service  # noqa: E402


def parse_iso(s: str) -> datetime.datetime:
    # Accept "...Z" by converting to "+00:00"
    if s.endswith("Z"):
        s = s[:-1] + "+00:00"
    return datetime.datetime.fromisoformat(s)


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--start", required=True, help="Window start (ISO 8601, e.g. 2026-05-25T11:00:00+08:00)")
    ap.add_argument("--end", required=True, help="Window end (ISO 8601)")
    ap.add_argument("--pad-minutes", type=int, default=15,
                    help="Pad window by N minutes on each side (default: 15)")
    ap.add_argument("--calendar", default="primary",
                    help="Calendar ID (default: primary)")
    ap.add_argument("--max-results", type=int, default=10)
    args = ap.parse_args()

    try:
        start = parse_iso(args.start)
        end = parse_iso(args.end)
    except ValueError as e:
        print(f"bad ISO timestamp: {e}", file=sys.stderr)
        sys.exit(2)

    pad = datetime.timedelta(minutes=args.pad_minutes)
    time_min = (start - pad).isoformat()
    time_max = (end + pad).isoformat()

    cal = get_calendar_service()
    try:
        result = cal.events().list(
            calendarId=args.calendar,
            timeMin=time_min,
            timeMax=time_max,
            singleEvents=True,
            orderBy="startTime",
            maxResults=args.max_results,
        ).execute()
    except Exception as e:
        print(f"Calendar API error: {e}", file=sys.stderr)
        sys.exit(1)

    candidates = []
    for ev in result.get("items", []):
        # Skip cancelled / declined / all-day non-meeting events
        if ev.get("status") == "cancelled":
            continue
        ev_start = ev.get("start", {}).get("dateTime") or ev.get("start", {}).get("date")
        ev_end = ev.get("end", {}).get("dateTime") or ev.get("end", {}).get("date")
        if not ev_start or not ev_end:
            continue
        # Skip all-day (date only, no dateTime)
        if "T" not in ev_start:
            continue

        attendees = ev.get("attendees", []) or []
        attendee_emails = [a.get("email") for a in attendees if a.get("email")]
        candidates.append({
            "id": ev.get("id"),
            "title": ev.get("summary", "(no title)"),
            "start": ev_start,
            "end": ev_end,
            "organizer": ev.get("organizer", {}).get("email"),
            "attendee_count": len(attendees),
            "attendee_emails": attendee_emails,
            "location": ev.get("location"),
            "html_link": ev.get("htmlLink"),
            "has_description": bool(ev.get("description")),
            "has_attachments": bool(ev.get("attachments")),
        })

    json.dump(candidates, sys.stdout, ensure_ascii=False, indent=2)
    sys.stdout.write("\n")


if __name__ == "__main__":
    main()
