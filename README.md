# xai-harness-faithfulness

**Faithfulness of the Harness: Attributing Tool-Selection Divergence in LLM Agents**

Course proposal and experiment repository for an xAI study comparing how much of the behavioral difference between AI coding agents (Claude Code, Codex CLI, OpenCode, Hermes) comes from the harness design versus the underlying model.

## Research Question

When two AI agents produce different tool sequences on the same task, how much of that divergence is explained by harness design (system prompt, tool definitions, skill invocation logic, memory) versus the model itself — and how much is interaction or noise?

## Design

**2 × 3 partial factorial across harness × model:**

| | Claude Code | OpenCode | Hermes | Codex CLI |
|-|:-----------:|:--------:|:------:|:---------:|
| Haiku 4.5 | anchor | ✓ | ✓ | — |
| GPT-5.4-mini | — | ✓ | ✓ | anchor |

6 configs × 20 agentic tasks, balanced as 5 categories × 4 tasks:
bug fix / rename / add tests / add logging / benchmark.

**4 xAI attribution methods (white-box):**
- M1: System prompt attribution — source/dossier prompt-layer evidence; direct runtime ablation is recorded only where harness patchability supports it.
- M2: Tool definition and affordance attribution — source/dossier/tool-surface evidence; direct uniform tool-schema perturbation is not claimed across closed/native harnesses.
- M3: Behavioral counterfactual swap — rewrite task input and execute counterfactual traces.
- M4: Planning-loop trace — compare public trace visibility and private audit evidence while omitting hidden chain-of-thought.

**Metrics:** Jaccard similarity, disagreement rate, success correlation, five-dimension agent-card matrix (fidelity / stability / robustness / actionability / governability).

## Trace Recording Policy

GitHub stores only summary/public artifacts: normalized traces under `traces/`
and verification reports under `docs/verification/`. Full plaintext audit
records, including visible model messages, tool inputs/outputs, errors, and
recoveries, are stored outside git on the VPS under
`/data/harness-lab/private-audits/` and may be mirrored locally under
`private-audits/` on the Mac.

Do not commit raw harness logs, full private audits, secrets, or raw hidden
chain-of-thought. See
`docs/specs/2026-06-04-trace-recording-policy.md` before running any Pilot,
rerun, or Phase 2 batch.

Every real run uses a fresh harness HOME under
`/data/harness-lab/runs/<config>/<task>/<repeat>/home`; the shared
`/data/harness-lab/home` directory is only a static install/config template.
Do not run Pilot, Phase 2, or reruns from a shared writable harness HOME.

Phase 2 formal baseline traces are repeats 1-3 only. Repeat 0 is reserved for
Pilot traces and must not be mixed into factorial statistics or HCI ground-truth
labels.

Baseline traces record the observed chosen-tool sequence: ordered tool names,
argument summaries, timestamps where available, outcome, tokens, evidence level,
raw artifact paths, and private audit path. They do not directly record every
unselected alternative tool or hidden internal rationale. Phase 2 baseline
traces keep `decision_points=[]`; Phase 3 attribution labels live under
`analysis/phase3/` and combine source/dossier M1/M2 evidence, direct M3
counterfactual traces, and M4 trace review.

Current committed status: Phase 2 formal baselines and Phase 3 attribution/HCI labels are complete. The Phase 3 interface for downstream analysis is `analysis/phase3/hci-ground-truth-labels.json`.

## Research Questions

| RQ | Question |
|----|---------|
| RQ1 | Do the 4 xAI methods agree on attribution for the same decision point? What is the disagreement pattern? |
| RQ2 | Does high disagreement correlate with task failure? Can it serve as a governance trigger? |
| RQ3 | How do harness main effect, model main effect, and interaction explain tool-selection divergence? |
| RQ4 | Can results be translated into an agent-card template? |

## Repository Structure

```
proposal.pdf       Experiment proposal
runner/            Experiment runner, adapters, validators, Phase 3 analysis commands
tasks/             Agentic task suite and graders
traces/            Committed normalized public traces
analysis/phase3/   Phase 3 seed manifest, attribution records, HCI labels
docs/specs/        Study design and trace recording policy
docs/verification/ Phase completion reports and validation notes
```

Full private audits and raw harness logs are intentionally outside git under
`/data/harness-lab/` on the VPS.
The VPS/Mac private layer is the complete visible audit trail, not a store for
raw hidden chain-of-thought. GitHub keeps the summarized/redacted public layer.

Before Phase 4 analysis or report writing, read
`docs/specs/2026-06-04-phase4-analysis-guardrails.md` for the audience,
XAI/HCI boundary, task-suite scope, and non-overclaim rules. For the HCI report,
also use `docs/specs/2026-06-04-hci-human-study-plan.md`; the HCI component
requires a small human study and cannot be replaced by xAI metrics alone.
