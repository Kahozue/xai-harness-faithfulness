# ENVIRONMENT.lock — 凍結實驗環境（版本全釘死）

> 所有 harness 與模型版本在此釘死。任何變更須更新本檔並記錄日期與理由。
> 凍結日期：2026-06-03（UTC）。建置者：Phase 0 隔離建置流程（見 `infra/`）。

## 平台
- Host: Oracle Linux Server 9.7 (aarch64), VPS tokyo-a1（150.230.202.49）
- node: v22.22.2 | npm: 10.9.7 | python: 3.11.13 | git: 2.47.3
- 隔離：`LAB=/data/harness-lab`，`LAB_HOME=/data/harness-lab/home`（專屬 HOME），`LAB_BIN=/data/harness-lab/bin`
- secrets：`~/.harness-exp/{anthropic.env,openai.env}`（chmod 600，repo 外，永不進 git）
- runtime 產物（binaries、LAB_HOME、smoke workdirs）全在 `/data/harness-lab/`（repo 外，不追蹤）

## 模型（帶日期 snapshot）
- Haiku 4.5: `claude-haiku-4-5-20251001`（Anthropic 原生 api.anthropic.com）
- GPT-5.4-mini: `gpt-5.4-mini-2026-03-17`（OpenAI 原生 api.openai.com）
- reasoning effort: high（全部；各 harness 注入機制見下表）

## 模型路由（控制變數）
| 模型 | 後端 | 使用此模型的 harness |
|------|------|----------------------|
| Haiku 4.5 | Anthropic 原生 | Claude Code、OpenCode、Hermes |
| GPT-5.4-mini | OpenAI 原生 | Codex CLI、OpenCode、Hermes |

## Harness 版本（已釘死）
| Harness | 版本 | 安裝來源 | 安裝路徑 | 安裝日期 |
|---------|------|----------|----------|----------|
| Claude Code | 2.1.88 | local tarball `claude-code-2.1.88.tgz` | `/data/harness-lab/claude-code/prefix` | 2026-06-03 |
| claude-trace | 1.0.4 | npm `@loki-zhou/claude-trace@1.0.4` | `/data/harness-lab/trace/prefix` | 2026-06-03 |
| Codex CLI | 0.136.0 | npm `@openai/codex@0.136.0` | `/data/harness-lab/codex/prefix` | 2026-06-03 |
| OpenCode | 1.15.13 | npm `opencode-ai@1.15.13` | `/data/harness-lab/opencode/prefix` | 2026-06-03 |
| Hermes | 0.13.0 (2026.5.7) | 全新乾淨隔離實例（共享生產同版二進位 `/home/opc/.local/bin/hermes`，獨立 `HERMES_HOME`） | `HERMES_HOME=/data/harness-lab/home/.hermes` | 2026-06-03 |

> 白箱參照：Claude Code 2.1.88 的 restored-src 置於 `/data/harness-lab/claude-code/restored-src`（供 dossier 與 Phase 3 M1/M2）。

## 每個 harness 的模型注入 / high effort / trace 擷取 / 認證（Phase 0 校正所得）
| Harness | 模型注入 | high effort | trace 來源 | 認證 |
|---------|----------|-------------|------------|------|
| Claude Code | `claude --model <id> --effort high`（經 `claude-trace --run-with`） | CLI 固定 `--effort high`；Haiku 4.5 在 2.1.88 source 中不支援 `output_config.effort`，實際 request 以 `thinking.type=enabled`、`budget_tokens=31999` 呈現 | claude-trace `.claude-trace/*.jsonl`（含 system / tools / tool_use） | `ANTHROPIC_API_KEY` 環境變數（Anthropic 原生） |
| Codex CLI | `$LAB_HOME/.codex/config.toml` `model=`；`codex exec` | `config.toml` `model_reasoning_effort="high"` | `codex exec --json` JSONL（agent_message / command_execution / file_change） | `codex login --with-api-key`（寫入 `$LAB_HOME/.codex/auth.json`，File 模式） |
| OpenCode | `opencode run -m <provider>/<id>` | `run --variant high`（provider-specific reasoning effort） | `opencode run --format json` JSONL（tool_use / step events） | `opencode.json` `provider.*.options.apiKey={env:...}` |
| Hermes | `hermes -z PROMPT -m <id> --provider <provider>`（**分開形式**；合併 `-m provider/model` 對 snapshot id 會靜默失敗） | `config.yaml` `agent.reasoning_effort: high` | `$HERMES_HOME/sessions/session_*.json`（含 system_prompt / tools / 有序 tool_calls）；另有 `request_dump_*.json` 原始請求 | `config.yaml` `providers.*.key_env` + `$HERMES_HOME/.env`；anthropic 走 `api_mode: anthropic_messages`（原生 Messages API） |

## Phase 0 smoke 結果（單檔 bug fix：`add` 由 `a - b` 改為 `a + b`）
| Config | Harness | Model | 結果 | trace |
|--------|---------|-------|------|-------|
| 1 | Claude Code | Haiku 4.5 | FIXED | jsonl（14 對請求，含 system/tools/tool_use） |
| 6 | Codex CLI | GPT-5.4-mini | FIXED | JSONL（command_execution + file_change） |
| 2 | OpenCode | Haiku 4.5 | FIXED | JSON（read + edit） |
| 4 | OpenCode | GPT-5.4-mini | FIXED | JSON（apply_patch + read，reasoning tokens 有值） |
| 3 | Hermes | Haiku 4.5 | FIXED | session JSON（read_file + patch，anthropic_messages 原生） |
| 5 | Hermes | GPT-5.4-mini | FIXED | session JSON（read_file + patch） |

## 隔離與安全證明
- 生產 Hermes（花帆）未受影響：`/home/opc/.hermes/config.yaml` mtime 全程恆為 `2026-05-14 17:20:03`（凍結錨點）；`hermes-gateway` 全程 `active`。
- lab Hermes 為全新乾淨實例：`HERMES_HOME` 獨立、`memories/` 空、`SOUL.md`（513B 預設）與生產（1195B）不同檔，非複製。
- 所有 harness 設定/狀態隔離於 `LAB_HOME`（各自 `.claude` / `.codex` / `.config/opencode` / `.hermes`），不碰 `/home/opc` 生產 dotfiles。
- secrets 永不進 git：trace（含 Hermes session JSON）經精準檢查無真實 key（`sk-proj-`/`sk-ant-` 計數為 0）；`.env`/`auth.json` 皆 chmod 600 且在 repo 外。

## 閘道路由
- 同一模型固定走同一後端：Haiku 4.5 → Anthropic 原生；GPT-5.4-mini → OpenAI 原生。WorldRouter 退為備援、不進主實驗。
