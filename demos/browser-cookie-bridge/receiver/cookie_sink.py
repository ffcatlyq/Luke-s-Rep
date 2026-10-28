#!/usr/bin/env python3
"""cookie-bridge 落盘 SSOT —— 「给定 {service, cookies, bearer} → 域过滤 + 写文件」的唯一实现。

两个消费端共享这套逻辑，避免双写：
  · cookie_receiver.py（local transport，HTTP POST → WSL/build-cli）
  · gdrive_cookie_sync.py（gdrive transport，Drive 密文 → Ona 容器）

两端落盘格式、域过滤、mode 600、bearer 旁路必须完全一致，业务脚本（shortlink_client.py 等）
才能零改动复用。改落盘行为只改这一处。
"""
from __future__ import annotations

import datetime as _dt
import json
import os
import sys
import tempfile
from pathlib import Path


def now_iso() -> str:
    return _dt.datetime.now(_dt.timezone.utc).astimezone().isoformat(timespec="seconds")


def expand_path(p: str) -> Path:
    return Path(os.path.expandvars(os.path.expanduser(p)))


def atomic_write_json(path: Path, payload: dict) -> None:
    """原子写：tmp + rename，避免读到半截文件。mode 600。"""
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, tmp = tempfile.mkstemp(prefix=".cookies-", dir=str(path.parent))
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as f:
            json.dump(payload, f, ensure_ascii=False, indent=2)
        os.chmod(tmp, 0o600)
        os.replace(tmp, path)
    except Exception:
        if os.path.exists(tmp):
            os.unlink(tmp)
        raise


def load_config(path: Path) -> dict:
    if not path.exists():
        sys.exit(f"config not found: {path}\n  cp config.example.json config.json")
    cfg = json.loads(path.read_text(encoding="utf-8"))
    services = cfg.get("services", {})
    if not isinstance(services, dict) or not services:
        sys.exit("config.services is empty")
    for name, svc in services.items():
        if not isinstance(svc, dict):
            sys.exit(f"config.services.{name} must be object")
        if not svc.get("domains") or not svc.get("output"):
            sys.exit(f"config.services.{name} requires domains and output")
    return cfg


def cookie_matches(cookie_domain: str, allowed_domains: set[str]) -> bool:
    """RFC 6265 §5.1.3 domain matching：cookie 属于 host H 当 cookie domain == H 或为 H 的祖先域。
    例 .roche.com 的 PF / XSRF-TOKEN 也应保留给 cidm.roche.com。"""
    cd = (cookie_domain or "").lstrip(".").lower()
    if not cd:
        return False
    return any(sd == cd or sd.endswith("." + cd) for sd in allowed_domains)


class UnknownService(Exception):
    """service 不在 config 里。"""


def write_service_payload(cfg: dict, service: str, cookies: list, bearer: str | None = None) -> dict:
    """域过滤 + 落盘 cookies.json（+ bearer 旁路 tokenOutput）。SSOT，两端共用。

    返回 summary：{written, cookie_count, token_written, domains, kept, dropped}。
    raises UnknownService（service 不在 cfg）/ OSError（写失败）。
    """
    svc_cfg = cfg["services"].get(service)
    if not svc_cfg:
        raise UnknownService(service)

    allowed = {d.lstrip(".").lower() for d in svc_cfg.get("domains", [])}
    kept = [c for c in cookies if cookie_matches(c.get("domain", ""), allowed)]

    out_path = expand_path(svc_cfg["output"])
    atomic_write_json(out_path, {
        "_meta": {
            "service": service,
            "synced_at": now_iso(),
            "cookie_count": len(kept),
            "domains": sorted({c.get("domain", "") for c in kept}),
        },
        "cookies": kept,
    })

    # bearer 旁路：仅当 service 声明 tokenOutput 才落。token 不与 cookie 混写（敏感度/生命周期不同）。
    token_written = None
    token_out_cfg = svc_cfg.get("tokenOutput")
    if bearer and isinstance(bearer, str) and token_out_cfg:
        tok_path = expand_path(token_out_cfg)
        atomic_write_json(tok_path, {
            "_meta": {"service": service, "synced_at": now_iso()},
            "bearer": bearer.strip(),
        })
        token_written = str(tok_path)

    return {
        "written": str(out_path),
        "cookie_count": len(kept),
        "token_written": token_written,
        "domains": sorted({c.get("domain", "") for c in kept}),
        "kept": len(kept),
        "dropped": len(cookies) - len(kept),
    }
