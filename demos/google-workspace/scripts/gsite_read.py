"""
读取 Roche 内网 Google Sites（gSite）页面内容。

gSite 有两套独立的访问控制，本工具自动选路径：

  A. 源文件共享到你账号的 site —— Drive API 列得到，
     直接 drive.files().export(fileId, "text/plain") 拿全文。零额外配置。

  B. 没共享、按"组织内可见 / AD 组"发布的 site（如 published named
     site `/roche.com/<name>/...`）—— Drive 列不到本体，OAuth token
     也不能渲染网页（sites.google.com 只吃浏览器 SSO cookie）。
     只能走 cookie-bridge 同步的 google 登录 cookie 再 curl。

用法：
    # 自动选路径（推荐）：给 URL 或 site 名，先试 Drive，失败回退 cookie
    python3 gsite_read.py "https://sites.google.com/roche.com/integrated-evidence-planning/..."
    python3 gsite_read.py "罗氏制药中国"

    # 只列出 Drive 可见的 gSite（A 类，能直接 export 的）
    python3 gsite_read.py --list

    # 强制走某条路径
    python3 gsite_read.py <url|name> --via drive
    python3 gsite_read.py <url> --via cookie

cookie 路径前置（B 类 site 首次）：
    1. 浏览器登录目标 gSite（走完 Roche SSO）
    2. cookie-bridge 扩展 popup → service=gsite → Sync Now
       （host_permissions 含 sites.google.com 变更后需在 chrome://extensions 重载扩展）
    3. 重跑本脚本

数据敏感度：gSite 内容默认按 C3/C4 处理，导出的 .md/.txt 不进 hub，
落私 repo $WORKDOCS_PATH/ 或纯本地 /tmp/。
"""
import argparse
import json
import os
import sys
from pathlib import Path

from gw_client import get_drive_service

MIME_SITE = "application/vnd.google-apps.site"
COOKIE_FILE = Path("~/.config/gsite/cookies.json").expanduser()
COOKIE_ENV = "GSITE_COOKIES_JSON"


# ── A 类：Drive export ────────────────────────────────────────

def list_visible_sites(drive):
    """列出当前账号 Drive 可见的全部 gSite（源文件已共享给你的）。"""
    sites, token = [], None
    while True:
        r = drive.files().list(
            q=f"mimeType='{MIME_SITE}'",
            fields="nextPageToken, files(id,name,webViewLink)",
            pageSize=100, includeItemsFromAllDrives=True,
            supportsAllDrives=True, pageToken=token,
        ).execute()
        sites.extend(r.get("files", []))
        token = r.get("nextPageToken")
        if not token:
            break
    return sites


def find_site_by_name(drive, name):
    """按名字在可见 gSite 里找，返回 file dict 或 None。"""
    for s in list_visible_sites(drive):
        if s["name"] == name or name in s["name"]:
            return s
    return None


def read_via_drive(drive, file_id):
    """Drive export text/plain 拿全文。失败抛异常（让调用方回退 cookie）。"""
    content = drive.files().export(fileId=file_id, mimeType="text/plain").execute()
    return content.decode("utf-8", "ignore") if isinstance(content, bytes) else content


# ── B 类：cookie-bridge curl ──────────────────────────────────

def _load_cookies():
    raw = os.environ.get(COOKIE_ENV)
    if raw:
        payload = json.loads(raw)
    elif COOKIE_FILE.exists():
        payload = json.loads(COOKIE_FILE.read_text(encoding="utf-8"))
    else:
        print(f"❌ cookie 文件不存在: {COOKIE_FILE}")
        print(f"   也可通过 env 注入：export {COOKIE_ENV}=<json>")
        print("   或先跑 demos/browser-cookie-bridge：")
        print("     1. 浏览器登录目标 gSite（走完 Roche SSO）")
        print("     2. 扩展 popup → service=gsite → Sync Now")
        print("     3. host_permissions 变更后需在 chrome://extensions 重载扩展")
        sys.exit(1)
    cookies = payload.get("cookies") or []
    if not cookies:
        sys.exit(f"❌ cookie 列表为空: {COOKIE_FILE}")
    return cookies


