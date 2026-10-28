#!/usr/bin/env bash
# 文档一致性核对 — 揪出根文档与实际结构的漂移。
# 覆盖检查项 1-4（技能漏登记 / 坏路径 / 死链 / 失效图例），第 5 项计数给实际值供人工对比。
# 从仓库根运行：bash skills/docs-consistency-check/scripts/check-docs.sh
set -uo pipefail

# 定位仓库根（脚本在 skills/docs-consistency-check/scripts/ 下）
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../../.." && pwd)"
cd "$ROOT" || exit 2

ROOT_DOCS=(AGENTS.md README.md ONBOARDING.md skills/README.md)
FAIL=0
say()  { printf '%s\n' "$*"; }
head2(){ printf '\n=== %s ===\n' "$*"; }

# ---------- 1. 技能清单完整：磁盘技能是否都在文档某处出现 ----------
head2 "1. 技能漏登记检查"
# 业务技能：目录型 skills/<name>/ + 单文件 skills/<name>.md
biz=$( { find skills -maxdepth 1 -mindepth 1 -type d -printf '%f\n'; \
         find skills -maxdepth 1 -name '*.md' -printf '%f\n' | sed 's/\.md$//'; } \
       | grep -v '^README$' | sort -u )
# 工具技能：.claude/skills/<name>/
tool=$(find .claude/skills -maxdepth 1 -mindepth 1 -type d -printf '%f\n' 2>/dev/null | sort -u)

alldocs=$(cat "${ROOT_DOCS[@]}" 2>/dev/null)
miss=0
for s in $biz $tool; do
  if ! grep -q -- "$s" <<<"$alldocs"; then
    say "❌ 技能未在任何根文档登记: $s"; miss=1; FAIL=1
  fi
done
[ "$miss" = 0 ] && say "✅ 所有磁盘技能都已在文档中出现"

# ---------- 2. 引用路径存在：只查“根相对”路径（以已知顶层目录开头）----------
# 只验证明确从仓库根出发的路径（skills/… docs/… .claude/… 等）。
# 裸文件名（franchise.md）、同目录相对引用（SKILL.md、templates/）是上下文相对的，
# 无法可靠按根解析，故不在此检查——它们若出现在 markdown 链接里会被第 3 项死链检查覆盖。
head2 "2. 根相对路径存在检查"
TOPDIRS='skills|docs|compliance|knowledge-packs|\.claude|\.ona|assets|demos|outputs'
for doc in "${ROOT_DOCS[@]}"; do
  [ -f "$doc" ] || continue
  grep -oE '`[A-Za-z0-9_./-]+`' "$doc" | tr -d '`' | sort -u \
    | grep -E "^($TOPDIRS)/" \
    | while read -r p; do
        base="${p%%#*}"; base="${base%/}"
        case "$base" in
          *'<'*|*'>'*|*'*'*) continue;;          # 通配/占位
          *.local.yaml|*.local.yml) continue;;   # 每用户运行时文件（gitignore，由 .example 生成）
        esac
        [ -e "$base" ] || say "❌ [$doc] 引用不存在的根相对路径: $p"
      done
done
say "（以上如无 ❌ 即根相对路径全部存在）"

# ---------- 3. 内部链接不死：](target) ----------
head2 "3. 死链检查"
for doc in "${ROOT_DOCS[@]}"; do
  [ -f "$doc" ] || continue
  grep -oE '\]\(([^)]+)\)' "$doc" | sed -E 's/\]\(//; s/\)$//' \
    | grep -vE '^https?://|^mailto:' \
    | while read -r link; do
        t="${link%%#*}"; [ -z "$t" ] && continue
        [ -e "$t" ] || say "❌ [$doc] 死链: $link"
      done
done
say "（以上如无 ❌ 即无死链）"

# ---------- 4. 状态图例有效：图例标记是否仍有技能在用 ----------
head2 "4. 失效状态图例检查"
# 检查常见的“待适配/⏳”类残留：出现在图例说明但正文已无对应标记的技能
for doc in README.md skills/README.md; do
  [ -f "$doc" ] || continue
  if grep -q '⏳' "$doc"; then
    # ⏳ 同时出现在“图例定义行”和“至少一个技能行”才算有效
    legend=$(grep -c '⏳.*=' "$doc")
    used=$(grep '⏳' "$doc" | grep -vc '⏳.*=')
    if [ "$legend" -gt 0 ] && [ "$used" -eq 0 ]; then
      say "❌ [$doc] 定义了 ⏳ 图例但无任何技能在用——应删图例"; FAIL=1
    fi
  fi
done
say "（以上如无 ❌ 即无失效图例）"

# ---------- 5. 计数声明：给实际值供人工比对 ----------
head2 "5. 计数（人工对比文档中的硬数字）"
say "实际产品数（默认血液）: $(find knowledge-packs/hematology/products -maxdepth 1 -mindepth 1 -type d 2>/dev/null | wc -l)"
say "实际业务技能数: $(wc -w <<<"$biz")"
say "实际工具技能数: $(wc -w <<<"$tool")"
say "→ 对照 README/ONBOARDING 里“N 个产品/技能”等表述是否一致。"

# ---------- 结果 ----------
head2 "结果"
if [ "$FAIL" -eq 0 ]; then
  say "✅ 硬检查通过（无漏登记/死链/失效图例）。仍需人工核对语义过时与计数。"
else
  say "❌ 存在硬问题，见上方 ❌。修复后重跑。"
fi
exit "$FAIL"
