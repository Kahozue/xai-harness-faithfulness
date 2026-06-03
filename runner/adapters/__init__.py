from runner.adapters.claude_code import ClaudeCodeAdapter
from runner.adapters.codex import CodexAdapter

ADAPTERS = {
    "claude_code": ClaudeCodeAdapter,
    "codex": CodexAdapter,
    # opencode / hermes 於 Task 13-14 加入
}


def get_adapter(harness: str):
    return ADAPTERS[harness]()
