#!/usr/bin/env bash
set -euo pipefail
source "$(dirname "$0")/../00-paths.sh"
WORK="$LAB/smoke/cc"; rm -rf "$WORK"; mkdir -p "$WORK"
cat > "$WORK/hello.py" <<'PY'
def add(a, b):
    return a - b   # bug: should be +
PY
export HOME="$LAB_HOME"
export ANTHROPIC_API_KEY   # 來自 00-paths.sh 載入的 secrets → Anthropic 原生
export PATH="$LAB_BIN:$PATH"  # 讓 claude-trace 在 PATH 解析到釘死的 claude 2.1.88
# Claude Code 非互動模式 + 指定 Haiku + 經 claude-trace 攔截 API 流量
cd "$WORK"
"$LAB_BIN/claude-trace" --include-all-requests --run-with \
  -p "Fix the bug in hello.py so add returns the sum. Use your tools to edit the file." \
  --model "$ANTHROPIC_MODEL" --permission-mode acceptEdits 2>&1 | tail -20 || true
echo "--- trace files ---"
find "$WORK/.claude-trace" -name '*.jsonl' -printf '%p\n' 2>/dev/null || echo "no trace dir"
