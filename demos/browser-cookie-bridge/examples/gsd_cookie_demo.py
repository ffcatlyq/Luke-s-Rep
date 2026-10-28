#!/usr/bin/env python3
"""GSD demo - 用浏览器同步过来的 cookie 调 GSD API，不走 NTLM。

前置条件:
  1. 浏览器已经登录 GSD (https://apps.sha.roche.com/GSD/)
  2. cookie_receiver.py 在跑，service=gsd 配置已加
  3. 扩展同步过 cookie，~/.config/gsd/cookies.json 存在

用法:
    python3 gsd_cookie_demo.py                # 默认调 AdminManager.GetUserMenu
    python3 gsd_cookie_demo.py --owner GrantManager --opid GetTaskList

注意:
  本脚本仅供 PoC 验证，确认浏览器 cookie 模型对 GSD 是否可行。
  生产用法见 huy30 团队的 scripts/gsd_client.py（当前走 NTLM，未来可基于本脚本改 cookie 路径）。
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import requests


COOKIE_FILE = Path("~/.config/gsd/cookies.json").expanduser()
GSD_BASE = "https://apps.sha.roche.com/GSD"
GSD_POST = f"{GSD_BASE}/main/PostProcess"


def load_cookies(path: Path) -> list[dict]:
    if not path.exists():
        sys.exit(
            f"cookie file not found: {path}\n"
            f"  起 receiver: python3 ../receiver/cookie_receiver.py --config ../receiver/config.json\n"
            f"  扩展 popup 选 service=gsd 后点 Sync Now"
        )
    payload = json.loads(path.read_text(encoding="utf-8"))
    cookies = payload.get("cookies") or []
    if not cookies:
        sys.exit(f"no cookies in {path} — 浏览器登录 GSD 后再 Sync Now")
    return cookies


def make_session(cookies: list[dict]) -> requests.Session:
    s = requests.Session()
    for c in cookies:
        s.cookies.set(
            c["name"],
            c["value"],
            domain=c.get("domain", "").lstrip("."),
            path=c.get("path", "/"),
        )
    s.headers.update({
        "Accept": "application/json",
        "Content-Type": "application/json; charset=UTF-8",
        "X-Requested-With": "XMLHttpRequest",
    })
    return s


def call_post_process(session: requests.Session, owner: str, opid: str, content: str | dict = "") -> dict:
    payload = {
        "OwnerClass": owner,
        "OPID": opid,
        "Content": content if isinstance(content, str) else json.dumps(content),
        "Token": "",
        "FromFlag": 1,
        "Files": None,
        "IsOK": False,
        "ErrorCode": None,
        "ErrorMessage": "",
    }
    r = session.post(GSD_POST, json=payload, timeout=30)
    if r.status_code == 401:
        sys.exit("401 — cookie 无效或过期，浏览器重新登录后 Sync Now")
    if r.status_code != 200:
        sys.exit(f"HTTP {r.status_code}: {r.text[:300]}")
    return r.json()


def main() -> None:
    ap = argparse.ArgumentParser(description="GSD demo via browser cookie")
    ap.add_argument("--owner", default="AdminManager", help="OwnerClass (default: AdminManager)")
    ap.add_argument("--opid", default="GetUserMenu", help="OPID (default: GetUserMenu)")
    ap.add_argument("--content", default="false", help='Content payload (default: "false")')
    ap.add_argument("--cookie-file", default=str(COOKIE_FILE), help="cookie json path")
    args = ap.parse_args()

    cookies = load_cookies(Path(args.cookie_file).expanduser())
    print(f"[demo] loaded {len(cookies)} cookies from {args.cookie_file}", file=sys.stderr)

    session = make_session(cookies)
    print(f"[demo] POST {GSD_POST}  OwnerClass={args.owner} OPID={args.opid}", file=sys.stderr)

    data = call_post_process(session, args.owner, args.opid, args.content)
    if data.get("IsOK"):
        print("[demo] OK ✓ session 有效", file=sys.stderr)
    else:
        print(f"[demo] IsOK=false: {data.get('ErrorMessage', '')}", file=sys.stderr)

    print(json.dumps(data, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
