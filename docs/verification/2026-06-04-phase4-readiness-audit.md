# Phase 4 readiness audit (2026-06-04)

Scope: verify whether committed Phase 0-3 artifacts are sufficient to enter
Phase 4 metrics/analysis without launching harnesses or spending model tokens.
The authoritative check was run on the VPS checkout
`/data/repos/xai-harness-faithfulness`.

## Conclusion

Phase 4 is ready to start from an artifact/data-integrity perspective.

The required Phase 4 inputs are present and internally consistent:

- Formal Phase 2 baseline traces: `traces/<config>/<task>/{1,2,3}.json`.
- Phase 3 attribution records: `analysis/phase3/attribution-results.json`.
- HCI ground-truth labels: `analysis/phase3/hci-ground-truth-labels.json`.
- Phase 4 analysis guardrails:
  `docs/specs/2026-06-04-phase4-analysis-guardrails.md`.
- HCI human-study plan:
  `docs/specs/2026-06-04-hci-human-study-plan.md`.

The HCI report must include at least a small participant study; xAI metrics,
screenshots, or dashboards alone are not sufficient HCI evidence.

Artifact boundary: the VPS/Mac private layer is the complete visible audit
trail, not a hidden-reasoning store. GitHub keeps the summarized/redacted public
layer only.

Repeat 0 Pilot traces and Phase 3 counterfactual repeats 301-312 and
401/403/404 exist, but are explicitly context-only and must not enter Phase 4
factorial baseline statistics.

## Gate command

```text
/data/harness-lab/runner-venv/bin/python -m runner phase4-ready --indent 0
```

Result summary:

```text
ok: true
formal_trace_count: 360
config_counts: c1=60, c2=60, c3=60, c4=60, c5=60, c6=60
task_count: 20
phase2_gate: ok, found_traces=360, expected_traces=360
phase3: selected_seed_count=12, hci_label_count=20
guardrails: present, missing_terms=0
hci_study_plan: present, missing_terms=0
label_distribution: harness_main_effect=6, interaction=8, model_main_effect=6
decision_kind_distribution: initial_tool_strategy=12, semantic_output_convention=3, task_success_gap=5
failures: []
```

Non-formal repeat warning is expected:

```text
repeat 0: 6 pilot traces
repeats 301-312: Phase 3 direct-file counterfactuals, two traces each
repeats 401, 403, 404: Phase 3 semantic convention counterfactuals, two traces each
```

## Fixes made during this audit

- Added `python -m runner phase4-ready` as a read-only Phase 4 readiness gate.
- Added tests for Phase 4 readiness and public hidden-reasoning hygiene.
- Added Phase 4 analysis guardrails for the final-report audience, XAI/HCI
  boundary, task-suite sampling, task difficulty, harness-affinity risk,
  benchmark-vs-controlled split, and robustness limits.
- Added the HCI human-study requirement: participants, task, comparison
  condition, HCI metrics, open-ended feedback, and voluntary/anonymized handling.
- Added a separate HCI human-study plan with target `n=6-10`, within-subject
  comparison conditions, required HCI metrics, and reporting boundaries.
- Replaced public Claude Code and Hermes smoke fixtures with minimal sanitized
  synthetic fixtures. They still exercise adapter parsing, but no longer commit
  raw thinking text, signature payloads, encrypted reasoning payloads, full raw
  logs, or raw prompt/tool dumps.

## Remaining interpretation boundaries

- Phase 2 baseline statistics must use formal repeats 1-3 only.
- Phase 3 repeats 301-312 and 401/403/404 are attribution/context evidence only.
- Phase 2 traces are chosen-tool-sequence evidence; they do not expose hidden
  alternatives or hidden rationale.
- M1/M2 are source/dossier-derived boundaries, not uniform direct runtime
  ablation across all harnesses.
- The final report audience is MIS graduate students and the instructor. Do not
  frame the conclusion as a general coding-agent benchmark or as an HCI user
  study; it is a bounded xAI/pipeline diagnosis with HCI interpretation.
- The final HCI report still needs a small human study before HCI claims can be
  presented as evaluated. Phase 0-3 artifacts are sufficient to design that
  study, but do not replace it.
