#!/usr/bin/env python3
"""
Send a welcome email to a freshly-onboarded ford member.

Used by .github/workflows/ford-approve.yml after PR merge. Can also be run
locally: re-send / preview / draft.

Auth: reuses get_gmail_service() from gw_client.py (Project Secret GOOGLE_TOKEN_JSON
or /tmp/google_token.json). Sender = current authenticated user (you@roche.com).

Usage:
    python3 ford_welcome_email.py send \
        --display-name "Jingzi Xu" \
        --handle xuj67_roche \
        --short-id xuj67 \
        --to jingzi.xu@roche.com \
        --pages-url https://probable-adventure-1q52vql.pages.github.io/ \
        --shortlink-url https://go.roche.com/silicon-hitchhiker.ford.xuj67 \
        --pr-url https://github.com/roche-innersource/cd2-ai-hackathon-hub/pull/82 \
        --shortlink-status ok

    python3 ford_welcome_email.py preview --display-name ... (same args, prints HTML, no API)
    python3 ford_welcome_email.py draft  ... (same args, creates Gmail draft, no send)

--shortlink-status:
    ok           → "短链已配好"
    pages_url    → "短链 cookie 暂时过期，已用你的个人页 URL 顶替；admin 后续 rotate 后回填"
    pending      → "你还没填个人页 URL；建好后告诉 admin"
    secret_missing / api_error → 同 pages_url 措辞（fallback 已生效或将由 admin 手动建短链）

Workflow integration: ford-approve.yml passes status from the shortlink step.
"""
from __future__ import annotations

import argparse
import base64
import sys
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from pathlib import Path

# Ensure local imports work whether run from demos/ or from workflow runner cwd
HERE = Path(__file__).resolve().parent
if str(HERE) not in sys.path:
    sys.path.insert(0, str(HERE))

from gw_client import get_gmail_service  # noqa: E402


SUBJECT_TEMPLATE = "欢迎加入 silicon-hitchhiker / ford 外勤研究员 — {display_name}"


def build_body_html(args: argparse.Namespace) -> str:
    short_link_section = ""
    if args.shortlink_status == "ok":
        short_link_section = (
            f'<li>你的短链：<a href="{args.shortlink_url}">{args.shortlink_url}</a>，'
            "已经把你设为 additional owner，可以自己改跳转目标</li>"
        )
    elif args.shortlink_status == "pending":
        # 还没个人页 → 短链没东西可指，等页搭好再建
        short_link_section = (
            f'<li>短链 <code>silicon-hitchhiker.ford.{args.short_id}</code> '
            "要等你搭好个人页之后才能建（短链得指向一个落地页）。"
            "按下方提示搭好个人页 ping 我，我会跑 "
            "<code>tools/refresh-ford-roster-shortlinks.py</code> 一起建好 + 回填 roster</li>"
        )
    else:
        # pages_url fallback / secret_missing / api_error 共用一套措辞（有页, cookie/secret 暂不可用）
        short_link_section = (
            f'<li>短链 <code>silicon-hitchhiker.ford.{args.short_id}</code> '
            "暂时还没建好（go.roche.com cookie 临时过期）。"
            "我会在 cookie 更新后跑 <code>tools/refresh-ford-roster-shortlinks.py</code> 自动回填，"
            "中间你直接用个人页 URL 分享就行</li>"
        )

    pages_section = ""
    if args.pages_url:
        pages_section = (
            f'<li>你的个人页：<a href="{args.pages_url}">{args.pages_url}</a></li>'
        )
    else:
        pages_section = (
            '<li>你还没提交个人页 URL——参考 <a href="https://github.com/roche-innersource/silicon-hitchhiker/blob/main/docs/guide/ford-program.md">ford-program.md</a> 搭一份，'
            "搭好后 ping 我，我来更新 roster + 建短链</li>"
        )

    pr_section = ""
    if args.pr_url:
        pr_section = f'<li>本次 onboard 的 PR：<a href="{args.pr_url}">{args.pr_url}</a></li>'

    body = f"""
<p>Hi {args.display_name},</p>

<p>恭喜，你已经加入 silicon-hitchhiker 项目的 ford 外勤研究员。</p>

<p><b>已经为你做好的：</b></p>
<ul>
  <li>把你（<code>{args.handle}</code>）加为 hub repo 的 direct collaborator（push 权限）</li>
  {short_link_section}
  {pages_section}
  {pr_section}
</ul>

<p><b>建议你接下来：</b></p>
<ul>
  <li>读 <a href="https://github.com/roche-innersource/silicon-hitchhiker/blob/main/docs/guide/ford-program.md">docs/guide/ford-program.md</a>，了解 ford 角色边界、共享 skill 套件位置、协作流程</li>
  <li>任何对 hub 的改动走 <code>feat/&lt;topic&gt;</code> branch + PR，CI 会跑 slidev build / lint</li>
  <li>欢迎在 silicon-hitchhiker 微信群里报到（如果还没拉你进群，回复这封邮件告诉我）</li>
</ul>

<p>欢迎入伙。任何问题直接回邮件。</p>
"""
    return body.strip()


