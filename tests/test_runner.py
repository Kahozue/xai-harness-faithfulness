from __future__ import annotations

import json
from types import SimpleNamespace

from runner import cli
from runner import runner as R
from runner.trace_schema import validate_trace


class _MockAdapter:
    name = "claude_code"
    version = "test-adapter"

    def env(self, secrets, model_snapshot):
        return {}

    def command(self, prompt, model_snapshot, provider):
        return ["/bin/sh", "-c", "printf raw > mock.raw; printf launch"]

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

    trace = R.run_once(1, "bugfix-t2-01", 0, secrets={"ANTHROPIC_API_KEY": "x"})

    validate_trace(trace)
    assert trace["run_id"] == "c1__claude_code__bugfix-t2-01__r0"
    assert trace["tool_calls"][0]["tool_name"] == "Read"
    assert trace["outcome"]["success"] is False
    assert trace["system_present"] is True
    assert trace["outcome"]["launch_returncode"] == 0

    raw_dir = runs / "1" / "bugfix-t2-01" / "0" / "raw"
    assert (raw_dir / "mock.raw").read_text() == "raw"
    assert (raw_dir / "claude_code.log").read_text() == "launch"

    saved = json.loads((traces / "1" / "bugfix-t2-01" / "0.json").read_text())
    assert saved["raw_log_path"] == str(raw_dir)
    assert saved["raw_artifacts"]["mock_raw"].endswith("mock.raw")


def test_cli_pilot_dry_list(capsys):
    rc = cli.main(["pilot", "--dry-list"])
    assert rc == 0
    out = json.loads(capsys.readouterr().out)
    assert len(out["planned"]) == 6
    assert out["planned"][0] == {"config": 1, "task": "bugfix-t2-01", "repeat": 0}
    assert out["planned"][-1] == {"config": 6, "task": "bench-grade-school", "repeat": 0}
