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
- M1: System prompt ablation — remove / replace sections
- M2: Tool definition perturbation — rename, alter docstring, remove specific tool
- M3: Behavioral counterfactual swap — rewrite task input
- M4: Planning-loop trace — harness hook intercepts reasoning steps

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

## Research Questions

| RQ | Question |
|----|---------|
| RQ1 | Do the 4 xAI methods agree on attribution for the same decision point? What is the disagreement pattern? |
| RQ2 | Does high disagreement correlate with task failure? Can it serve as a governance trigger? |
| RQ3 | How do harness main effect, model main effect, and interaction explain tool-selection divergence? |
| RQ4 | Can results be translated into an agent-card template? |

## Repository Structure

```
proposal.pdf    Experiment proposal
```

Experiment scripts, traces, and analysis will be added as the study progresses.
