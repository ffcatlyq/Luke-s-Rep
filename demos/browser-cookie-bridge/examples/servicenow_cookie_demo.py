#!/usr/bin/env python3
"""ServiceNow demo - 用浏览器同步过来的 cookie 调 ServiceNow REST API。

前置条件:
  1. Chrome 已经走 SAML SSO 登录 ServiceNow (https://roche.service-now.com/)
  2. cookie_receiver.py 在 WSL2 跑，service=servicenow 配置已加
  3. 扩展同步过 cookie，~/.config/servicenow/cookies.json 存在

用法:
    python3 servicenow_cookie_demo.py                      # 默认查 1 条 incident
    python3 servicenow_cookie_demo.py --table sys_user --query "user_name=javascript:gs.getUserName()"
    python3 servicenow_cookie_demo.py --whoami             # 查当前登录身份

注意:
  WSL2 部分公司网络环境不通 ServiceNow SaaS，DNS 解析或 TCP 连接会超时。
  跑不通时改用 examples/servicenow_via_windows.sh（通过 powershell.exe 反向调 Windows curl）。
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

import requests


COOKIE_FILE = Path("~/.config/servicenow/cookies.json").expanduser()
SNOW_BASE = "https://roche.service-now.com"
# /api/now/* REST API 不接受 SAML cookie auth，必须配合 g_ck (Glide CSRF token) 作为 X-UserToken。
# g_ck 嵌在登录后的 UI 页面 HTML 里。
GCK_PATTERN = re.compile(r'g_ck\s*=\s*["\']([0-9a-f]{40,80})["\']')
HOMEPAGE_FOR_GCK = f"{SNOW_BASE}/now/nav/ui/classic/params/target/home_splash.do"


def load_cookies(path: Path) -> list[dict]:
    if not path.exists():
        sys.exit(
            f"cookie file not found: {path}\n"
            f"  浏览器登录 ServiceNow 后扩展 popup 选 service=servicenow → Sync Now"
        )
    payload = json.loads(path.read_text(encoding="utf-8"))
    cookies = payload.get("cookies") or []
    if not cookies:
        sys.exit(f"no cookies in {path}")
    print(f"[demo] loaded {len(cookies)} cookies (synced at {payload['_meta'].get('synced_at')})", file=sys.stderr)
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
        # 像浏览器一点。某些 ServiceNow 实例对纯库标识 UA 做了限制
        "User-Agent": "Mozilla/5.0 (browser-cookie-bridge-demo) ServiceNow REST",
    })
    return s


def fetch_g_ck(session: requests.Session) -> str:
    """从登录后的 UI 主页抓 g_ck token。

    ServiceNow 的 /api/now/* REST 端点不认 SAML cookie，必须配合 X-UserToken header
    (= g_ck) 才能 200。g_ck 嵌在 UI 页面的 inline JS 里。
    """
    print(f"[demo] fetching g_ck from UI page...", file=sys.stderr)
    r = session.get(HOMEPAGE_FOR_GCK, timeout=15, allow_redirects=True)
    if r.status_code != 200:
        sys.exit(f"❌ 拿 g_ck 失败 HTTP {r.status_code}\n  cookie 可能已失效，浏览器重新登录后 Sync Now")
    m = GCK_PATTERN.search(r.text)
    if not m:
        sys.exit("❌ HTML 里没找到 g_ck，ServiceNow 实例可能 UI 路径不一样\n  改 HOMEPAGE_FOR_GCK 常量或换其他 endpoint")
    g_ck = m.group(1)
    print(f"[demo] g_ck obtained: {g_ck[:16]}... (len={len(g_ck)})", file=sys.stderr)
    return g_ck


def query_table(session: requests.Session, table: str, query: str = "", limit: int = 1, fields: str = "") -> dict:
    params = {"sysparm_limit": limit}
    if query:
        params["sysparm_query"] = query
    if fields:
        params["sysparm_fields"] = fields
    url = f"{SNOW_BASE}/api/now/table/{table}"
    print(f"[demo] GET {url}  params={params}", file=sys.stderr)
    # 必须带 X-UserToken (g_ck) 才能调通 REST API
    if "X-UserToken" not in session.headers:
        session.headers["X-UserToken"] = fetch_g_ck(session)
    r = session.get(url, params=params, timeout=30, allow_redirects=False)

    # 302 通常是被踢去 SSO 登录页（cookie 失效）
    if r.status_code in (301, 302):
        loc = r.headers.get("Location", "")
        sys.exit(f"❌ HTTP {r.status_code} → {loc[:120]}\n  cookie 无效或过期，浏览器重新登录 ServiceNow 后 Sync Now")
    if r.status_code == 401:
        sys.exit("❌ 401 Unauthorized — cookie 无效，浏览器重新登录后 Sync Now")
    if r.status_code != 200:
        sys.exit(f"❌ HTTP {r.status_code}: {r.text[:300]}")

    return r.json()


def main() -> None:
    ap = argparse.ArgumentParser(description="ServiceNow demo via browser cookie")
    ap.add_argument("--table", default="incident", help="table name (default: incident)")
    ap.add_argument("--query", default="", help="sysparm_query")
    ap.add_argument("--limit", type=int, default=1, help="sysparm_limit (default 1)")
    ap.add_argument("--fields", default="", help="sysparm_fields (comma-separated)")
    ap.add_argument("--whoami", action="store_true", help="查当前登录身份")
    ap.add_argument("--cookie-file", default=str(COOKIE_FILE), help="cookie json path")
    args = ap.parse_args()

    cookies = load_cookies(Path(args.cookie_file).expanduser())
    session = make_session(cookies)

    if args.whoami:
        # 走 sys_user 表，按 javascript:gs.getUserName() 查当前登录用户
        data = query_table(
            session,
            "sys_user",
            query="user_name=javascript:gs.getUserName()",
            limit=1,
            fields="user_name,name,email,sys_id,active",
        )
        results = data.get("result", [])
        if not results:
            sys.exit("❌ whoami 返回空，cookie 可能身份异常")
        u = results[0]
        print(f"[demo] OK ✓ session 有效", file=sys.stderr)
        print(f"  user_name: {u.get('user_name')}")
        print(f"  name:      {u.get('name')}")
        print(f"  email:     {u.get('email')}")
        print(f"  sys_id:    {u.get('sys_id')}")
        print(f"  active:    {u.get('active')}")
        return

    fields = args.fields or ("number,short_description,state,sys_created_on" if args.table == "incident" else "")
    data = query_table(session, args.table, args.query, args.limit, fields)
    results = data.get("result", [])
    print(f"[demo] OK ✓ 查到 {len(results)} 条 {args.table}", file=sys.stderr)
    print(json.dumps(data, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
