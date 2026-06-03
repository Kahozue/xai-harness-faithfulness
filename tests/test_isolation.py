from __future__ import annotations

from runner import isolation


def test_prepare_codex_home_copies_auth_but_not_state(monkeypatch, tmp_path):
    base = tmp_path / "base"
    (base / ".codex" / "sessions").mkdir(parents=True)
    (base / ".codex" / "config.toml").write_text('model = "old"\n[projects."/old"]\ntrust_level = "trusted"\n')
    (base / ".codex" / "auth.json").write_text('{"token":"redacted"}')
    (base / ".codex" / "memories_1.sqlite").write_text("memory")
    (base / ".codex" / "sessions" / "rollout-old.jsonl").write_text("{}")
    monkeypatch.setattr(isolation.paths, "LAB_HOME", base)

    run_home = isolation.prepare_run_home("codex", tmp_path / "run-home")

    assert (run_home / ".codex" / "auth.json").exists()
    config = (run_home / ".codex" / "config.toml").read_text()
    assert 'model = "gpt-5.4-mini-2026-03-17"' in config
    assert "[projects." not in config
    assert not (run_home / ".codex" / "memories_1.sqlite").exists()
    assert not (run_home / ".codex" / "sessions").exists()


def test_prepare_harness_homes_exclude_sessions_and_databases(monkeypatch, tmp_path):
    base = tmp_path / "base"
    (base / ".config" / "opencode").mkdir(parents=True)
    (base / ".config" / "opencode" / "opencode.json").write_text("{}")
    (base / ".local" / "share" / "opencode").mkdir(parents=True)
    (base / ".local" / "share" / "opencode" / "opencode.db").write_text("db")

    (base / ".hermes" / "sessions").mkdir(parents=True)
    (base / ".hermes" / "config.yaml").write_text("model: {}\n")
    (base / ".hermes" / ".env").write_text("OPENAI_API_KEY=x\n")
    (base / ".hermes" / "SOUL.md").write_text("soul")
    (base / ".hermes" / "auth.json").write_text("{}")
    (base / ".hermes" / "state.db").write_text("db")
    (base / ".hermes" / "sessions" / "session_old.json").write_text("{}")

    (base / ".claude" / "projects").mkdir(parents=True)
    (base / ".claude" / "policy-limits.json").write_text("{}")
    (base / ".claude" / "projects" / "old.json").write_text("{}")
    (base / ".claude.json").write_text("{}")
    monkeypatch.setattr(isolation.paths, "LAB_HOME", base)

    opencode_home = isolation.prepare_run_home("opencode", tmp_path / "opencode-home")
    assert (opencode_home / ".config" / "opencode" / "opencode.json").exists()
    assert not (opencode_home / ".local" / "share" / "opencode" / "opencode.db").exists()

    hermes_home = isolation.prepare_run_home("hermes", tmp_path / "hermes-home")
    assert (hermes_home / ".hermes" / "config.yaml").exists()
    assert (hermes_home / ".hermes" / ".env").exists()
    assert not (hermes_home / ".hermes" / "state.db").exists()
    assert not (hermes_home / ".hermes" / "sessions").exists()

    claude_home = isolation.prepare_run_home("claude_code", tmp_path / "claude-home")
    assert (claude_home / ".claude" / "policy-limits.json").exists()
    assert not (claude_home / ".claude.json").exists()
    assert not (claude_home / ".claude" / "projects").exists()


def test_env_for_run_home_sets_hermes_home(tmp_path):
    run_home = tmp_path / "home"
    assert isolation.env_for_run_home("codex", run_home) == {"HOME": str(run_home)}
    assert isolation.env_for_run_home("hermes", run_home) == {
        "HOME": str(run_home),
        "HERMES_HOME": str(run_home / ".hermes"),
    }
