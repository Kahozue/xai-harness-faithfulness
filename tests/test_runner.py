from __future__ import annotations

import json
import subprocess
from types import SimpleNamespace

import pytest

from runner import cli
from runner import runner as R
from runner.trace_schema import validate_trace


class _MockAdapter:
    name = "claude_code"
    version = "test-adapter"

    def env(self, secrets, model_snapshot):
        return {"HOME": "/shared/template-home"}

    def command(self, prompt, model_snapshot, provider, workdir=None):
        return ["/bin/sh", "-c", "printf raw > mock.raw; printf launch; printf \"$HOME\" > seen_home"]

    def raw_artifacts(self, workdir):
        return {"mock_raw": workdir / "mock.raw"}

    def normalize(self, workdir):
        return {
            "tool_calls": [{"step": 1, "tool_name": "Read", "args_summary": "calckit/money.py", "ts": None}],
            "reasoning_steps": [],
            "decision_points": [],
            "tokens": {"input": None, "cached_input": None, "output": None},
            "turns": 1,
            "runtime_budget": {
                "max_output_tokens": 64000,
                "thinking_budget_tokens": 63999,
                "context_window_tokens": 200000,
                "effort_source": "mock",
            },
            "system_present": True,
            "evidence_levels": {"tool_calls": "direct", "system_present": "direct"},
        }


def test_run_once_produces_valid_trace_and_persists(monkeypatch, tmp_path):
    runs = tmp_path / "runs"
    traces = tmp_path / "traces"

    monkeypatch.setattr(R, "get_adapter", lambda harness: _MockAdapter())
    monkeypatch.setattr(R, "run_grader", lambda task, wd: SimpleNamespace(success=False, detail="baseline fail"))
    monkeypatch.setattr(R.persist, "run_dir", lambda c, t, r: runs / str(c) / t / str(r))
    monkeypatch.setattr(R.persist, "trace_path", lambda c, t, r: traces / str(c) / t / f"{r}.json")
    monkeypatch.setattr(R.persist, "private_audit_path", lambda c, t, r: traces / "private" / str(c) / t / f"{r}.md")

    trace = R.run_once(1, "bugfix-t2-01", 0, secrets={"ANTHROPIC_API_KEY": "x"})

    validate_trace(trace)
    assert trace["run_id"] == "c1__claude_code__bugfix-t2-01__r0"
    assert trace["tool_calls"][0]["tool_name"] == "Read"
    assert trace["outcome"]["success"] is False
    assert trace["system_present"] is True
    assert trace["outcome"]["launch_returncode"] == 0
    assert trace["private_audit_path"].endswith("private/1/bugfix-t2-01/0.md")

    raw_dir = runs / "1" / "bugfix-t2-01" / "0" / "raw"
    assert (raw_dir / "mock.raw").read_text() == "raw"
    assert (raw_dir / "claude_code.log").read_text() == "launch"
    assert (runs / "1" / "bugfix-t2-01" / "0" / "home").exists()
    assert (runs / "1" / "bugfix-t2-01" / "0" / "workdir" / "seen_home").read_text() == str(
        runs / "1" / "bugfix-t2-01" / "0" / "home"
    )

    audit = traces / "private" / "1" / "bugfix-t2-01" / "0.md"
    assert "Private full run audit" in audit.read_text()
    assert "mock_raw" in audit.read_text()

    saved = json.loads((traces / "1" / "bugfix-t2-01" / "0.json").read_text())
    assert saved["raw_log_path"] == str(raw_dir)
    assert saved["raw_artifacts"]["mock_raw"].endswith("mock.raw")
    assert saved["private_audit_path"].endswith("private/1/bugfix-t2-01/0.md")


def test_run_once_refuses_to_overwrite_existing_trace(monkeypatch, tmp_path):
    runs = tmp_path / "runs"
    traces = tmp_path / "traces"
    existing = traces / "1" / "bugfix-t2-01" / "0.json"
    existing.parent.mkdir(parents=True)
    existing.write_text("{}")

    monkeypatch.setattr(R, "get_adapter", lambda harness: _MockAdapter())
    monkeypatch.setattr(R.persist, "run_dir", lambda c, t, r: runs / str(c) / t / str(r))
    monkeypatch.setattr(R.persist, "trace_path", lambda c, t, r: traces / str(c) / t / f"{r}.json")

    with pytest.raises(FileExistsError):
        R.run_once(1, "bugfix-t2-01", 0, secrets={"ANTHROPIC_API_KEY": "x"})

    assert not (runs / "1" / "bugfix-t2-01" / "0" / "workdir").exists()


def test_cli_pilot_dry_list(capsys):
    rc = cli.main(["pilot", "--dry-list"])
    assert rc == 0
    out = json.loads(capsys.readouterr().out)
    assert out["count"] == 6
    assert len(out["planned"]) == 6
    assert out["planned"][0] == {"config": 1, "task": "bugfix-t2-01", "repeat": 0}
    assert out["planned"][-1] == {"config": 6, "task": "bench-grade-school", "repeat": 0}


def test_phase2_plan_defaults_to_full_factorial(monkeypatch):
    tasks = [{"id": f"task-{i:02d}"} for i in range(20)]
    monkeypatch.setattr(cli, "load_tasks", lambda: tasks)

    planned = cli._phase2_plan()

    assert len(planned) == 6 * 20 * 3
    assert planned[0] == {"config": 1, "task": "task-00", "repeat": 1}
    assert planned[2] == {"config": 1, "task": "task-00", "repeat": 3}
    assert planned[-1] == {"config": 6, "task": "task-19", "repeat": 3}


