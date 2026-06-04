# Phase 2 quota blocker（2026-06-04）

Scope: clean isolated Phase 2 batch launched from commit `1171d38` with per-run
HOME isolation, OpenCode `--dir <workdir>`, and repo-baseline escape guard.

## Batch status

The clean batch completed all planned runner slots:

```text
phase2_start: 1
phase2_run_start: 360
phase2_run_result: 360
phase2_complete: {"completed": 360, "errors": 0}
```

Trace validation status:

```text
expected traces: 360
found traces: 360
missing: 0
invalid schema: 0
```

However, Phase 2 is not analysis-ready because config 3 is not valid behavioral
data.

## Blocking issue

Config 3 (`hermes` + `claude-haiku-4-5-20251001` via Anthropic) failed every
run before any assistant/tool behavior occurred:

```text
config 1: n=60, success=48, tool_calls_total=503
config 2: n=60, success=11, tool_calls_total=135
config 3: n=60, success=0,  tool_calls_total=0
config 4: n=60, success=51, tool_calls_total=604
config 5: n=60, success=46, tool_calls_total=452
config 6: n=60, success=52, tool_calls_total=546
```

For config 3, all 60 Hermes request dumps contain the same Anthropic quota
failure:

```text
You have reached your specified API usage limits.
You will regain access on 2026-07-01 at 00:00 UTC.
```

The sessions contain only the user message (`messages=1`) and no assistant/tool
messages. The normalized traces therefore show `tool_calls=[]`, `turns=0`, and
grader failures caused by unchanged workdirs. These are infrastructure/quota
failures, not harness/model behavior.

## Evidence paths

- Batch log:
  `/data/harness-lab/phase2/phase2-isolated-20260603T202227Z.jsonl`
- Example config 3 trace:
  `traces/3/bugfix-t2-01/1.json`
- Example config 3 private audit:
  `/data/harness-lab/private-audits/3/bugfix-t2-01/1.md`
- Example config 3 request dump:
  `/data/harness-lab/runs/3/bugfix-t2-01/1/home/.hermes/sessions/request_dump_20260604_050041_5e3e19_20260604_050042_509073.json`

## Required decision

Do not use config 3 as behavioral data without an explicit analysis decision.
One of these must happen before Phase 2 can be considered complete:

1. Wait until Anthropic quota resets, then rerun config 3 only.
2. Provide/use another Anthropic key and rerun config 3 now.
3. Mark config 3 as infrastructure-missing and proceed with a documented
   5-config limitation.

Until that decision is made and executed, Phase 2 remains blocked for xAI/HCI
analysis.
