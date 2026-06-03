# Phase 0 — 乾淨隔離建置 + Harness 機制 Dossier 實作計畫

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 在跑任何實驗前，於隔離環境釘死安裝四個 harness（Claude Code 2.1.88、Codex CLI、OpenCode、全新乾淨 Hermes 0.13.0），各自能用指定模型於 high effort 跑通並擷取到可比的 trace，並產出逐 harness 機制 dossier 與 `ENVIRONMENT.lock.md`，作為實驗嚴謹性與報告論述的「底」。

**Architecture:** 所有實驗 harness 安裝於 `/data/harness-lab/`，以**專屬 LAB_HOME** 隔離所有設定與狀態（不碰生產服務的 `/home/opc` dotfiles，尤其不碰正式 Hermes）；secrets 由 `~/.harness-exp/` 注入；二進位以絕對路徑呼叫並釘死版本。每個 harness 有「安裝 → 認證/設定模型與 high effort → smoke 跑通 → 驗證 trace 可擷取」四關，全部驗證以可重跑指令 + 明確預期輸出表示。

**Tech Stack:** Oracle Linux aarch64、node v22.22.2、npm 10.9.7、Python 3.11.13、git；模型 `claude-haiku-4-5-20251001`（Anthropic 原生）、`gpt-5.4-mini-2026-03-17`（OpenAI 原生）；claude-trace `@loki-zhou/claude-trace@1.0.4`。

**執行位置：** 全部在 server `opc@150.230.202.49`，repo `/data/repos/xai-harness-faithfulness`。本機（Mac）僅提供 `claude-code-2.1.88.tgz` 與 restored-src。

**Gate：** 全部 13 task 完成後，dossier 與 `ENVIRONMENT.lock.md` 須經使用者審閱通過，才進入 Phase 1。

---

## 檔案結構（本 Phase 產出）

repo `xai-harness-faithfulness/` 內：
- Create: `infra/00-paths.sh` — 定義 `LAB`, `LAB_HOME`, 各 harness 路徑、secrets 來源
- Create: `infra/install-claude-code.sh`、`install-claude-trace.sh`、`install-codex.sh`、`install-opencode.sh`、`install-hermes-clean.sh`
- Create: `infra/smoke/smoke-claude-code.sh`、`smoke-codex.sh`、`smoke-opencode.sh`、`smoke-hermes.sh`
- Create: `infra/verify-isolation.sh`
- Create: `ENVIRONMENT.lock.md`
- Create: `docs/dossier/00-overview.md`、`claude-code.md`、`codex-cli.md`、`opencode.md`、`hermes.md`、`hermes-memory.md`、`cross-harness-comparison.md`

runtime（repo 外，不進 git）：`/data/harness-lab/`（binaries、LAB_HOME、smoke workdirs）。

---

## Task 1: 隔離 lab 骨架 + 路徑/環境設定 + lock 骨架

**Files:**
- Create: `infra/00-paths.sh`
- Create: `ENVIRONMENT.lock.md`

- [ ] **Step 1: 寫 `infra/00-paths.sh`**

```bash
#!/usr/bin/env bash
# 所有實驗 harness 的共用路徑與隔離環境。source 此檔後再呼叫各 harness。
set -euo pipefail
export LAB="/data/harness-lab"
export LAB_HOME="$LAB/home"          # 專屬 HOME：隔離所有 harness 的 dotfile 設定/狀態
export LAB_BIN="$LAB/bin"
export SECRETS="$HOME/.harness-exp"  # repo 外 secrets（git 不追蹤）
export ANTHROPIC_MODEL="claude-haiku-4-5-20251001"
export OPENAI_MODEL="gpt-5.4-mini-2026-03-17"
mkdir -p "$LAB" "$LAB_HOME" "$LAB_BIN" "$LAB/smoke"
# 載入 secrets（檔案需 chmod 600，已於既有流程建立）
set -a
[ -f "$SECRETS/anthropic.env" ] && . "$SECRETS/anthropic.env"
[ -f "$SECRETS/openai.env" ] && . "$SECRETS/openai.env"
set +a
```

- [ ] **Step 2: 確保 OpenAI secret 也獨立存放（與 Anthropic 一致）**

Run:
```bash
ssh -i ~/.ssh/SSH_Tokyo_A1_Private.key opc@150.230.202.49 'bash -lc "
umask 077; mkdir -p ~/.harness-exp
if [ ! -f ~/.harness-exp/openai.env ]; then
  set -a; . ~/.hermes/.env; set +a
  printf \"OPENAI_API_KEY=%s\n\" \"\$OPENAI_API_KEY\" > ~/.harness-exp/openai.env
  chmod 600 ~/.harness-exp/openai.env
fi
ls -l ~/.harness-exp/openai.env"'
```
Expected: 列出 `-rw-------` 的 `openai.env`。

- [ ] **Step 3: 寫 `ENVIRONMENT.lock.md` 骨架（值在 Task 7 補齊）**

