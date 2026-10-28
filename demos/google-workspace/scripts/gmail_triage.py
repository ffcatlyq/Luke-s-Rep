#!/usr/bin/env python3
"""
Gmail inbox triage: create filters + archive existing noise.

Usage:
    python3 gmail_triage.py dry-run     # preview what would happen
    python3 gmail_triage.py execute     # create filters + archive matching emails
    python3 gmail_triage.py status      # show current inbox stats
"""
from __future__ import annotations

import sys
import time
from dataclasses import dataclass

from gw_client import get_gmail_service

# ── Triage rules ──────────────────────────────────────────────────────────

@dataclass
class TriageRule:
    name: str
    query: str           # Gmail search query
    label: str           # label to apply (created if missing)
    skip_inbox: bool = True   # remove INBOX label (archive)
    mark_read: bool = True    # remove UNREAD label

RULES: list[TriageRule] = [
    TriageRule(
        name="Jira 通知",
        query="from:globaljira@roche.com",
        label="Auto/Jira",
    ),
    TriageRule(
        name="CIDM 通知",
        query="from:cidm-no-reply@roche.com",
        label="Auto/CIDM",
    ),
    TriageRule(
        name="GitHub EMU 系统",
        query="from:glofct_github@msxdl.roche.com",
        label="Auto/GitHub-EMU",
    ),
    TriageRule(
        name="GitHub 通知",
        query="from:notifications@github.com",
        label="Auto/GitHub",
    ),
    TriageRule(
        name="学术/课程平台",
        query="from:academia-mail.com OR from:deeplearning.ai OR from:kaggle.com",
        label="Auto/学习",
    ),
    TriageRule(
        name="社交媒体",
        query="from:linkedin.com OR from:mail.instagram.com OR from:facebookmail.com",
        label="Auto/社交",
    ),
    TriageRule(
        name="HR/Workday",
        query="from:roche-workday-donotreply@roche.com OR from:people.portal@roche.com",
        label="Auto/HR",
    ),
    TriageRule(
        name="公司通告",
        query=(
            "from:global.rdt_communications@roche.com OR "
            "from:global.dataone_contact@roche.com OR "
            "from:apac.it_communications@roche.com OR "
            "from:shanghai.internal_communications@roche.com"
        ),
        label="Auto/公司通告",
    ),
    TriageRule(
        name="GitLab 通知",
        query="from:code.roche.com",
        label="GitLab",
    ),
    TriageRule(
        name="Google/GCP 通知",
        query="from:googlecloud@google.com OR from:google-workspace-alerts-noreply@google.com",
        label="Auto/Google",
    ),
    TriageRule(
        name="Noreply 系统邮件",
        query="from:noreply@roche.com",
        label="Auto/系统",
    ),
]

# ── Helpers ───────────────────────────────────────────────────────────────

def _get_or_create_label(gmail, label_name: str) -> str:
    """Get label ID by name, create if missing. Supports nested labels like 'Auto/Jira'."""
    labels = gmail.users().labels().list(userId='me').execute().get('labels', [])
    for l in labels:
        if l['name'] == label_name:
            return l['id']

    # Create
    body = {
        'name': label_name,
        'labelListVisibility': 'labelShow',
        'messageListVisibility': 'show',
    }
    created = gmail.users().labels().create(userId='me', body=body).execute()
    return created['id']


def _search_messages(gmail, query: str, label: str = None) -> list[str]:
    """Return all message IDs matching query."""
    ids = []
    page_token = None
    q = query
    if label:
        q = f"label:{label} {query}"
    while True:
        resp = gmail.users().messages().list(
            userId='me', q=q, maxResults=500, pageToken=page_token
        ).execute()
        ids.extend([m['id'] for m in resp.get('messages', [])])
        page_token = resp.get('nextPageToken')
        if not page_token:
            break
    return ids


def _batch_modify(gmail, msg_ids: list[str], add_labels: list[str],
                  remove_labels: list[str], batch_size: int = 1000):
    """Batch modify messages (add/remove labels)."""
    for i in range(0, len(msg_ids), batch_size):
        batch = msg_ids[i:i+batch_size]
        gmail.users().messages().batchModify(
            userId='me',
            body={
                'ids': batch,
                'addLabelIds': add_labels,
                'removeLabelIds': remove_labels,
            }
        ).execute()
        if i + batch_size < len(msg_ids):
            time.sleep(0.5)  # rate limit courtesy


