# Model-reasoning (thinking/CoT) capture investigation

Date: 2026-06-05

## Question

Review of the v2 presentation deck flagged that the Haiku model reasoning was
described as "hidden chain-of-thought omitted" uniformly. This investigation
determines, per harness, whether the model reasoning is genuinely unobtainable
or simply was not captured.

## Method

A logging reverse-proxy was placed on the Anthropic endpoint. It captures the
full request plus the SSE response (including `thinking` blocks) and forwards to
`api.anthropic.com` unchanged. OpenCode was routed via its `opencode.json`
anthropic `options.baseURL`; Hermes via the `ANTHROPIC_BASE_URL` env. Production
Hermes source was never modified; Hermes extended thinking was enabled by
injecting `thinking={type:enabled, budget_tokens:16000}` (with `temperature=1`)
into the request at the proxy. Re-runs used repeat indices 10/11 so the formal
360 baseline (repeats 1-3) was untouched. Configs and proxy were restored after.

## Findings

| Config (Haiku) | Reasoning observability | Result |
|---|---|---|
| 1 Claude Code | thinking budget 63999; claude-trace already captures it | ALREADY CAPTURED in baseline raw (`runs/1/.../raw/log-*.jsonl`). Prior "omitted" wording was a policy/wording gap, not a capture failure. |
| 2 OpenCode | thinking budget 16000; returned by API | CAPTURABLE, was not captured before (`opencode export` strips thinking). Proxy captured all 20 tasks, 97,560 chars. |
| 3 Hermes (native) | no `thinking` field sent (budget 0) | NOTHING TO CAPTURE natively. `reasoning_effort:high` only wires OpenAI, not Anthropic thinking. |
| 3 Hermes (forced) | thinking enabled via proxy injection | Capturable but thin: 20 tasks, 6,393 chars (mostly first turn; Hermes does not preserve thinking blocks across tool turns). |
| 4/5/6 GPT-5.4-mini (OpenAI) | reasoning encrypted | GENUINELY NOT OBTAINABLE. `encrypted_content` (~1000-3200 chars) is not decodable; only a plaintext summary + token counts are returned. |

## Non-uniform effort

The deck's "all configs at high effort" is not uniform on the Anthropic path:
actual thinking budgets in the corrected baseline are Claude Code 63999,
OpenCode 16000, and Hermes forced-proxy 16000. The Hermes native 0 result is
kept only as a failed-control diagnostic. This supports the "effort is not
perfectly equivalent across harnesses" caveat.

## XAI-C03 case (bugfix-t2-03)

The captured OpenCode reasoning shows why it scored 0/3: it committed to the
`-$12.50` convention (sign before `$`) and self-"verified" against the visible
test (which only checks positives), declaring success. The hidden grader expects
`format_amount(-12.5) == "$-12.50"` (sign after `$`). The failure cause is
visible only in the captured reasoning, not in pass/fail or the tool path.

## Artifacts

- Full reconstructed thinking (private, not committed):
  `/data/harness-lab/thinking-capture/{2,3}/<task>.txt`.
- Pack-level summary (committed):
  `analysis/phase5/xai-presentation-pack/ppt-handoff/v2_7/thinking-capture-summary.json`.
- Deck reflecting these facts: slide 3 provider visibility, slide 11 Thinking column,
  slide 23 (XAI-C03) captured-thinking reveal.

## Baseline integrity

Formal 360 baseline (repeats 1-3) untouched; supplementary re-runs used repeat
10/11 and their trace byproducts were removed after extraction. `git status`
clean except the new committed deck + this report.
