# Phase 4 report support pack (2026-06-04)

Purpose: collect the fine-grained Phase 4 outputs needed to answer HCI/XAI report requirements, teacher review points, and peer feedback without relying on hidden GitHub-only views.

## Boundary

- Authority: VPS checkout `/data/repos/xai-harness-faithfulness` plus `/data/harness-lab` raw/private artifacts.
- Public artifacts are sanitized summaries and generated analysis outputs.
- Human-study materials are prepared here; actual HCI claims still require human responses.

## Environment control evidence

| Config | Harness | Model | Provider | Versions | Runtime budget variants | Raw/private refs |
| --- | --- | --- | --- | --- | --- | --- |
| c1 | claude_code | haiku | anthropic | 2.1.88 | {'context_window_tokens': 200000, 'effort_source': 'cli --effort high + env budgets', 'max_output_tokens': 64000, 'thinking_budget_tokens': 63999} x60 | raw 60/60; private 60/60 |
| c2 | opencode | haiku | anthropic | 1.15.13 | {'context_window_tokens': None, 'effort_source': 'opencode run --variant high', 'max_output_tokens': None, 'thinking_budget_tokens': None} x60 | raw 60/60; private 60/60 |
| c3 | hermes | haiku | anthropic | 0.13.0 | {'context_window_tokens': None, 'effort_source': 'hermes -z -m MODEL --provider PROVIDER --yolo; no explicit effort flag', 'max_output_tokens': None, 'thinking_budget_tokens': None} x60 | raw 60/60; private 60/60 |
| c4 | opencode | gptmini | openai | 1.15.13 | {'context_window_tokens': None, 'effort_source': 'opencode run --variant high', 'max_output_tokens': None, 'thinking_budget_tokens': None} x60 | raw 60/60; private 60/60 |
| c5 | hermes | gptmini | openai | 0.13.0 | {'context_window_tokens': None, 'effort_source': 'hermes -z -m MODEL --provider PROVIDER --yolo; no explicit effort flag', 'max_output_tokens': None, 'thinking_budget_tokens': None} x60 | raw 60/60; private 60/60 |
| c6 | codex | gptmini | openai | 0.136.0 | {'context_window_tokens': 258400, 'effort_source': '$LAB_HOME/.codex/config.toml reasoning_effort=high', 'max_output_tokens': None, 'thinking_budget_tokens': None} x60 | raw 60/60; private 60/60 |

## Task-level evidence table

| Task | Category | Source | Success | Mean tools | Config stdev |
| --- | --- | --- | --- | --- | --- |
| addlog-t2-01 | add_logging | controlled | 18/18 (1.000) | 4.500 | 0.000 |
| addlog-t2-02 | add_logging | controlled | 18/18 (1.000) | 5.000 | 0.000 |
| addlog-t2-03 | add_logging | controlled | 18/18 (1.000) | 4.500 | 0.000 |
| addlog-t2-04 | add_logging | controlled | 18/18 (1.000) | 4.667 | 0.000 |
| addtests-t2-01 | add_tests | controlled | 18/18 (1.000) | 6.778 | 0.000 |
| addtests-t2-02 | add_tests | controlled | 14/18 (0.778) | 7.000 | 0.314 |
| addtests-t2-03 | add_tests | controlled | 18/18 (1.000) | 6.778 | 0.000 |
| addtests-t2-04 | add_tests | controlled | 18/18 (1.000) | 6.667 | 0.000 |
| bench-bottle-song | benchmark | aider_polyglot | 11/18 (0.611) | 14.167 | 0.299 |
| bench-grade-school | benchmark | aider_polyglot | 2/18 (0.111) | 8.611 | 0.157 |
| bench-phone-number | benchmark | aider_polyglot | 1/18 (0.056) | 10.944 | 0.124 |
| bench-pig-latin | benchmark | aider_polyglot | 14/18 (0.778) | 8.778 | 0.157 |
| bugfix-t2-01 | bug_fix | controlled | 18/18 (1.000) | 7.389 | 0.000 |
| bugfix-t2-02 | bug_fix | controlled | 18/18 (1.000) | 4.944 | 0.000 |
| bugfix-t2-03 | bug_fix | controlled | 1/18 (0.056) | 6.278 | 0.124 |
| bugfix-t2-04 | bug_fix | controlled | 18/18 (1.000) | 5.722 | 0.000 |
| rename-t2-01 | rename | controlled | 18/18 (1.000) | 17.111 | 0.000 |
| rename-t2-02 | rename | controlled | 18/18 (1.000) | 15.167 | 0.000 |
| rename-t2-03 | rename | controlled | 18/18 (1.000) | 14.944 | 0.000 |
| rename-t2-04 | rename | controlled | 18/18 (1.000) | 15.333 | 0.000 |

