# Phase 5 XAI Presentation Data Pack

Scope: data, chart assets, source mapping, and slide-ready analysis for the XAI presentation only. No PPTX is generated here.

## Evidence Boundary

- Baseline statistics use only formal Phase 2 repeats 1-3.
- Pilot repeat 0 and Phase 3 counterfactual/extra repeats are case/method evidence, not baseline rates.
- HCI human-study claims are intentionally excluded; this pack only preserves material that can later feed the HCI phase.
- VPS authority: `/data/repos/xai-harness-faithfulness`; private/raw replay remains outside git under `/data/harness-lab/`.

## Headline Numbers

- Formal traces: 360 formal traces.
- Overall success: 295/360 (81.9%).
- Task suite: 20 tasks: 5 categories x 4.
- Public trace JSON inventory: 396 public trace JSON files; only 360 are formal baseline.
- Disagreement vs success-gap association: r=0.003 over 300 config-pair/task observations.
- Unanimous M1-M4 agreement: 10/20 (50.0%).

## Main Files

- Manifest: `analysis/phase5/xai-presentation-pack/manifest.json`
- Slide data map: `analysis/phase5/xai-presentation-pack/slide-data-map.json`
- Slide-ready compact JSON: `analysis/phase5/xai-presentation-pack/slide-ready-data.json`
- Table directory: `analysis/phase5/xai-presentation-pack/tables`
- Chart directory: `analysis/phase5/xai-presentation-pack/charts`

## Chart Menu

| Chart | Status | Use |
|---|---|---|
| `analysis/phase4/figures/jaccard-matrix.svg` | existing_phase4 | RQ3: how large the harness/model tool-set differences are. |
| `analysis/phase4/figures/factorial-contrast-bars.svg` | existing_phase4 | RQ3: descriptive contrast across harness/model/mixed comparisons. |
| `analysis/phase4/figures/disagreement-success-scatter.svg` | existing_phase4 | RQ2: sequence disagreement is almost unrelated to success gap here. |
| `analysis/phase4/figures/method-consistency.svg` | existing_phase4 | RQ1: M1-M4 agreement over selected high-divergence decision points. |
| `analysis/phase4/figures/agent-card-matrix.svg` | existing_phase4 | RQ4: condensed descriptive agent-card proxy dimensions. |
| `analysis/phase5/xai-presentation-pack/charts/attribution-action-map.svg` | generated_phase5_pack | Map XAI findings to prompt/tool-surface governance actions. |
| `analysis/phase5/xai-presentation-pack/charts/category-success-cost.svg` | generated_phase5_pack | Category success vs tool-call effort. |
| `analysis/phase5/xai-presentation-pack/charts/config-routing-grid.svg` | generated_phase5_pack | Harness x model routing grid: anchor vs crossed interaction cells. |
| `analysis/phase5/xai-presentation-pack/charts/config-success-bars.svg` | generated_phase5_pack | Topline config success comparison. |
| `analysis/phase5/xai-presentation-pack/charts/controlled-vs-benchmark.svg` | generated_phase5_pack | Controlled vs benchmark split. |
| `analysis/phase5/xai-presentation-pack/charts/environment-controls-matrix.svg` | generated_phase5_pack | Environment lock table as chart. |
| `analysis/phase5/xai-presentation-pack/charts/factorial-by-split.svg` | generated_phase5_pack | Contrast metrics separated by controlled/benchmark split. |
| `analysis/phase5/xai-presentation-pack/charts/first-tool-family-stacked-by-config.svg` | generated_phase5_pack | Harness first-action style comparison. |
| `analysis/phase5/xai-presentation-pack/charts/method-evidence-ladder.svg` | generated_phase5_pack | M1-M4 method evidence boundary. |
| `analysis/phase5/xai-presentation-pack/charts/phase3-label-summary.svg` | generated_phase5_pack | Attribution label and agreement distributions. |
| `analysis/phase5/xai-presentation-pack/charts/research-design-pipeline.svg` | generated_phase5_pack | Method pipeline overview. |
| `analysis/phase5/xai-presentation-pack/charts/task-difficulty-ranked.svg` | generated_phase5_pack | Task-level difficulty ranking. |
| `analysis/phase5/xai-presentation-pack/charts/task-success-heatmap.svg` | generated_phase5_pack | Task/config success matrix. |
| `analysis/phase5/xai-presentation-pack/charts/task-suite-composition.svg` | generated_phase5_pack | Task category/source composition. |
| `analysis/phase5/xai-presentation-pack/charts/trace-inventory.svg` | generated_phase5_pack | Evidence scale and baseline/nonbaseline boundary. |
| `analysis/phase5/xai-presentation-pack/charts/trace-schema-evidence.svg` | generated_phase5_pack | Normalized trace schema evidence model. |
| `analysis/phase5/xai-presentation-pack/charts/xai-case-card-01.svg` | generated_phase5_pack | Concrete case walkthrough candidate. |
| `analysis/phase5/xai-presentation-pack/charts/xai-case-card-02.svg` | generated_phase5_pack | Concrete case walkthrough candidate. |
| `analysis/phase5/xai-presentation-pack/charts/xai-case-card-03.svg` | generated_phase5_pack | Concrete case walkthrough candidate. |
| `analysis/phase5/xai-presentation-pack/charts/xai-case-card-04.svg` | generated_phase5_pack | Concrete case walkthrough candidate. |
| `analysis/phase5/xai-presentation-pack/charts/xai-case-card-05.svg` | generated_phase5_pack | Concrete case walkthrough candidate. |
| `analysis/phase5/xai-presentation-pack/charts/xai-case-card-06.svg` | generated_phase5_pack | Concrete case walkthrough candidate. |

## Slide Use

Use `slide-data-map.json` for the page-by-page mapping. It names the table(s), chart(s), source path, and caveat for each of the 24 planned slides.

## Do Not Mix Into XAI

- Human-study participant results.
- Trust calibration or perceived safety claims.
- Claims that Phase 3 selected labels estimate prevalence over all traces.
- Claims that the 20-task Python suite generalizes to all agentic coding work.
