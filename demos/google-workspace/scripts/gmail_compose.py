#!/usr/bin/env python3
"""
Gmail draft compose & sync — md (with YAML frontmatter) ↔ Gmail Draft.

Workflow:
    1. Write a markdown file with YAML frontmatter (to/cc/subject/signature).
    2. `python3 gmail_compose.py sync path/to/email.md`
       - First run: creates a Gmail draft, writes `gmail_draft_id` back to the md frontmatter.
       - Subsequent runs: detects `gmail_draft_id` in frontmatter, updates that draft in place.
    3. Iterate by editing the md and re-running sync. The draft_id stays stable.
    4. `python3 gmail_compose.py send path/to/email.md` to send the draft.

Frontmatter:
    ---
    to: [alice@x.com, bob@y.com]
    cc: [charlie@x.com]                    # optional
    bcc: [dave@x.com]                      # optional
    subject: 请教：xxx
    attachments: [./data.xlsx, ../report.pdf]  # optional — file paths relative to the md file
    signature: default                     # default | minimal | none
    reply_to: <Message-ID@mail.gmail.com>  # optional — RFC822 Message-ID of email being replied to;
                                           # makes the draft thread under that conversation
    gmail_draft_id: r-xxx                  # auto-managed, do not hand-edit
    ---

    正文 markdown.
"""
from __future__ import annotations

import argparse
import base64
import mimetypes
import re
import sys
from email.mime.base import MIMEBase
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email import encoders
from pathlib import Path

import yaml
from markdown_it import MarkdownIt

from gw_client import get_gmail_service

# ── Frontmatter ───────────────────────────────────────────────────────────

FRONTMATTER_RE = re.compile(r"^---[ \t]*\n(.*?)\n---[ \t]*\n(.*)$", re.DOTALL)


def parse_md(path: Path) -> tuple[dict, str]:
    text = path.read_text(encoding="utf-8")
    m = FRONTMATTER_RE.match(text)
    if not m:
        sys.exit(f"error: {path} has no YAML frontmatter (--- ... ---)")
    fm = yaml.safe_load(m.group(1)) or {}
    body = m.group(2)
    if not fm.get("to"):
        sys.exit(f"error: {path} frontmatter missing 'to'")
    if not fm.get("subject"):
        sys.exit(f"error: {path} frontmatter missing 'subject'")
    return fm, body


def write_back_draft_id(path: Path, draft_id: str) -> None:
    """Update the md file's frontmatter with gmail_draft_id (idempotent)."""
    text = path.read_text(encoding="utf-8")
    m = FRONTMATTER_RE.match(text)
    fm = yaml.safe_load(m.group(1)) or {}
    body = m.group(2)
    fm["gmail_draft_id"] = draft_id
    new_fm = yaml.safe_dump(fm, allow_unicode=True, sort_keys=False).strip()
    path.write_text(f"---\n{new_fm}\n---\n{body}", encoding="utf-8")


# ── Signature ─────────────────────────────────────────────────────────────


def get_signature(gmail, style: str = "default") -> str:
    if style == "none":
        return ""
    sendas = gmail.users().settings().sendAs().list(userId="me").execute()
    for s in sendas.get("sendAs", []):
        if s.get("isDefault"):
            sig = s.get("signature", "") or ""
            if style == "minimal":
                # 极简：仅姓名 + email
                return (
                    '<div style="font-family:Arial,sans-serif;font-size:10pt;color:#555">'
                    "Silicon Hitchhiker</div>"
                )
            return sig
    return ""


# ── Markdown → HTML ───────────────────────────────────────────────────────


def md_to_html(body_md: str) -> str:
    md = MarkdownIt("commonmark", {"html": True, "breaks": False, "linkify": True}).enable("table")
    return md.render(body_md)


# Inline styles for heading tags so email clients (which often strip <style>) render them tight.
HEADING_STYLES = {
    "h1": "font-size:13pt;margin:16px 0 6px;font-weight:600;",
    "h2": "font-size:12pt;margin:14px 0 5px;font-weight:600;",
    "h3": "font-size:11pt;margin:12px 0 4px;font-weight:600;",
    "h4": "font-size:10pt;margin:10px 0 4px;font-weight:600;",
    "p":  "margin:6px 0;",
}

