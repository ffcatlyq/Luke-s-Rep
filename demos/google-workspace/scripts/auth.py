"""
Google Workspace OAuth 授权脚本（本地 HTTP server 模式）。

用法（通过 VS Code SSH 连接 Ona 环境）：
  1. 在 Ona 终端运行: python3 auth.py
  2. VS Code 自动将 19876 端口转发到本地
  3. 复制打印的 URL 到本地浏览器打开
  4. 在 Google consent 页面点 Allow
  5. 浏览器自动跳转到 localhost:19876/callback，脚本自动捕获 token

原理：
  脚本在 Ona 容器内启动 HTTP server 监听 19876 端口。
  VS Code SSH 端口转发将本地 localhost:19876 映射到容器内 19876。
  Google OAuth redirect 到 localhost:19876/callback 时，请求通过
  SSH 隧道到达容器内的 HTTP server，完成 code → token 交换。
"""
import json
import os
import re
import sys
import threading
from http.server import HTTPServer, BaseHTTPRequestHandler
from urllib.parse import urlparse, parse_qs

from google_auth_oauthlib.flow import Flow

from gw_client import SCOPES

PORT = 19876
TOKEN_PATH = "/tmp/google_token.json"
CLIENT_SECRET_PATH = "/tmp/oauth_client.json"
REDIRECT_URI = f"http://localhost:{PORT}/callback"

# 在 handler 和 main 之间传递 authorization code
auth_code = None
auth_error = None
server_ready = threading.Event()
code_received = threading.Event()


class OAuthCallbackHandler(BaseHTTPRequestHandler):
    """处理 Google OAuth callback，提取 authorization code。"""

    def do_GET(self):
        global auth_code, auth_error

        parsed = urlparse(self.path)
        params = parse_qs(parsed.query)

        if parsed.path == "/callback":
            error = params.get("error", [None])[0]
            if error:
                auth_error = error
                self._respond(
                    400,
                    f"❌ 授权失败: {error}\n\n可以关闭此页面。",
                )
                code_received.set()
                return

            code = params.get("code", [None])[0]
            if code:
                auth_code = code
                self._respond(
                    200,
                    "✅ 授权成功！已收到 authorization code。\n\n可以关闭此页面，回到终端查看结果。",
                )
                code_received.set()
                return

        self._respond(404, "Not found")

    def _respond(self, status, message):
        self.send_response(status)
        self.send_header("Content-Type", "text/plain; charset=utf-8")
        self.end_headers()
        self.wfile.write(message.encode("utf-8"))

    def log_message(self, format, *args):
        """静默 HTTP 日志，避免干扰终端输出。"""
        pass


def setup_client_secret():
    """从环境变量写入临时 client secret 文件。"""
    raw = os.environ.get("GOOGLE_OAUTH_CLIENT_JSON")
    if not raw:
        print("❌ 环境变量 GOOGLE_OAUTH_CLIENT_JSON 未设置")
        print()
        print("设置方式：")
        print('  export GOOGLE_OAUTH_CLIENT_JSON=\'{"installed":{...}}\'')
        print()
        print("JSON 内容从 GCP Console → APIs & Services → Credentials")
        print("→ OAuth 2.0 Client IDs → Download JSON 获取。")
        sys.exit(1)
    with open(CLIENT_SECRET_PATH, "w") as f:
        f.write(raw)


def start_callback_server():
    """在后台线程启动 HTTP server 监听 callback。"""
    server = HTTPServer(("0.0.0.0", PORT), OAuthCallbackHandler)
    server_ready.set()

    while not code_received.is_set():
        server.handle_request()

    server.server_close()


def sync_to_bashrc(token_data):
    """如果 ~/.bashrc 已经维护了 GOOGLE_TOKEN_JSON，自动更新为新 token。

    revoke + re-consent 后 .bashrc 里的旧 token 会污染新 shell——
    这里替换为新 token 的紧凑单行 JSON。仅在 .bashrc 已有这一行时
    才更新（避免对没用这个模式的用户引入新行为）。
    """
    bashrc = os.path.expanduser("~/.bashrc")
    if not os.path.exists(bashrc):
        return False

    with open(bashrc) as f:
        content = f.read()

    pattern = r"^export GOOGLE_TOKEN_JSON=.*$"
    if not re.search(pattern, content, flags=re.MULTILINE):
        return False

    compact = json.dumps(token_data, separators=(",", ":"))
    new_line = f"export GOOGLE_TOKEN_JSON='{compact}'"
    new_content = re.sub(pattern, new_line, content, flags=re.MULTILINE)

    with open(bashrc, "w") as f:
        f.write(new_content)
    os.chmod(bashrc, 0o600)
    return True


