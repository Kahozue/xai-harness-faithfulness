# Skill probe summary（2026-06-04）

Scope: small Claude Code behavior probe requested before the next phase. This
was not a formal Pilot matrix run and did not write to `traces/`.

## Question

Why did the Phase 1 Pilot not use skills? If a model is explicitly told that a
skill is available and asked to use it, will it invoke the `Skill` tool?

## Method

Ran Claude Code / Haiku 4.5 in an isolated scratch directory:

```text
/data/harness-lab/skill-probes/2026-06-04-claude-skill-explicit
```

Prompt summary:

```text
If the Skill tool is available, use the Skill tool exactly once with the
keybindings-help skill, then answer whether you used a skill. Do not edit files.
```

Full plaintext private audit:

```text
/data/harness-lab/private-audits/skill-probes/2026-06-04-claude-skill-explicit.md
```

Mac mirror:

```text
private-audits/skill-probes/2026-06-04-claude-skill-explicit.md
```

## Result

Tool sequence:

```text
Skill
```

Visible final answer:

```text
Yes, I used the keybindings-help skill.
```

Token summary from normalized parser:

```text
input=7, cached_input=15810, output=275
```

## Interpretation

The Pilot did not use skills because the task prompts did not require them and
the model chose direct file/shell/edit tools. Skill availability itself works:
when explicitly asked to use a safe skill, Claude Code invoked `Skill` exactly
once.

Implication for Phase 2: if skill-use behavior is part of the research question,
add a dedicated skill-trigger task or perturbation. Do not infer "skills are
unavailable" from ordinary coding tasks where no skill was semantically needed.
