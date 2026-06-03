from pathlib import Path
from runner.adapters.claude_code import ClaudeCodeAdapter

FIX = Path(__file__).parent / "fixtures" / "cc.smoke.jsonl"


def test_command_shape():
    a = ClaudeCodeAdapter()
    cmd = a.command("FIX BUG", "claude-haiku-4-5-20251001", "anthropic")
    assert cmd[0].endswith("claude-trace")
    assert "--model" in cmd and "claude-haiku-4-5-20251001" in cmd
    assert "--effort" in cmd


def test_env_sets_budgets():
    a = ClaudeCodeAdapter()
    env = a.env({"ANTHROPIC_API_KEY": "x"}, "claude-haiku-4-5-20251001")
    assert env["CLAUDE_CODE_MAX_OUTPUT_TOKENS"] == "64000"
    assert env["MAX_THINKING_TOKENS"] == "63999"
    assert env["HOME"].endswith("/home")


def test_normalize_extracts_tool_sequence_from_fixture(tmp_path):
    td = tmp_path / ".claude-trace"
    td.mkdir()
    (td / "log.jsonl").write_text(FIX.read_text())
    out = ClaudeCodeAdapter().normalize(tmp_path)
    names = [tc["tool_name"] for tc in out["tool_calls"]]
    assert names, "應從 SSE trace 解析出至少一個 tool_use"
    assert out["runtime_budget"]["max_output_tokens"] == 64000
    assert out["runtime_budget"]["thinking_budget_tokens"] == 63999
    assert out["system_present"] is True
    assert out["turns"] >= 1


def test_raw_artifacts_keep_claude_trace_jsonl_and_html(tmp_path):
    td = tmp_path / ".claude-trace"
    td.mkdir()
    (td / "log-2026.jsonl").write_text(FIX.read_text())
    (td / "log-2026.html").write_text("<html>trace</html>")

    arts = ClaudeCodeAdapter().raw_artifacts(tmp_path)

    assert arts["trace_jsonl"].name == "log-2026.jsonl"
    assert arts["trace_html"].name == "log-2026.html"
