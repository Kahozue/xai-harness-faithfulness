from runner import paths


def test_lab_paths_are_absolute():
    assert paths.LAB.is_absolute()
    assert paths.RUNS == paths.LAB / "runs"
    assert paths.RUNNER_VENV.exists(), "venv 應已於 Task1 Step3 建好"


def test_models_pinned():
    assert paths.ANTHROPIC_MODEL == "claude-haiku-4-5-20251001"
    assert paths.OPENAI_MODEL == "gpt-5.4-mini-2026-03-17"


def test_secrets_loadable_without_leaking():
    s = paths.load_secrets()
    # 不斷言值，只斷言兩把 key 都載入得到（檔案存在於 server）
    assert "ANTHROPIC_API_KEY" in s
    assert "OPENAI_API_KEY" in s