def _create_filter(gmail, query: str, label_id: str, skip_inbox: bool, mark_read: bool):
    """Create a Gmail filter for future messages."""
    # Parse query into filter criteria
    # Gmail filters use 'from' field, we extract from the query
    criteria = {'query': query}

    action = {'addLabelIds': [label_id]}
    if skip_inbox:
        action['removeLabelIds'] = ['INBOX']

    body = {'criteria': criteria, 'action': action}

    try:
        gmail.users().settings().filters().create(userId='me', body=body).execute()
        return True
    except Exception as e:
        print(f"  ⚠️  Filter creation failed: {e}")
        return False


# ── Commands ──────────────────────────────────────────────────────────────

def cmd_status(gmail):
    """Show current inbox stats."""
    profile = gmail.users().getProfile(userId='me').execute()
    print(f"Email: {profile['emailAddress']}")
    print(f"Total messages: {profile['messagesTotal']}")
    print(f"Total threads: {profile['threadsTotal']}")

    # Inbox stats
    inbox = gmail.users().labels().get(userId='me', id='INBOX').execute()
    print(f"\nINBOX: {inbox['messagesTotal']} total, {inbox['messagesUnread']} unread")

    # Check Auto/* labels
    labels = gmail.users().labels().list(userId='me').execute().get('labels', [])
    auto_labels = [l for l in labels if l['name'].startswith('Auto/')]
    if auto_labels:
        print(f"\nAuto/* labels:")
        for l in sorted(auto_labels, key=lambda x: x['name']):
            detail = gmail.users().labels().get(userId='me', id=l['id']).execute()
            print(f"  {detail['messagesTotal']:>5}  {l['name']}")


def cmd_dry_run(gmail):
    """Preview what each rule would match."""
    print("=== DRY RUN: Gmail Triage ===\n")

    total_matched = 0
    total_inbox_matched = 0

    for rule in RULES:
        # All matching messages
        all_ids = _search_messages(gmail, rule.query)
        # Only those still in inbox
        inbox_ids = _search_messages(gmail, rule.query, label="inbox")

        total_matched += len(all_ids)
        total_inbox_matched += len(inbox_ids)

        print(f"  [{rule.name}]")
        print(f"    Query: {rule.query}")
        print(f"    Label: {rule.label}")
        print(f"    Total matches: {all_ids.__len__()}")
        print(f"    Still in INBOX: {len(inbox_ids)}")
        print(f"    Action: {'archive + ' if rule.skip_inbox else ''}{'mark read + ' if rule.mark_read else ''}label")
        print()

    print(f"--- Summary ---")
    print(f"Total matches across all rules: {total_matched}")
    print(f"Messages to archive from INBOX: {total_inbox_matched}")

    inbox = gmail.users().labels().get(userId='me', id='INBOX').execute()
    remaining = inbox['messagesTotal'] - total_inbox_matched
    remaining_unread = inbox['messagesUnread'] - total_inbox_matched  # rough estimate
    print(f"\nCurrent INBOX: {inbox['messagesTotal']} total, {inbox['messagesUnread']} unread")
    print(f"After triage:  ~{max(0, remaining)} total, ~{max(0, remaining_unread)} unread (estimate)")


def cmd_execute(gmail):
    """Create filters + archive existing matching emails."""
    print("=== EXECUTING: Gmail Triage ===\n")

    for rule in RULES:
        print(f"[{rule.name}]")

        # 1. Create label
        label_id = _get_or_create_label(gmail, rule.label)
        print(f"  Label '{rule.label}' ready (id: {label_id})")

        # 2. Create filter for future messages
        ok = _create_filter(gmail, rule.query, label_id, rule.skip_inbox, rule.mark_read)
        if ok:
            print(f"  ✅ Filter created")
        else:
            print(f"  ⚠️  Filter skipped (may already exist)")

        # 3. Archive existing messages in inbox
        inbox_ids = _search_messages(gmail, rule.query, label="inbox")
        if inbox_ids:
            remove = []
            if rule.skip_inbox:
                remove.append('INBOX')
            if rule.mark_read:
                remove.append('UNREAD')

            _batch_modify(gmail, inbox_ids, add_labels=[label_id], remove_labels=remove)
            print(f"  ✅ Archived {len(inbox_ids)} messages")
        else:
            print(f"  (no inbox messages to archive)")

        print()

    # Final status
    print("--- Done! Final status ---")
    cmd_status(gmail)


# ── Main ──────────────────────────────────────────────────────────────────

def main():
    if len(sys.argv) < 2 or sys.argv[1] not in ('dry-run', 'execute', 'status'):
        print("Usage: python3 gmail_triage.py [dry-run|execute|status]")
        sys.exit(1)

    gmail = get_gmail_service()
    cmd = sys.argv[1]

    if cmd == 'status':
        cmd_status(gmail)
    elif cmd == 'dry-run':
        cmd_dry_run(gmail)
    elif cmd == 'execute':
        cmd_execute(gmail)


if __name__ == '__main__':
    main()
