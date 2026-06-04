# Phase 4 analysis guardrails

Purpose: keep Phase 4 metrics and the final report aligned with the actual
evidence base, course expectations, and HCI/XAI boundary.

## Audience and report framing

The final report audience is MIS graduate students and the instructor. The
presentation should explain the research question, method, task sampling,
environment controls, results, limitations, and implications clearly enough for
classroom peer review. It should not be framed as a product procurement report
or as a claim about all coding agents in all settings.

Use the course framing:

- xAI side: pipeline-level diagnosis of harness/tool-path divergence,
  attribution evidence, logging, versioning, and agent-card governance.
- HCI side: how a human reader can correctly understand, question, verify, and
  act on agent behavior. HCI discussion should use mental model, trust
  calibration, automation bias, situation awareness, checkpoint/recovery, and
  evidence presentation. Do not present xAI metrics alone as HCI evaluation.

## Required HCI human study

The HCI report must include a human study. The study can be small-scale and
classroom-feasible, but it cannot be replaced by xAI metrics, screenshots, or a
dashboard alone.

Minimum acceptable design:

- participants: a small convenience sample from MIS graduate students or peers;
- task: participants inspect selected agent trace/summary cases and answer what
  they understand, trust, would verify, or would do next;
- condition: compare at least two presentation styles, such as summary-only vs
  summary plus evidence/limitations/checkpoint cues;
- metrics: include at least clarity, trust calibration, verification intention
  or action choice, perceived safety/control, and cognitive load or effort;
- qualitative feedback: include at least one open-ended question about what was
  confusing, what evidence helped, and what would change their decision;
- ethics: explain voluntary participation, anonymization, no grade penalty, and
  that raw individual responses are not published.

The human study is for HCI claims about understanding, trust calibration,
verification, and interaction design. It should not be used to re-label the xAI
ground truth unless a separate annotation protocol is explicitly designed.

## Non-overclaim rule

The current data support observations about tool-path divergence on this task
suite. They do not justify broad claims about all coding-agent tasks, all
languages, all frameworks, large repositories, or production software
engineering work.

Acceptable claim:

> In this controlled 20-task suite, the six harness/model configurations show
> measurable tool-path divergence, and the selected high-divergence cases can be
> attributed with bounded M1-M4 evidence.

Avoid:

> Harness X is generally better for coding agents.

## Task sampling boundary

The 20 tasks are a balanced, researcher-constructed task suite:

- 5 categories x 4 tasks: `bug_fix`, `rename`, `add_tests`, `add_logging`,
  `benchmark`.
- 16 controlled Python target-repo tasks.
- 4 Python/Exercism benchmark tasks sourced through Aider-polyglot provenance.

This is stratified coverage for tool-path comparison, not random sampling from
the full population of coding-agent work.

## Difficulty calibration boundary

Task difficulty was calibrated for pipeline signal rather than leaderboard
coverage:

- hidden graders fail on the baseline state and pass on reference solutions;
- Phase 1 Pilot avoided all-pass/all-fail collapse;
- Phase 2 formal matrix produced both successes and failures, leaving room for
  tool-path divergence and success-gap analysis.

Report difficulty as a controlled-study design choice. Do not imply the suite
fully represents real-world task difficulty.

## Harness-affinity boundary

The suite may favor some harness affordances:

- all tasks are Python;
- many tasks reward read/edit/shell loops;
- controlled tasks are small and file-local compared with large production
  repositories;
- benchmark tasks are algorithmic and may differ from repository-maintenance
  tasks;
- tool vocabularies differ by harness, so Phase 3 selection canonicalizes tool
  names into families for cross-harness comparison.

Phase 4 should report category-level and tool-family-level results so a
harness-specific tool surface is not mistaken for a universal capability claim.

## Benchmark vs controlled-task analysis

Analyze benchmark tasks separately from controlled software-engineering tasks,
then optionally show a pooled view with an explicit warning.

Required split:

- `benchmark`: algorithmic Exercism-style tasks.
- controlled software-engineering tasks: `bug_fix`, `rename`, `add_tests`,
  `add_logging`.

The pooled 20-task result is useful as a study summary, but category-level
plots are needed before interpreting harness/model effects.

## Robustness not covered

The current Phase 0-3 data do not include robustness tests across:

- programming languages beyond Python;
- frameworks beyond the small controlled package and benchmark baselines;
- large or multi-repository projects;
- long-horizon tasks with many files and dependencies;
- production deployment drift over time.

These belong in limitations and future work, not in the main claim.

## Phase 4 reporting requirements

Phase 4 analysis must:

- use formal Phase 2 repeats 1-3 only for baseline statistics;
- exclude repeat 0 Pilot and repeats 301-312 / 401 / 403 / 404 from factorial
  baseline statistics;
- keep M1/M2 evidence boundaries visible: source/dossier-derived, not uniform
  direct runtime ablation across all harnesses;
- treat Phase 3 counterfactual traces as attribution/context evidence only;
- separate xAI findings from HCI interpretation;
- include limitations before or alongside conclusion slides, not only in an
  appendix.
