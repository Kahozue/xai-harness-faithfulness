# Phase 1 pre-pilot documentation audit（2026-06-04）

本文件記錄 Task 11 決策後的文件一致性修正。它不是 Phase 1 最終 completion audit；
真實 Pilot 仍需使用者明確確認後才可開跑，因為會消耗 API token。

## Current implementation state

已完成並 commit：

| Task | Commit | Evidence |
|------|--------|----------|
| Task 11 task count rebalance | `ca5f1b6` | `tasks/registry.yaml` 定案五類各 4 題 |
| Task 12 Codex adapter | `34336ff` | `runner/adapters/codex.py` + `tests/test_adapter_codex.py` |
| Task 13 OpenCode adapter | `b36b21f` | `runner/adapters/opencode.py` + `tests/test_adapter_opencode.py` |
| Task 14 Hermes adapter | `9e9291d` | `runner/adapters/hermes.py` + `tests/test_adapter_hermes.py` |
| Task 15 runner orchestration | `f3617e1` | `runner/runner.py`、`persist.py`、CLI、mock runner tests |

尚未完成：

| Item | Status | Reason |
|------|--------|--------|
| Task 16 Pilot | Waiting for explicit user approval | Pilot runs real harnesses and spends API token |
| Task 17 final completion audit + push | Pending | Requires Pilot traces/report first |

## Task suite correction

Authoritative current task count:

```text
20 {'bug_fix': 4, 'rename': 4, 'add_tests': 4, 'add_logging': 4, 'benchmark': 4}
```

Task ids:

```text
bugfix-t2-01..04
rename-t2-01..04
addtests-t2-01..04
addlog-t2-01..04
bench-grade-school
bench-phone-number
bench-pig-latin
bench-bottle-song
```

This supersedes older plan text that said four categories x 5 tasks, bug_fix x5,
or SWE-bench Verified Tier-1 anchors.

## Methodology correction

SWE-bench Verified, docker, and qemu are not part of Phase 1 implementation.
They were abandoned because the aarch64 native path caused dependency drift and
oracle instability, and because SWE-bench primarily tests patch correctness
rather than the dependent variable here: harness-driven tool-selection sequence
divergence.

Benchmark tasks now come from Aider-polyglot Python/Exercism:

```text
grade-school
phone-number
pig-latin
bottle-song
```

## Files corrected in this pass

| File | Correction |
|------|------------|
| `README.md` | Updated task summary from four categories to five categories x 4 tasks |
| `docs/specs/2026-06-03-xai-harness-faithfulness-design.md` | Updated §6.1, risk, and related-work wording to Aider-polyglot benchmark + controlled Tier-2 |
| `docs/plans/2026-06-04-phase1-task-suite-runner-trace-pilot.md` | Added implementation amendment; corrected task count, Task 16/17 numbering, pilot sample, and superseded SWE-bench Task 9 block |

## Verification run before committing this audit

```bash
cd /data/repos/xai-harness-faithfulness
/data/harness-lab/runner-venv/bin/python -c "from runner.provision import load_tasks; from collections import Counter; ts=load_tasks(); print(len(ts), dict(Counter(t['category'] for t in ts)))"
/data/harness-lab/runner-venv/bin/python -m pytest tests/ -q
rg -n "bug_fix=5|bug_fix = 5|bug_fix=1|rename=5|add_tests=5|add_logging=5|四類各 5|4 類 ×5|tasks/tier1|runner/swebench|tests/test_swebench_select|bugfix-t2-05" README.md docs tasks runner tests --glob '!docs/verification/2026-06-04-phase1-pre-pilot-doc-audit.md'
```

Expected: task count is five categories x 4; pytest is green; grep has no
actionable stale implementation instruction. Mentions of SWE-bench are allowed
only as abandoned route / related-work context.

Observed on 2026-06-04:

```text
20 {'bug_fix': 4, 'rename': 4, 'add_tests': 4, 'add_logging': 4, 'benchmark': 4}
.......................................................                  [100%]
```

The targeted stale-text scan returned no output after excluding this audit file.
