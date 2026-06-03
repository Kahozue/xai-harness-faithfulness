#!/usr/bin/env bash
set -euo pipefail
source "$(dirname "$0")/../00-paths.sh"
# 共享二進位在真實 HOME 的 ~/.local/bin；config/state 以 HERMES_HOME/HOME 隔離。
REAL_HOME="$HOME"
HERMES_BIN="$REAL_HOME/.local/bin/hermes"
export HOME="$LAB_HOME" HERMES_HOME="$LAB_HOME/.hermes" ANTHROPIC_API_KEY OPENAI_API_KEY
run_one () {
  local tag="$1" provider="$2" model="$3"
  local WORK="$LAB/smoke/hermes-$tag"; rm -rf "$WORK"; mkdir -p "$WORK"; cd "$WORK"
  printf 'def add(a, b):\n    return a - b\n' > hello.py
  # -z 一次性非互動；用 -m MODEL --provider PROVIDER 分開形式（合併式 -m provider/model 對
  # snapshot model id 會靜默失敗）；--yolo 自動接受工具（headless 不卡審批）。
  "$HERMES_BIN" -z "Fix the bug in hello.py so add returns the sum, by editing the file." \
    -m "$model" --provider "$provider" --yolo 2>&1 | tee hermes.log | tail -20
  # Hermes trace 來源：最新 session JSON（含 system_prompt / tools 定義 / 有序 tool_calls，無 secret）
  local sess; sess=$(ls -t "$HERMES_HOME/sessions/"session_*.json 2>/dev/null | head -1 || true)
  if [ -z "$sess" ]; then
    echo "missing Hermes session trace"
    exit 1
  fi
  cp "$sess" "$WORK/trace.session.json" && echo "trace -> $WORK/trace.session.json"
  echo "--- $tag result ---"; cat hello.py
  grep -q 'return a + b' hello.py
  grep -q 'tool_calls' "$WORK/trace.session.json"
}
run_one haiku   anthropic "$ANTHROPIC_MODEL"
run_one gptmini openai    "$OPENAI_MODEL"
