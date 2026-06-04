# Phase 4 metrics and analysis report (2026-06-04)

Scope: Phase 4 analyzes formal Phase 2 repeats 1-3 and Phase 3 attribution/HCI-label artifacts on the VPS checkout `/data/repos/xai-harness-faithfulness`.

## Evidence boundary

- Baseline statistics use only `traces/<config>/<task>/{1,2,3}.json`.
- Pilot repeat 0 and Phase 3 counterfactual repeats 301-312 / 401 / 403 / 404 are excluded from baseline statistics.
- The VPS private/raw layer remains the complete replay record; public committed traces are sanitized summaries.
- HCI human-study claims are not made here. These metrics provide evidence cases and presentation material for the HCI study.

## Generated artifacts

- Metrics JSON: `analysis/phase4/metrics-summary.json`.
- HCI case pack: `analysis/phase4/hci-case-pack.json`.
- Teacher/requirements traceability: `analysis/phase4/teacher-requirements-traceability.json`.
- Jaccard matrix: `analysis/phase4/figures/jaccard-matrix.svg`.
- Disagreement vs success-gap scatter: `analysis/phase4/figures/disagreement-success-scatter.svg`.
- Factorial contrast bars: `analysis/phase4/figures/factorial-contrast-bars.svg`.
- Method-consistency matrix: `analysis/phase4/figures/method-consistency.svg`.
- Agent-card matrix: `analysis/phase4/figures/agent-card-matrix.svg`.

## Topline

- Formal traces analyzed: 360 across 6 configs x 20 tasks x repeats [1, 2, 3].
- Overall success: 295/360 (0.819).
- Mean tool calls per trace: 8.764; mean wall time: 29.328s.
- Sequence-disagreement vs success-gap Pearson r: 0.003 over 300 config-pair/task observations.
- Sequence-disagreement vs mean failure-rate Pearson r: -0.005.
- Phase 3 HCI labels: 20; unanimous M1-M4 agreement: 10/20 (0.500).

## Config summary

| Config | Harness | Model | Success | Tool calls | Wall time | Stability |
| --- | --- | --- | --- | --- | --- | --- |
| c1 | claude_code | haiku | 0.800 (60 runs) | 8.383 | 29.183 | 0.781 |
| c2 | opencode | haiku | 0.800 (60 runs) | 10.183 | 30.202 | 0.799 |
| c3 | hermes | haiku | 0.833 (60 runs) | 7.317 | 24.364 | 0.817 |
| c4 | opencode | gptmini | 0.850 (60 runs) | 10.067 | 33.809 | 0.786 |
| c5 | hermes | gptmini | 0.767 (60 runs) | 7.533 | 37.504 | 0.857 |
| c6 | codex | gptmini | 0.867 (60 runs) | 9.100 | 20.907 | 0.896 |

## Controlled vs benchmark split

| Split | Categories | n | Success | Mean tool calls |
| --- | --- | --- | --- | --- |
| controlled | add_logging, add_tests, bug_fix, rename | 288 | 267/288 (0.927) | 8.299 |
| benchmark | benchmark | 72 | 28/72 (0.389) | 10.625 |

## Category summary

| Category | Tasks | n | Success | Mean tools | Mean wall time |
| --- | --- | --- | --- | --- | --- |
| add_logging | 4 | 72 | 72/72 (1.000) | 4.667 | 16.174 |
| add_tests | 4 | 72 | 68/72 (0.944) | 6.806 | 20.176 |
| benchmark | 4 | 72 | 28/72 (0.389) | 10.625 | 53.460 |
| bug_fix | 4 | 72 | 55/72 (0.764) | 6.083 | 20.544 |
| rename | 4 | 72 | 72/72 (1.000) | 15.639 | 36.287 |

## Factorial contrast summary

The 6-cell matrix is partly anchored: Claude Code appears only with Haiku, and Codex appears only with GPT-mini. Causal interaction summaries therefore use the crossed OpenCode/Hermes cells only.

| Contrast | n | Jaccard | Seq disagreement | Success gap | Failure rate |
| --- | --- | --- | --- | --- | --- |
| harness_same_model | 120 | 0.667 | 0.439 | 0.056 | 0.181 |
| mixed_harness_model | 140 | 0.606 | 0.533 | 0.067 | 0.179 |
| model_swap_same_harness | 40 | 0.746 | 0.420 | 0.092 | 0.188 |

## Phase 3 method consistency

- Factorial labels: {'harness_main_effect': 6, 'interaction': 8, 'model_main_effect': 6}.
- Decision kinds: {'initial_tool_strategy': 12, 'semantic_output_convention': 3, 'task_success_gap': 5}.
- Confidence: {'high': 15, 'medium': 5}.
- Agreement counts: {'2': 5, '3': 5, '4': 10}.

## Agent-card matrix

Dimension definitions are descriptive proxies for this controlled Python suite: fidelity=success rate, stability=repeat sequence similarity, robustness=minimum category success rate, actionability=trace evidence completeness, governability=failed-run diagnosability or trace governance coverage.

| Config | fidelity | stability | robustness | actionability | governability |
| --- | --- | --- | --- | --- | --- |
| c1 | 0.800 | 0.781 | 0.250 | 1.000 | 1.000 |
| c2 | 0.800 | 0.799 | 0.250 | 1.000 | 1.000 |
| c3 | 0.833 | 0.817 | 0.417 | 1.000 | 1.000 |
| c4 | 0.850 | 0.786 | 0.667 | 1.000 | 1.000 |
| c5 | 0.767 | 0.857 | 0.250 | 1.000 | 1.000 |
| c6 | 0.867 | 0.896 | 0.500 | 1.000 | 1.000 |

## Reporting limitations

- The task suite is 20 controlled Python tasks, not a random sample of all coding-agent work.
- Benchmark tasks should be interpreted separately from controlled software-engineering tasks.
- Robustness across languages, frameworks, large repositories, and long-horizon production work is not covered.
- Phase 3 labels are selected high-divergence decision points; they are not a prevalence estimate over all Phase 2 traces.
- HCI conclusions require the separate human study described in `docs/specs/2026-06-04-hci-human-study-plan.md`.
