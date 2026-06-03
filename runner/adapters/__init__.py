from runner.adapters.claude_code import ClaudeCodeAdapter

ADAPTERS = {
    "claude_code": ClaudeCodeAdapter,
    # codex / opencode / hermes 於 Task 11-13 加入
}


def get_adapter(harness: str):
    return ADAPTERS[harness]()
