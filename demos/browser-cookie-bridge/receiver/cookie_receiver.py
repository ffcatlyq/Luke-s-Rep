#!/usr/bin/env python3
"""Browser Cookie Bridge - 本地 receiver。

监听 127.0.0.1:<port>，接收浏览器扩展推送的 cookie，按 service 配置写到对应文件。

启动:
    python3 cookie_receiver.py --config config.json

可选参数:
    --port <int>       指定端口（默认随机 1024-65535）
    --token <str>      指定 token（默认随机生成）
    --host <str>       绑定 host（默认 127.0.0.1，不要改成 0.0.0.0）
    --name <str>       receiver 标识名（/health 返回，多 receiver 辨识用）；
                       默认取 config 顶层 "name"，再兜底 hostname

接口:
    GET  /health       存活检查（无认证）
    POST /sync         接收 cookie（要 Authorization: Bearer <token>）

请求体:
    {"service": "gsd", "cookies": [{"name": "...", "value": "...", "domain": "...", ...}]}

响应:
    200  {"ok": true, "written": "/path/to/cookies.json"}
    401  {"ok": false, "error": "invalid token"}
    400  {"ok": false, "error": "..."}
"""
from __future__ import annotations

import argparse
import json
import os
import secrets
import sys
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Any

# 落盘逻辑（域过滤 + 原子写 mode 600 + bearer 旁路 + config schema）的 SSOT 在 cookie_sink，
# gdrive_cookie_sync.py 也 import 同一份，两个 transport 落盘行为一致。
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from cookie_sink import (  # noqa: E402
    now_iso, load_config, write_service_payload, UnknownService,
)


# 仅允许扩展 origin。Edge / Chrome 扩展是 chrome-extension://，Firefox 是 moz-extension://。
ALLOWED_ORIGIN_PREFIXES = ("chrome-extension://", "moz-extension://", "edge-extension://")


def log(msg: str) -> None:
    print(f"[bridge {now_iso()}] {msg}", flush=True)


class Handler(BaseHTTPRequestHandler):
    server_version = "BrowserCookieBridge/0.1"

    # 关掉 BaseHTTPRequestHandler 默认 stderr 日志，统一走 log()。
    def log_message(self, fmt: str, *args: Any) -> None:
        pass

    @property
    def cfg(self) -> dict:
        return self.server.cfg  # type: ignore[attr-defined]

    @property
    def token(self) -> str:
        return self.server.token  # type: ignore[attr-defined]

    @property
    def name(self) -> str:
        return self.server.name  # type: ignore[attr-defined]

    def _cors_headers(self) -> None:
        origin = self.headers.get("Origin", "")
        if any(origin.startswith(p) for p in ALLOWED_ORIGIN_PREFIXES):
            self.send_header("Access-Control-Allow-Origin", origin)
            self.send_header("Access-Control-Allow-Methods", "POST, GET, OPTIONS")
            self.send_header("Access-Control-Allow-Headers", "Authorization, Content-Type")
            self.send_header("Access-Control-Max-Age", "600")
            # Chrome Private Network Access (PNA): chrome-extension:// fetch 到 127.0.0.1
            # 必须带这个 header，否则 Chrome 102+ 直接 block。
            self.send_header("Access-Control-Allow-Private-Network", "true")

    def _json(self, status: int, body: dict) -> None:
        data = json.dumps(body).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(data)))
        self._cors_headers()
        self.end_headers()
        self.wfile.write(data)

    def do_OPTIONS(self) -> None:  # noqa: N802
        self.send_response(204)
        self._cors_headers()
        self.end_headers()

    def do_GET(self) -> None:  # noqa: N802
        if self.path == "/health":
            # 返回 service 名字列表 + 每个 service 的 domains 和 keepAlivePath（output 路径不暴露）。
            # keepAlivePath 缺则不返字段；扩展据此决定是否给该 service 注册 keep-alive alarm。
            services_summary = {}
            for name, svc in self.cfg["services"].items():
                detail: dict = {"domains": svc.get("domains", [])}
                if svc.get("keepAlivePath"):
                    detail["keepAlivePath"] = svc["keepAlivePath"]
                # captureBearer：透传给扩展，让它给该 service 的域挂 webRequest 抓 Bearer。
                # （output/tokenOutput 等落盘路径不暴露，captureBearer 只是个开关布尔，可暴露。）
                if svc.get("captureBearer"):
                    detail["captureBearer"] = True
                services_summary[name] = detail
            self._json(200, {
                "ok": True,
                "version": "0.1",
                # name：receiver 标识（env/config/hostname，见 main()）。多 receiver 扇出时
                # popup 逐行拉 /health 显示「端口 → name」辨识容器。非敏感——别塞 secret。
                "name": self.name,
                "services": list(self.cfg["services"].keys()),  # 旧字段保留兼容
                "services_detail": services_summary,
            })
            return
        self._json(404, {"ok": False, "error": "not found"})

    def do_POST(self) -> None:  # noqa: N802
        if self.path != "/sync":
            self._json(404, {"ok": False, "error": "not found"})
            return

        # token 校验
        auth = self.headers.get("Authorization", "")
        expected = f"Bearer {self.token}"
        if not auth or not secrets.compare_digest(auth, expected):
            log(f"sync rejected: invalid token from {self.client_address[0]}")
            self._json(401, {"ok": False, "error": "invalid token"})
            return

        # 读 body
        try:
            length = int(self.headers.get("Content-Length", "0"))
            if length <= 0 or length > 1_000_000:  # 1MB 上限
                self._json(400, {"ok": False, "error": "bad content-length"})
                return
            raw = self.rfile.read(length)
            payload = json.loads(raw)
        except (ValueError, json.JSONDecodeError) as e:
            self._json(400, {"ok": False, "error": f"bad json: {e}"})
            return

        service = payload.get("service")
        cookies = payload.get("cookies")
        if not isinstance(service, str) or not isinstance(cookies, list):
            self._json(400, {"ok": False, "error": "missing service or cookies"})
            return

        # 域过滤 + 落盘 + bearer 旁路：走共享 SSOT（cookie_sink.write_service_payload），
        # gdrive transport 消费端用的是同一份逻辑，落盘格式一致。
        try:
            summary = write_service_payload(self.cfg, service, cookies, payload.get("bearer"))
        except UnknownService:
            self._json(400, {"ok": False, "error": f"unknown service: {service}"})
            return
        except OSError as e:
            log(f"sync error service={service} write failed: {e}")
            self._json(500, {"ok": False, "error": f"write failed: {e}"})
            return

        if summary["cookie_count"] == 0:
            log(f"sync warn service={service} got {len(cookies)} cookies but none match allowed domains")
        domain_summary = ",".join(summary["domains"]) or "(none)"
        tok_note = f" token->{summary['token_written']}" if summary["token_written"] else ""
        log(f"sync ok service={service} domain={domain_summary} cookies={summary['cookie_count']} -> {summary['written']}{tok_note}")
        self._json(200, {"ok": True, "written": summary["written"], "cookie_count": summary["cookie_count"],
                         "token_written": summary["token_written"]})


