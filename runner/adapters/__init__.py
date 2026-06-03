from runner.adapters.claude_code import ClaudeCodeAdapter
from runner.adapters.codex import CodexAdapter
from runner.adapters.opencode import OpenCodeAdapter

ADAPTERS = {
    "claude_code": ClaudeCodeAdapter,
    "codex": CodexAdapter,
    "opencode": OpenCodeAdapter,
    # hermes 於 Task 14 加入
}


def get_adapter(harness: str):
    return ADAPTERS[harness]()
