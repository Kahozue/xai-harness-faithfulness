# Phase 0 task1-task13 audit（2026-06-03）

範圍：只驗證 `xai-harness-faithfulness` 的 Phase 0 task1-task13。未啟動 Phase 1、Phase 2、baseline factorial、HCI pair viewer 或任何正式實驗。

## 結論

Phase 0 的 13 個 task 已可接受為完成；本次 audit 另外補了兩個硬缺口：

- Claude Code smoke 補上 `--effort high`，符合 Phase 0 對全 harness high effort 的要求。
- 四個 smoke script 補上 hard assertions；之後若 agent 沒修好檔案或 trace 缺 tool sequence，script 會直接 fail，不再被 `|| true` 掩蓋。

仍需使用者 gate：`ENVIRONMENT.lock.md` 與七份 dossier 要經使用者審閱通過，才可進 Phase 1。不可直接跳 Phase 2。

## 實際環境

| 項目 | 值 |
| --- | --- |
| VPS | `opc@150.230.202.49` (`tokyo-a1`) |
| repo | `/data/repos/xai-harness-faithfulness` |
| LAB | `/data/harness-lab` |
| LAB_HOME | `/data/harness-lab/home` |
| LAB_BIN | `/data/harness-lab/bin` |
| secrets | `/home/opc/.harness-exp/{anthropic.env,openai.env}` (`0600`, repo 外) |
| xAI branch | `main` |
| HCI dependency | `/data/repos/hci-agent-attribution` 只讀確認；它依賴本 repo 的 factorial trace 作 ground truth，目前不應啟動 |

版本驗證：

| component | verified value |
| --- | --- |
| OS | Oracle Linux Server 9.7 aarch64 |
| node / npm | v22.22.2 / 10.9.7 |
| python / git | Python 3.11.13 / git 2.47.3 |
| Claude Code | 2.1.88 |
| claude-trace | 1.0.4 |
| Codex CLI | 0.136.0 |
| OpenCode | 1.15.13 |
| Hermes | 0.13.0 (2026.5.7) |

## Task-by-task audit

| Task | Status | Evidence |
| --- | --- | --- |
| 1. Lab paths + lock skeleton | PASS | `infra/00-paths.sh` sets `LAB`, `LAB_HOME`, `LAB_BIN`, model ids, secrets loading; both API keys load as `yes`; secrets are `0600`. |
| 2. Claude Code 2.1.88 install | PASS | `/data/harness-lab/bin/claude --version` returns `2.1.88`; installed from `/data/harness-lab/claude-code/claude-code-2.1.88.tgz`. |
| 3. claude-trace + Claude smoke | PASS after audit fix | `@loki-zhou/claude-trace` is `1.0.4`; `smoke-claude-code.sh` now passes `--effort high`; `hello.py` is fixed; trace contains `system`, `tools`, and `tool_use`. |
| 4. Codex CLI + OpenAI smoke | PASS | Codex is `0.136.0`; `$LAB_HOME/.codex/config.toml` pins model and `model_reasoning_effort="high"`; session JSONL confirms model, high effort marker, base instructions, user prompt, and tool/action lines. |
| 5. OpenCode dual provider smoke | PASS | OpenCode is `1.15.13`; config declares Anthropic/OpenAI providers and custom GPT snapshot; Haiku and GPT mini smoke outputs are fixed and `oc.log` contains `tool_use`. |
| 6. Clean Hermes + isolation smoke | PASS | Lab Hermes uses independent `HERMES_HOME=/data/harness-lab/home/.hermes`; production gateway is `active`; both Hermes smoke outputs are fixed and session traces contain `system_prompt`, `tools`, and tool calls. |
| 7. `ENVIRONMENT.lock.md` finalized | PASS | No deliverable TBD remains in `ENVIRONMENT.lock.md`; table has exact versions, paths, high effort injection, auth, trace source, smoke results, and isolation notes. |
| 8. Claude Code dossier | PASS after audit fix | `docs/dossier/claude-code.md` covers system prompt, tools, tool-selection, loop, memory, trace; now documents `--effort high` and API effort propagation. |
| 9. Codex dossier | PASS | `docs/dossier/codex-cli.md` covers base instructions, tool/action trajectory, planning, memory/session state, high effort, auth, and trace sources. |
| 10. OpenCode dossier | PASS | `docs/dossier/opencode.md` covers provider config, tool definitions, tool-selection differences, loop, state DB/export, high variant, and trace evidence. |
| 11. Hermes + memory dossier | PASS | `docs/dossier/hermes.md` and `docs/dossier/hermes-memory.md` cover system prompt, tool registry, provider transport, memory/SOUL/compression/convergence, trigger conditions, and experiment implications. |
| 12. Cross-harness overview | PASS | `docs/dossier/00-overview.md` and `cross-harness-comparison.md` include M1-M4 entrypoints, evidence levels, and cross-harness comparison. |
| 13. Gate package + push | PASS pending this audit commit | Six smoke artifacts are fixed; origin was already synced before this audit. Push this audit commit, then wait for user review before Phase 1. |

