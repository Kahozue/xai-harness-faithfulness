# Phase 2 isolation reset（2026-06-04）

Scope: Phase 2 full-factorial launch attempt that began at
`/data/harness-lab/phase2/phase2-20260603T193705Z.jsonl`.

## Decision

The initial Phase 2 batch was stopped and invalidated before completion. It used
clean per-run workdirs, but harness writable state still pointed at the shared
template HOME `/data/harness-lab/home`. That leaves a cross-run contamination
risk through Claude Code project history, Codex sessions/state/memory, OpenCode
DB/log state, and Hermes sessions/state/memory.

These partial traces are not valid Phase 2 data and must not be used for xAI or
HCI analysis.

## Required fix before restart

- Every experiment run must use a fresh HOME at
  `/data/harness-lab/runs/<config>/<task>/<repeat>/home`.
- `/data/harness-lab/home` is only an install/config template.
- The per-run HOME may contain static config/auth needed to launch the harness.
- The per-run HOME must not copy sessions, project history, state databases,
  memories, logs, caches, or previous project trust entries.
- Codex and Hermes session normalization must use only the session artifact from
  the current run's HOME, copied into the workdir by the runner.
- Codex and Hermes adapters must not fall back to latest sessions under the
  shared lab HOME.

## Invalidated artifact handling

The stopped batch produced only partial config 1 traces. Before the clean Phase 2
restart, those repeat 1-3 artifacts should be moved out of the committed trace
tree and out of the active private-audit/run directories into a quarantine
folder under `/data/harness-lab/phase2/invalid-shared-home-*`.

The clean restart should reuse repeats 1, 2, and 3 only after the invalid shared
HOME artifacts are quarantined.
