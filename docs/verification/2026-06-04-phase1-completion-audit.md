# Phase 1 completion audit（2026-06-04）

Scope: Phase 1 Task 1-17 completion gate. All verification was run on the VPS
`opc@150.230.202.49` in `/data/repos/xai-harness-faithfulness`. The Mac was used
only for temporary document staging and private audit mirroring.

Phase 2 full factorial was not started.

## Conclusion

Phase 1 is complete and ready for user review. The repository now contains the
controlled task suite, hidden graders, runner, four harness adapters, normalized
trace schema, Pilot summary traces, trace recording policy, and GitHub-safe
verification reports.

The full plaintext records needed for later analysis are present outside git on
the VPS and mirrored on the Mac. GitHub contains only summary/public artifacts.

Next allowed action: wait for explicit user approval before starting Phase 2.

## Final Phase 1 state

| Area | Status | Evidence |
|---|---|---|
| Task suite | PASS | 20 tasks total: 5 categories x 4 tasks. |
| Difficulty calibration | PASS | Baseline-fail calibration is covered by tests; no missing hidden graders. |
| Config registry | PASS | 6 configs: Claude Code, OpenCode, Hermes, Codex across Haiku/GPT-mini where supported. |
| Runner and persistence | PASS | `runner run` / `runner pilot`; raw, private audit, and summary trace layers. |
| Trace schema | PASS | 6 Pilot traces validate with `validate_trace()`. |
| Private full records | PASS | Per-run private audits exist for all 6 Pilot traces. |
| Claude trace depth | PASS | Claude Code uses `claude-trace --include-all-requests`; JSONL and HTML are saved. |
| Overwrite safety | PASS | Existing trace paths fail fast unless `--overwrite` or unique repeat is used. |
| GitHub/public split | PASS | No `private-audits/**` or `*deep-trace-audit*` files are tracked. |
| Skill probe | PASS | Explicit safe skill prompt invoked `Skill`; Pilot non-use means no task need, not missing capability. |

## Deliverables

Code and data:

- `tasks/registry.yaml`: 20 registered tasks.
- `tasks/target_repo/`: controlled Python package baseline.
- `tasks/benchmark/*/baseline/`: Aider-polyglot / Exercism benchmark baselines.
- `tasks/graders/*_test.py`: hidden pytest graders.
- `runner/trace_schema.py`: normalized cross-harness trace schema.
- `runner/runner.py`, `runner/persist.py`, `runner/cli.py`: orchestration,
  raw persistence, private audit generation, trace persistence, overwrite guard.
- `runner/private_audit.py`: private plaintext audit generator.
- `runner/adapters/{claude_code,codex,opencode,hermes}.py`: four harness adapters.
- `traces/{1,6}/*/0.json`: six GitHub-safe Pilot summary traces.

Documentation:

- `docs/verification/2026-06-04-phase1-task1-15-pre-task16-audit.md`
- `docs/verification/2026-06-04-phase1-pilot-report.md`
- `docs/verification/2026-06-04-skill-probe-summary.md`
- `docs/verification/2026-06-04-phase1-completion-audit.md`
- `docs/specs/2026-06-04-trace-recording-policy.md`
- `docs/plans/2026-06-04-phase1-task-suite-runner-trace-pilot.md`

Private plaintext records:

- VPS manual deep audit:
  `/data/harness-lab/private-audits/manual/2026-06-04-phase1-pilot-deep-trace-audit.full.md`
- VPS per-run Pilot audits:
  `/data/harness-lab/private-audits/{1,6}/<task>/0.md`
- VPS skill probe audit:
  `/data/harness-lab/private-audits/skill-probes/2026-06-04-claude-skill-explicit.md`
- Mac mirror:
  `/Users/researcher/Desktop/Master/Oracle/private-audits/`

## Verification results

Repository state at audit start:

```text
## main...origin/main
a88369b docs(verification): enforce Phase 1 trace recording policy
```

Test suite:

```text
/data/harness-lab/runner-venv/bin/python -m pytest tests/ -q
.............................................................            [100%]
```

Task and config counts:

```text
tasks 20
categories {'bug_fix': 4, 'rename': 4, 'add_tests': 4, 'add_logging': 4, 'benchmark': 4}
tiers {2: 16, 1: 4}
sources {'controlled': 16, 'aider_polyglot': 4}
duplicate_ids []
missing_graders []
configs 6
```

Pilot dry-list:

```text
config 1: bugfix-t2-01, rename-t2-01, bench-grade-school
config 6: bugfix-t2-01, rename-t2-01, bench-grade-school
```

Trace validation and private-audit links:

```text
trace_files 6
traces/1/bench-grade-school/0.json private_audit_path ... exists True
traces/1/bugfix-t2-01/0.json private_audit_path ... exists True
traces/1/rename-t2-01/0.json private_audit_path ... exists True
traces/6/bench-grade-school/0.json private_audit_path ... exists True
traces/6/bugfix-t2-01/0.json private_audit_path ... exists True
traces/6/rename-t2-01/0.json private_audit_path ... exists True
trace validation + private audit links ok
```

Claude Code raw artifact depth:

```text
traces/1/bench-grade-school/0.json trace_html ... exists True
traces/1/bugfix-t2-01/0.json trace_html ... exists True
traces/1/rename-t2-01/0.json trace_html ... exists True
```

Overwrite guard:

```text
/data/harness-lab/runner-venv/bin/python -m runner pilot --repeat 0
rc=1
{
  "error": "trace_exists",
  "existing": [
    ".../traces/1/bugfix-t2-01/0.json",
    ".../traces/1/rename-t2-01/0.json",
    ".../traces/1/bench-grade-school/0.json",
    ".../traces/6/bugfix-t2-01/0.json",
    ".../traces/6/rename-t2-01/0.json",
    ".../traces/6/bench-grade-school/0.json"
  ]
}
```

GitHub-safe check:

```text
git ls-files "private-audits/**" "docs/verification/*deep-trace-audit*"
# no output
```

Secret-pattern scan notes: public files contain only variable names, scripts, or
sanitization instructions such as `OPENAI_API_KEY`, `ANTHROPIC_API_KEY`, and
`bearer`; no actual `sk-proj-` or `sk-ant-` secret values were found in public
Phase 1 traces or reports.

## Pilot result recap

| Config | Harness | Task | Success | Tool count | Private audit |
|---:|---|---|---|---:|---|
| 1 | Claude Code / Haiku | `bugfix-t2-01` | true | 6 | `/data/harness-lab/private-audits/1/bugfix-t2-01/0.md` |
| 1 | Claude Code / Haiku | `rename-t2-01` | true | 14 | `/data/harness-lab/private-audits/1/rename-t2-01/0.md` |
| 1 | Claude Code / Haiku | `bench-grade-school` | false | 10 | `/data/harness-lab/private-audits/1/bench-grade-school/0.md` |
| 6 | Codex / GPT-mini | `bugfix-t2-01` | true | 7 | `/data/harness-lab/private-audits/6/bugfix-t2-01/0.md` |
| 6 | Codex / GPT-mini | `rename-t2-01` | true | 24 | `/data/harness-lab/private-audits/6/rename-t2-01/0.md` |
| 6 | Codex / GPT-mini | `bench-grade-school` | false | 10 | `/data/harness-lab/private-audits/6/bench-grade-school/0.md` |

Interpretation: Pilot passed the pipeline gate. Controlled tasks show successful
repair/rename behavior; benchmark failures produce useful hard-case divergence
signal. The suite is not too easy at the Phase 1 gate.

## Known limits before Phase 2

- Phase 2 full factorial is still not run.
- Pilot has only two anchor configs and one repeat.
- Benchmark tasks should be watched in Phase 2 for all-fail cells.
- Token accounting is harness-specific and should be treated carefully.
- Raw hidden chain-of-thought is intentionally not committed; private audits use
  visible messages, tool I/O, and reasoning presence/count instead.

## Gate

Phase 1 is complete. Do not start Phase 2 until the user explicitly approves the
full 6 configs x 20 tasks x repeats run.