# Inline styles for tables — email clients strip <style>, and markdown tables otherwise
# render borderless with cells crammed together. border + padding separate the columns.
TABLE_STYLES = {
    "table": "border-collapse:collapse;width:100%;margin:8px 0;font-size:9.5pt;",
    "th": "border:1px solid #d1d5db;padding:5px 9px;background:#f3f4f6;font-weight:600;",
    "td": "border:1px solid #e5e7eb;padding:5px 9px;",
}


def _style_tag(html: str, tag: str, style: str) -> str:
    """Inject inline style into a tag, whether it's bare (<td>) or already
    carries attributes (<td style="text-align:right">). Existing styles win
    (appended after ours) so markdown's right-align is preserved."""
    # bare tag → add style
    html = re.sub(rf"<{tag}>", f'<{tag} style="{style}">', html)
    # tag with existing style attr → prepend ours, keep theirs
    html = re.sub(
        rf'<{tag} style="(?![^"]*{re.escape(style[:12])})',
        f'<{tag} style="{style}',
        html,
    )
    return html


def _inject_inline_styles(html: str) -> str:
    for tag, style in HEADING_STYLES.items():
        html = html.replace(f"<{tag}>", f'<{tag} style="{style}">')
    for tag, style in TABLE_STYLES.items():
        html = _style_tag(html, tag, style)
    return html


def render_email_html(body_md: str, signature_html: str) -> str:
    body_html = _inject_inline_styles(md_to_html(body_md))
    return (
        '<div style="font-family:Arial,sans-serif;font-size:10pt;color:#222;line-height:1.4">'
        f"{body_html}"
        '<br/>'
        f"{signature_html}"
        "</div>"
    )


# ── Threading lookup ──────────────────────────────────────────────────────


def find_thread_for_reply(gmail, rfc822_id: str) -> dict | None:
    """Look up a message by RFC822 Message-ID. Returns dict with threadId,
    message_id (the target's own Message-ID header), references (existing chain),
    or None if not found."""
    rfc = rfc822_id.strip()
    if rfc.startswith("<") and rfc.endswith(">"):
        rfc = rfc[1:-1]
    result = gmail.users().messages().list(
        userId="me", q=f"rfc822msgid:{rfc}", maxResults=1
    ).execute()
    msgs = result.get("messages", [])
    if not msgs:
        return None
    msg = gmail.users().messages().get(
        userId="me", id=msgs[0]["id"], format="metadata",
        metadataHeaders=["Message-ID", "References", "In-Reply-To"],
    ).execute()
    h = {x["name"]: x["value"] for x in msg["payload"]["headers"]}
    return {
        "thread_id": msg["threadId"],
        "message_id": h.get("Message-ID", f"<{rfc}>"),
        "references": h.get("References", ""),
    }


# ── MIME builder ──────────────────────────────────────────────────────────


def build_raw_message(fm: dict, html: str, reply_info: dict | None = None,
                      base_dir: Path | None = None) -> str:
    attachments = _resolve_attachments(fm.get("attachments"), base_dir)

    body = MIMEMultipart("alternative")
    body.attach(MIMEText(html, "html", "utf-8"))

    if attachments:
        msg: MIMEMultipart = MIMEMultipart("mixed")
        msg.attach(body)
        for path in attachments:
            msg.attach(_build_attachment_part(path))
    else:
        msg = body

    msg["To"] = _join_emails(fm.get("to"))
    if fm.get("cc"):
        msg["Cc"] = _join_emails(fm["cc"])
    if fm.get("bcc"):
        msg["Bcc"] = _join_emails(fm["bcc"])
    msg["Subject"] = fm["subject"]
    if reply_info:
        msg["In-Reply-To"] = reply_info["message_id"]
        chain = (reply_info.get("references", "") + " " + reply_info["message_id"]).strip()
        msg["References"] = chain
    return base64.urlsafe_b64encode(msg.as_bytes()).decode()


def _resolve_attachments(value, base_dir: Path | None) -> list[Path]:
    if not value:
        return []
    items = value if isinstance(value, list) else [value]
    base_dir = base_dir or Path.cwd()
    resolved: list[Path] = []
    for item in items:
        p = Path(item)
        if not p.is_absolute():
            p = (base_dir / p).resolve()
        if not p.is_file():
            sys.exit(f"error: attachment not found: {item} (resolved to {p})")
        resolved.append(p)
    return resolved


