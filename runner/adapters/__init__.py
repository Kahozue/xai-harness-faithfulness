from runner.adapters.claude_code import ClaudeCodeAdapter
from runner.adapters.codex import CodexAdapter
from runner.adapters.hermes import HermesAdapter
from runner.adapters.opencode import OpenCodeAdapter

ADAPTERS = {
    "claude_code": ClaudeCodeAdapter,
    "codex": CodexAdapter,
    "hermes": HermesAdapter,
    "opencode": OpenCodeAdapter,
}


def get_adapter(harness: str):
    return ADAPTERS[harness]()
