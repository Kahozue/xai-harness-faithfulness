#!/usr/bin/env bash
set -euo pipefail
source "$(dirname "$0")/../00-paths.sh"
WORK="$LAB/smoke/codex"; rm -rf "$WORK"; mkdir -p "$WORK"
cat > "$WORK/hello.py" <<'PY'
def add(a, b):
    return a - b
PY
export HOME="$LAB_HOME" OPENAI_API_KEY
cd "$WORK"
# 非互動 exec；本機為專屬隔離 lab（externally sandboxed），bypass 確保 headless 不卡審批/landlock。
# model 與 high effort 來自 $LAB_HOME/.codex/config.toml；--json 輸出 JSONL 事件流（reasoning + tool/command 呼叫）作 trace 來源。
"$LAB_BIN/codex" exec --skip-git-repo-check --dangerously-bypass-approvals-and-sandbox --json \
  "Fix the bug in hello.py so add returns the sum, by editing the file." 2>&1 | tee "$WORK/codex.log" | tail -20 || true
echo "--- result ---"; cat hello.py
