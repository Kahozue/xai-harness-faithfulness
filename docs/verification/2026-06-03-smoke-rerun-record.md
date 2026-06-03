# Smoke rerun record（2026-06-03）

Scope: Phase 0 task1-task13 verification only. This rerun did not start Phase 1 or Phase 2. Raw runtime logs remain under `/data/harness-lab/smoke/` outside git; this document commits only sanitized structural evidence because raw traces can contain request metadata and must not become a secrets-adjacent artifact.

## SDK/source decision

Claude Code 2.1.88 was checked against `/data/harness-lab/claude-code/restored-src` before finalizing the smoke gate:

- `entrypoints/sdk/coreSchemas.ts` exposes `ThinkingConfigSchema` and agent `effort`.
- `main.tsx` reads `MAX_THINKING_TOKENS` and converts it to `thinkingConfig: {type: enabled, budgetTokens}`.
- `services/api/claude.ts` resolves `CLAUDE_CODE_MAX_OUTPUT_TOKENS` into request `max_tokens`, then clamps thinking budget to `max_tokens - 1`.
- `utils/context.ts` sets Haiku 4.5 max output upper limit to 64,000 and thus max budget thinking to 63,999.
- `utils/thinking.ts` shows Haiku 4.5 supports budget thinking but not adaptive thinking.
- `utils/effort.ts` excludes `haiku` from `output_config.effort`; `max` effort is not public-supported for this model.

Decision: do not force unsupported `CLAUDE_CODE_ALWAYS_ENABLE_EFFORT`. For Claude Code / Haiku 4.5, the highest verifiable setting is:

```bash
CLAUDE_CODE_EFFORT_LEVEL=high
CLAUDE_CODE_MAX_OUTPUT_TOKENS=64000
MAX_THINKING_TOKENS=63999
claude --model claude-haiku-4-5-20251001 --effort high
```

## Commands run

```bash
cd /data/repos/xai-harness-faithfulness
bash infra/smoke/smoke-claude-code.sh

for t in cc codex opencode-haiku opencode-gptmini hermes-haiku hermes-gptmini; do
  f=/data/harness-lab/smoke/$t/hello.py
  printf "%-18s " "$t"
  [ -f "$f" ] && rg -q "return a \\+ b" "$f" && echo FIXED || echo NOTFIXED
done
```

## Result summary

| Config | Artifact | Result | Sanitized trace evidence |
| --- | --- | --- | --- |
| Claude Code / Haiku | `/data/harness-lab/smoke/cc/hello.py` | FIXED | `/data/harness-lab/smoke/cc/.claude-trace/log-2026-06-03-14-03-20.jsonl`: 3 main requests, model `claude-haiku-4-5-20251001`, all `max_tokens=64000`, all `thinking={type: enabled, budget_tokens: 63999}`, all include `system`, all include 23 tools, `tool_use` observed, no `output_config`. |
| Codex CLI / GPT mini | `/data/harness-lab/smoke/codex/hello.py` | FIXED | `codex.log`: 19 JSONL lines, 8 `command_execution` markers, 2 `file_change` markers. Latest session JSONL: 38 lines, model `gpt-5.4-mini-2026-03-17`, effort `high`, tools `exec_command` x4 and `apply_patch` x1. |
| OpenCode / Haiku | `/data/harness-lab/smoke/opencode-haiku/hello.py` | FIXED | `oc.log`: 11 JSONL lines, 2 `tool_use` events, tool names `read` and `edit`. |
| OpenCode / GPT mini | `/data/harness-lab/smoke/opencode-gptmini/hello.py` | FIXED | `oc.log`: 20 JSONL lines, 5 `tool_use` events, tool names `glob`, `read`, and `apply_patch`. |
| Hermes / Haiku | `/data/harness-lab/smoke/hermes-haiku/hello.py` | FIXED | `trace.session.json`: model `claude-haiku-4-5-20251001`, top-level `system_prompt` and 18 tools, tool calls present (`read_file` / `patch` path verified by structural scan). |
| Hermes / GPT mini | `/data/harness-lab/smoke/hermes-gptmini/hello.py` | FIXED | `trace.session.json`: model `gpt-5.4-mini-2026-03-17`, top-level `system_prompt` and 18 tools, tool calls present (`read_file` / `patch` path verified by structural scan). |

All six smoke artifacts contain `return a + b` after rerun/inspection.

## PPT/report note

No `.ppt`, `.pptx`, or `.key` file exists in the xAI repo at this phase. The required PPT/report disclosure is therefore pinned here and in `HCI_REPORT_NOON_REQUIREMENTS.md`: include harness versions, model snapshots, provider route, reasoning effort, Claude Code `max_tokens=64000`, `thinking.budget_tokens=63999`, Haiku 4.5 200k context window, and the raw-log-vs-sanitized-summary evidence policy.
