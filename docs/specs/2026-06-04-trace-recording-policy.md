# Trace recording policy（summary/public vs full/private）

This policy is mandatory for Phase 1 onward.

## Artifact split

Every real harness run must keep two record layers:

| Layer | Location | GitHub status | Contents |
|---|---|---|---|
| Summary/public | `traces/<config>/<task>/<repeat>.json`, `docs/verification/*report.md` | committed | normalized schema fields, tool names, argument summaries, outcome, tokens, raw artifact paths, private audit path |
| Full/private plaintext | `/data/harness-lab/private-audits/<config>/<task>/<repeat>.md` on VPS; mirrored under `private-audits/` on Mac when needed | never committed | visible model messages, tool inputs/outputs, errors, recoveries, raw artifact references, failure diagnosis |

Raw harness logs stay outside git under `/data/harness-lab/runs/.../raw`.
They are also plaintext and private.

`Full/private` means the local/VPS record keeps the complete visible audit trail
needed for verification. It does not mean raw hidden chain-of-thought is saved.
GitHub keeps only the summarized/redacted public layer.

## Baseline trace semantics

Phase 2 baseline traces are evidence of the observed chosen-tool path. The
public `tool_calls` array is the primary dependent variable for tool-selection
divergence: ordered tool names plus compact argument summaries. The baseline
does not claim to expose every unchosen alternative or hidden rationale. The
committed Phase 2 `decision_points` array remains empty. Phase 3 attribution
labels are stored under `analysis/phase3/` and may reference baseline and
counterfactual traces; they do not backfill hidden alternatives into the
baseline trace files.

## Non-negotiable rules

- Do not commit full private audits to git/GitHub.
- Do not commit raw harness logs.
- Do not commit secrets.
- Do not transcribe raw hidden chain-of-thought from Claude/Anthropic thinking
  blocks or encrypted reasoning payloads. Record presence/count and use visible
  model messages plus tool behavior for reasoning summaries.
- Keep detailed private audits unencrypted on VPS/Mac unless the user explicitly
  asks for encryption later.
- The committed summary trace may include a `private_audit_path` so future
  operators know where the local/VPS full record lives.

## Runner behavior

`runner run` and `runner pilot` must:

- write raw artifacts under `/data/harness-lab/runs/.../raw`;
- create a fresh per-run HOME under `/data/harness-lab/runs/<config>/<task>/<repeat>/home`;
- treat `/data/harness-lab/home` only as a static install/config template, never
  as the writable HOME for an experiment run;
- copy only required static config/auth into the per-run HOME, excluding
  sessions, project histories, memories, state databases, logs, caches, and
  prior run trust entries;
- for Claude Code, run through `claude-trace --include-all-requests` and save
  both `.claude-trace/*.jsonl` and the generated `.html` report;
- for Codex and Hermes, copy the session artifact from the current run's
  isolated HOME into the workdir before normalization; adapters must not fall
  back to "latest" session files under the shared lab HOME;
- for OpenCode, pass `--dir <workdir>` explicitly; subprocess `cwd` alone is
  not sufficient to constrain OpenCode's project root;
- check protected repo baseline paths after harness execution and before
  grading; if a harness modifies `tasks/target_repo` or `tasks/benchmark`,
  save the repo-escape status/diff/untracked files under that run's workdir,
  restore the protected baseline, and treat the run as invalid/error;
- write a private plaintext audit under `/data/harness-lab/private-audits/...`;
- write the committed summary trace under `traces/...`;
- refuse to overwrite an existing summary trace by default;
- require an explicit `--overwrite` flag or a unique `--repeat` index for any
  intentional rerun.

This prevents smoke/probe runs from silently overwriting matrix traces and
prevents cross-run harness state from contaminating tool-selection behavior.

## Documentation behavior

Verification reports committed to GitHub should be concise summaries. If a deep
trace review is performed, put the full version in the private layer and mention
its private path from the GitHub-safe report.

Formal Phase 2 reports must use repeats 1, 2, and 3 only. Repeat 0 is Pilot data
and must not be counted in the 6 x 20 x 3 factorial matrix. Before reporting
Phase 2 as complete, run `python -m runner phase2-validate` on the VPS and cite
its summary. This gate checks schema validity, private audit links, raw artifact
links, run-local HOME directories, and infrastructure-limit failure signatures.

When handing off to another model/operator, point them to this file before any
new Pilot, full-factorial, rerun, or Phase 2 execution.

## Test coverage expectation

The test suite must cover:

- private audit generation in `run_once`;
- overwrite refusal when a trace already exists;
- parser coverage for Claude Code, Codex, OpenCode, and Hermes fixtures;
- per-run HOME isolation and exclusion of sessions/state/memory;
- no Codex/Hermes adapter fallback to shared lab HOME sessions;
- hidden-thinking exclusion from generated private audit markdown.