```markdown
# ENVIRONMENT.lock — 凍結實驗環境（版本全釘死）

> 所有 harness 與模型版本在此釘死。任何變更須更新本檔並記錄日期與理由。

## 平台
- Host: Oracle Linux (aarch64), VPS tokyo-a1
- node: v22.22.2 | npm: 10.9.7 | python: 3.11.13 | git: 2.47.3
- 隔離：LAB=/data/harness-lab，LAB_HOME=/data/harness-lab/home（專屬 HOME），secrets 於 ~/.harness-exp（repo 外）

## 模型（帶日期 snapshot）
- Haiku 4.5: `claude-haiku-4-5-20251001`（Anthropic 原生 api.anthropic.com）
- GPT-5.4-mini: `gpt-5.4-mini-2026-03-17`（OpenAI 原生 api.openai.com）
- reasoning effort: high（全部）

## Harness 版本（Task 2-7 填入確切值）
| Harness | 版本 | 安裝來源 | 安裝路徑 | 安裝日期 |
|---------|------|----------|----------|----------|
| Claude Code | 2.1.88 | local tarball | (TBD Task2) | (TBD) |
| claude-trace | 1.0.4 | npm @loki-zhou/claude-trace | (TBD Task3) | (TBD) |
| Codex CLI | (TBD Task4) | npm | (TBD) | (TBD) |
| OpenCode | (TBD Task5) | npm | (TBD) | (TBD) |
| Hermes | 0.13.0 | clean isolated instance | (TBD Task6) | (TBD) |
```

（註：上表 TBD 為待 Task 執行時以實際值取代的填寫欄位，非設計空白。）

- [ ] **Step 4: 驗證 paths 可載入**

Run:
```bash
ssh -i ~/.ssh/SSH_Tokyo_A1_Private.key opc@150.230.202.49 \
 'cd /data/repos/xai-harness-faithfulness && bash -c "source infra/00-paths.sh && echo LAB=$LAB LAB_HOME=$LAB_HOME && echo anthropic_key_loaded=${ANTHROPIC_API_KEY:+yes} openai_key_loaded=${OPENAI_API_KEY:+yes}"'
```
Expected: `LAB=/data/harness-lab LAB_HOME=/data/harness-lab/home` 且 `anthropic_key_loaded=yes openai_key_loaded=yes`。

- [ ] **Step 5: Commit**

```bash
git add infra/00-paths.sh ENVIRONMENT.lock.md
git commit -m "infra: add isolated lab paths and environment lock skeleton


```

---

## Task 2: 安裝 Claude Code 2.1.88（離線 tarball，釘死）

**Files:**
- Create: `infra/install-claude-code.sh`

- [ ] **Step 1: 從 Mac 傳 tarball 與 restored-src 到 server lab**

Run（在 Mac）：
```bash
KEY=~/.ssh/SSH_Tokyo_A1_Private.key; HOST=opc@150.230.202.49
SRC=/Users/researcher/Downloads/claude-code-sourcemap-main
ssh -i $KEY $HOST 'mkdir -p /data/harness-lab/claude-code/pkg /data/harness-lab/claude-code/restored-src'
scp -i $KEY "$SRC/claude-code-2.1.88.tgz" $HOST:/data/harness-lab/claude-code/
rsync -az -e "ssh -i $KEY" "$SRC/restored-src/src/" $HOST:/data/harness-lab/claude-code/restored-src/
```
Expected: scp/rsync 完成無錯。

- [ ] **Step 2: 寫 `infra/install-claude-code.sh`（lab-local 安裝，不污染全域）**

```bash
#!/usr/bin/env bash
set -euo pipefail
source "$(dirname "$0")/00-paths.sh"
CC_PREFIX="$LAB/claude-code/prefix"
mkdir -p "$CC_PREFIX"
# 以 lab-local prefix 安裝指定 tarball，絕不抓 npm 最新
npm install --prefix "$CC_PREFIX" "$LAB/claude-code/claude-code-2.1.88.tgz"
ln -sf "$CC_PREFIX/node_modules/.bin/claude" "$LAB_BIN/claude"
echo "installed claude at $LAB_BIN/claude"
```

- [ ] **Step 3: 執行安裝**

Run:
```bash
ssh -i ~/.ssh/SSH_Tokyo_A1_Private.key opc@150.230.202.49 \
 'cd /data/repos/xai-harness-faithfulness && bash infra/install-claude-code.sh'
```
Expected: 安裝完成、印出 `installed claude at /data/harness-lab/bin/claude`。

- [ ] **Step 4: 驗證版本確為 2.1.88**

Run:
```bash
ssh -i ~/.ssh/SSH_Tokyo_A1_Private.key opc@150.230.202.49 \
 'HOME=/data/harness-lab/home /data/harness-lab/bin/claude --version'
```
Expected: 輸出包含 `2.1.88`。若不符，停止並排查 tarball。

- [ ] **Step 5: Commit**

```bash
git add infra/install-claude-code.sh
git commit -m "infra: pin-install Claude Code 2.1.88 from local tarball (lab-local)


```

---

## Task 3: 安裝 claude-trace 1.0.4 + Anthropic 原生認證 + Claude Code smoke + trace 驗證

**Files:**
- Create: `infra/install-claude-trace.sh`
- Create: `infra/smoke/smoke-claude-code.sh`

- [ ] **Step 1: 寫 `infra/install-claude-trace.sh`**

