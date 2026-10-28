#!/usr/bin/env bash
# setup-engine.sh — 把 ppt-master 引擎(上游 hugohe3/ppt-master)装到本机,float 到最新 + 冒烟测。
#
# 为什么这样:引擎不 vendor 进 hub(大、上游活跃维护、我们故意不改),但新容器里它会消失。
# 本脚本按需装回:sparse checkout 只拉引擎(skills/ + requirements.txt),跳过 ~1.3GB 的
# examples/ 大二进制;拿最新(不钉 SHA,skill 与时俱进);装完跑冒烟测——用最新 + 出问题当场
# 暴露,而不是用旧 + 享受不到改进。上游改了 flag(如 `--only native` 已在新版移除)冒烟会红。
#
# 用法: bash setup-engine.sh            # 默认装到 $HOME/ppt-master
#        PPT_MASTER_DIR=/path bash setup-engine.sh
set -euo pipefail

ENGINE_DIR="${PPT_MASTER_DIR:-$HOME/ppt-master}"
REPO="https://github.com/hugohe3/ppt-master.git"
HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

echo "[setup-engine] target: $ENGINE_DIR"
if [ -d "$ENGINE_DIR/.git" ]; then
  echo "[setup-engine] existing clone → pull latest"
  git -C "$ENGINE_DIR" pull --ff-only
else
  echo "[setup-engine] sparse clone (engine only, skip examples/ ~1.3GB)"
  git clone --depth 1 --filter=blob:none --sparse "$REPO" "$ENGINE_DIR"
  # cone mode auto-includes all root-level files (requirements.txt, README...) + the skills/ tree
  git -C "$ENGINE_DIR" sparse-checkout set skills
fi

VENV="$ENGINE_DIR/.venv"
[ -d "$VENV" ] || python3 -m venv "$VENV"
PY="$VENV/bin/python"
echo "[setup-engine] installing engine deps + Roche extras"
"$VENV/bin/pip" install -q --upgrade pip
"$VENV/bin/pip" install -q -r "$ENGINE_DIR/skills/ppt-master/requirements.txt"
# Roche 适配额外依赖:cairosvg(_pipeline 预览)、matplotlib(公式渲染)、fonttools+brotli(字体嵌入/woff2)、PyMuPDF(source_to_md 已在上游 reqs)
"$VENV/bin/pip" install -q cairosvg matplotlib fonttools brotli

echo "[setup-engine] smoke test (canary: canonical export must still work on latest)"
if "$PY" "$HERE/smoke_test.py" "$ENGINE_DIR"; then
  echo "[setup-engine] OK — engine at $ENGINE_DIR ; venv $VENV"
  echo "[setup-engine] activate: source $VENV/bin/activate"
else
  echo "[setup-engine] SMOKE FAILED — 上游可能改了导出接口(flag/语义)。"
  echo "               看 smoke 输出 → 更新 SKILL.md 的 canonical 导出命令,再重跑。"
  exit 1
fi
