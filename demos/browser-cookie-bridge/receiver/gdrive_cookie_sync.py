#!/usr/bin/env python3
"""cookie-bridge gdrive transport —— Ona 侧消费端。

把浏览器扩展加密上传到 Google Drive 的 cookie 密文，落到本机 ~/.config/<service>/cookies.json，
让业务脚本（shortlink_client.py 等）零改动复用。是 local receiver 的「另一条出口」，不是替代。

数据流：
    [扩展] AES-GCM 加密 -> Drive: My Drive/.cookie-bridge/<service>.enc
                                        |
    [本脚本] gw_client 读 -> 解密 -> cookie_sink.write_service_payload 落盘 (mode 600)
                                        |
                                  异步即焚：删 Drive 密文

用法（先 export COOKIE_BRIDGE_PASSPHRASE，与扩展 popup 里填的同一口令）：
    python3 gdrive_cookie_sync.py --config config.json                # 单次，消费所有 service
    python3 gdrive_cookie_sync.py --config config.json --service cidm # 单次，仅 cidm
    python3 gdrive_cookie_sync.py --config config.json --watch        # 轮询常驻（见下方告警）
    python3 gdrive_cookie_sync.py --config config.json --reap         # 只清理超 TTL 的孤儿密文

默认 on-demand 单次。--watch 是 footgun：Ona 容器 ephemeral，watcher 随 rebuild 死掉则即焚
不再触发、密文在 Drive 堆积。故 --watch 每轮附带 TTL 孤儿清理（--ttl，默认 1h）作 backstop。
低频场景（ford onboard 偶尔一次）建议单次跑，别常驻。
"""
from __future__ import annotations

import argparse
import datetime as _dt
import io
import json
import os
import sys
import time
from pathlib import Path

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from cookie_sink import load_config, write_service_payload, UnknownService  # noqa: E402
from cookie_crypto import decrypt_envelope, PassphraseMismatch  # noqa: E402

FOLDER = ".cookie-bridge"
FOLDER_MIME = "application/vnd.google-apps.folder"
ENC_SUFFIX = ".enc"


def log(msg: str) -> None:
    ts = _dt.datetime.now(_dt.timezone.utc).astimezone().isoformat(timespec="seconds")
    print(f"[gdrive-sync {ts}] {msg}", flush=True)


def _import_gw_client():
    """gw_client 是 google-workspace demo 的 auth SSOT，按需 import（避免硬依赖装不上时整脚本挂）。
    路径：本 demo 在 demos/browser-cookie-bridge/receiver/，gw_client 在 demos/google-workspace/scripts/。
    可用 GW_CLIENT_DIR 覆盖。"""
    override = os.environ.get("GW_CLIENT_DIR")
    candidates = [override] if override else []
    # 从 receiver/ 往上找 demos/ 根，再拼 google-workspace/scripts
    p = Path(HERE)
    for _ in range(6):
        if (p / "demos" / "google-workspace" / "scripts" / "gw_client.py").exists():
            candidates.append(str(p / "demos" / "google-workspace" / "scripts"))
            break
        p = p.parent
    for c in candidates:
        if c and (Path(c) / "gw_client.py").exists():
            sys.path.insert(0, c)
            import gw_client  # type: ignore
            return gw_client
    sys.exit("找不到 gw_client.py —— 设 GW_CLIENT_DIR 指向 demos/google-workspace/scripts")


def find_folder_id(drive):
    q = (f"name='{FOLDER}' and mimeType='{FOLDER_MIME}' "
         f"and trashed=false and 'me' in owners")
    hits = drive.files().list(q=q, fields="files(id)", spaces="drive").execute().get("files", [])
    return hits[0]["id"] if hits else None


def list_enc_files(drive, folder_id, only_service=None):
    q = f"'{folder_id}' in parents and trashed=false"
    files = drive.files().list(
        q=q, fields="files(id,name,modifiedTime,size)", spaces="drive"
    ).execute().get("files", [])
    out = []
    for f in files:
        if not f["name"].endswith(ENC_SUFFIX):
            continue
        service = f["name"][: -len(ENC_SUFFIX)]
        if only_service and service != only_service:
            continue
        out.append((service, f))
    return out


def download_bytes(drive, file_id) -> bytes:
    from googleapiclient.http import MediaIoBaseDownload
    buf = io.BytesIO()
    dl = MediaIoBaseDownload(buf, drive.files().get_media(fileId=file_id))
    done = False
    while not done:
        _, done = dl.next_chunk()
    return buf.getvalue()


def _age_seconds(modified_time: str) -> float:
    # Drive RFC3339 e.g. 2026-06-30T11:38:03.551Z
    t = _dt.datetime.fromisoformat(modified_time.replace("Z", "+00:00"))
    return (_dt.datetime.now(_dt.timezone.utc) - t).total_seconds()