```bash
#!/usr/bin/env bash
set -euo pipefail
source "$(dirname "$0")/00-paths.sh"
CT_PREFIX="$LAB/trace/prefix"
mkdir -p "$CT_PREFIX"
npm install --prefix "$CT_PREFIX" "@loki-zhou/claude-trace@1.0.4"
ln -sf "$CT_PREFIX/node_modules/.bin/claude-trace" "$LAB_BIN/claude-trace"
"$LAB_BIN/claude-trace" --version 2>/dev/null || echo "claude-trace installed (no --version)"
```

- [ ] **Step 2: 執行安裝並驗證**

Run:
```bash
ssh -i ~/.ssh/SSH_Tokyo_A1_Private.key opc@150.230.202.49 \
 'cd /data/repos/xai-harness-faithfulness && bash infra/install-claude-trace.sh && ls -l /data/harness-lab/bin/claude-trace'
```
Expected: symlink 存在。

- [ ] **Step 3: 寫 `infra/smoke/smoke-claude-code.sh`（非互動、Haiku、high effort、經 claude-trace 擷取）**

```bash
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
# Claude Code 非互動模式 + 指定 Haiku + 經 claude-trace 攔截 API 流量
cd "$WORK"
"$LAB_BIN/claude-trace" --include-all-requests --run-with \
  -p "Fix the bug in hello.py so add returns the sum. Use your tools to edit the file." \
  --model "$ANTHROPIC_MODEL" --permission-mode acceptEdits 2>&1 | tail -20 || true
echo "--- trace files ---"
find "$WORK/.claude-trace" -name '*.jsonl' -printf '%p\n' 2>/dev/null || echo "no trace dir"
```

（註：`--run-with` 後的確切 Claude Code 旗標於執行時依 `claude --help`（2.1.88）校正；non-interactive 用 `-p`，自動接受編輯用 permission-mode。此步若旗標需微調，於本 task 內就地修正後再驗證。）

- [ ] **Step 4: 跑 smoke 並驗證「檔案被修正」+「trace 擷取到 system prompt/tool 定義/tool 序列」**

Run:
```bash
ssh -i ~/.ssh/SSH_Tokyo_A1_Private.key opc@150.230.202.49 \
 'cd /data/repos/xai-harness-faithfulness && bash infra/smoke/smoke-claude-code.sh; echo "=== result ==="; cat /data/harness-lab/smoke/cc/hello.py; echo "=== trace keys ==="; f=$(find /data/harness-lab/smoke/cc/.claude-trace -name "*.jsonl" | head -1); head -c 1200 "$f"'
```
Expected: `hello.py` 內 `add` 變成 `a + b`；trace jsonl 內含 `system`（system prompt）、`tools`（tool 定義）、以及 assistant 的 `tool_use`（tool 序列）欄位。若 trace 未含 tool 定義，加 `--include-all-requests` 已啟用；確認 endpoint 為 `api.anthropic.com`。

- [ ] **Step 5: Commit**

```bash
git add infra/install-claude-trace.sh infra/smoke/smoke-claude-code.sh
git commit -m "infra: claude-trace 1.0.4 + Claude Code smoke (Haiku, native, trace-captured)


```

---

## Task 4: 安裝 Codex CLI（釘版）+ OpenAI 原生 gpt-5.4-mini + high effort + smoke + trace

**Files:**
- Create: `infra/install-codex.sh`
- Create: `infra/smoke/smoke-codex.sh`

- [ ] **Step 1: 探索並釘死 Codex CLI 版本**

Run:
```bash
ssh -i ~/.ssh/SSH_Tokyo_A1_Private.key opc@150.230.202.49 'npm view @openai/codex version && npm view @openai/codex dist-tags'
```
Expected: 印出最新 version；記下作為釘死版本（寫入 `ENVIRONMENT.lock.md` 與下方腳本）。

- [ ] **Step 2: 寫 `infra/install-codex.sh`（用 Step1 得到的確切版本號取代 `<VER>`）**

```bash
#!/usr/bin/env bash
set -euo pipefail
source "$(dirname "$0")/00-paths.sh"
CODEX_PREFIX="$LAB/codex/prefix"; mkdir -p "$CODEX_PREFIX"
npm install --prefix "$CODEX_PREFIX" "@openai/codex@<VER>"   # <VER> = Step1 釘死值
ln -sf "$CODEX_PREFIX/node_modules/.bin/codex" "$LAB_BIN/codex"
HOME="$LAB_HOME" "$LAB_BIN/codex" --version
```

- [ ] **Step 3: 設定 Codex 用 OpenAI 原生 + gpt-5.4-mini + high reasoning（lab HOME 下的 config）**

```bash
#!/usr/bin/env bash
# 寫入 $LAB_HOME/.codex/config.toml（隔離設定）
source "$(dirname "$0")/00-paths.sh"
mkdir -p "$LAB_HOME/.codex"
cat > "$LAB_HOME/.codex/config.toml" <<TOML
model = "$OPENAI_MODEL"
model_reasoning_effort = "high"
TOML
# OpenAI key 經環境變數提供（OPENAI_API_KEY 已由 00-paths.sh 載入）
echo "codex config written"
```
（註：Codex 的確切 config 鍵名以 `codex --help` 與其 config 文件校正；`model_reasoning_effort`、`model` 為現行鍵名，若版本不同就地修正。auth 走 `OPENAI_API_KEY` 環境變數。）

