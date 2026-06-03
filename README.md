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

6 configs × 20 agentic tasks (rename / add tests / add logging / simple bug fix).

**4 xAI attribution methods (white-box):**
- M1: System prompt ablation — remove / replace sections
- M2: Tool definition perturbation — rename, alter docstring, remove specific tool
- M3: Behavioral counterfactual swap — rewrite task input
- M4: Planning-loop trace — harness hook intercepts reasoning steps

**Metrics:** Jaccard similarity, disagreement rate, success correlation, five-dimension agent-card matrix (fidelity / stability / robustness / actionability / governability).

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
