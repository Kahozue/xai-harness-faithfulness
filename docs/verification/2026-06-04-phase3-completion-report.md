# Phase 3 completion report (2026-06-04)

Scope: M1-M4 white-box attribution over the selected high-divergence Phase 2 decision-point seeds.

## Artifact summary

- Selected seeds: 12.
- Decision points / HCI labels: 20.
- M3 direct-file counterfactual repeats: 301-312.
- M3 semantic currency-convention repeats: 401, 403, 404.
- Raw private audits remain outside git under `/data/harness-lab/private-audits/`.

## Requirement audit

| Requirement | Evidence | Status |
|---|---|---|
| Divergent decision-point subset selected before attribution | `analysis/phase3/decision-point-seeds.json` ranks 160 candidates and selects 12 seeds across same-model harness and same-harness model-swap strata | done |
| M1 system-prompt attribution | Each decision point has an M1 record derived from harness dossier/source/trace prompt visibility; direct runtime prompt ablation is not claimed because patchability differs across closed/native harnesses | done with source-derived boundary |
| M2 tool-definition attribution | Each decision point has an M2 record derived from observed tool surfaces, CLI affordances, and dossier/source tool-registry evidence; direct uniform tool-schema perturbation is not claimed | done with source-derived boundary |
| M3 behavior counterfactuals | Direct counterfactual traces exist for repeat 301-312 and semantic repeats 401/403/404; traces are committed and private audits remain outside git | done |
| M4 planning-loop/trace evidence | Each decision point has M4 trace visibility evidence from baseline and counterfactual traces, with hidden chain-of-thought omitted by policy | done |
| HCI ground-truth labels | `analysis/phase3/hci-ground-truth-labels.json` contains exactly 20 labels with method agreement, contrast metadata, confidence, and evidence boundaries | done |

## Method boundary

- M1: source/dossier prompt-layer evidence; direct prompt patchability differs by harness.
- M2: source/dossier/tool-surface evidence; direct tool-definition patchability differs by harness.
- M3: executed counterfactual runs in repeat ranges 301-312 and 401/403/404.
- M4: trace/planning-loop visibility evidence from public traces and private audits; hidden chain-of-thought omitted.

## Method evidence distribution

| Method | Evidence level | Decision records |
|---|---|---:|
| M1 | `source-derived` | 20 |
| M2 | `source-derived` | 20 |
| M3 | `direct-run` | 20 |
| M4 | `direct` | 20 |

## HCI label distribution

| Label | Count |
|---|---:|
| `harness_main_effect` | 6 |
| `interaction` | 8 |
| `model_main_effect` | 6 |

| Decision kind | Count |
|---|---:|
| `initial_tool_strategy` | 12 |
| `semantic_output_convention` | 3 |
| `task_success_gap` | 5 |

## Seed-level summary

| Seed | Task | Pair | Decision labels |
|---|---|---|---|
| PH3-DP-001 | bugfix-t2-03 | c2-c3 | initial_tool_strategy=harness_main_effect, semantic_output_convention=interaction |
| PH3-DP-002 | addtests-t2-04 | c2-c3 | initial_tool_strategy=harness_main_effect |
| PH3-DP-003 | bugfix-t2-03 | c1-c2 | initial_tool_strategy=harness_main_effect, semantic_output_convention=interaction |
| PH3-DP-004 | bugfix-t2-03 | c5-c6 | initial_tool_strategy=harness_main_effect, semantic_output_convention=interaction, task_success_gap=interaction |
| PH3-DP-005 | addlog-t2-03 | c5-c6 | initial_tool_strategy=harness_main_effect |
| PH3-DP-006 | addlog-t2-04 | c4-c6 | initial_tool_strategy=harness_main_effect |
| PH3-DP-007 | bench-bottle-song | c2-c4 | initial_tool_strategy=model_main_effect, task_success_gap=interaction |
| PH3-DP-008 | bench-pig-latin | c2-c4 | initial_tool_strategy=model_main_effect, task_success_gap=interaction |
| PH3-DP-009 | bench-grade-school | c2-c4 | initial_tool_strategy=model_main_effect, task_success_gap=interaction |
| PH3-DP-010 | bugfix-t2-04 | c3-c5 | initial_tool_strategy=model_main_effect |
| PH3-DP-011 | addtests-t2-02 | c3-c5 | initial_tool_strategy=model_main_effect, task_success_gap=interaction |
| PH3-DP-012 | addlog-t2-01 | c3-c5 | initial_tool_strategy=model_main_effect |

## Phase 3 conclusion

Phase 3 now has auditable M1-M4 evidence records for the selected divergent decision-point subset. Tool-path style differences are primarily explained by harness/tool-surface effects in same-model strata and model effects in same-harness model-swap strata. M3 counterfactuals show that direct target-file disclosure often reduces search overhead and sometimes closes success gaps, while the `bugfix-t2-03` failures required a separate semantic convention counterfactual. Those cases are labeled as interaction rather than pure harness or model main effects.

The committed HCI interface is `analysis/phase3/hci-ground-truth-labels.json`. It contains exactly 20 contrastive labels derived from the selected Phase 3 seeds and should be used instead of raw private audits.