- [ ] **Step 4: 寫 `infra/smoke/smoke-codex.sh`（非互動 `codex exec`）**

```bash
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
"$LAB_BIN/codex" exec --skip-git-repo-check \
  "Fix the bug in hello.py so add returns the sum, by editing the file." 2>&1 | tee "$WORK/codex.log" | tail -20
echo "--- result ---"; cat hello.py
```

- [ ] **Step 5: 跑安裝+設定+smoke，驗證修正成功且 log 含 tool/command 序列**

Run:
```bash
ssh -i ~/.ssh/SSH_Tokyo_A1_Private.key opc@150.230.202.49 \
 'cd /data/repos/xai-harness-faithfulness && bash infra/install-codex.sh && bash infra/smoke/smoke-codex.sh'
```
Expected: `hello.py` 變 `a + b`；`codex.log` 含其工具/指令呼叫紀錄（後續 trace 介面卡來源）。

- [ ] **Step 6: Commit**

```bash
git add infra/install-codex.sh infra/smoke/smoke-codex.sh
git commit -m "infra: pin-install Codex CLI + OpenAI gpt-5.4-mini high-effort smoke


```

---

## Task 5: 安裝 OpenCode（釘版）+ 雙 provider（Anthropic+OpenAI）+ 雙模型 smoke + trace

**Files:**
- Create: `infra/install-opencode.sh`
- Create: `infra/smoke/smoke-opencode.sh`

- [ ] **Step 1: 探索並釘死 OpenCode 版本與套件名**

Run:
```bash
ssh -i ~/.ssh/SSH_Tokyo_A1_Private.key opc@150.230.202.49 'npm view opencode-ai version 2>/dev/null; npm view opencode version 2>/dev/null'
```
Expected: 取得正確套件名與最新版；釘死記錄。

- [ ] **Step 2: 寫 `infra/install-opencode.sh`（用 Step1 確切套件名與版本）**

```bash
#!/usr/bin/env bash
set -euo pipefail
source "$(dirname "$0")/00-paths.sh"
OC_PREFIX="$LAB/opencode/prefix"; mkdir -p "$OC_PREFIX"
npm install --prefix "$OC_PREFIX" "opencode-ai@<VER>"   # <VER>/套件名 = Step1 釘死值
ln -sf "$OC_PREFIX/node_modules/.bin/opencode" "$LAB_BIN/opencode"
HOME="$LAB_HOME" "$LAB_BIN/opencode" --version
```

- [ ] **Step 3: 寫 OpenCode 設定（隔離於 $LAB_HOME），兩個 provider 走原生端點**

```bash
#!/usr/bin/env bash
source "$(dirname "$0")/00-paths.sh"
mkdir -p "$LAB_HOME/.config/opencode"
cat > "$LAB_HOME/.config/opencode/opencode.json" <<JSON
{
  "\$schema": "https://opencode.ai/config.json",
  "provider": {
    "anthropic": { "options": { "apiKey": "{env:ANTHROPIC_API_KEY}" } },
    "openai": { "options": { "apiKey": "{env:OPENAI_API_KEY}" } }
  }
}
JSON
echo "opencode config written"
```
（註：OpenCode config schema 以其官方 `opencode.json` 為準；provider/model id 對應 `anthropic/claude-haiku-4-5-20251001` 與 `openai/gpt-5.4-mini-2026-03-17`；reasoning effort 經 model options 設定，依其文件校正。）

- [ ] **Step 4: 寫 `infra/smoke/smoke-opencode.sh`（兩個模型各跑一次）**

```bash
#!/usr/bin/env bash
set -euo pipefail
source "$(dirname "$0")/../00-paths.sh"
export HOME="$LAB_HOME" ANTHROPIC_API_KEY OPENAI_API_KEY
run_one () {
  local tag="$1" model="$2"
  local WORK="$LAB/smoke/opencode-$tag"; rm -rf "$WORK"; mkdir -p "$WORK"; cd "$WORK"
  printf 'def add(a, b):\n    return a - b\n' > hello.py
  "$LAB_BIN/opencode" run --model "$model" \
    "Fix the bug in hello.py so add returns the sum, by editing the file." 2>&1 | tee oc.log | tail -15
  echo "--- $tag result ---"; cat hello.py
}
run_one haiku  "anthropic/$ANTHROPIC_MODEL"
run_one gptmini "openai/$OPENAI_MODEL"
```

- [ ] **Step 5: 跑安裝+設定+smoke，驗證兩模型都修正成功**

Run:
```bash
ssh -i ~/.ssh/SSH_Tokyo_A1_Private.key opc@150.230.202.49 \
 'cd /data/repos/xai-harness-faithfulness && bash infra/install-opencode.sh && bash infra/smoke/smoke-opencode.sh'
```
Expected: 兩個 `hello.py` 皆變 `a + b`；`oc.log` 含工具呼叫序列。

