#!/usr/bin/env bash
# plan-alignment-guard — PreToolUse hook（matcher: ExitPlanMode）：出计划前强制过五要素对齐清单。
#
# 为什么有它：AGENTS.md 第 4 章「先对齐再执行 / 派活五要素」是 prompt 规则，LLM 在长会话里
# 会忘、会把"在 plan 里写了一节叫对齐的内容"误当成"真的过了对齐"就退出 plan。这个 hook 用
# 代码兜底：ExitPlanMode 必触发一次 ask，把五要素清单怼到眼前，逼 LLM 停一下、用户也看得见。
#
# 能力边界（诚实）：这是提示型护栏，不是验证型。hook 验证不了"LLM 是否真逐条对齐过五要素"
# （对齐是思维动作，hook 看不到）。它只保证"停一下 + 清单可见"，不保证对齐质量。
#
# SSOT：五要素与协作原则的权威表述在 AGENTS.md 第 4 章，本脚本只放速记 + 指针，不复制全文。
#
# 实现说明：本环境无 python/node，用 bash + jq（镜像已含）。jq 缺失时 fail-open 放行。
# 故意 fail-open：任何解析失败都静默放行（exit 0），hook 自身的 bug 不该卡住 ExitPlanMode。

set -euo pipefail

# jq 不存在则放行（fail-open）
command -v jq >/dev/null 2>&1 || exit 0

raw="$(cat 2>/dev/null || true)"
[ -z "$raw" ] && exit 0

tool_name="$(printf '%s' "$raw" | jq -r '.tool_name // empty' 2>/dev/null || true)"
[ "$tool_name" != "ExitPlanMode" ] && exit 0

read -r -d '' CHECKLIST <<'EOF' || true
出计划前五要素对齐自检（逐条真过，缺项即回去补 plan 再退；完整见 AGENTS.md 第 4 章）：
① 目标——是否已复述用户目标做对齐？步骤是否拆好、检查过遗漏/错误？
② 上下文——源材料在哪、哪些标了「待核实」？限制是否交代清楚？
③ 动作——这是分析/对比/生成？是否选对了 skill（见 skills/）？笨方法是否提了优化建议？
④ 边界——什么不能做（对外物料/讲者/合规灰区按高代价处理）、哪里可发挥，是否明确？
⑤ 验收——合格标准是什么？是否把验证写进了流程？
不是「plan 里写了一节对齐」就算数——要真逐条想过，并把待确认项打在正文里问用户。
EOF

jq -n --arg reason "$CHECKLIST" '{
  hookSpecificOutput: {
    hookEventName: "PreToolUse",
    permissionDecision: "ask",
    permissionDecisionReason: $reason
  }
}'
exit 0
