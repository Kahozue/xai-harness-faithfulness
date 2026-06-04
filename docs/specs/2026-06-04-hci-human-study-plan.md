# HCI human study plan

Purpose: provide the minimum classroom-feasible human study needed for the HCI
final report. This study evaluates how people understand and use the presented
agent-trace evidence. It does not replace the xAI attribution pipeline and does
not relabel xAI ground truth.

## Research question

When MIS graduate students inspect selected agent trace summaries, does a
presentation that includes evidence, limitations, and action/checkpoint cues
support better understanding and verification behavior than a summary-only
presentation?

## Participants

- Target: MIS graduate students or peer classmates.
- Scale: small convenience sample is acceptable, target `n=6-10`.
- Handling: participation is voluntary, anonymous/code-based, and unrelated to
  grades. Do not publish raw individual responses.

## Materials

Use 4-6 selected Phase 3 HCI-label cases from
`analysis/phase3/hci-ground-truth-labels.json`.

Recommended case mix:

- at least one `harness_main_effect` initial-tool-strategy case;
- at least one `model_main_effect` initial-tool-strategy case;
- at least one `interaction` or semantic-convention case;
- at least one task-success-gap case.

The cases should be rendered in two presentation styles:

- Condition A: summary-only view, showing task, two agent outcomes, and compact
  tool sequence summary.
- Condition B: evidence + limitation + action view, showing the same summary
  plus evidence snippets, confidence/limitation note, and suggested verification
  or checkpoint action.

## Procedure

Use a within-subject design so a small sample can still compare conditions:

1. Brief participants on the task and explain that the study concerns interface
   understanding, not their programming ability.
2. Show 2-3 cases in Condition A and 2-3 cases in Condition B, counterbalancing
   order if feasible.
3. For each case, ask participants to identify what happened, which evidence
   they would inspect, whether they would trust the agent result, and what they
   would do next.
4. Collect Likert ratings and one short open-ended response per case.

## Metrics

Required HCI measures:

- clarity: how clearly the participant understands what happened;
- trust calibration: whether trust matches evidence strength/limitations;
- verification intention or action choice: whether the participant chooses to
  inspect evidence, rerun, ask for more information, or accept/reject;
- perceived safety/control: whether the participant feels able to catch or
  recover from the agent error;
- cognitive load or effort: whether the presentation is understandable without
  excessive burden.

Optional behavioral coding:

- correct identification of the main difference between the two agents;
- whether the participant notices the limitation/non-overclaim warning;
- whether the participant chooses an appropriate next action.

## Analysis

Report descriptive statistics first because the sample is small:

- mean/median Likert ratings by condition;
- counts of verification/action choices by condition;
- short qualitative themes from open-ended responses.

If sample size permits, add only light inferential analysis:

- paired comparison for within-subject Likert ratings;
- Fisher exact or descriptive count comparison for action choices.

Avoid overclaiming statistical significance. The goal is to support HCI
reflection about clarity, trust calibration, verification, and control.

## Reporting boundary

The human study supports HCI claims about how people understand and use the
presentation. It does not prove the harness attribution itself; that remains the
xAI evidence chain from Phase 2/3.
