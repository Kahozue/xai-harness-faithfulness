# Phase 1 task1-task15 pre-task16 audit（2026-06-04）

Scope: Phase 1 task1-task15 only. This audit did not run Task 16 Pilot and did
not spend model/API token. All verification commands were run on the VPS
`opc@150.230.202.49` in `/data/repos/xai-harness-faithfulness`; the Mac checkout
was used only as a temporary document staging view.

## Conclusion

Task1-task15 are acceptable to gate into Task 16 after this audit fix is
committed on the VPS. The implementation is not merely documentation: the VPS
test suite passes, the task registry has 20 tasks, hidden-test baseline
calibration is active, and `python -m runner pilot --dry-list` plans exactly the
six non-full-run Pilot cases.

Two record/reproducibility gaps were found and fixed in this pass:

- `tests/fixtures/{codex,opencode-haiku,opencode-gptmini}.smoke.log` existed on
  the VPS and were required by adapter tests, but `.gitignore` ignored `*.log`,
  so a fresh checkout would miss them. `.gitignore` now explicitly allows these
  sanitized smoke fixtures to be tracked.
- After the suite rebalance from five controlled tasks per category to five
  categories x 4 tasks, obsolete unreferenced grader files remained:
  `rename-t2-05_test.py`, `addtests-t2-05_test.py`, and `addlog-t2-05_test.py`.
  They were removed to avoid future confusion.

Task 16 remains gated because it launches real harnesses and spends token.

## Task-by-task status

| Task | Status | Evidence |
| --- | --- | --- |
| 1. Engine skeleton, venv, paths, requirements | PASS | `6e9559c`; `runner/paths.py`, `runner/requirements.txt`, `pytest.ini`, `tests/test_paths.py`; `ENVIRONMENT.lock.md` records `/data/harness-lab/runner-venv`. |
| 2. Normalized trace schema | PASS | `91f09d8`; `runner/trace_schema.py`; schema includes `tool_calls`, outcome, tokens, runtime budget, `system_present`, and evidence levels. |
| 3. Six config registry | PASS | `b5cadda`; `runner/configs.py`; configs 1-6 preserve native provider routing. |
| 4. Controlled target repo, registry seed, provision | PASS | `d9f6ee3`; `tasks/target_repo`, `tasks/registry.yaml`, `runner/provision.py`; hidden graders are not copied into workdir. |
| 5. Unified hidden-pytest grader | PASS | `2596821`; `runner/grader.py`; baseline fail and reference pass covered in tests. |
| 6. Rename task category | PASS after rebalance | `0044c08` created rename tasks; `f6fce45` rebalanced to `rename-t2-01..04`; obsolete `rename-t2-05` grader removed in this audit. |
| 7. Add-tests task category | PASS after rebalance | `0b8fb08` created add_tests tasks; `f6fce45` rebalanced to `addtests-t2-01..04`; obsolete `addtests-t2-05` grader removed in this audit. |
| 8. Add-logging task category | PASS after rebalance | `c41c10d` created add_logging tasks; `f6fce45` rebalanced to `addlog-t2-01..04`; obsolete `addlog-t2-05` grader removed in this audit. |
| 9. Benchmark tasks and bug_fix completion | PASS | `6ec1db1` replaced SWE-bench with Aider-polyglot Python/Exercism benchmark tasks; `f6fce45` finalized `bugfix-t2-01..04`. |
| 10. Adapter base + Claude Code adapter | PASS | `ca0ffb0`; `runner/adapters/base.py`, `claude_code.py`; fixture-backed SSE normalizer test. |
| 11. Controlled suite rebalance | PASS | `f6fce45`; final registry is 20 tasks, five categories x 4; SWE-bench route is explicitly abandoned. |
| 12. Codex adapter | PASS after fixture tracking fix | `1c230ef`; `runner/adapters/codex.py`; `tests/fixtures/codex.smoke.log` is now tracked instead of only present on VPS. |
| 13. OpenCode adapter | PASS after fixture tracking fix | `9ff148d`; `runner/adapters/opencode.py`; both OpenCode smoke logs are now tracked instead of only present on VPS. |
| 14. Hermes adapter | PASS | `875ef21`; `runner/adapters/hermes.py`; fixture-backed session JSON normalizer tests. |
| 15. Runner orchestration, persistence, CLI | PASS | `d565ec2`; `runner/runner.py`, `runner/persist.py`, `runner/cli.py`, `runner/__main__.py`; mock runner test and Pilot dry-list pass. |

## Task suite and difficulty check

The current suite has 20 tasks:

```text
bug_fix: 4
rename: 4
add_tests: 4
add_logging: 4
benchmark: 4
tier 2 controlled: 16
tier 1 benchmark: 4
```

This is not "too easy to distinguish" at the pre-pilot stage for three reasons:

- Baseline-fail calibration covers every registered task. `tests/test_calibration.py`
  provisions each task before any agent fix and requires the hidden grader to
  fail, preventing already-solved or no-op tasks.
- The suite mixes low-friction controlled tasks with harder benchmark tasks.
  Rename/add_logging/add_tests should expose tool-path and editing-style
  differences even when they pass; benchmark tasks add implementation depth so
  success does not trivially hit 100 percent.
- The Pilot sample includes one bug fix, one rename, and one benchmark task
  across config 1 and config 6. That is enough to test trace capture, grader
  correctness, and whether the anchor harnesses show non-identical tool paths
  before spending on the full factorial.

Risk to watch in Task 16: if all six Pilot runs pass with nearly identical
single-tool paths, Phase 2 should swap one Pilot-controlled task for
`bench-phone-number` or `bench-pig-latin` before full scale. Do not make that
decision before seeing real Pilot traces.

## Verification on VPS

Commands run:

```bash
cd /data/repos/xai-harness-faithfulness
git status --short --ignored tests/fixtures .gitignore tasks/graders
/data/harness-lab/runner-venv/bin/python -m pytest tests/ -q
/data/harness-lab/runner-venv/bin/python - <<'PY'
from runner.provision import load_tasks
from collections import Counter
from pathlib import Path
ts = load_tasks()
print(len(ts), dict(Counter(t["category"] for t in ts)),
      dict(Counter(t["tier"] for t in ts)), dict(Counter(t["source"] for t in ts)))
ids = [t["id"] for t in ts]
print([x for x, c in Counter(ids).items() if c > 1])
print([
    (t["id"], "hidden_tests", t["grader"]["hidden_tests"])
    for t in ts
    if not Path(t["grader"]["hidden_tests"]).exists()
])
PY
/data/harness-lab/runner-venv/bin/python -m runner pilot --dry-list
```

Observed before this audit fix:

```text
!! tests/fixtures/codex.smoke.log
!! tests/fixtures/opencode-gptmini.smoke.log
!! tests/fixtures/opencode-haiku.smoke.log
.......................................................                  [100%]
20 {'bug_fix': 4, 'rename': 4, 'add_tests': 4, 'add_logging': 4, 'benchmark': 4}
{2: 16, 1: 4}
{'controlled': 16, 'aider_polyglot': 4}
duplicates []
missing []
```

Pilot dry-list:

```text
config 1: bugfix-t2-01, rename-t2-01, bench-grade-school
config 6: bugfix-t2-01, rename-t2-01, bench-grade-school
```

## Gate

After committing this audit fix, the next allowed action is to ask the user for
explicit approval to start Task 16 Pilot. Do not run Task 16 automatically.