## Smoke artifact status

| config | path | expected result | trace evidence |
| --- | --- | --- | --- |
| Claude Code / Haiku | `/data/harness-lab/smoke/cc/hello.py` | `return a + b` | `.claude-trace/*.jsonl` with `system`, `tools`, `tool_use`, `thinking.type=enabled`, `budget_tokens=31999`; Haiku has no `output_config.effort` field |
| Codex / GPT mini | `/data/harness-lab/smoke/codex/hello.py` | `return a + b` | `codex.log` plus `$LAB_HOME/.codex/sessions/...jsonl` |
| OpenCode / Haiku | `/data/harness-lab/smoke/opencode-haiku/hello.py` | `return a + b` | `oc.log` with `tool_use` |
| OpenCode / GPT mini | `/data/harness-lab/smoke/opencode-gptmini/hello.py` | `return a + b` | `oc.log` with `tool_use` |
| Hermes / Haiku | `/data/harness-lab/smoke/hermes-haiku/hello.py` | `return a + b` | `trace.session.json` with tool calls |
| Hermes / GPT mini | `/data/harness-lab/smoke/hermes-gptmini/hello.py` | `return a + b` | `trace.session.json` with tool calls |

## Verification commands to reuse

```bash
cd /data/repos/xai-harness-faithfulness

# Versions
HOME=/data/harness-lab/home /data/harness-lab/bin/claude --version
HOME=/data/harness-lab/home /data/harness-lab/bin/codex --version
HOME=/data/harness-lab/home /data/harness-lab/bin/opencode --version
/home/opc/.local/bin/hermes --version

# Isolation
bash infra/verify-isolation.sh

# Smoke result summary without rerunning models
for t in cc codex opencode-haiku opencode-gptmini hermes-haiku hermes-gptmini; do
  f=/data/harness-lab/smoke/$t/hello.py
  printf "%-18s " "$t"
  [ -f "$f" ] && grep -q "a + b" "$f" && echo FIXED || echo NOTFIXED
done

# Placeholder scan for deliverables
grep -RInE "TBD|TODO|待補|<VER>|placeholder" ENVIRONMENT.lock.md docs/dossier infra README.md || true
```

Note：`docs/plans/2026-06-03-phase0-harness-setup-and-dossier.md` 是原始計畫書，內含示範 TBD / `<VER>` / unchecked boxes 屬設計文字；deliverable placeholder scan 不應把該計畫檔當成完成品檢查。

## Follow-up information already pinned for later phases

Do not ask again unless the repo changes:

- Model matrix: Claude Code/Haiku, OpenCode/Haiku, Hermes/Haiku, OpenCode/GPT mini, Hermes/GPT mini, Codex/GPT mini.
- Same model route rule: Haiku uses Anthropic native; GPT mini uses OpenAI native; WorldRouter is backup only and not part of the main experiment.
- Codex auth caveat: Codex 0.136 needs `codex login --with-api-key` into `$LAB_HOME/.codex/auth.json`; plain `OPENAI_API_KEY` alone was not enough.
- OpenCode caveat: `gpt-5.4-mini-2026-03-17` must be declared as a custom OpenAI model in `opencode.json`.
- Hermes caveat: use `-m "$model" --provider "$provider"` as separate flags; combined `provider/model` can silently fail for snapshot ids.
- Claude Code caveat: use `--effort high`; for Haiku 4.5, verify the CLI flag plus trace `thinking.type=enabled` / `budget_tokens=31999` because source `modelSupportsEffort()` excludes `haiku` from `output_config.effort`.
- Trace normalization starting points: Claude `.claude-trace/*.jsonl`, Codex stdout JSONL plus session JSONL, OpenCode JSON stdout/export, Hermes `session_*.json`.
- HCI dependency: HCI cannot proceed meaningfully until xAI produces factorial traces; HCI README explicitly treats xAI traces as ground truth.

## Gate status

Phase 0 is ready for user review after this audit commit is pushed. Next allowed step is Phase 1 planning/pilot only after explicit approval. Phase 2 remains blocked by design.
