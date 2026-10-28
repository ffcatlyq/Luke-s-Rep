#!/usr/bin/env bash
# add-service.sh —— 把"加新 service"5 步压成 1 步。
#
# 自动改:
#   1. extension/manifest.json 的 host_permissions
#   2. receiver/config.json 的 services
#   3. receiver/config.example.json 同步
#   4. cp 到 /mnt/c/tools/cookie-bridge-extension/（Windows 实际跑的副本）
#   5. systemctl --user restart cookie-bridge
#
# 用户仍需手工: chrome://extensions 点扩展刷新（让 manifest 生效）
#
# 自动跑: probe-service.sh 探测协议类，输出 client 适配建议
#
# 用法:
#   ./add-service.sh                              # 交互式 prompt
#   ./add-service.sh <name> <domain> [<keepalive_path>]
#   例如:
#     ./add-service.sh confluence wiki.roche.com
#     ./add-service.sh jira jira.roche.com /rest/auth/1/session

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
BRIDGE_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"
MANIFEST="$BRIDGE_DIR/extension/manifest.json"
CONFIG="$BRIDGE_DIR/receiver/config.json"
CONFIG_EXAMPLE="$BRIDGE_DIR/receiver/config.example.json"
WIN_EXT_DIR="/mnt/c/tools/cookie-bridge-extension"

# ── 1. 读参数 ──
NAME="${1:-}"
DOMAIN="${2:-}"
KEEPALIVE="${3:-}"

if [[ -z "$NAME" ]]; then
  read -rp "Service name (英文短标识, 如 confluence): " NAME
fi
if [[ -z "$DOMAIN" ]]; then
  read -rp "Domain (主域, 如 wiki.roche.com): " DOMAIN
fi
if [[ -z "$KEEPALIVE" && -z "${3+set}" ]]; then
  read -rp "Keep-alive path (可选, 留空跳过): " KEEPALIVE || true
fi

# 校验
if ! [[ "$NAME" =~ ^[a-z][a-z0-9_-]*$ ]]; then
  echo "Error: name 必须小写字母开头, 只含 a-z 0-9 _ -" >&2; exit 1
fi
if ! [[ "$DOMAIN" =~ ^[a-z0-9]([a-z0-9.-]*[a-z0-9])?$ ]]; then
  echo "Error: domain 格式不对（如 wiki.roche.com）" >&2; exit 1
fi

OUTPUT="~/.config/$NAME/cookies.json"

echo ""
echo "── 即将添加 service:"
echo "   name:       $NAME"
echo "   domain:     $DOMAIN"
echo "   output:     $OUTPUT"
[[ -n "$KEEPALIVE" ]] && echo "   keepAlive:  $KEEPALIVE"
echo ""
read -rp "继续? [y/N] " CONFIRM
[[ "$CONFIRM" =~ ^[yY]$ ]] || { echo "已取消"; exit 0; }

# ── 2. 改 manifest.json (host_permissions) ──
# 用 python 做 JSON 写入更稳，避免 sed 破坏格式
python3 <<PY
import json
from pathlib import Path

manifest_path = Path("$MANIFEST")
manifest = json.loads(manifest_path.read_text())
hp = manifest.setdefault("host_permissions", [])
patterns = [f"https://{'$DOMAIN'}/*"]
# 若 domain 是 sub.example.com 形式，子域 wildcard 也加上（覆盖兄弟子域）
parts = "$DOMAIN".split(".")
if len(parts) >= 3:
    apex = ".".join(parts[-2:])
    patterns.append(f"https://*.{apex}/*")
for p in patterns:
    if p not in hp:
        hp.append(p)
manifest_path.write_text(json.dumps(manifest, indent=2, ensure_ascii=False) + "\n")
print(f"   ✓ manifest.json host_permissions += {patterns}")
PY

# ── 3. 改 receiver/config.json + config.example.json ──
python3 <<PY
import json
from pathlib import Path

for path_str in ["$CONFIG", "$CONFIG_EXAMPLE"]:
    path = Path(path_str)
    cfg = json.loads(path.read_text())
    services = cfg.setdefault("services", {})
    entry = {
        "domains": ["$DOMAIN"],
        "output": "$OUTPUT",
    }
    if "$KEEPALIVE":
        entry["keepAlivePath"] = "$KEEPALIVE"
    services["$NAME"] = entry
    path.write_text(json.dumps(cfg, indent=2, ensure_ascii=False) + "\n")
    print(f"   ✓ {path.name} services.$NAME 已写入")
PY

# ── 4. 同步 manifest 到 Windows extension 目录 ──
if [[ -d "$WIN_EXT_DIR" ]]; then
  cp "$MANIFEST" "$WIN_EXT_DIR/manifest.json"
  echo "   ✓ manifest 同步到 $WIN_EXT_DIR/"
else
  echo "   ⚠ $WIN_EXT_DIR 不存在，跳过 Windows 同步（如果你不在 WSL 环境忽略此条）"
fi

# ── 5. 重启 receiver ──
if systemctl --user is-enabled cookie-bridge >/dev/null 2>&1; then
  systemctl --user restart cookie-bridge
  sleep 1
  if systemctl --user is-active cookie-bridge | grep -q active; then
    echo "   ✓ cookie-bridge.service 重启完成"
  else
    echo "   ⚠ cookie-bridge.service 重启后非 active，跑 'systemctl --user status cookie-bridge' 看日志"
  fi
else
  echo "   ⚠ cookie-bridge.service 未 enable（可能用 setsid 启动），手工重启 receiver"
fi

# ── 6. 建 output 目录 ──
mkdir -p "$(eval echo "${OUTPUT%/cookies.json}")"

# ── 7. probe 协议 + 给 client 模板建议 ──
echo ""
echo "── 探测目标协议类型..."
PROBE_URL="https://$DOMAIN/"
if "$SCRIPT_DIR/probe-service.sh" "$PROBE_URL" 2>&1; then
  :
else
  echo "   (协议未自动识别——加完之后请人工判断 client 模板)"
fi

# ── 8. 给用户最后操作指引 ──
echo ""
echo "═════════════════════════════════════════════════════"
echo "你这边还要做 2 步:"
echo "  1. chrome://extensions → Roche Cookie Bridge → 点刷新（让 host_permissions 生效）"
echo "  2. 浏览器登录 https://$DOMAIN/ → popup 选 service '$NAME' → Sync Now"
echo ""
echo "之后:"
echo "  - cookie 落到 $OUTPUT"
echo "  - 业务 client 模板见 demos/browser-cookie-bridge/docs/RECIPES.md"
echo "═════════════════════════════════════════════════════"