def _build_attachment_part(path: Path) -> MIMEBase:
    ctype, encoding = mimetypes.guess_type(str(path))
    if ctype is None or encoding is not None:
        ctype = "application/octet-stream"
    maintype, subtype = ctype.split("/", 1)
    part = MIMEBase(maintype, subtype)
    part.set_payload(path.read_bytes())
    encoders.encode_base64(part)
    part.add_header("Content-Disposition", "attachment", filename=path.name)
    return part


def _join_emails(value) -> str:
    if isinstance(value, list):
        return ", ".join(value)
    return str(value)


# ── Commands ──────────────────────────────────────────────────────────────


def cmd_sync(path: Path) -> None:
    fm, body = parse_md(path)
    gmail = get_gmail_service()
    sig = get_signature(gmail, fm.get("signature", "default"))
    html = render_email_html(body, sig)

    reply_info = None
    target_thread_id = None
    if fm.get("reply_to"):
        reply_info = find_thread_for_reply(gmail, fm["reply_to"])
        if reply_info:
            target_thread_id = reply_info["thread_id"]
            print(f"reply_to resolved: thread_id={target_thread_id}")
        else:
            print(f"warn: reply_to message not found ({fm['reply_to']}); creating standalone draft")

    raw = build_raw_message(fm, html, reply_info, base_dir=path.parent)

    existing_id = fm.get("gmail_draft_id")
    message_body: dict = {"raw": raw}
    if target_thread_id:
        message_body["threadId"] = target_thread_id

    if existing_id:
        # If existing draft is in a different thread than target, recreate.
        try:
            existing = gmail.users().drafts().get(userId="me", id=existing_id, format="metadata").execute()
            existing_thread = existing.get("message", {}).get("threadId")
        except Exception:
            existing_thread = None
        if target_thread_id and existing_thread and existing_thread != target_thread_id:
            gmail.users().drafts().delete(userId="me", id=existing_id).execute()
            existing_id = None
            print(f"existing draft was in wrong thread ({existing_thread}); recreating in {target_thread_id}")

    if existing_id:
        result = gmail.users().drafts().update(
            userId="me", id=existing_id,
            body={"id": existing_id, "message": message_body},
        ).execute()
        action = "updated"
    else:
        result = gmail.users().drafts().create(
            userId="me", body={"message": message_body}
        ).execute()
        action = "created"
        write_back_draft_id(path, result["id"])

    msg_id = result["message"]["id"]
    thread_id = result["message"].get("threadId", "")
    print(f"{action}: draft_id={result['id']}  msg_id={msg_id}  thread_id={thread_id}")
    print(f"view:  https://mail.google.com/mail/u/0/#drafts/{msg_id}")


def cmd_send(path: Path) -> None:
    fm, _ = parse_md(path)
    draft_id = fm.get("gmail_draft_id")
    if not draft_id:
        sys.exit(f"error: {path} has no gmail_draft_id — run sync first")
    gmail = get_gmail_service()
    result = gmail.users().drafts().send(userId="me", body={"id": draft_id}).execute()
    print(f"sent: msg_id={result['id']}  thread_id={result.get('threadId','')}")


def cmd_preview(path: Path) -> None:
    fm, body = parse_md(path)
    sig = '<p style="color:#555">[signature placeholder]</p>'
    html = render_email_html(body, sig)
    print(f"To: {_join_emails(fm.get('to'))}")
    if fm.get("cc"):
        print(f"Cc: {_join_emails(fm['cc'])}")
    print(f"Subject: {fm['subject']}")
    print("---")
    print(html)


# ── CLI ───────────────────────────────────────────────────────────────────


def main() -> None:
    p = argparse.ArgumentParser(prog="gmail_compose")
    sub = p.add_subparsers(dest="cmd", required=True)

    sp_sync = sub.add_parser("sync", help="create or update Gmail draft from md")
    sp_sync.add_argument("path", type=Path)

    sp_send = sub.add_parser("send", help="send the draft bound to this md")
    sp_send.add_argument("path", type=Path)

    sp_preview = sub.add_parser("preview", help="dry-run: render md to HTML, no API call")
    sp_preview.add_argument("path", type=Path)

    args = p.parse_args()
    if not args.path.exists():
        sys.exit(f"error: {args.path} not found")

    {"sync": cmd_sync, "send": cmd_send, "preview": cmd_preview}[args.cmd](args.path)


if __name__ == "__main__":
    main()
