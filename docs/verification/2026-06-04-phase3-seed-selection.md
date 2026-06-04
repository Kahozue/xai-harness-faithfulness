# Phase 3 decision-point seed selection (2026-06-04)

Scope: select auditable high-divergence Phase 2 chosen-tool sequence pairs for Phase 3 M1-M4 white-box attribution.

## Method

- Source traces: formal Phase 2 repeats [1, 2, 3] only.
- Candidate count: 160; selected seeds: 12.
- Score: `selection_score = sequence_divergence + 0.25 * success_gap`.
- `sequence_divergence` is the mean pairwise blend of tool-family Jaccard disagreement and normalized edit distance across the 3x3 repeat pairs.
- Tool names are canonicalized into families (`read`, `search`, `edit`, `shell`, `plan`) so harness vocabulary differences do not dominate the score.

## Selected seeds

| Seed | Stratum | Task | Pair | Score | Seq div | Success gap | First-tool signal |
|---|---|---|---|---:|---:|---:|---|
| PH3-DP-001 | haiku_same_model_harness | bugfix-t2-03 | c2-c3 | 0.641 | 0.641 | 0.000 | c2 {'read': 2, 'shell': 1} vs c3 {'read': 3}; success 0/3 vs 0/3 |
| PH3-DP-002 | haiku_same_model_harness | addtests-t2-04 | c2-c3 | 0.626 | 0.626 | 0.000 | c2 {'read': 3} vs c3 {'read': 3}; success 3/3 vs 3/3 |
| PH3-DP-003 | haiku_same_model_harness | bugfix-t2-03 | c1-c2 | 0.581 | 0.581 | 0.000 | c1 {'read': 2, 'shell': 1} vs c2 {'read': 2, 'shell': 1}; success 0/3 vs 0/3 |
| PH3-DP-004 | gptmini_same_model_harness | bugfix-t2-03 | c5-c6 | 0.928 | 0.845 | 0.333 | c5 {'search': 3} vs c6 {'shell': 3}; success 0/3 vs 1/3 |
| PH3-DP-005 | gptmini_same_model_harness | addlog-t2-03 | c5-c6 | 0.875 | 0.875 | 0.000 | c5 {'search': 3} vs c6 {'shell': 3}; success 3/3 vs 3/3 |
| PH3-DP-006 | gptmini_same_model_harness | addlog-t2-04 | c4-c6 | 0.875 | 0.875 | 0.000 | c4 {'search': 3} vs c6 {'shell': 3}; success 3/3 vs 3/3 |
| PH3-DP-007 | opencode_model_swap | bench-bottle-song | c2-c4 | 0.774 | 0.607 | 0.667 | c2 {'read': 1, 'shell': 2} vs c4 {'plan': 2, 'search': 1}; success 1/3 vs 3/3 |
| PH3-DP-008 | opencode_model_swap | bench-pig-latin | c2-c4 | 0.655 | 0.572 | 0.333 | c2 {'read': 1, 'shell': 2} vs c4 {'search': 3}; success 2/3 vs 3/3 |
| PH3-DP-009 | opencode_model_swap | bench-grade-school | c2-c4 | 0.618 | 0.534 | 0.333 | c2 {'read': 2, 'shell': 1} vs c4 {'plan': 1, 'search': 2}; success 0/3 vs 1/3 |
| PH3-DP-010 | hermes_model_swap | bugfix-t2-04 | c3-c5 | 0.630 | 0.630 | 0.000 | c3 {'read': 3} vs c5 {'search': 3}; success 3/3 vs 3/3 |
| PH3-DP-011 | hermes_model_swap | addtests-t2-02 | c3-c5 | 0.582 | 0.416 | 0.667 | c3 {'read': 3} vs c5 {'search': 3}; success 3/3 vs 1/3 |
| PH3-DP-012 | hermes_model_swap | addlog-t2-01 | c3-c5 | 0.570 | 0.570 | 0.000 | c3 {'read': 3} vs c5 {'search': 3}; success 3/3 vs 3/3 |

## Phase 3 usage

Use these seeds as the initial M1-M4 queue. For each seed, Phase 3 should inspect the referenced private audit/raw traces, define the concrete observable decision point, then attach the relevant M1/M2 source-derived prompt/tool-surface evidence, run direct M3 task counterfactuals where needed, and compare M4 planning-trace visibility.

Boundary: Phase 2 traces have `decision_points=[]`; this file does not invent hidden alternatives. It records chosen-tool divergence seeds that Phase 3 must validate through source/dossier evidence, direct counterfactual traces, and white-box trace review.

