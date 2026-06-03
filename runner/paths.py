"""實驗引擎的路徑與 secrets 載入，鏡像 infra/00-paths.sh（單一事實來源仍是該 shell 檔）。"""
from __future__ import annotations
import os
from pathlib import Path

REPO = Path("/data/repos/xai-harness-faithfulness")
LAB = Path("/data/harness-lab")
LAB_HOME = LAB / "home"
LAB_BIN = LAB / "bin"
RUNS = LAB / "runs"
RUNNER_VENV = LAB / "runner-venv"
SECRETS = Path.home() / ".harness-exp"

ANTHROPIC_MODEL = "claude-haiku-4-5-20251001"
OPENAI_MODEL = "gpt-5.4-mini-2026-03-17"
HERMES_BIN = Path.home() / ".local" / "bin" / "hermes"  # 二進位在真實 HOME（見 smoke-hermes.sh）


def load_secrets() -> dict[str, str]:
    """從 ~/.harness-exp/{anthropic,openai}.env 讀 KEY=VALUE；不印出值。"""
    env: dict[str, str] = {}
    for name in ("anthropic.env", "openai.env"):
        p = SECRETS / name
        if not p.exists():
            continue
        for line in p.read_text().splitlines():
            line = line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            k, _, v = line.partition("=")
            env[k.strip()] = v.strip()
    return env


def has_secret(name: str) -> bool:
    return name in load_secrets()
