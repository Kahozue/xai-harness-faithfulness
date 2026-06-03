from pathlib import Path

from runner.adapters import get_adapter
from runner.adapters.opencode import OpenCodeAdapter

FIX_HAIKU = Path(__file__).parent / "fixtures" / "opencode-haiku.smoke.log"
FIX_GPTMINI = Path(__file__).parent / "fixtures" / "opencode-gptmini.smoke.log"


def test_command_shape():
    a = OpenCodeAdapter()
    cmd = a.command("FIX BUG", "claude-haiku-4-5-20251001", "anthropic")
    assert cmd[0].endswith("opencode")
    assert cmd[:2] == [cmd[0], "run"]
    assert "--model" in cmd
    assert "anthropic/claude-haiku-4-5-20251001" in cmd
    assert "--variant" in cmd and "high" in cmd
    assert "--format" in cmd and "json" in cmd


def test_env_uses_isolated_home_and_provider_keys():
    a = OpenCodeAdapter()
    env = a.env({"ANTHROPIC_API_KEY": "a", "OPENAI_API_KEY": "o"}, "claude-haiku-4-5-20251001")
    assert env["HOME"].endswith("/home")
    assert env["ANTHROPIC_API_KEY"] == "a"
    assert env["OPENAI_API_KEY"] == "o"
    assert "/data/harness-lab/bin" in env["PATH"]


def test_registry_includes_opencode():
    assert isinstance(get_adapter("opencode"), OpenCodeAdapter)


def test_normalize_haiku_fixture(tmp_path):
    (tmp_path / "oc.log").write_text(FIX_HAIKU.read_text())
    out = OpenCodeAdapter().normalize(tmp_path)
    assert [tc["tool_name"] for tc in out["tool_calls"]] == ["read", "edit"]
    assert "filePath=" in out["tool_calls"][0]["args_summary"]
    assert "oldString=" in out["tool_calls"][1]["args_summary"]
    assert out["tool_calls"][0]["ts"].endswith("Z")
    assert out["tokens"] == {"input": 33, "cached_input": 17188, "output": 457}
    assert out["turns"] == 3
    assert out["system_present"] is False
    assert out["evidence_levels"]["system_present"] == "unknown"


def test_normalize_gptmini_fixture(tmp_path):
    (tmp_path / "oc.log").write_text(FIX_GPTMINI.read_text())
    out = OpenCodeAdapter().normalize(tmp_path)
    assert [tc["tool_name"] for tc in out["tool_calls"]] == [
        "glob",
        "glob",
        "read",
        "apply_patch",
        "read",
    ]
    assert "pattern=**/hello.py" in out["tool_calls"][0]["args_summary"]
    assert "patchText=" in out["tool_calls"][3]["args_summary"]
    assert out["tokens"] == {"input": 7616, "cached_input": 25600, "output": 381}
    assert out["turns"] == 5
    assert {"type": "reasoning_tokens", "tokens": 70} in out["reasoning_steps"]
