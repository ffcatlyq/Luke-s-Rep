#!/usr/bin/env bash
# skill-capture-reminder — Stop hook：会话停下时提醒「这次流程要不要沉淀成 skill」。
#
# 为什么有它：AGENTS.md 第 4.6 节要求「每次任务后主动问是否沉淀成 skill」，但这是 prompt
# 规则，LLM 长会话里会忘、干完就收尾。这个 Stop hook 补上「自动」那一环：干了实质工作的
# 会话停下时，把沉淀提醒留在 transcript，让「封装/优化 skill」这个 SOP 循环别断。
#
# 能力边界（诚实）：提示型，非强制型。只保证「提醒出现」，保证不了 LLM 真去沉淀。写/优化
# skill 的方法见 skills/_meta-authoring.md。
#
# 节流（否则 Stop 每个 turn 都触发会极吵）——两道闸，都过才提醒：
#   闸1 实质工作：本会话 Write/Edit/MultiEdit/Bash 调用累计 < WORK_THRESHOLD 则静默。
#   闸2 增量节流：cache 记「上次提醒时的累计数」，当前累计 − 上次 ≥ REMIND_DELTA 才再提醒。
#
# 实现说明：本环境无 python/node，用 bash + jq（镜像已含）。jq 缺失时 fail-open 放行。
# 故意 fail-open：任何解析/读取失败都静默放行（exit 0）。

set -euo pipefail

WORK_THRESHOLD=3      # 闸1：实质工作的最小工具调用数
REMIND_DELTA=10       # 闸2：距上次提醒新增工具调用数达此值才再提醒
CACHE_DIR="$HOME/.cache/pm-agent-skill-capture"

command -v jq >/dev/null 2>&1 || exit 0

raw="$(cat 2>/dev/null || true)"
[ -z "$raw" ] && exit 0

# 防死循环：已在 Stop hook 触发的续跑里，不再触发
stop_active="$(printf '%s' "$raw" | jq -r '.stop_hook_active // false' 2>/dev/null || echo false)"
[ "$stop_active" = "true" ] && exit 0

session_id="$(printf '%s' "$raw" | jq -r '.session_id // empty' 2>/dev/null || true)"
transcript="$(printf '%s' "$raw" | jq -r '.transcript_path // empty' 2>/dev/null || true)"
[ -z "$session_id" ] && exit 0
[ -z "$transcript" ] && exit 0
[ ! -f "$transcript" ] && exit 0

# 统计 transcript 里 Write/Edit/MultiEdit/Bash 的 tool_use 数
work="$(jq -r '
  (.message.content // empty)
  | if type=="array" then .[] else empty end
  | select(type=="object" and .type=="tool_use"
      and (.name=="Write" or .name=="Edit" or .name=="MultiEdit" or .name=="Bash"))
  | .name
' "$transcript" 2>/dev/null | grep -c . || true)"
[ -z "$work" ] && work=0

# 闸1
[ "$work" -lt "$WORK_THRESHOLD" ] && exit 0

# 闸2：增量节流
safe="$(printf '%s' "$session_id" | tr -cd 'A-Za-z0-9_-')"
cache_file="$CACHE_DIR/$safe"
last=0
reminded_before=false
if [ -f "$cache_file" ]; then
  reminded_before=true
  last="$(cat "$cache_file" 2>/dev/null || echo 0)"
  case "$last" in ''|*[!0-9]*) last=0 ;; esac
fi
if [ "$reminded_before" = "true" ] && [ $((work - last)) -lt "$REMIND_DELTA" ]; then
  exit 0
fi

# 命中：更新 cache（写失败不阻断提醒）
mkdir -p "$CACHE_DIR" 2>/dev/null || true
printf '%s' "$work" > "$cache_file" 2>/dev/null || true

read -r -d '' REMINDER <<'EOF' || true
会话收尾自检：这次任务的流程值得沉淀成 skill 吗？——判据是「会重复 + 有可复用步骤 + 有质量要求」。值得就现在做：新建 skills/<动词-名词>.md，或把新踩的坑/检查项补进已有 skill（方法见 skills/_meta-authoring.md）。一次性机械改动则跳过。这是提醒，不强制。
EOF

jq -n --arg msg "$REMINDER" '{
  systemMessage: $msg,
  hookSpecificOutput: {
    hookEventName: "Stop",
    additionalContext: $msg
  }
}'
exit 0