- [ ] **Step 6: Commit**

```bash
git add infra/install-opencode.sh infra/smoke/smoke-opencode.sh
git commit -m "infra: pin-install OpenCode + dual-provider, dual-model smoke


```

---

## Task 6: 全新乾淨隔離 Hermes 0.13.0 + 雙模型 + 隔離驗證 + smoke + trace

**Files:**
- Create: `infra/install-hermes-clean.sh`
- Create: `infra/verify-isolation.sh`
- Create: `infra/smoke/smoke-hermes.sh`

- [ ] **Step 1: 探索 Hermes 設定路徑機制（確認 HOME override 能隔離）**

Run:
```bash
ssh -i ~/.ssh/SSH_Tokyo_A1_Private.key opc@150.230.202.49 \
 'hermes --version; echo "---"; HOME=/data/harness-lab/home hermes --help 2>&1 | head -40'
```
Expected: 版本 0.13.0；確認其 config/memory 讀自 `$HOME/.hermes`（故 `HOME=$LAB_HOME` 即可得全新乾淨實例）。若 Hermes 用其他 env（如 `HERMES_HOME`），改用之並記錄。

- [ ] **Step 2: 寫 `infra/install-hermes-clean.sh`（全新乾淨 config/memory，雙 provider）**

```bash
#!/usr/bin/env bash
set -euo pipefail
source "$(dirname "$0")/00-paths.sh"
# 用現有已安裝的 hermes 二進位（0.13.0），但全新隔離 HOME → 全新 config + 空 memory
export HOME="$LAB_HOME"
mkdir -p "$LAB_HOME/.hermes"
cat > "$LAB_HOME/.hermes/.env" <<ENV
ANTHROPIC_API_KEY=${ANTHROPIC_API_KEY}
OPENAI_API_KEY=${OPENAI_API_KEY}
ENV
chmod 600 "$LAB_HOME/.hermes/.env"
cat > "$LAB_HOME/.hermes/config.yaml" <<YAML
providers:
  anthropic:
    base_url: https://api.anthropic.com
    key_env: ANTHROPIC_API_KEY
  openai:
    base_url: https://api.openai.com/v1
    key_env: OPENAI_API_KEY
model:
  default: ${OPENAI_MODEL}
YAML
echo "clean hermes config written under $LAB_HOME/.hermes"
ls -la "$LAB_HOME/.hermes"
```
（註：config.yaml 的確切 schema 以 Hermes 0.13.0 文件/現有生產 config 為範本校正；reasoning effort=high 的設定鍵依其文件加入。providers 區塊參考既有記憶中的格式。）

- [ ] **Step 3: 寫 `infra/verify-isolation.sh`（證明沒碰生產 Hermes）**

```bash
#!/usr/bin/env bash
set -euo pipefail
source "$(dirname "$0")/00-paths.sh"
echo "=== production hermes (/home/opc/.hermes) 應維持不變 ==="
echo "prod memory mtime: $(stat -c '%y' /home/opc/.hermes/memories/MEMORY.md 2>/dev/null || echo NA)"
echo "prod config  mtime: $(stat -c '%y' /home/opc/.hermes/config.yaml 2>/dev/null || echo NA)"
echo "=== prod hermes gateway 仍在跑且未被干擾 ==="
systemctl --user is-active hermes-gateway 2>/dev/null || echo "gateway state unknown"
echo "=== lab hermes 用獨立 HOME ==="
echo "lab .hermes exists: $([ -d "$LAB_HOME/.hermes" ] && echo yes || echo no)"
echo "lab != prod home: $([ "$LAB_HOME" != "$HOME" ] && echo yes || echo no)"
```

- [ ] **Step 4: 跑安裝 + 隔離驗證**

Run:
```bash
ssh -i ~/.ssh/SSH_Tokyo_A1_Private.key opc@150.230.202.49 \
 'cd /data/repos/xai-harness-faithfulness && bash infra/install-hermes-clean.sh && bash infra/verify-isolation.sh'
```
Expected: lab `.hermes` 建好；prod `/home/opc/.hermes` 的 mtime 不因本次而改（記錄之）；gateway `active`。

- [ ] **Step 5: 寫 `infra/smoke/smoke-hermes.sh`（兩模型，擷取 reasoning + tool 序列）**

```bash
#!/usr/bin/env bash
set -euo pipefail
source "$(dirname "$0")/../00-paths.sh"
export HOME="$LAB_HOME" ANTHROPIC_API_KEY OPENAI_API_KEY
run_one () {
  local tag="$1" model="$2"
  local WORK="$LAB/smoke/hermes-$tag"; rm -rf "$WORK"; mkdir -p "$WORK"; cd "$WORK"
  printf 'def add(a, b):\n    return a - b\n' > hello.py
  hermes run --model "$model" \
    "Fix the bug in hello.py so add returns the sum, by editing the file." 2>&1 | tee hermes.log | tail -15
  echo "--- $tag result ---"; cat hello.py
}
run_one haiku  "anthropic/$ANTHROPIC_MODEL"
run_one gptmini "openai/$OPENAI_MODEL"
```
（註：Hermes 非互動子指令與 `--model` 旗標以 `hermes --help` 校正；若需以 config.default 切模型則改之。）