def read_via_cookie(url):
    """带浏览器 SSO cookie GET 已发布 gSite 页面，返回正文文本。"""
    import requests

    try:
        from bs4 import BeautifulSoup
    except ImportError:
        BeautifulSoup = None

    session = requests.Session()
    session.headers["User-Agent"] = "Mozilla/5.0 (gsite_read/cookie)"
    for c in _load_cookies():
        session.cookies.set(
            c["name"], c["value"],
            domain=c.get("domain", "").lstrip("."),
            path=c.get("path", "/"),
        )
    resp = session.get(url, allow_redirects=True, timeout=30)
    final = resp.url
    if "accounts.google.com" in final or "signin" in final.lower():
        sys.exit(
            "❌ 被重定向到登录页 —— cookie 失效或缺失。\n"
            "   浏览器重新登录该 gSite → 扩展 service=gsite Sync Now → 重跑。"
        )
    html = resp.text
    if BeautifulSoup:
        soup = BeautifulSoup(html, "html.parser")
        for tag in soup(["script", "style", "noscript"]):
            tag.decompose()
        text = soup.get_text("\n")
        return "\n".join(line.strip() for line in text.splitlines() if line.strip())
    # 没装 bs4 时退回原始 HTML（提示用户）
    print("⚠️  未装 beautifulsoup4，输出原始 HTML（pip install beautifulsoup4 可转纯文本）", file=sys.stderr)
    return html


# ── 调度 ──────────────────────────────────────────────────────

def main():
    ap = argparse.ArgumentParser(description="读取 Roche 内网 gSite 页面内容")
    ap.add_argument("target", nargs="?", help="gSite URL 或 site 名")
    ap.add_argument("--list", action="store_true", help="列出 Drive 可见的 gSite（A 类）")
    ap.add_argument("--via", choices=["auto", "drive", "cookie"], default="auto",
                    help="强制路径（默认 auto：先 Drive 后 cookie）")
    ap.add_argument("--output", help="输出到文件（默认 stdout）")
    args = ap.parse_args()

    drive = get_drive_service()

    if args.list:
        sites = list_visible_sites(drive)
        print(f"Drive 可见 gSite: {len(sites)} 个（这些可直接 export，无需 cookie）\n")
        for s in sites:
            print(f"  {s['name']}\n    id={s['id']}  {s.get('webViewLink','')}")
        return

    if not args.target:
        ap.error("需要 target（URL 或 site 名），或用 --list")

    target = args.target
    is_url = target.startswith("http")
    text = None

    # 路径选择
    if args.via in ("auto", "drive"):
        # 按名字找；URL 无法直接映射到 fileId（published named site 不暴露 id），
        # 所以 URL 形态下 drive 路径只能靠名字匹配（取 URL 倒数第二段做模糊名）
        if is_url:
            guess = target.rstrip("/").split("/")[-2].replace("-", " ")
            site = find_site_by_name(drive, guess)
        else:
            site = find_site_by_name(drive, target)
        if site:
            try:
                text = read_via_drive(drive, site["id"])
                print(f"✅ Drive export 命中「{site['name']}」({len(text)} 字)", file=sys.stderr)
            except Exception as e:
                print(f"⚠️  Drive export 失败（{str(e)[:80]}），回退 cookie", file=sys.stderr)
        elif args.via == "drive":
            sys.exit("❌ Drive 可见列表里没找到该 site —— 它没共享给你，请用 --via cookie")
        else:
            print("ℹ️  Drive 列表无此 site（未共享），回退 cookie 路径", file=sys.stderr)

    if text is None and args.via in ("auto", "cookie"):
        if not is_url:
            sys.exit("❌ cookie 路径需要完整 URL（site 名无法定位已发布页面）")
        text = read_via_cookie(target)
        print(f"✅ cookie 路径读到 {len(text)} 字", file=sys.stderr)

    if text is None:
        sys.exit("❌ 两条路径都没拿到内容")

    if args.output:
        Path(args.output).write_text(text, encoding="utf-8")
        print(f"已写入 {args.output}", file=sys.stderr)
    else:
        try:
            print(text)
        except BrokenPipeError:
            # 下游管道（如 | head）提前关闭，正常退出不报栈
            try:
                sys.stdout.close()
            except Exception:
                pass


if __name__ == "__main__":
    main()
