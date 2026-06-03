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
export CLAUDE_CODE_EFFORT_LEVEL=high
export CLAUDE_CODE_MAX_OUTPUT_TOKENS=64000
export MAX_THINKING_TOKENS=63999
# Claude Code 非互動模式 + 指定 Haiku + 經 claude-trace 攔截 API 流量。
# Haiku 4.5 不支援 output_config.effort；最高可驗證控制點是 64000 max_tokens + 63999 thinking budget。
cd "$WORK"
"$LAB_BIN/claude-trace" --include-all-requests --run-with \
  -p "Fix the bug in hello.py so add returns the sum. Use your tools to edit the file." \
  --model "$ANTHROPIC_MODEL" --effort high --permission-mode acceptEdits 2>&1 | tail -20
echo "--- result ---"; cat hello.py
grep -q 'return a + b' hello.py
echo "--- trace files ---"
mapfile -t traces < <(find "$WORK/.claude-trace" -name '*.jsonl' -printf '%p\n' 2>/dev/null)
if [ "${#traces[@]}" -eq 0 ]; then
  echo "no trace dir"
  exit 1
fi
printf '%s\n' "${traces[@]}"
grep -q '"tools"' "${traces[0]}"
grep -q 'tool_use' "${traces[0]}"
grep -q '"max_tokens":64000' "${traces[0]}"
grep -q '"budget_tokens":63999' "${traces[0]}"