def consume_once(drive, cfg, passphrase, only_service=None) -> int:
    """消费一轮：读→解密→落盘→即焚。返回成功落盘的 service 数。"""
    folder_id = find_folder_id(drive)
    if not folder_id:
        log("no .cookie-bridge folder on Drive (nothing to consume)")
        return 0
    targets = list_enc_files(drive, folder_id, only_service)
    if not targets:
        log("no .enc to consume" + (f" for service={only_service}" if only_service else ""))
        return 0

    ok = 0
    for service, f in targets:
        try:
            blob = download_bytes(drive, f["id"])
            envelope = json.loads(blob)
        except Exception as e:  # noqa: BLE001
            log(f"skip service={service}: read/parse failed: {e}")
            continue
        try:
            plaintext = decrypt_envelope(envelope, passphrase)
        except PassphraseMismatch:
            # 不删——让用户改对口令后重试。这是 review finding #5 要的明确报错。
            log(f"FAIL service={service}: passphrase mismatch（不即焚，改对 COOKIE_BRIDGE_PASSPHRASE 后重跑）")
            continue
        try:
            payload = json.loads(plaintext)
        except json.JSONDecodeError as e:
            log(f"skip service={service}: decrypted payload not JSON: {e}")
            continue

        body_service = payload.get("service", service)
        cookies = payload.get("cookies", [])
        bearer = payload.get("bearer")
        try:
            summary = write_service_payload(cfg, body_service, cookies, bearer)
        except UnknownService:
            log(f"skip service={body_service}: not in config.services")
            continue
        except OSError as e:
            log(f"FAIL service={body_service}: write failed: {e}（不即焚）")
            continue

        tok = f" token->{summary['token_written']}" if summary["token_written"] else ""
        log(f"ok service={body_service} cookies={summary['cookie_count']} "
            f"(dropped {summary['dropped']}) -> {summary['written']}{tok}")
        ok += 1
        # 异步即焚：落盘成功后才删 Drive 密文（落盘失败上面已 continue 不删）
        try:
            drive.files().delete(fileId=f["id"]).execute()
            log(f"   即焚: deleted Drive {f['name']} ({f['id']})")
        except Exception as e:  # noqa: BLE001
            log(f"   warn: 即焚 delete failed for {f['id']}: {e}（密文仍在 Drive，下轮重试）")
    return ok


def reap_orphans(drive, ttl_seconds: int, only_service=None) -> int:
    """清理超 TTL 的孤儿密文（backstop：没消费端跑时密文不会无限堆积）。"""
    folder_id = find_folder_id(drive)
    if not folder_id:
        return 0
    reaped = 0
    for service, f in list_enc_files(drive, folder_id, only_service):
        age = _age_seconds(f["modifiedTime"])
        if age > ttl_seconds:
            try:
                drive.files().delete(fileId=f["id"]).execute()
                log(f"reaped orphan {f['name']} (age {int(age)}s > ttl {ttl_seconds}s)")
                reaped += 1
            except Exception as e:  # noqa: BLE001
                log(f"warn: reap failed {f['id']}: {e}")
    return reaped


def main() -> None:
    ap = argparse.ArgumentParser(description="cookie-bridge gdrive transport: Ona 消费端")
    ap.add_argument("--config", default="config.json", help="config.json（与 receiver 同一份）；不存在时自动回退 config.example.json")
    ap.add_argument("--service", default=None, help="只消费某个 service（默认全部）")
    ap.add_argument("--watch", action="store_true", help="轮询常驻（ephemeral 容器慎用，见模块 docstring）")
    ap.add_argument("--interval", type=int, default=30, help="--watch 轮询间隔秒（默认 30）")
    ap.add_argument("--ttl", type=int, default=3600, help="孤儿密文清理阈值秒（默认 3600）")
    ap.add_argument("--reap", action="store_true", help="只清理超 TTL 孤儿密文后退出")
    args = ap.parse_args()

    passphrase = os.environ.get("COOKIE_BRIDGE_PASSPHRASE")
    if not passphrase:
        sys.exit("缺 COOKIE_BRIDGE_PASSPHRASE 环境变量（与扩展 popup 里填的同一口令）")

    cfg_path = Path(args.config).expanduser()
    if not cfg_path.exists():
        example = cfg_path.with_name("config.example.json")
        if example.exists():
            log(f"{cfg_path.name} 不存在，回退用 {example.name}（fresh 环境零配置即用；要自定义就 cp 一份改）")
            cfg_path = example
        else:
            sys.exit(f"配置不存在：{cfg_path}（也没有 {example.name} 可回退）")
    cfg = load_config(cfg_path)
    gw = _import_gw_client()
    drive = gw.get_drive_service()

    if args.reap:
        n = reap_orphans(drive, args.ttl, args.service)
        log(f"reap done: {n} orphan(s) removed")
        return

    if not args.watch:
        consume_once(drive, cfg, passphrase, args.service)
        return

    log(f"watch mode: interval={args.interval}s ttl={args.ttl}s （Ctrl+C 停）")
    try:
        while True:
            consume_once(drive, cfg, passphrase, args.service)
            reap_orphans(drive, args.ttl, args.service)  # backstop
            time.sleep(args.interval)
    except KeyboardInterrupt:
        log("stopped")


if __name__ == "__main__":
    main()
