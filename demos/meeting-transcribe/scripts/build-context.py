"""Build enrichment context for a Calendar event: attendees with title +
manager (one hop), event details, agenda, optional Drive doc bodies.

Used by:
- meeting-minutes skill: pass `--event-id <id>` to get attendee titles for
  speaker attribution
- meeting-prep skill: pass `--event-id <id> --include-docs` to get full
  attached doc bodies for pre-meeting briefing

Usage:
    python3 build-context.py --event-id abc123

    # Include attached Doc bodies (truncated)
    python3 build-context.py --event-id abc123 --include-docs

    # Include with custom truncation
    python3 build-context.py --event-id abc123 --include-docs --max-doc-bytes 10000

Output (JSON to stdout):
    {
      "event": {
        "id": "abc123",
        "title": "IMP subsidy meeting",
        "start": "...", "end": "...",
        "description": "...",
        "organizer": {"email": "...", "name": "...", "title": "..."},
        "html_link": "..."
      },
      "attendees": [
        {
          "email": "rong.fu@roche.com",
          "name": "Rong Fu",
          "title": "PD lead",
          "department": "PD China",
          "manager": {"email": "...", "name": "...", "title": "..."}
        },
        ...
      ],
      "attachments": [
        {"title": "Agenda", "url": "...", "mime_type": "...", "body": "..."}
      ]
    }
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

_HERE = Path(__file__).resolve().parent
_GW_SCRIPTS = _HERE.parent.parent / "google-workspace" / "scripts"
sys.path.insert(0, str(_GW_SCRIPTS))

from gw_client import get_calendar_service, get_people_service, get_drive_service  # noqa: E402

DEFAULT_PERSON_FIELDS = "names,emailAddresses,organizations,relations"


def _short_org(person: dict) -> dict:
    """Extract title/department/manager email from a People person record."""
    out = {"title": None, "department": None, "manager_email": None}
    orgs = person.get("organizations") or []
    if orgs:
        org = orgs[0]
        out["title"] = org.get("title")
        out["department"] = org.get("department")
    for rel in person.get("relations") or []:
        if rel.get("type") == "manager":
            out["manager_email"] = rel.get("person")
            break
    return out


def _name_from_person(person: dict) -> str | None:
    names = person.get("names") or []
    return names[0].get("displayName") if names else None


def lookup_person(people, email: str) -> dict | None:
    """Lookup directory profile by email via searchDirectoryPeople (full email match)."""
    try:
        result = people.people().searchDirectoryPeople(
            query=email,
            readMask=DEFAULT_PERSON_FIELDS,
            sources=["DIRECTORY_SOURCE_TYPE_DOMAIN_PROFILE"],
            pageSize=5,
        ).execute()
    except Exception as e:
        print(f"warn: People API search failed for {email}: {e}", file=sys.stderr)
        return None

    for p in result.get("people", []):
        for em in p.get("emailAddresses", []):
            if em.get("value", "").lower() == email.lower():
                return p
    return None


def enrich_attendee(people, email: str, with_manager: bool = True) -> dict:
    """Return attendee dict with name, title, department, manager (one hop)."""
    out = {
        "email": email,
        "name": None,
        "title": None,
        "department": None,
        "manager": None,
    }
    person = lookup_person(people, email)
    if not person:
        return out
    out["name"] = _name_from_person(person)
    org = _short_org(person)
    out["title"] = org["title"]
    out["department"] = org["department"]

    if with_manager and org["manager_email"]:
        mgr_person = lookup_person(people, org["manager_email"])
        if mgr_person:
            mgr_org = _short_org(mgr_person)
            out["manager"] = {
                "email": org["manager_email"],
                "name": _name_from_person(mgr_person),
                "title": mgr_org["title"],
            }
        else:
            out["manager"] = {"email": org["manager_email"], "name": None, "title": None}
    return out


def export_drive_doc(drive, file_id: str, max_bytes: int) -> str | None:
    """Export a Drive Doc as plain text, truncated."""
    try:
        body = drive.files().export(fileId=file_id, mimeType="text/plain").execute()
        if isinstance(body, bytes):
            text = body.decode("utf-8", errors="replace")
        else:
            text = str(body)
        if len(text) > max_bytes:
            text = text[:max_bytes] + f"\n...[truncated at {max_bytes} bytes]"
        return text
    except Exception as e:
        print(f"warn: Drive export failed for {file_id}: {e}", file=sys.stderr)
        return None


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--event-id", required=True, help="Calendar event ID")
    ap.add_argument("--calendar", default="primary")
    ap.add_argument("--include-docs", action="store_true",
                    help="Export attached Doc bodies (default: false)")
    ap.add_argument("--max-doc-bytes", type=int, default=5000,
                    help="Max bytes per exported Doc (default: 5000)")
    ap.add_argument("--no-manager", action="store_true",
                    help="Skip manager lookup (one less People API hop per attendee)")
    args = ap.parse_args()

    cal = get_calendar_service()
    people = get_people_service()

    try:
        ev = cal.events().get(calendarId=args.calendar, eventId=args.event_id).execute()
    except Exception as e:
        print(f"Calendar event lookup failed: {e}", file=sys.stderr)
        sys.exit(1)

    organizer_email = ev.get("organizer", {}).get("email")
    organizer = enrich_attendee(people, organizer_email, with_manager=not args.no_manager) if organizer_email else None

    out_event = {
        "id": ev.get("id"),
        "title": ev.get("summary"),
        "start": ev.get("start", {}).get("dateTime") or ev.get("start", {}).get("date"),
        "end": ev.get("end", {}).get("dateTime") or ev.get("end", {}).get("date"),
        "description": ev.get("description"),
        "organizer": organizer,
        "html_link": ev.get("htmlLink"),
        "location": ev.get("location"),
    }

    attendees_out = []
    for a in ev.get("attendees", []) or []:
        email = a.get("email")
        if not email:
            continue
        if email == organizer_email:
            continue  # already enriched as organizer
        attendees_out.append(enrich_attendee(people, email, with_manager=not args.no_manager))

    attachments_out = []
    if ev.get("attachments"):
        drive = get_drive_service() if args.include_docs else None
        for att in ev["attachments"]:
            entry = {
                "title": att.get("title"),
                "url": att.get("fileUrl"),
                "mime_type": att.get("mimeType"),
                "file_id": att.get("fileId"),
            }
            if args.include_docs and att.get("fileId") and att.get("mimeType") == "application/vnd.google-apps.document":
                entry["body"] = export_drive_doc(drive, att["fileId"], args.max_doc_bytes)
            attachments_out.append(entry)

    output = {
        "event": out_event,
        "attendees": attendees_out,
        "attachments": attachments_out,
    }
    json.dump(output, sys.stdout, ensure_ascii=False, indent=2)
    sys.stdout.write("\n")


if __name__ == "__main__":
    main()
