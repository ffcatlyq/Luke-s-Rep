"""
Google Workspace API 客户端，自动管理 token 刷新。

使用方式：
    from gw_client import get_drive_service, get_docs_service, get_sheets_service

    drive = get_drive_service()
    results = drive.files().list(pageSize=10).execute()

Token 加载优先级：
    1. 文件 /tmp/google_token.json（auth.py 授权后写入，永远是最新）
    2. 环境变量 GOOGLE_TOKEN_JSON（环境重建/新 shell 后的 fallback）

文件优先的原因：revoke + re-consent 后只有 /tmp 文件是新 token，
环境变量（来自 .bashrc 或 Ona Secret）可能仍是旧 token。
auth.py 完成授权时会自动 sync 新 token 到 ~/.bashrc。
"""
import json
import os
import sys

from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request
from google.auth.exceptions import RefreshError
from googleapiclient.discovery import build

TOKEN_PATH = "/tmp/google_token.json"
TOKEN_ENV = "GOOGLE_TOKEN_JSON"

SCOPES = [
    "https://www.googleapis.com/auth/drive",
    "https://www.googleapis.com/auth/documents",
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/gmail.modify",
    "https://www.googleapis.com/auth/gmail.settings.basic",
    "https://www.googleapis.com/auth/calendar",
    "https://www.googleapis.com/auth/presentations",
    # Google Chat API — full access
    "https://www.googleapis.com/auth/chat.messages",
    "https://www.googleapis.com/auth/chat.messages.readonly",
    "https://www.googleapis.com/auth/chat.messages.reactions",
    "https://www.googleapis.com/auth/chat.messages.reactions.readonly",
    "https://www.googleapis.com/auth/chat.messages.create",
    "https://www.googleapis.com/auth/chat.spaces",
    "https://www.googleapis.com/auth/chat.spaces.readonly",
    "https://www.googleapis.com/auth/chat.memberships",
    "https://www.googleapis.com/auth/chat.memberships.readonly",
    "https://www.googleapis.com/auth/chat.users.availability",
    "https://www.googleapis.com/auth/chat.users.availability.readonly",
    "https://www.googleapis.com/auth/chat.users.readstate.readonly",
    "https://www.googleapis.com/auth/chat.admin.memberships",
    "https://www.googleapis.com/auth/chat.delete",
    # People API — 解析 Chat sender ID 为姓名/邮箱
    "https://www.googleapis.com/auth/directory.readonly",
    # Cloud Search API — RocheHome search
    "https://www.googleapis.com/auth/cloud_search.query",
    # Google Forms API — read form structure & responses
    "https://www.googleapis.com/auth/forms.body.readonly",
    "https://www.googleapis.com/auth/forms.responses.readonly",
    # Google Tasks API — read/write personal todo lists
    "https://www.googleapis.com/auth/tasks",
    # Admin SDK Directory API — list domain calendar resources (rooms / equipment)
    "https://www.googleapis.com/auth/admin.directory.resource.calendar.readonly",
    # Search Console API — 搜索表现/属性只读（demos/search-console）
    "https://www.googleapis.com/auth/webmasters.readonly",
]


def _load_token_data() -> dict:
    """加载 token JSON，文件优先。

    revoke + re-consent 后只有 /tmp 文件是新 token，环境变量
    （.bashrc / Ona Secret）可能仍是旧的——优先文件能避免 invalid_grant。
    """
    if os.path.exists(TOKEN_PATH):
        with open(TOKEN_PATH) as f:
            return json.load(f)

    raw = os.environ.get(TOKEN_ENV)
    if raw:
        return json.loads(raw)

    print(f"❌ Token 未找到")
    print(f"   未设置环境变量 {TOKEN_ENV}，且文件 {TOKEN_PATH} 不存在。")
    print("   请先运行 auth.py 完成授权。")
    sys.exit(1)


def get_credentials() -> Credentials:
    """加载并自动刷新 OAuth credentials。

    如果 access_token 过期，用 refresh_token 自动刷新。
    刷新后回写到文件（如果 token 来源是文件）。
    """
    token_data = _load_token_data()
    # 用 token 自带的 scopes（实际授权的），不是代码 SCOPES（声明的）
    # 否则 refresh 时 Google 会因为请求未授权 scope 而返回 invalid_scope
    granted_scopes = token_data.get("scopes") or SCOPES
    creds = Credentials.from_authorized_user_info(token_data, granted_scopes)

    if creds.expired and creds.refresh_token:
        try:
            creds.refresh(Request())
        except RefreshError as e:
            msg = str(e)
            print("❌ Token 刷新失败。")
            if "invalid_grant" in msg:
                print("   refresh_token 已被 revoke 或过期（常见于用户在 myaccount.google.com 撤销访问后）。")
                print("   请运行 auth.py 重新授权：")
                print("     cd demos/google-workspace/scripts && python3 auth.py")
            else:
                print(f"   {msg}")
            sys.exit(1)
        # 回写刷新后的 token 到文件（方便下次直接用）
        token_data["token"] = creds.token
        with open(TOKEN_PATH, "w") as f:
            json.dump(token_data, f, indent=2)

    return creds


def get_drive_service():
    """返回 Google Drive API v3 service。"""
    return build("drive", "v3", credentials=get_credentials())


def get_docs_service():
    """返回 Google Docs API v1 service。"""
    return build("docs", "v1", credentials=get_credentials())


def get_sheets_service():
    """返回 Google Sheets API v4 service。"""
    return build("sheets", "v4", credentials=get_credentials())


def get_gmail_service():
    """返回 Gmail API v1 service。"""
    return build("gmail", "v1", credentials=get_credentials())


def get_calendar_service():
    """返回 Google Calendar API v3 service。"""
    return build("calendar", "v3", credentials=get_credentials())


def get_slides_service():
    """返回 Google Slides API v1 service。"""
    return build("slides", "v1", credentials=get_credentials())


def get_chat_service():
    """返回 Google Chat API v1 service。"""
    return build("chat", "v1", credentials=get_credentials())


def get_forms_service():
    """返回 Google Forms API v1 service。"""
    return build("forms", "v1", credentials=get_credentials())


def get_people_service():
    """返回 Google People API v1 service。"""
    return build("people", "v1", credentials=get_credentials())


def get_tasks_service():
    """返回 Google Tasks API service (v1)."""
    return build("tasks", "v1", credentials=get_credentials())


def get_admin_directory_service():
    """返回 Admin SDK Directory API v1 service（用于列 calendar resources / rooms）。"""
    return build("admin", "directory_v1", credentials=get_credentials())


def get_searchconsole_service():
    """返回 Google Search Console API v1 service（用于 demos/search-console 拉搜索表现）。"""
    return build("searchconsole", "v1", credentials=get_credentials())


if __name__ == "__main__":
    # 快速验证 token 是否有效
    creds = get_credentials()
    print(f"✅ Token 有效，过期时间: {creds.expiry}")
    print(f"   Scopes: {', '.join(creds.scopes or [])}")

    drive = get_drive_service()
    about = drive.about().get(fields="user").execute()
    user = about.get("user", {})
    print(f"   用户: {user.get('displayName')} ({user.get('emailAddress')})")