def pick_port() -> int:
    """从内核拿一个空闲端口（绑定 0 让 OS 分配，立即关闭，复用号码）。"""
    import socket
    s = socket.socket()
    s.bind(("127.0.0.1", 0))
    p = s.getsockname()[1]
    s.close()
    return p


def main() -> None:
    parser = argparse.ArgumentParser(description="Browser Cookie Bridge receiver")
    parser.add_argument("--config", required=True, help="path to config.json")
    parser.add_argument("--host", default="127.0.0.1", help="bind host (default: 127.0.0.1)")
    parser.add_argument("--port", type=int, default=0, help="bind port (default: random)")
    parser.add_argument("--token", default="", help="override token (default: random 32 bytes)")
    parser.add_argument("--name", default="", help="receiver identifier for /health (default: config 'name' or hostname)")
    args = parser.parse_args()

    if args.host != "127.0.0.1":
        log(f"WARN host={args.host} is not 127.0.0.1, make sure you know what you're doing")

    cfg = load_config(Path(args.config).expanduser())
    token = args.token or secrets.token_urlsafe(32)
    port = args.port or pick_port()
    # name 解析：--name（来自 COOKIE_BRIDGE_RECEIVER_NAME）> config 顶层 "name" > hostname 兜底。
    import socket
    name = args.name or cfg.get("name") or socket.gethostname()

    # ThreadingHTTPServer：每请求一线程，避免单线程被高频 auto-sync（浏览 google/youtube 时
    # cookie 每秒变、扩展狂打 /sync）打满 → 手动 sync / /health 排队超时。daemon_threads 默认 True。
    server = ThreadingHTTPServer((args.host, port), Handler)
    server.daemon_threads = True
    server.cfg = cfg          # type: ignore[attr-defined]
    server.token = token      # type: ignore[attr-defined]
    server.name = name        # type: ignore[attr-defined]

    log(f"listening on http://{args.host}:{port}")
    log(f"name: {name}")
    log(f"token: {token}")
    log(f"services: {', '.join(cfg['services'].keys())}")
    log("ready. Ctrl+C to stop.")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        log("shutting down")
        server.server_close()


if __name__ == "__main__":
    main()