## HCI case pack

Coverage: {'case_count': 6, 'factorial_labels': {'harness_main_effect': 2, 'interaction': 3, 'model_main_effect': 1}, 'decision_kinds': {'initial_tool_strategy': 3, 'semantic_output_convention': 1, 'task_success_gap': 2}, 'task_categories': {'add_logging': 1, 'add_tests': 2, 'benchmark': 2, 'bug_fix': 1}, 'required_plan_coverage': {'harness_main_effect_initial_tool_strategy': True, 'model_main_effect_initial_tool_strategy': True, 'interaction_or_semantic_case': True, 'task_success_gap_case': True}}.

| Case | Label | Task | Attribution | Decision | Coverage role |
| --- | --- | --- | --- | --- | --- |
| HCI-PH4-01 | PH3-DP-002-A-initial-strategy | addtests-t2-04 | harness_main_effect | initial_tool_strategy | harness |
| HCI-PH4-02 | PH3-DP-007-A-initial-strategy | bench-bottle-song | model_main_effect | initial_tool_strategy | model |
| HCI-PH4-03 | PH3-DP-001-B-currency-convention | bugfix-t2-03 | interaction | semantic_output_convention | interaction, semantic |
| HCI-PH4-04 | PH3-DP-011-C-success-gap | addtests-t2-02 | interaction | task_success_gap | interaction, success-gap |
| HCI-PH4-05 | PH3-DP-007-C-success-gap | bench-bottle-song | interaction | task_success_gap | interaction, success-gap |
| HCI-PH4-06 | PH3-DP-005-A-initial-strategy | addlog-t2-03 | harness_main_effect | initial_tool_strategy | harness |

## Teacher / requirement traceability

| Requirement | Status | Artifacts |
| --- | --- | --- |
| Explain research question, method, task sampling, environment controls, results, limitations, and implications for MIS classroom review. | covered_by_phase4_artifacts | docs/verification/2026-06-04-phase4-analysis-report.md, docs/verification/2026-06-04-phase4-report-support-pack.md, analysis/phase4/metrics-summary.json |
| Keep XAI findings separate from HCI evaluation; do not present xAI metrics alone as HCI evaluation. | covered_with_boundary_note | docs/verification/2026-06-04-phase4-analysis-report.md, analysis/phase4/hci-case-pack.json |
| Required HCI human study with participants, two presentation styles, clarity/trust/verification/safety/load metrics, qualitative feedback, and ethics. | materials_prepared_human_responses_still_required | analysis/phase4/hci-case-pack.json, docs/verification/2026-06-04-phase4-report-support-pack.md |
| Fixed test environment, versions, model snapshots, provider route, reasoning effort, token/thinking/context-window settings, raw logs outside git. | covered_by_vps_gate_and_trace_fields | analysis/phase4/metrics-summary.json, ENVIRONMENT.lock.md |
| Use charts/tables/process evidence rather than long prose only. | covered_with_generated_figures | analysis/phase4/figures/jaccard-matrix.svg, analysis/phase4/figures/disagreement-success-scatter.svg, analysis/phase4/figures/factorial-contrast-bars.svg, analysis/phase4/figures/method-consistency.svg, analysis/phase4/figures/agent-card-matrix.svg, docs/verification/2026-06-04-phase4-report-support-pack.md |
| Non-overclaim: current data support only this controlled 20-task suite. | covered_with_limitations | docs/verification/2026-06-04-phase4-analysis-report.md, docs/verification/2026-06-04-phase4-report-support-pack.md |
| Analyze benchmark tasks separately from controlled software-engineering tasks. | covered_with_split_tables | analysis/phase4/metrics-summary.json, docs/verification/2026-06-04-phase4-analysis-report.md |
| Task sampling, difficulty calibration, harness-affinity bias, and robustness gaps must be explicit. | covered_with_limitations_and_task_metadata | docs/verification/2026-06-04-phase4-analysis-report.md, docs/verification/2026-06-04-phase4-report-support-pack.md |
| Provide concrete cases so peers can understand risks and evidence dependencies. | covered_with_case_pack | analysis/phase4/hci-case-pack.json, docs/verification/2026-06-04-phase4-report-support-pack.md |
| Agent-card matrix across fidelity, stability, robustness, actionability, governability. | covered_as_descriptive_proxy | analysis/phase4/metrics-summary.json, analysis/phase4/figures/agent-card-matrix.svg |