def get_signature(gmail) -> str:
    sendas = gmail.users().settings().sendAs().list(userId="me").execute()
    for s in sendas.get("sendAs", []):
        if s.get("isDefault"):
            return s.get("signature", "") or ""
    return ""


def render_full_html(body_html: str, signature_html: str) -> str:
    return (
        '<div style="font-family:Arial,sans-serif;font-size:10pt;color:#222;line-height:1.4">'
        f"{body_html}"
        '<br/>'
        f"{signature_html}"
        "</div>"
    )


def build_raw_message(to: str, cc: list[str], subject: str, html: str) -> str:
    msg = MIMEMultipart("alternative")
    msg["To"] = to
    if cc:
        msg["Cc"] = ", ".join(cc)
    msg["Subject"] = subject
    msg.attach(MIMEText(html, "html", "utf-8"))
    return base64.urlsafe_b64encode(msg.as_bytes()).decode()


def make_args() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = p.add_subparsers(dest="cmd", required=True)
    for sub_name in ("send", "draft", "preview"):
        sp = sub.add_parser(sub_name)
        sp.add_argument("--display-name", required=True)
        sp.add_argument("--handle", required=True)
        sp.add_argument("--short-id", required=True)
        sp.add_argument("--to", required=True, help="recipient email")
        sp.add_argument("--cc", default="", help="comma-separated CC list (optional)")
        sp.add_argument("--pages-url", default="")
        sp.add_argument("--shortlink-url", default="")
        sp.add_argument("--pr-url", default="")
        sp.add_argument(
            "--shortlink-status",
            default="pending",
            choices=["ok", "pending", "no_pages_url", "secret_missing", "api_error", "pages_url"],
            help="status from the workflow's shortlink step",
        )
    return p


def main() -> int:
    args = make_args().parse_args()
    body_html = build_body_html(args)
    cc_list = [e.strip() for e in args.cc.split(",") if e.strip()]

    if args.cmd == "preview":
        # Stub a fake signature to render
        full = render_full_html(body_html, '<p style="color:#888">[default signature]</p>')
        print(f"To: {args.to}")
        if cc_list:
            print(f"Cc: {', '.join(cc_list)}")
        print(f"Subject: {SUBJECT_TEMPLATE.format(display_name=args.display_name)}")
        print("---")
        print(full)
        return 0

    gmail = get_gmail_service()
    signature = get_signature(gmail)
    full_html = render_full_html(body_html, signature)
    raw = build_raw_message(
        args.to, cc_list,
        SUBJECT_TEMPLATE.format(display_name=args.display_name),
        full_html,
    )

    if args.cmd == "draft":
        result = gmail.users().drafts().create(userId="me", body={"message": {"raw": raw}}).execute()
        print(f"draft created: id={result['id']}  msg_id={result['message']['id']}")
        print(f"view: https://mail.google.com/mail/u/0/#drafts/{result['message']['id']}")
        return 0

    if args.cmd == "send":
        result = gmail.users().messages().send(userId="me", body={"raw": raw}).execute()
        print(f"sent: id={result['id']}  thread={result.get('threadId', '')}")
        return 0

    return 1


if __name__ == "__main__":
    sys.exit(main())