def verify_token(token_data):
    """用获取的 token 调用 Drive API 验证。"""
    from googleapiclient.discovery import build
    from google.oauth2.credentials import Credentials

    creds = Credentials.from_authorized_user_info(token_data, SCOPES)
    service = build("drive", "v3", credentials=creds)
    results = (
        service.files()
        .list(pageSize=5, fields="files(id, name, mimeType)")
        .execute()
    )
    files = results.get("files", [])

    if files:
        print(f"\n✅ Drive API 验证成功！前 {len(files)} 个文件：")
        for f in files:
            print(f"   {f['name']} ({f['mimeType']})")
    else:
        print("\n⚠️ Drive API 连接成功，但未找到文件。")


def main():
    setup_client_secret()

    # 1. 启动 callback server
    server_thread = threading.Thread(target=start_callback_server, daemon=True)
    server_thread.start()
    server_ready.wait()
    print(f"✅ Callback server 已启动，监听端口 {PORT}")

    # 2. 生成授权 URL
    flow = Flow.from_client_secrets_file(
        CLIENT_SECRET_PATH,
        scopes=SCOPES,
        redirect_uri=REDIRECT_URI,
    )

    auth_url, state = flow.authorization_url(
        access_type="offline",
        include_granted_scopes="true",
        prompt="consent",
    )

    print()
    print("=" * 60)
    print("在本地浏览器中打开以下 URL 完成授权：")
    print("=" * 60)
    print(auth_url)
    print("=" * 60)
    print()
    print("确保 VS Code 已将端口 19876 转发到本地。")
    print("点击 Allow 后，浏览器会自动跳转，脚本自动完成。")
    print()
    print("等待授权回调...")

    # 3. 等待 callback（最多 5 分钟）
    if not code_received.wait(timeout=300):
        print("\n❌ 等待超时（5 分钟），请重新运行。")
        sys.exit(1)

    if auth_error:
        print(f"\n❌ 授权失败: {auth_error}")
        sys.exit(1)

    if not auth_code:
        print("\n❌ 未收到 authorization code")
        sys.exit(1)

    print("✅ 收到 authorization code，正在交换 token...")

    # 4. 用 code 换 token
    flow.fetch_token(code=auth_code)
    creds = flow.credentials

    token_data = {
        "token": creds.token,
        "refresh_token": creds.refresh_token,
        "token_uri": creds.token_uri,
        "client_id": creds.client_id,
        "client_secret": creds.client_secret,
        "scopes": list(creds.scopes),
    }
    with open(TOKEN_PATH, "w") as f:
        json.dump(token_data, f, indent=2)

    print(f"✅ Token 已保存到 {TOKEN_PATH}")

    # 5. 验证
    verify_token(token_data)

    # 6. 自动同步到 ~/.bashrc（如果已经维护了 GOOGLE_TOKEN_JSON）
    if sync_to_bashrc(token_data):
        print()
        print("✅ Token 已同步到 ~/.bashrc（chmod 600）。新 shell 会用这个 token。")
        print("   如需当前 shell 立刻生效：source ~/.bashrc")

    # 7. 提示持久化到 Ona secret
    print()
    print("=" * 60)
    print("将 token 存入 Ona Project Secret 以避免环境重建后重新授权：")
    print("=" * 60)
    print()
    print("  1. 打开 Ona Web UI → Project → Secrets")
    print("  2. New Secret → Type: Environment variable")
    print(f"  3. Name: GOOGLE_TOKEN_JSON")
    print(f"  4. Value: 粘贴以下 JSON（一行）：")
    print()
    print(json.dumps(token_data))
    print()
    print("存入后，gw_client.py 会优先从环境变量加载 token，")
    print("环境重建后无需重新运行 auth.py。")
    print("=" * 60)


if __name__ == "__main__":
    main()
