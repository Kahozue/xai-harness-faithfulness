from pathlib import Path

from runner.adapters import get_adapter
from runner.adapters.hermes import HermesAdapter

FIX_HAIKU = Path(__file__).parent / "fixtures" / "hermes-haiku.smoke.json"
FIX_GPTMINI = Path(__file__).parent / "fixtures" / "hermes-gptmini.smoke.json"


def test_command_shape():
    a = HermesAdapter()
    cmd = a.command("FIX BUG", "claude-haiku-4-5-20251001", "anthropic")
    assert cmd[0].endswith("hermes")
    assert cmd[1:3] == ["-z", "FIX BUG"]
    assert "-m" in cmd and "claude-haiku-4-5-20251001" in cmd
    assert "--provider" in cmd and "anthropic" in cmd
    assert "--yolo" in cmd


def test_env_uses_isolated_home_and_provider_keys():
    a = HermesAdapter()
    env = a.env({"ANTHROPIC_API_KEY": "a", "OPENAI_API_KEY": "o"}, "claude-haiku-4-5-20251001")
    assert env["HOME"].endswith("/home")
    assert env["HERMES_HOME"].endswith("/home/.hermes")
    assert env["ANTHROPIC_API_KEY"] == "a"
    assert env["OPENAI_API_KEY"] == "o"


def test_registry_includes_hermes():
    assert isinstance(get_adapter("hermes"), HermesAdapter)


def test_normalize_haiku_fixture(tmp_path):
    (tmp_path / "trace.session.json").write_text(FIX_HAIKU.read_text())
    out = HermesAdapter().normalize(tmp_path)
    assert [tc["tool_name"] for tc in out["tool_calls"]] == ["read_file", "patch"]
    assert "path=hello.py" in out["tool_calls"][0]["args_summary"]
    assert "old_string=" in out["tool_calls"][1]["args_summary"]
    assert out["system_present"] is True
    assert out["tokens"] == {"input": None, "cached_input": None, "output": None}
    assert out["turns"] == 3
    assert out["evidence_levels"]["tokens"] == "unknown"


def test_normalize_gptmini_fixture_reasoning(tmp_path):
    (tmp_path / "trace.session.json").write_text(FIX_GPTMINI.read_text())
    out = HermesAdapter().normalize(tmp_path)
    assert [tc["tool_name"] for tc in out["tool_calls"]] == ["read_file", "patch"]
    assert out["system_present"] is True
    assert out["reasoning_steps"], "GPT-mini Hermes fixture exposes reasoning metadata"
    assert out["evidence_levels"]["reasoning_steps"] == "direct"


def test_raw_artifacts_never_fall_back_to_shared_lab_home(tmp_path):
    (tmp_path / "hermes.log").write_text("stdout")

    arts = HermesAdapter().raw_artifacts(tmp_path)

    assert arts == {"stdout_log": tmp_path / "hermes.log"}
