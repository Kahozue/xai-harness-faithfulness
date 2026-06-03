# Phase 1 Pilot report（2026-06-04）

Scope: Phase 1 Task 16 Pilot only. This produced the planned 2 configs x
3 tasks = 6 committed Pilot matrix traces on the VPS `opc@150.230.202.49` in
`/data/repos/xai-harness-faithfulness`. Before the matrix, one pre-loop smoke
run was also executed for config 1 / `bugfix-t2-01` / repeat 0. It did not start
Phase 2 full factorial.

Environment reference: `ENVIRONMENT.lock.md@3d309d2`. Runner venv:
`/data/harness-lab/runner-venv` with Python 3.11.13 and pinned dependencies in
`runner/requirements.txt`. Raw logs remain outside git under
`/data/harness-lab/runs/`; committed artifacts are sanitized normalized traces
under `traces/`.

Private full trace supplement: the detailed plaintext audit with per-run tool
input/output summaries, visible model messages, skill-use status, errors,
recoveries, and benchmark failure diagnosis is intentionally not committed to
git/GitHub. It is stored on the VPS under
`/data/harness-lab/private-audits/manual/2026-06-04-phase1-pilot-deep-trace-audit.full.md`
and mirrored on the Mac under `private-audits/`.

## Pilot matrix

Configs:

- Config 1: Claude Code 2.1.88 / Haiku 4.5 via Anthropic native
- Config 6: Codex CLI 0.136.0 / GPT-5.4-mini via OpenAI native

Tasks:

- `bugfix-t2-01`（controlled bug_fix）
- `rename-t2-01`（controlled rename）
- `bench-grade-school`（Aider-polyglot / Exercism benchmark）

## Result table

The table below covers the six committed matrix traces. The pre-loop smoke raw
log remains at
`/data/harness-lab/runs/1/bugfix-t2-01/0/raw/log-2026-06-03-18-47-08.jsonl`.
Because the smoke and later matrix run both used repeat 0, the later matrix run
overwrote the normalized smoke trace at `traces/1/bugfix-t2-01/0.json`.

| Config | Harness | Task | Success | Tool count | Tool sequence | Wall s | Input | Cached input | Output |
|---:|---|---|---|---:|---|---:|---:|---:|---:|
| 1 | claude_code | bench-grade-school | false | 10 | `Bash -> Read -> Glob -> Bash -> Bash -> Bash -> Bash -> Bash -> Edit -> Bash` | 29.031 | 7 | 18938 | 2817 |
| 1 | claude_code | bugfix-t2-01 | true | 6 | `Read -> Glob -> Bash -> Read -> Edit -> Read` | 19.727 | 7 | 17950 | 1961 |
| 1 | claude_code | rename-t2-01 | true | 14 | `Glob -> Glob -> Bash -> Read -> Read -> Read -> Read -> Edit -> Edit -> Edit -> Edit -> Read -> Read -> Read` | 30.050 | 7 | 19487 | 2511 |
| 6 | codex | bench-grade-school | false | 10 | `command_execution -> command_execution -> command_execution -> command_execution -> file_change -> command_execution -> command_execution -> file_change -> command_execution -> command_execution` | 23.020 | 87003 | 73984 | 3052 |
| 6 | codex | bugfix-t2-01 | true | 7 | `command_execution -> command_execution -> command_execution -> command_execution -> file_change -> command_execution -> command_execution` | 15.361 | 57347 | 44032 | 1613 |
| 6 | codex | rename-t2-01 | true | 24 | `command_execution -> command_execution -> command_execution -> command_execution -> command_execution -> command_execution -> command_execution -> command_execution -> command_execution -> command_execution -> file_change -> command_execution -> command_execution -> command_execution -> command_execution -> file_change -> command_execution -> command_execution -> command_execution -> command_execution -> command_execution -> command_execution -> command_execution -> command_execution` | 41.075 | 184774 | 176000 | 5519 |

Summary:

```text
success: 4 / 6
trace files: 6
schema validation: pass
all tool sequences non-empty: pass
total wall time: 158.264s
average wall time: 26.377s
total output tokens recorded: 17473
```

## Gate criteria

| Criterion | Status | Evidence |
|---|---|---|
| Adapter captures tool sequence | PASS | All six normalized traces have `tool_calls >= 1`; counts are 6, 14, 10, 7, 24, 10. |
| Grader works | PASS | Controlled bugfix and rename pass for both anchor configs; benchmark fails with concrete hidden-test failures, not harness/runtime failure. |
| Trace normalization complete | PASS | `validate_trace()` passed for all six `traces/*/*/0.json` files. |
| Cost/time acceptable | PASS for Pilot | No timeout; wall time range 15.361s to 41.075s. Sequential full factorial rough estimate from Pilot mean is about 2.64h for 360 runs, before accounting for slower harnesses/tasks and retries. |

Non-token verification after Pilot:

```text
/data/harness-lab/runner-venv/bin/python -m pytest tests/ -q
.......................................................                  [100%]
```

Secret scan:

```text
rg sensitive-token-patterns traces/
```

Observed: no output.

## Cross-harness observations

The Pilot already shows usable divergence signal:

- `bugfix-t2-01`: both pass. Claude Code uses direct file-oriented tools
  (`Read`, `Glob`, `Bash`, `Edit`, verification `Read`), while Codex emits
  command/file-change events (`command_execution`, `file_change`) around the
  same behavioral fix.
- `rename-t2-01`: both pass, but Codex uses a much longer sequence
  (24 normalized tool events, including two `file_change` events), while Claude
  Code uses 14 events with explicit `Edit` operations. This is strong enough for
  tool-sequence divergence analysis.
- `bench-grade-school`: both fail, but not in the same trace surface. Claude
  Code exposes shell/read/edit-style operations with 9 hidden-test failures.
  Codex exposes command/file-change events with 10 hidden-test failures. This
  gives a useful hard-task failure case without breaking the pipeline.

Interpretation: the suite is not too easy at the Pilot checkpoint. Controlled
tasks confirm the grader can recognize success; benchmark adds failure signal;
tool paths differ even on successful tasks.

## Known limitations

- Pilot only covers two anchor configs. It validates the pipeline, not the full
  6-config factorial.
- The pre-loop smoke reused the same config/task/repeat path as the later matrix
  run. The raw smoke log remains, but the normalized trace was overwritten. For
  Phase 2, use unique repeat indexes for smoke/probe runs or add an explicit
  runner overwrite policy.
- Codex token fields are much larger than Claude Code token fields because the
  harnesses expose different usage accounting surfaces. Treat token comparisons
  as per-harness operational metadata unless normalized further.
- `bench-grade-school` may be too strict for both anchor models in one shot. It
  is still useful as a hard case, but Phase 2 should monitor whether benchmark
  tasks produce all-fail cells across all configs.

## Recommendation

Phase 1 Pilot passes the gate criteria. It is reasonable to proceed to Task 17
completion audit and then ask for Phase 2 approval. Do not start Phase 2 full
factorial automatically.