- [ ] **Step 6: 跑 smoke，驗證兩模型修正成功且 log 有 reasoning/tool 序列**

Run:
```bash
ssh -i ~/.ssh/SSH_Tokyo_A1_Private.key opc@150.230.202.49 \
 'cd /data/repos/xai-harness-faithfulness && bash infra/smoke/smoke-hermes.sh'
```
Expected: 兩個 `hello.py` 皆 `a + b`；log 含工具序列。

- [ ] **Step 7: Commit**

```bash
git add infra/install-hermes-clean.sh infra/verify-isolation.sh infra/smoke/smoke-hermes.sh
git commit -m "infra: clean isolated Hermes 0.13.0 instance + isolation verify + dual-model smoke


```

---

## Task 7: 補齊 `ENVIRONMENT.lock.md` 確切版本

**Files:**
- Modify: `ENVIRONMENT.lock.md`

- [ ] **Step 1: 蒐集全部確切版本**

Run:
```bash
ssh -i ~/.ssh/SSH_Tokyo_A1_Private.key opc@150.230.202.49 'bash -lc "
export HOME=/data/harness-lab/home; B=/data/harness-lab/bin
echo claude: \$($B/claude --version 2>&1)
echo codex:  \$($B/codex --version 2>&1)
echo opencode: \$($B/opencode --version 2>&1)
echo hermes: \$(hermes --version 2>&1)
echo claude-trace: \$(cat /data/harness-lab/trace/prefix/node_modules/@loki-zhou/claude-trace/package.json | python3 -c \"import json,sys;print(json.load(sys.stdin)['version'])\")
echo date: \$(date -u +%Y-%m-%dT%H:%MZ)
"'
```
Expected: 四個 harness + claude-trace 的確切版本字串。

- [ ] **Step 2: 用實際值取代 `ENVIRONMENT.lock.md` 表內 TBD（含安裝路徑 `/data/harness-lab/.../prefix`、安裝日期）**

（依 Step1 輸出，把表格 4 列填滿，無 TBD 殘留。）

- [ ] **Step 3: 驗證無 TBD 殘留**

Run:
```bash
ssh -i ~/.ssh/SSH_Tokyo_A1_Private.key opc@150.230.202.49 \
 'grep -c TBD /data/repos/xai-harness-faithfulness/ENVIRONMENT.lock.md'
```
Expected: `0`。

- [ ] **Step 4: Commit**

```bash
git add ENVIRONMENT.lock.md
git commit -m "docs: finalize ENVIRONMENT.lock with exact pinned versions


```

---

## Task 8: Dossier — Claude Code（以 2.1.88 restored-src 為白箱依據）

**Files:**
- Create: `docs/dossier/claude-code.md`

- [ ] **Step 1: 定位 system prompt 與 tool 定義於 restored-src**

Run:
```bash
ssh -i ~/.ssh/SSH_Tokyo_A1_Private.key opc@150.230.202.49 'bash -lc "
SRC=/data/harness-lab/claude-code/restored-src
echo === tools dir ===; ls \$SRC/tools 2>/dev/null | head -40
echo === system prompt 候選 ===; grep -rilE \"You are|system prompt|<system\" \$SRC 2>/dev/null | head -20
echo === planning/loop 候選 ===; ls \$SRC | grep -iE \"loop|agent|planner|coordinator\" 2>/dev/null
"'
```
Expected: 列出 tool 實作檔、system prompt 所在、planning loop 模組。

- [ ] **Step 2: 寫 `docs/dossier/claude-code.md`（必含下列章節）**

必含章節（每節都要有實質內容，引用 restored-src 檔路徑/行號 + 對應 smoke trace 觀察）：
1. 版本與安裝（2.1.88，tarball）
2. system prompt 結構與關鍵段落（引 restored-src）
3. tool 集合與定義/docstring（列出 tools/ 下各 tool）
4. 工具選擇的理由與決策邏輯（agent loop 如何決定下一步工具）
5. planning / agent loop 結構
6. memory / 狀態機制
7. 如何注入模型（Haiku）與 high effort、如何掛 claude-trace
8. 與 smoke trace 對照（實際擷取到的 system/tools/tool_use 佐證）

- [ ] **Step 3: 驗證 dossier 完整性（章節齊全、無佔位）**

Run:
```bash
ssh -i ~/.ssh/SSH_Tokyo_A1_Private.key opc@150.230.202.49 'bash -lc "
f=/data/repos/xai-harness-faithfulness/docs/dossier/claude-code.md
for h in \"system prompt\" \"工具選擇\" \"planning\" \"memory\" \"claude-trace\"; do grep -q \"\$h\" \"\$f\" && echo OK:\$h || echo MISS:\$h; done
grep -ciE \"TBD|TODO|待補\" \"\$f\"
"'
```
Expected: 五項皆 `OK`；TBD 計數 `0`。

- [ ] **Step 4: Commit**

```bash
git add docs/dossier/claude-code.md
git commit -m "docs(dossier): Claude Code mechanism (system prompt, tools, tool-selection, loop)


```

---

## Task 9: Dossier — Codex CLI

