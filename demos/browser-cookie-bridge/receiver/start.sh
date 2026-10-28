#!/usr/bin/env bash
# Browser Cookie Bridge receiver — 持久化端口和 token 的启动 wrapper。
#
# 第一次跑：生成 PORT + TOKEN 写到 ~/.config/cookie-bridge/env (mode 600)
# 之后跑：从同一份 env 文件读，receiver 每次重启端口和 token 都不变
#
# 用户体验：popup 配一次 Local receiver + Token 永久不变，不再随 receiver 重启换。
#
# 多容器共享 token：export COOKIE_BRIDGE_RECEIVER_TOKEN=<同一个>（可再 COOKIE_BRIDGE_RECEIVER_PORT）
# 覆盖持久化值，让多个 Ona 容器的 receiver 用同一 token 起，扩展一个 token 扇出打全部。
#
# 可辨识：export COOKIE_BRIDGE_RECEIVER_NAME=<项目 slug> 给 receiver 起个名，/health 会返回，
# popup 点 ↻ 后每行显示「端口 → name」，多容器不用脑记哪个转发端口是哪个容器。不设则兜底 hostname。
#
# 安全 trade-off（详见 docs/ARCHITECTURE.md 决策 5）：
# - token 落盘到 ~/.config/cookie-bridge/env (mode 600，仅 owner 可读)
# - 文件不进 git（在 hub repo 之外的 ~/.config/）
# - 同机其他进程仍可以读这个文件（如果 OS 用户被攻陷，blast radius 是同一份 cookie）
# - 不希望落盘的话直接跑 cookie_receiver.py，每次随机生成

set -euo pipefail

ENV_FILE="${HOME}/.config/cookie-bridge/env"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
CONFIG_FILE="${SCRIPT_DIR}/config.json"

# config.json 不存在时回退 config.example.json（fresh 容器 clone 后没有 config.json——
# 它在 .gitignore 里，只 track config.example.json；automations 自动起要靠这个回退才不挂）。
# 镜像 gdrive_cookie_sync.py 的回退行为。
if [ ! -f "$CONFIG_FILE" ]; then
  EXAMPLE="${SCRIPT_DIR}/config.example.json"
  if [ -f "$EXAMPLE" ]; then
    echo "[start] config.json not found, falling back to config.example.json (zero-config on fresh env; cp a copy to customize)"
    CONFIG_FILE="$EXAMPLE"
  else
    echo "[start] config file not found: $CONFIG_FILE (no config.example.json to fall back to either)"
    exit 1
  fi
fi

# 第一次跑：生成持久化 PORT + TOKEN
if [ ! -f "$ENV_FILE" ]; then
  mkdir -p "$(dirname "$ENV_FILE")"
  PORT=$((RANDOM % 20000 + 30000))
  TOKEN=$(python3 -c "import secrets; print(secrets.token_urlsafe(32))")
  cat > "$ENV_FILE" <<EOF
PORT=$PORT
TOKEN=$TOKEN
EOF
  chmod 600 "$ENV_FILE"
  echo "[start] generated $ENV_FILE"
  echo "[start]   PORT=$PORT"
  echo "[start]   TOKEN=$TOKEN"
  echo "[start] paste these two into the Chrome extension popup's Receiver URL and Token fields"
  echo "[start]   Receiver URL: http://127.0.0.1:$PORT"
  echo "[start]   Token: $TOKEN"
  echo
fi

# shellcheck disable=SC1090
source "$ENV_FILE"

# 环境变量覆盖（优先级：env var > 持久化 env 文件 > 首次随机）。
# 多容器共享同一 token：在每个容器 export COOKIE_BRIDGE_RECEIVER_TOKEN=<同一个>，
# 扩展 popup 就用这一个 token 打全部 receiver（多 receiver 扇出，见 docs/INSTALL.md）。
PORT="${COOKIE_BRIDGE_RECEIVER_PORT:-$PORT}"
TOKEN="${COOKIE_BRIDGE_RECEIVER_TOKEN:-$TOKEN}"
if [ -n "${COOKIE_BRIDGE_RECEIVER_TOKEN:-}" ] || [ -n "${COOKIE_BRIDGE_RECEIVER_PORT:-}" ]; then
  echo "[start] env override active → Receiver URL: http://127.0.0.1:$PORT (token from COOKIE_BRIDGE_RECEIVER_TOKEN/env file)"
fi

exec python3 "${SCRIPT_DIR}/cookie_receiver.py" \
  --config "$CONFIG_FILE" \
  --port "$PORT" \
  --token "$TOKEN" \
  --name "${COOKIE_BRIDGE_RECEIVER_NAME:-}"
