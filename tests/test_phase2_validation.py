from __future__ import annotations

import json
from pathlib import Path

from runner import paths
from runner.configs import Config
from runner.phase2_validation import validate_phase2


def _trace(raw: Path, audit: Path, tools: list[dict] | None = None) -> dict:
    return {
        "run_id": "c1__hermes__task-a__r1",
        "config_id": 1,
        "harness": "hermes",
        "harness_version": "test",
        "model": "model-a",
        "model_snapshot": "model-a",
        "task_id": "task-a",
        "task_category": "bug_fix",
        "repeat_index": 1,
        "reasoning_effort": "high",
        "tool_calls": tools if tools is not None else [
            {"step": 1, "tool_name": "read_file", "args_summary": "path=x", "ts": None}
        ],
        "reasoning_steps": [],
        "decision_points": [],
        "outcome": {
            "success": True,
            "grader_detail": "ok",
            "final_diff_path": None,
            "launch_returncode": 0,
            "launch_timed_out": False,
        },
        "tokens": {"input": None, "cached_input": None, "output": None},
        "wall_time_s": 1.0,
        "turns": 1,
        "runtime_budget": {"effort_source": "test"},
        "system_present": True,
        "raw_log_path": str(raw),
        "env_lock_ref": "ENVIRONMENT.lock.md@test",
        "timestamp": "2026-06-04T00:00:00Z",
        "evidence_levels": {"tool_calls": "direct"},
        "raw_artifacts": {"stdout_jsonl": str(raw / "trace.log")},
        "private_audit_path": str(audit),
    }


def _write_complete_trace(tmp_path: Path, monkeypatch, tools: list[dict] | None = None, raw_text: str = "ok") -> None:
    repo = tmp_path / "repo"
    runs = tmp_path / "runs"
    audits = tmp_path / "private-audits"
    raw = runs / "1" / "task-a" / "1" / "raw"
    home = runs / "1" / "task-a" / "1" / "home"
    audit = audits / "1" / "task-a" / "1.md"
    trace_path = repo / "traces" / "1" / "task-a" / "1.json"

    raw.mkdir(parents=True)
    home.mkdir(parents=True)
    audit.parent.mkdir(parents=True)
    trace_path.parent.mkdir(parents=True)
    (raw / "trace.log").write_text(raw_text)
    audit.write_text("audit")
    trace_path.write_text(json.dumps(_trace(raw, audit, tools=tools)))

    monkeypatch.setattr(paths, "REPO", repo)
    monkeypatch.setattr(paths, "RUNS", runs)
    monkeypatch.setattr(paths, "PRIVATE_AUDITS", audits)
    monkeypatch.setattr(paths, "LAB_HOME", tmp_path / "template-home")


def test_validate_phase2_accepts_complete_matrix(monkeypatch, tmp_path):
    from runner import phase2_validation as pv

    _write_complete_trace(tmp_path, monkeypatch)
    monkeypatch.setattr(pv, "CONFIGS", [Config(1, "hermes", "haiku", "model-a", "anthropic", "")])
    monkeypatch.setattr(pv, "load_tasks", lambda: [{"id": "task-a"}])

    report = validate_phase2(repeat_start=1, repeats=1)

    assert report["ok"] is True
    assert report["expected_traces"] == 1
    assert report["found_traces"] == 1
    assert report["config_summary"][0]["tool_calls_total"] == 1
    assert report["failures"]["missing_traces"] == []


def test_validate_phase2_detects_quota_zero_config(monkeypatch, tmp_path):
    from runner import phase2_validation as pv

    _write_complete_trace(
        tmp_path,
        monkeypatch,
        tools=[],
        raw_text="You have reached your specified API usage limits.",
    )
    monkeypatch.setattr(pv, "CONFIGS", [Config(1, "hermes", "haiku", "model-a", "anthropic", "")])
    monkeypatch.setattr(pv, "load_tasks", lambda: [{"id": "task-a"}])

    report = validate_phase2(repeat_start=1, repeats=1)

    assert report["ok"] is False
    assert report["failures"]["all_zero_tool_configs"] == [1]
    assert report["failures"]["infra_failure_flags"][0]["pattern"] == "specified api usage limits"


def test_validate_phase2_reports_missing_home(monkeypatch, tmp_path):
    from runner import phase2_validation as pv

    _write_complete_trace(tmp_path, monkeypatch)
    missing_home = tmp_path / "runs" / "1" / "task-a" / "1" / "home"
    missing_home.rmdir()
    monkeypatch.setattr(pv, "CONFIGS", [Config(1, "hermes", "haiku", "model-a", "anthropic", "")])
    monkeypatch.setattr(pv, "load_tasks", lambda: [{"id": "task-a"}])

    report = validate_phase2(repeat_start=1, repeats=1)

    assert report["ok"] is False
    assert str(missing_home) in report["failures"]["missing_run_homes"]