**Files:**
- Create: `docs/dossier/codex-cli.md`

- [ ] **Step 1: 取得 Codex 原始碼/可觀察結構**

Run:
```bash
ssh -i ~/.ssh/SSH_Tokyo_A1_Private.key opc@150.230.202.49 'bash -lc "
P=/data/harness-lab/codex/prefix/node_modules/@openai/codex
ls \$P 2>/dev/null | head; echo ---; HOME=/data/harness-lab/home /data/harness-lab/bin/codex --help 2>&1 | head -50
"'
```
Expected: codex 套件結構 + help（model/effort/exec 旗標）。

- [ ] **Step 2: 寫 `docs/dossier/codex-cli.md`**（同 Task8 的八章節結構，對象換成 Codex；工具選擇邏輯以 help/config/observed log 為據；trace 來源為 `codex.log`/exec 輸出）

- [ ] **Step 3: 驗證完整性**

Run:
```bash
ssh -i ~/.ssh/SSH_Tokyo_A1_Private.key opc@150.230.202.49 'bash -lc "
f=/data/repos/xai-harness-faithfulness/docs/dossier/codex-cli.md
for h in \"system prompt\" \"工具選擇\" \"planning\" \"memory\" \"trace\"; do grep -q \"\$h\" \"\$f\" && echo OK:\$h || echo MISS:\$h; done
grep -ciE \"TBD|TODO|待補\" \"\$f\""'
```
Expected: 全 `OK`；TBD `0`。

- [ ] **Step 4: Commit**

```bash
git add docs/dossier/codex-cli.md
git commit -m "docs(dossier): Codex CLI mechanism


```

---

## Task 10: Dossier — OpenCode

**Files:**
- Create: `docs/dossier/opencode.md`

- [ ] **Step 1: 取得 OpenCode 結構與設定機制**

Run:
```bash
ssh -i ~/.ssh/SSH_Tokyo_A1_Private.key opc@150.230.202.49 'bash -lc "
P=/data/harness-lab/opencode/prefix/node_modules
ls \$P | grep -i opencode; echo ---; HOME=/data/harness-lab/home /data/harness-lab/bin/opencode --help 2>&1 | head -50
"'
```
Expected: opencode 套件 + help（run/model/provider）。

- [ ] **Step 2: 寫 `docs/dossier/opencode.md`**（八章節；工具選擇邏輯與 provider/model 設定；trace 來源 `oc.log`）

- [ ] **Step 3: 驗證完整性**

Run:
```bash
ssh -i ~/.ssh/SSH_Tokyo_A1_Private.key opc@150.230.202.49 'bash -lc "
f=/data/repos/xai-harness-faithfulness/docs/dossier/opencode.md
for h in \"system prompt\" \"工具選擇\" \"planning\" \"memory\" \"trace\"; do grep -q \"\$h\" \"\$f\" && echo OK:\$h || echo MISS:\$h; done
grep -ciE \"TBD|TODO|待補\" \"\$f\""'
```
Expected: 全 `OK`；TBD `0`。

- [ ] **Step 4: Commit**

```bash
git add docs/dossier/opencode.md
git commit -m "docs(dossier): OpenCode mechanism


```

---

## Task 11: Dossier — Hermes + 記憶機制專章（讀生產源碼 `/data/hermes-agent`）

**Files:**
- Create: `docs/dossier/hermes.md`
- Create: `docs/dossier/hermes-memory.md`

- [ ] **Step 1: 定位 Hermes 記憶機制源碼**

Run:
```bash
ssh -i ~/.ssh/SSH_Tokyo_A1_Private.key opc@150.230.202.49 'bash -lc "
SRC=/data/hermes-agent
grep -rilE \"memory|compress|consolidat|converg|summari|SOUL\" \$SRC --include=*.py --include=*.ts 2>/dev/null | head -30
"'
```
Expected: 記憶相關模組清單（壓縮/濃縮/收斂/SOUL）。

- [ ] **Step 2: 寫 `docs/dossier/hermes.md`**（八章節，對象 Hermes；以 `/data/hermes-agent` 源碼為據，但機制描述對應 lab 乾淨實例的行為）

- [ ] **Step 3: 寫 `docs/dossier/hermes-memory.md`（記憶機制專章）**

必含：記憶在什麼條件下**收斂／濃縮／成長變強**、觸發條件（時間？token？輪數？事件？）、SOUL.md 與 memory.md 的邊界與各自上限、壓縮/摘要流程、對實驗的意涵（為何要用乾淨空記憶實例以避免污染）。每點引源碼檔路徑/函式名佐證。

- [ ] **Step 4: 驗證兩檔完整性**

Run:
```bash
ssh -i ~/.ssh/SSH_Tokyo_A1_Private.key opc@150.230.202.49 'bash -lc "
f1=/data/repos/xai-harness-faithfulness/docs/dossier/hermes.md
f2=/data/repos/xai-harness-faithfulness/docs/dossier/hermes-memory.md
for h in \"system prompt\" \"工具選擇\" \"planning\" \"memory\"; do grep -q \"\$h\" \"\$f1\" && echo OK1:\$h || echo MISS1:\$h; done
for h in \"收斂\" \"濃縮\" \"觸發\" \"SOUL\" \"上限\"; do grep -q \"\$h\" \"\$f2\" && echo OK2:\$h || echo MISS2:\$h; done
grep -ciE \"TBD|TODO|待補\" \"\$f1\" \"\$f2\""'
```
Expected: 全 `OK`；TBD `0`。