def test_cli_phase2_dry_list_supports_filters(monkeypatch, capsys):
    monkeypatch.setattr(cli, "load_tasks", lambda: [{"id": "task-a"}, {"id": "task-b"}])

    rc = cli.main([
        "phase2",
        "--dry-list",
        "--config", "2",
        "--task", "task-b",
        "--repeat-start", "4",
        "--repeats", "2",
    ])

    assert rc == 0
    out = json.loads(capsys.readouterr().out)
    assert out["count"] == 2
    assert out["total_planned"] == 2
    assert out["planned"] == [
        {"config": 2, "task": "task-b", "repeat": 4},
        {"config": 2, "task": "task-b", "repeat": 5},
    ]


def test_cli_phase2_refuses_existing_trace_without_override(monkeypatch, tmp_path, capsys):
    existing = tmp_path / "traces" / "1" / "task-a" / "1.json"
    existing.parent.mkdir(parents=True)
    existing.write_text("{}")

    monkeypatch.setattr(cli, "load_tasks", lambda: [{"id": "task-a"}])
    monkeypatch.setattr(cli.persist, "trace_path", lambda c, t, r: tmp_path / "traces" / str(c) / t / f"{r}.json")

    rc = cli.main(["phase2", "--config", "1", "--task", "task-a", "--repeat-start", "1", "--repeats", "1"])

    assert rc == 1
    out = json.loads(capsys.readouterr().out)
    assert out["error"] == "trace_exists"
    assert out["existing"] == [str(existing)]


def test_cli_phase2_skip_existing_resumes_without_running_existing(monkeypatch, tmp_path, capsys):
    existing = tmp_path / "traces" / "1" / "task-a" / "1.json"
    existing.parent.mkdir(parents=True)
    existing.write_text("{}")

    monkeypatch.setattr(cli, "load_tasks", lambda: [{"id": "task-a"}])
    monkeypatch.setattr(cli.persist, "trace_path", lambda c, t, r: tmp_path / "traces" / str(c) / t / f"{r}.json")

    rc = cli.main([
        "phase2",
        "--dry-list",
        "--skip-existing",
        "--config", "1",
        "--task", "task-a",
        "--repeat-start", "1",
        "--repeats", "2",
    ])

    assert rc == 0
    out = json.loads(capsys.readouterr().out)
    assert out["count"] == 1
    assert out["skipped_existing"] == 1
    assert out["planned"] == [{"config": 1, "task": "task-a", "repeat": 2}]


def test_cli_phase2_run_streams_progress(monkeypatch, tmp_path, capsys):
    monkeypatch.setattr(cli, "load_tasks", lambda: [{"id": "task-a"}])
    monkeypatch.setattr(cli.persist, "trace_path", lambda c, t, r: tmp_path / "traces" / str(c) / t / f"{r}.json")

    def fake_run_once(config, task, repeat, timeout, overwrite=False):
        return {
            "run_id": f"c{config}__mock__{task}__r{repeat}",
            "config_id": config,
            "task_id": task,
            "repeat_index": repeat,
            "outcome": {"success": True},
            "tool_calls": [{"tool_name": "Read"}],
            "wall_time_s": 0.1,
            "private_audit_path": "/tmp/audit.md",
        }

    monkeypatch.setattr(cli, "run_once", fake_run_once)

    rc = cli.main(["phase2", "--config", "1", "--task", "task-a", "--repeat-start", "1", "--repeats", "1"])

    assert rc == 0
    events = [json.loads(line) for line in capsys.readouterr().out.splitlines()]
    assert [event["event"] for event in events] == [
        "phase2_start",
        "phase2_run_start",
        "phase2_run_result",
        "phase2_complete",
    ]
    assert events[2]["success"] is True
    assert events[3]["completed"] == 1


def test_repo_escape_guard_preserves_and_restores(monkeypatch, tmp_path):
    repo = tmp_path / "repo"
    protected = repo / "tasks" / "target_repo"
    protected.mkdir(parents=True)
    tracked = protected / "money.py"
    tracked.write_text("baseline\n")
    subprocess.run(["git", "init"], cwd=repo, check=True, capture_output=True)
    subprocess.run(["git", "add", "."], cwd=repo, check=True, capture_output=True)
    subprocess.run(
        ["git", "-c", "user.email=x@example.com", "-c", "user.name=x", "commit", "-m", "base"],
        cwd=repo,
        check=True,
        capture_output=True,
    )
    tracked.write_text("mutated\n")
    untracked = protected / "new.py"
    untracked.write_text("new\n")
    monkeypatch.setattr(R.paths, "REPO", repo)

    status = R._protected_repo_status()
    assert "tasks/target_repo/money.py" in status
    assert "tasks/target_repo/new.py" in status

    workdir = tmp_path / "workdir"
    R._quarantine_repo_escape(workdir, status)

    assert tracked.read_text() == "baseline\n"
    assert not untracked.exists()
    assert "tasks/target_repo/money.py" in (workdir / "repo_escape.status").read_text()
    assert "mutated" in (workdir / "repo_escape.diff").read_text()
    assert (workdir / "repo_escape_untracked" / "tasks" / "target_repo" / "new.py").read_text() == "new\n"
