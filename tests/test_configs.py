from runner.configs import CONFIGS, get_config


def test_six_configs_exact():
    assert len(CONFIGS) == 6
    ids = [c.id for c in CONFIGS]
    assert ids == [1, 2, 3, 4, 5, 6]


def test_config_routing_matches_spec():
    by_id = {c.id: c for c in CONFIGS}
    assert (by_id[1].harness, by_id[1].provider) == ("claude_code", "anthropic")
    assert (by_id[2].harness, by_id[2].provider) == ("opencode", "anthropic")
    assert (by_id[3].harness, by_id[3].provider) == ("hermes", "anthropic")
    assert (by_id[4].harness, by_id[4].provider) == ("opencode", "openai")
    assert (by_id[5].harness, by_id[5].provider) == ("hermes", "openai")
    assert (by_id[6].harness, by_id[6].provider) == ("codex", "openai")


def test_haiku_configs_use_anthropic_native():
    for c in CONFIGS:
        if c.model_snapshot == "claude-haiku-4-5-20251001":
            assert c.provider == "anthropic"
        if c.model_snapshot == "gpt-5.4-mini-2026-03-17":
            assert c.provider == "openai"


def test_get_config():
    assert get_config(6).harness == "codex"
