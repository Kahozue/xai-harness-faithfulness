#!/usr/bin/env bash
set -euo pipefail
source "$(dirname "$0")/00-paths.sh"
CODEX_PREFIX="$LAB/codex/prefix"; mkdir -p "$CODEX_PREFIX"
npm install --prefix "$CODEX_PREFIX" "@openai/codex@0.136.0"   # 釘死版本（Task4 Step1 探得 latest=0.136.0）
ln -sf "$CODEX_PREFIX/node_modules/.bin/codex" "$LAB_BIN/codex"
HOME="$LAB_HOME" "$LAB_BIN/codex" --version
# --- 隔離 config（$LAB_HOME/.codex）：OpenAI 原生 + gpt-5.4-mini + high reasoning ---
mkdir -p "$LAB_HOME/.codex"
cat > "$LAB_HOME/.codex/config.toml" <<TOML
model = "$OPENAI_MODEL"
model_reasoning_effort = "high"
TOML
# 認證：Codex 0.136 用 File 模式 auth（$LAB_HOME/.codex/auth.json）；
# 純 OPENAI_API_KEY 環境變數不會附上 bearer，須以 --with-api-key（讀 stdin）寫入 auth.json。
printenv OPENAI_API_KEY | HOME="$LAB_HOME" "$LAB_BIN/codex" login --with-api-key
HOME="$LAB_HOME" "$LAB_BIN/codex" login status
echo "codex installed + isolated config + auth.json written under $LAB_HOME/.codex"
