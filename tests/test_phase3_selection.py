from __future__ import annotations

import json
from pathlib import Path

from runner import paths
from runner.phase3_selection import (
    build_phase3_seed_manifest,
    tool_family,
    write_phase3_seed_outputs,
)


def _trace(
    config: int,
    task: str,
    repeat: int,
    tools: list[str],
    success: bool = True,
    category: str = "bug_fix",
) -> dict:
    harness_by_config = {
        1: "claude_code",
        2: "opencode",
        3: "hermes",
        4: "opencode",
        5: "hermes",
        6: "codex",
    }
    model_by_config = {
        1: "claude-haiku-4-5-20251001",
        2: "claude-haiku-4-5-20251001",
        3: "claude-haiku-4-5-20251001",
        4: "gpt-5.4-mini-2026-03-17",
        5: "gpt-5.4-mini-2026-03-17",
        6: "gpt-5.4-mini-2026-03-17",
    }
    return {
        "config_id": config,
        "harness": harness_by_config[config],
        "model_snapshot": model_by_config[config],
        "task_id": task,
        "task_category": category,
        "repeat_index": repeat,
        "tool_calls": [
            {"step": index, "tool_name": tool, "args_summary": "", "ts": None}
            for index, tool in enumerate(tools, start=1)
        ],
        "outcome": {"success": success},
        "_trace_path": f"traces/{config}/{task}/{repeat}.json",
    }


def _cell(config: int, task: str, tools: list[str], success: bool = True) -> list[dict]:
    return [_trace(config, task, repeat, tools, success=success) for repeat in (1, 2, 3)]


def test_tool_family_normalizes_harness_tool_names():
    assert tool_family("Read") == "read"
    assert tool_family("read_file") == "read"
    assert tool_family("apply_patch") == "edit"
    assert tool_family("file_change") == "edit"
    assert tool_family("command_execution") == "shell"
    assert tool_family("search-files") == "search"


def test_phase3_seed_selection_is_stratified_and_ranked():
    traces = []
    # Same stratum, but task-a has a stronger c1-c2 sequence split than task-b.
    traces += _cell(1, "task-a", ["Read", "Edit"])
    traces += _cell(2, "task-a", ["bash", "bash", "edit"], success=False)
    traces += _cell(3, "task-a", ["read_file", "patch"])
    traces += _cell(1, "task-b", ["Read", "Edit"])
    traces += _cell(2, "task-b", ["read", "edit"])
    traces += _cell(3, "task-b", ["read_file", "patch"])

    # GPT-mini harness stratum.
    traces += _cell(4, "task-c", ["grep", "apply_patch"])
    traces += _cell(5, "task-c", ["search_files", "patch"])
    traces += _cell(6, "task-c", ["command_execution", "file_change"])

    # Model-swap strata.
    traces += _cell(2, "task-d", ["read", "edit"])
    traces += _cell(4, "task-d", ["glob", "bash", "apply_patch"])
    traces += _cell(3, "task-e", ["read_file", "patch"])
    traces += _cell(5, "task-e", ["search_files", "terminal", "patch"])

    manifest = build_phase3_seed_manifest(traces, per_stratum=1)

    assert manifest["source"]["trace_count"] == len(traces)
    assert len(manifest["selected"]) == 4
    assert [seed["seed_id"] for seed in manifest["selected"]] == [
        "PH3-DP-001",
        "PH3-DP-002",
        "PH3-DP-003",
        "PH3-DP-004",
    ]
    assert {seed["stratum"] for seed in manifest["selected"]} == {
        "haiku_same_model_harness",
        "gptmini_same_model_harness",
        "opencode_model_swap",
        "hermes_model_swap",
    }
    haiku_seed = manifest["selected"][0]
    assert haiku_seed["task_id"] == "task-a"
    assert haiku_seed["config_pair"] == [1, 2]
    assert haiku_seed["scores"]["success_gap"] == 1.0


def test_write_phase3_seed_outputs_resolves_repo_relative_paths(monkeypatch, tmp_path):
    monkeypatch.setattr(paths, "REPO", tmp_path)
    manifest = build_phase3_seed_manifest(
        _cell(1, "task-a", ["Read"]) + _cell(2, "task-a", ["bash"]),
        per_stratum=1,
    )

    manifest_path, report_path = write_phase3_seed_outputs(
        manifest,
        "analysis/phase3/seeds.json",
        Path("docs/verification/phase3.md"),
    )

    saved = json.loads(manifest_path.read_text())
    assert manifest_path == tmp_path / "analysis" / "phase3" / "seeds.json"
    assert report_path == tmp_path / "docs" / "verification" / "phase3.md"
    assert saved["selected"][0]["seed_id"] == "PH3-DP-001"
    assert "Phase 3 decision-point seed selection" in report_path.read_text()