## 15-slide support outline

| Slide | Title | Supports |
| --- | --- | --- |
| 1 | Research question and classroom framing | phase4 guardrails audience framing, source.data_boundary |
| 2 | Method overview before results | formal repeats 1-3, task suite 5 categories x 4 tasks, VPS environment controls |
| 3 | Fixed environment and trace evidence chain | environment_controls, ENVIRONMENT.lock.md, readiness.phase2_gate |
| 4 | Task sampling and difficulty calibration | category_summaries, task_summaries, hidden grader boundary |
| 5 | Overall success and tool-use overview | overall, config summary table |
| 6 | Controlled vs benchmark split | overall.task_splits, category_summaries |
| 7 | Tool-family Jaccard matrix | figures.jaccard_matrix, pairwise.by_config_pair |
| 8 | Disagreement and success-gap relationship | figures.disagreement_success_scatter, success_association |
| 9 | Factorial decomposition with anchor-cell boundary | factorial_decomposition, figures.factorial_contrast_bars |
| 10 | Phase 3 attribution and M1-M4 consistency | phase3_method_consistency, figures.method_consistency |
| 11 | Concrete HCI case examples | HCI-PH4-01, HCI-PH4-02 |
| 12 | HCI study design | hci_case_pack.procedure_support, measurement_items |
| 13 | Agent-card governance matrix | agent_cards, figures.agent_card_matrix |
| 14 | Limitations and non-overclaim | Python-only suite, benchmark split, Phase 3 selected-case boundary |
| 15 | Implications and next steps | HCI human response collection, cross-language robustness future work |

## Human-study measurement items

| Metric | Item | Scale |
| --- | --- | --- |
| clarity | I can explain what differed between the two agent runs. | 1-5 Likert |
| trust_calibration | My trust in the agent result matches the evidence and limitations shown. | 1-5 Likert |
| verification_intention_or_action_choice | What would you do next? | choice: accept / inspect evidence / rerun / ask for more information / reject |
| perceived_safety_control | I feel able to catch or recover from an agent mistake in this case. | 1-5 Likert |
| cognitive_load_effort | This presentation was understandable without excessive effort. | 1-5 Likert |
| qualitative_feedback | What evidence helped, what was confusing, and what would change your decision? | open text |

## Use in final reporting

- Use `analysis/phase4/metrics-summary.json` for numeric auditability.
- Use `analysis/phase4/hci-case-pack.json` for HCI condition A/B material generation.
- Use `analysis/phase4/teacher-requirements-traceability.json` as the checklist for teacher requirements.
- Use generated SVGs directly in slides or as report figures.
