# Phase 5 canonical consistency audit (2026-06-05)

Scope: verify that the 27-slide xAI presentation basis is internally complete
and that its referenced data, chart, source, screenshot, and boundary documents
exist after the old 24-slide HTML deck was discarded.

## Canonical basis

- Canonical slide draft:
  `analysis/phase5/xai-presentation-pack/deck/content-draft.md`.
- Canonical data map:
  `analysis/phase5/xai-presentation-pack/slide-data-map.json`.
- Canonical structure spec:
  `docs/specs/2026-06-04-phase5-xai-presentation-structure.md`.
- Deprecated deck:
  `analysis/phase5/xai-presentation-pack/deck/index.html` is intentionally
  absent and must not be used as a PPT source.

## Audit findings

- The data pack manifest and slide map paths resolve.
- `slide-data-map.json` contains 27 slides.
- Slide 22 uses the intended concrete XAI case:
  `XAI-C03 / bugfix-t2-03 / OpenCode vs Hermes` with
  `analysis/phase5/xai-presentation-pack/charts/xai-case-card-03.svg`.
- The old 24-slide `deck/index.html` file is absent.
- The screenshot README previously referenced the old execution-reality slide
  number; it now points to slide 15.
- The source index was incomplete for the 27-slide document logic. It now lists
  the canonical draft, manifest, slide map, screenshots README, trace policy,
  Phase 2 isolation/reset evidence, Phase 3 seed/attribution evidence, Phase 4
  guardrails, harness dossiers, runner trace schema, and the generator itself.

## Boundary checks

- Faithfulness remains defined as observable attribution support from visible
  trace, prompt/tool surface, source/dossier evidence, and counterfactual reruns.
  Hidden chain-of-thought is not exposed or claimed.
- M1/M2 remain source/dossier/tool-surface evidence, not uniform runtime
  ablations across all harnesses.
- Model contrasts remain model+provider-route contrasts.
- Agent-card actionability/governability remain coverage gates in the current
  data pack, not discriminative capability rankings.
- HCI human-study claims remain deferred.

## Verification commands

Mac checkout:

```bash
XAI_REPO=$PWD python -m runner phase5-xai-pack --indent 0
XAI_REPO=$PWD node <slide-map-path-check>
git diff --check
```

VPS checkout:

```bash
cd /data/repos/xai-harness-faithfulness
/data/harness-lab/runner-venv/bin/python -m pytest \
  tests/test_phase5_xai_pack.py \
  tests/test_phase4_analysis.py \
  tests/test_phase4_readiness.py -q
/data/harness-lab/runner-venv/bin/python -m runner phase5-xai-pack --indent 0
```

## Result

The canonical presentation package is complete when:

- Mac, VPS, and GitHub point to the same commit.
- The slide map has 27 slides.
- Every slide-map table/chart path resolves.
- The source index includes the expanded canonical evidence list.
- `deck/index.html` remains absent.
