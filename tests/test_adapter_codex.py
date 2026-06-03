from pathlib import Path

from runner.adapters import get_adapter
from runner.adapters.codex import CodexAdapter

FIX = Path(__file__).parent / "fixtures" / "codex.smoke.log"


def test_command_shape():
    a = CodexAdapter()
    cmd = a.command("FIX BUG", "gpt-5.4-mini-2026-03-17", "openai")
    assert cmd[0].endswith("codex")
    assert cmd[1] == "exec"
    assert "--json" in cmd
    assert "--skip-git-repo-check" in cmd
    assert "--dangerously-bypass-approvals-and-sandbox" in cmd
    assert "--model" not in cmd


def test_env_uses_isolated_home_and_openai_key():
    a = CodexAdapter()
    env = a.env({"OPENAI_API_KEY": "x"}, "gpt-5.4-mini-2026-03-17")
    assert env["HOME"].endswith("/home")
    assert env["OPENAI_API_KEY"] == "x"
    assert "/data/harness-lab/bin" in env["PATH"]


def test_registry_includes_codex():
    assert isinstance(get_adapter("codex"), CodexAdapter)


def test_normalize_extracts_tool_sequence_from_fixture(tmp_path):
    (tmp_path / "codex.log").write_text(FIX.read_text())
    (tmp_path / "codex.session.jsonl").write_text(
        "\n".join([
            '{"timestamp":"2026-06-03T13:57:43.700Z","type":"session_meta",'
            '"payload":{"cli_version":"0.136.0","base_instructions":{"text":"system"}}}',
            '{"timestamp":"2026-06-03T13:57:43.708Z","type":"event_msg",'
            '"payload":{"type":"task_started","model_context_window":258400}}',
            '{"timestamp":"2026-06-03T13:57:46.675Z","type":"response_item",'
            '"payload":{"type":"reasoning","summary":[],"encrypted_content":"x"}}',
        ])
    )

    out = CodexAdapter().normalize(tmp_path)
    names = [tc["tool_name"] for tc in out["tool_calls"]]
    assert names == [
        "command_execution",
        "command_execution",
        "command_execution",
        "file_change",
        "command_execution",
    ]
    assert "rg --files" in out["tool_calls"][0]["args_summary"]
    assert "hello.py:update" in out["tool_calls"][3]["args_summary"]
    assert out["tokens"] == {"input": 52377, "cached_input": 40960, "output": 581}
    assert out["turns"] == 1
    assert out["system_present"] is True
    assert out["runtime_budget"]["context_window_tokens"] == 258400
    assert any(step["type"] == "reasoning_tokens" for step in out["reasoning_steps"])


def test_raw_artifacts_never_fall_back_to_shared_lab_home(tmp_path):
    (tmp_path / "codex.log").write_text(FIX.read_text())

    arts = CodexAdapter().raw_artifacts(tmp_path)

    assert "stdout_jsonl" in arts
    assert "session_jsonl" not in arts
