"""Per-run harness HOME preparation.

The lab HOME under /data/harness-lab/home is an installation/config template.
Actual experiment runs must not share writable harness state, sessions, memory,
or history, so every run gets its own HOME under the run directory.
"""
from __future__ import annotations

import shutil
from pathlib import Path

from runner import paths


def _copy_file(src: Path, dst: Path) -> None:
    if not src.exists():
        return
    dst.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(src, dst)


def _write_codex_config(dst: Path) -> None:
    dst.parent.mkdir(parents=True, exist_ok=True)
    dst.write_text(
        "\n".join([
            f'model = "{paths.OPENAI_MODEL}"',
            'model_reasoning_effort = "high"',
            "",
        ])
    )


def prepare_run_home(harness: str, run_home: Path) -> Path:
    """Create a fresh writable HOME for one run and copy only static config/auth."""
    run_home = Path(run_home)
    if run_home.exists():
        shutil.rmtree(run_home)
    run_home.mkdir(parents=True, mode=0o700)

    if harness == "codex":
        _write_codex_config(run_home / ".codex" / "config.toml")
        _copy_file(paths.LAB_HOME / ".codex" / "auth.json", run_home / ".codex" / "auth.json")
    elif harness == "opencode":
        _copy_file(
            paths.LAB_HOME / ".config" / "opencode" / "opencode.json",
            run_home / ".config" / "opencode" / "opencode.json",
        )
    elif harness == "hermes":
        for rel in (".hermes/config.yaml", ".hermes/.env", ".hermes/SOUL.md", ".hermes/auth.json"):
            _copy_file(paths.LAB_HOME / rel, run_home / rel)
    elif harness == "claude_code":
        # Claude Code can run from an empty HOME with API-key auth. Keep project
        # history, shell snapshots, sessions, and cached feature files out.
        _copy_file(
            paths.LAB_HOME / ".claude" / "policy-limits.json",
            run_home / ".claude" / "policy-limits.json",
        )
    else:
        raise ValueError(f"unknown harness for isolation: {harness}")

    return run_home


def env_for_run_home(harness: str, run_home: Path) -> dict[str, str]:
    env = {"HOME": str(run_home)}
    if harness == "hermes":
        env["HERMES_HOME"] = str(run_home / ".hermes")
    return env
