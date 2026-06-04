# Phase 5 XAI data-pack report (2026-06-04)

Scope: prepare slide-ready XAI data, charts, and source mappings before building
the PPT. This step intentionally did not create or modify any `.pptx` file.

## Output

Primary pack:
`analysis/phase5/xai-presentation-pack/`

Key files:

- `analysis/phase5/xai-presentation-pack/README.md`
- `analysis/phase5/xai-presentation-pack/manifest.json`
- `analysis/phase5/xai-presentation-pack/slide-data-map.json`
- `analysis/phase5/xai-presentation-pack/slide-ready-data.json`
- `analysis/phase5/xai-presentation-pack/tables/chart-manifest.csv`

Generated content:

- 25 CSV tables under `analysis/phase5/xai-presentation-pack/tables/`.
- 20 new SVG charts under `analysis/phase5/xai-presentation-pack/charts/`.
- 5 existing Phase 4 SVG charts are referenced in the manifest and chart
  manifest rather than copied.
- 24-slide data map aligned with
  `docs/specs/2026-06-04-phase5-xai-presentation-structure.md`.

## Headline numbers prepared for slides

- Formal baseline traces: 360 = 6 configs x 20 tasks x 3 repeats.
- Public trace JSON inventory: 396 total; only 360 are formal baseline.
- Non-baseline context traces: 6 pilot traces and 30 Phase 3
  counterfactual/extra traces.
- Overall success: 295/360 = 0.819.
- Controlled split: 267/288 = 0.927.
- Benchmark split: 28/72 = 0.389.
- Disagreement vs success-gap Pearson r: 0.003 over 300 config-pair/task
  observations.
- Phase 3 M1-M4 unanimous agreement: 10/20 = 0.500.

## Boundary

- Baseline statistics use only `traces/<config>/<task>/{1,2,3}.json`.
- Pilot repeat `0` and Phase 3 counterfactual/extra repeats
  `301-312/401/403/404` are case or method evidence, not baseline rates.
- HCI human-study claims are excluded from this XAI data pack. No clarity,
  trust calibration, perceived safety, cognitive-load, or participant-response
  claims should be made from these files.
- Case cards are XAI walkthrough examples selected from high-divergence Phase 3
  labels; they are not prevalence estimates over all tasks.

## Verification on VPS

All verification ran in `/data/repos/xai-harness-faithfulness` using
`/data/harness-lab/runner-venv/bin/python`.

Commands:

```bash
/data/harness-lab/runner-venv/bin/python -m pytest \
  tests/test_phase5_xai_pack.py \
  tests/test_phase4_analysis.py \
  tests/test_phase4_readiness.py -q

/data/harness-lab/runner-venv/bin/python -m runner phase5-xai-pack --indent 2
```

Verification result:

- Related tests passed: 8/8.
- `manifest.json` reports `pptx_created=false`.
- 25 generated CSV tables are non-empty.
- 20 generated SVG charts parse as valid XML.
- No `.pptx` exists under `analysis/phase5/xai-presentation-pack/`.

