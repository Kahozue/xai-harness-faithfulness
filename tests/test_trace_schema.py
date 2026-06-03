import pytest
from runner.trace_schema import NormalizedTrace, ToolCall, validate_trace


def _minimal_kwargs():
    return dict(
        run_id="cc__bugfix-t2-01__0",
        config_id=1,
        harness="claude_code",
        harness_version="2.1.88",
        model="claude-haiku-4-5-20251001",
        model_snapshot="claude-haiku-4-5-20251001",
        task_id="bugfix-t2-01",
        task_category="bug_fix",
        repeat_index=0,
        reasoning_effort="high",
        tool_calls=[ToolCall(step=1, tool_name="Read", args_summary="hello.py", ts=None)],
        reasoning_steps=[],
        decision_points=[],
        outcome={"success": True, "grader_detail": "3 passed", "final_diff_path": None},
        tokens={"input": None, "cached_input": None, "output": None},
        wall_time_s=12.3,
        turns=3,
        runtime_budget={"max_output_tokens": 64000, "thinking_budget_tokens": 63999,
                        "context_window_tokens": 200000, "effort_source": "cli --effort high"},
        system_present=True,
        raw_log_path="/data/harness-lab/runs/1/bugfix-t2-01/0/raw/claude-trace.jsonl",
        env_lock_ref="ENVIRONMENT.lock.md@<commit>",
        timestamp="2026-06-04T10:00:00Z",
    )


def test_trace_roundtrips_to_dict():
    t = NormalizedTrace(**_minimal_kwargs())
    d = t.to_dict()
    assert d["tool_calls"][0]["tool_name"] == "Read"
    assert d["runtime_budget"]["max_output_tokens"] == 64000
    assert d["system_present"] is True


def test_validate_accepts_minimal():
    t = NormalizedTrace(**_minimal_kwargs())
    validate_trace(t.to_dict())  # 不應 raise


def test_validate_rejects_missing_required():
    d = NormalizedTrace(**_minimal_kwargs()).to_dict()
    del d["tool_calls"]
    with pytest.raises(Exception):
        validate_trace(d)


def test_tool_calls_are_ordered_by_step():
    kw = _minimal_kwargs()
    kw["tool_calls"] = [ToolCall(2, "Edit", "hello.py", None), ToolCall(1, "Read", "hello.py", None)]
    t = NormalizedTrace(**kw)
    steps = [tc["step"] for tc in t.to_dict()["tool_calls"]]
    assert steps == [1, 2], "to_dict 應依 step 排序，保證有序 tool 序列"
