# Phase 2 completion report (2026-06-04)

Scope: formal Phase 2 baseline factorial on the VPS checkout
`/data/repos/xai-harness-faithfulness`. The formal matrix is repeats 1, 2, and
3 only: 6 configs x 20 tasks x 3 repeats = 360 traces. Repeat 0 remains Phase 1
Pilot data and is not included in the statistics below.

## Conclusion

Phase 2 is complete and analysis-ready after two targeted post-limit-reset
reruns:

- Config 3 (`hermes` + `claude-haiku-4-5-20251001`) rerun log:
  `/data/harness-lab/phase2/phase2-config3-rerun-20260604T002520Z.jsonl`
- Config 2 (`opencode` + `claude-haiku-4-5-20251001`) rerun log:
  `/data/harness-lab/phase2/phase2-config2-rerun-20260604T014611Z.jsonl`

The final validation gate passed:

```text
python -m runner phase2-validate --indent 0
ok: true
expected_traces: 360
found_traces: 360
missing_traces: 0
invalid_json: 0
invalid_schema: 0
missing_private_audits: 0
missing_raw_dirs: 0
missing_raw_artifacts: 0
missing_run_homes: 0
nonisolated_run_homes: 0
infra_failure_flags: 0
all_zero_tool_configs: 0
```

Validation JSON is saved on the VPS at
`/data/harness-lab/phase2/phase2-validate-20260604.json`.

## Formal matrix summary

Overall formal Phase 2 result: 295 successes, 65
failures, 3155 normalized tool calls across 360 traces.

| Config | Harness | Model | n | Success | Fail | Zero-tool runs | Tool calls | Top tools |
|---:|---|---|---:|---:|---:|---:|---:|---|
| 1 | claude_code | claude-haiku-4-5-20251001 | 60 | 48 | 12 | 0 | 503 | Read:187, Bash:170, Edit:97, Glob:30, Write:14, Grep:4 |
| 2 | opencode | claude-haiku-4-5-20251001 | 60 | 48 | 12 | 0 | 611 | read:241, bash:189, edit:100, todowrite:62, write:12, glob:7 |
| 3 | hermes | claude-haiku-4-5-20251001 | 60 | 50 | 10 | 0 | 439 | read_file:157, terminal:114, patch:81, search_files:58, write_file:29 |
| 4 | opencode | gpt-5.4-mini-2026-03-17 | 60 | 51 | 9 | 0 | 604 | glob:177, read:155, bash:113, apply_patch:71, grep:48, todowrite:31 |
| 5 | hermes | gpt-5.4-mini-2026-03-17 | 60 | 46 | 14 | 0 | 452 | search_files:180, read_file:112, patch:69, terminal:64, write_file:16, execute_code:9 |
| 6 | codex | gpt-5.4-mini-2026-03-17 | 60 | 52 | 8 | 0 | 546 | command_execution:472, file_change:74 |

## Trace interpretation boundary

The core xAI dependent variable for Phase 2 is the observed chosen-tool path:
`tool_calls` as an ordered sequence of normalized tool names plus compact
argument summaries. This is sufficient for baseline factorial comparison of tool
selection divergence across harness/model cells.

Phase 2 baseline traces do not directly expose every unchosen tool alternative
or hidden internal rationale. The `decision_points` field is intentionally empty
for all 360 formal traces. Decision-point attribution is a Phase 3 task that
combines dossier/source M1/M2 evidence, direct M3 counterfactual traces, and M4
trace review; direct M1/M2 runtime perturbation is not claimed uniformly across
closed/native harnesses. PPT and report text should describe Phase 2 as chosen-tool-sequence
evidence, not as complete internal decision-tree evidence.

## Isolation and one-shot status

All formal traces point to run-local artifacts under
`/data/harness-lab/runs/<config>/<task>/<repeat>/`. The validation gate checked
that each formal run has its own HOME directory at
`/data/harness-lab/runs/<config>/<task>/<repeat>/home` and that no formal run
uses the shared template HOME `/data/harness-lab/home` as writable harness state.

The runner still refuses to overwrite traces unless `--overwrite` is passed
explicitly. The config 2 and config 3 reruns used `--overwrite` intentionally to
replace infrastructure-contaminated Anthropic-limit traces after the API limit
reset. Future smoke/probe runs should use repeat indexes outside 1-3 unless they
are intentional formal reruns.

## Public/private artifact split

Committed public artifacts:

- `traces/<config>/<task>/<repeat>.json` for formal repeats 1-3.
- `docs/verification/2026-06-04-phase2-completion-report.md`.
- Verification and policy docs explaining isolation, quota reruns, and trace
  semantics.

Private VPS artifacts, not committed:

- Per-run private audits under `/data/harness-lab/private-audits/<config>/<task>/<repeat>.md`.
- Raw harness logs under `/data/harness-lab/runs/<config>/<task>/<repeat>/raw/`.
- Batch logs and validation JSON under `/data/harness-lab/phase2/`.

## Notes for downstream xAI/HCI

- Use formal repeats 1-3 only for factorial statistics and HCI ground-truth pair
  construction.
- Do not include repeat 0 Pilot traces in Phase 2 aggregate metrics.
- Treat failures with non-empty tool paths as behavioral failures, not missing
  data.
- Treat `decision_points=[]` as an explicit Phase 2 boundary; populate or label
  decision points in Phase 3 rather than inferring hidden alternatives from the
  baseline alone.