- [ ] **Step 5: Commit**

```bash
git add docs/dossier/hermes.md docs/dossier/hermes-memory.md
git commit -m "docs(dossier): Hermes mechanism + memory convergence/compression chapter


```

---

## Task 12: 跨 harness 對照 + 機制總覽

**Files:**
- Create: `docs/dossier/00-overview.md`
- Create: `docs/dossier/cross-harness-comparison.md`

- [ ] **Step 1: 寫 `docs/dossier/cross-harness-comparison.md`（對照表）**

一張表，列四 harness 在以下維度的異同：system prompt 規模、tool 數量與種類、tool 選擇風格、planning 風格、memory 機制、模型注入方式、trace 擷取方式、white-box 可改入點（給 Phase 3 M1-M4 預備）。每格指向對應單一 harness dossier。

- [ ] **Step 2: 寫 `docs/dossier/00-overview.md`（導讀）**

導讀：dossier 目的、各檔索引、ENVIRONMENT.lock 連結、與 Phase 1-3 的關係（機制如何支撐 M1-M4 入點與 trace schema）。

- [ ] **Step 3: 驗證**

Run:
```bash
ssh -i ~/.ssh/SSH_Tokyo_A1_Private.key opc@150.230.202.49 'bash -lc "
d=/data/repos/xai-harness-faithfulness/docs/dossier
ls \$d; echo; grep -l \"white-box\\|M1\\|M2\\|M4\" \$d/cross-harness-comparison.md && echo has-whitebox-entrypoints
grep -ciE \"TBD|TODO|待補\" \$d/00-overview.md \$d/cross-harness-comparison.md"'
```
Expected: 七個 dossier 檔齊全；對照表含 white-box 入點；TBD `0`。

- [ ] **Step 4: Commit**

```bash
git add docs/dossier/00-overview.md docs/dossier/cross-harness-comparison.md
git commit -m "docs(dossier): cross-harness comparison + overview (white-box entrypoints for M1-M4)


```

---

## Task 13: Phase 0 gate 打包 + push + 請使用者審閱

**Files:** 無新檔（彙整）

- [ ] **Step 1: 產出 Phase 0 完成摘要**

Run（彙整 smoke 結果、版本、隔離證明）：
```bash
ssh -i ~/.ssh/SSH_Tokyo_A1_Private.key opc@150.230.202.49 'bash -lc "
echo === 四 harness smoke 結果 ===
for t in cc codex opencode-haiku opencode-gptmini hermes-haiku hermes-gptmini; do
  f=/data/harness-lab/smoke/$t/hello.py; [ -f \$f ] && echo \$t: \$(grep -q \"a + b\" \$f && echo FIXED || echo NOTFIXED)
done
echo === isolation ===; cd /data/repos/xai-harness-faithfulness && bash infra/verify-isolation.sh | tail -4
"'
```
Expected: 六個 smoke 全 `FIXED`；隔離驗證通過。

- [ ] **Step 2: Push 全部 Phase 0 commits**

```bash
ssh -i ~/.ssh/SSH_Tokyo_A1_Private.key opc@150.230.202.49 \
 'cd /data/repos/xai-harness-faithfulness && git push origin main'
```
Expected: push 成功。

- [ ] **Step 3: 請使用者審閱（GATE）**

向使用者報告：ENVIRONMENT.lock 確切版本、四 harness smoke 全通過、隔離證明（生產 Hermes 未受影響）、dossier 七檔重點。**取得核准後**才進入 Phase 1。若有修正，回到對應 task。

---

## Self-Review（對照 spec §3,§4,§5）

- **§3 版本鎖**：Task 1（骨架）+ Task 7（補齊）+ 各安裝 task 釘死版本 → 覆蓋。
- **§4 隔離與安全**：LAB_HOME 隔離（全 task）、Task 6 clean Hermes + verify-isolation、secrets 於 ~/.harness-exp（Task1 Step2）→ 覆蓋。
- **§5 機制 dossier**：Task 8-12 逐 harness + Hermes 記憶專章 + 跨 harness 對照 → 覆蓋。
- **四 harness 安裝 + 雙模型 + high effort + trace**：Task 2-6 → 覆蓋（Claude Code 僅 Haiku、Codex 僅 gpt-5.4-mini、OpenCode/Hermes 雙模型，符合 §4 config 表）。
- **Placeholder 掃描**：腳本中 `<VER>` 為「探索後釘死」的明確待填值，每處都有對應的 Step1 探索指令產生確值，非空白；dossier 完整性以 grep 檢查 TBD=0 強制。
- **型別/命名一致**：路徑變數 `LAB`/`LAB_HOME`/`LAB_BIN`、模型變數 `ANTHROPIC_MODEL`/`OPENAI_MODEL` 全程一致；symlink 一律落在 `$LAB_BIN`。
