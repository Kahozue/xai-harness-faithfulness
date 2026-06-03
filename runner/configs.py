"""§4 的 6 configs（控制變數：同一模型固定走同一後端）。"""
from __future__ import annotations
from dataclasses import dataclass
from runner import paths


@dataclass(frozen=True)
class Config:
    id: int
    harness: str       # claude_code | codex | opencode | hermes
    model_role: str    # haiku | gptmini
    model_snapshot: str
    provider: str      # anthropic | openai（後端 = 原生）
    role: str          # 說明（anchor 等）


_HAIKU = paths.ANTHROPIC_MODEL
_GPTMINI = paths.OPENAI_MODEL

CONFIGS: list[Config] = [
    Config(1, "claude_code", "haiku", _HAIKU, "anthropic", "anchor: 橫向 harness 基準"),
    Config(2, "opencode", "haiku", _HAIKU, "anthropic", ""),
    Config(3, "hermes", "haiku", _HAIKU, "anthropic", ""),
    Config(4, "opencode", "gptmini", _GPTMINI, "openai", ""),
    Config(5, "hermes", "gptmini", _GPTMINI, "openai", ""),
    Config(6, "codex", "gptmini", _GPTMINI, "openai", "anchor"),
]


def get_config(config_id: int) -> Config:
    for c in CONFIGS:
        if c.id == config_id:
            return c
    raise KeyError(f"unknown config_id={config_id}")
