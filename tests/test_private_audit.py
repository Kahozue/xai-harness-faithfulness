from __future__ import annotations

from pathlib import Path

from runner.private_audit import build_private_audit

FIX = Path(__file__).parent / "fixtures"


def _trace(harness: str, artifacts: dict[str, str]) -> dict:
    return {
        "run_id": f"test__{harness}__r0",
        "config_id": 1,
        "harness": harness,
        "harness_version": "test",
        "model": "model",
        "task_id": "bugfix-t2-01",
        "task_category": "bug_fix",
        "repeat_index": 0,
        "timestamp": "2026-06-04T00:00:00Z",
        "outcome": {"success": True, "grader_detail": "ok"},
        "wall_time_s": 1.0,
        "raw_log_path": "/tmp/raw",
        "tool_calls": [{"step": 1, "tool_name": "Read", "args_summary": "file_path=x", "ts": None}],
        "tokens": {"input": 1, "cached_input": 0, "output": 1},
        "runtime_budget": {"effort_source": "test"},
        "evidence_levels": {"tool_calls": "direct"},
        "raw_artifacts": artifacts,
    }


def test_private_audit_covers_claude_fixture_without_hidden_thinking():
    audit = build_private_audit(_trace("claude_code", {"trace_jsonl": str(FIX / "cc.smoke.jsonl")}))
    assert "Claude Code detailed timeline" in audit
    assert "thinking blocks present" in audit
    assert "Tool calls" in audit
    assert "用户提出" not in audit


def test_private_audit_covers_codex_fixture():
    audit = build_private_audit(_trace("codex", {"stdout_jsonl": str(FIX / "codex.smoke.log")}))
    assert "Codex detailed timeline" in audit
    assert "command_execution" in audit
    assert "file_change" in audit


def test_private_audit_covers_opencode_fixture():
    audit = build_private_audit(_trace("opencode", {"stdout_jsonl": str(FIX / "opencode-haiku.smoke.log")}))
    assert "OpenCode detailed timeline" in audit
    assert "read" in audit
    assert "edit" in audit


def test_private_audit_covers_hermes_fixture():
    audit = build_private_audit(_trace("hermes", {"session_json": str(FIX / "hermes-haiku.smoke.json")}))
    assert "Hermes detailed timeline" in audit
    assert "system prompt present: True" in audit
    assert "read_file" in audit
