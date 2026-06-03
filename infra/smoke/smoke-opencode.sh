#!/usr/bin/env bash
set -euo pipefail
source "$(dirname "$0")/../00-paths.sh"
export HOME="$LAB_HOME" ANTHROPIC_API_KEY OPENAI_API_KEY
run_one () {
  local tag="$1" model="$2"
  local WORK="$LAB/smoke/opencode-$tag"; rm -rf "$WORK"; mkdir -p "$WORK"; cd "$WORK"
  printf 'def add(a, b):\n    return a - b\n' > hello.py
  # --variant high：provider-specific reasoning effort=high；--format json：原始事件流作 trace 來源
  "$LAB_BIN/opencode" run --model "$model" --variant high --format json \
    "Fix the bug in hello.py so add returns the sum, by editing the file." 2>&1 | tee oc.log | tail -15 || true
  echo "--- $tag result ---"; cat hello.py
}
run_one haiku  "anthropic/$ANTHROPIC_MODEL"
run_one gptmini "openai/$OPENAI_MODEL"
