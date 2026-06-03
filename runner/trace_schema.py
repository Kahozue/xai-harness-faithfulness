"""§6.3 正規化 Trace schema：跨 harness 可比的單筆 run JSON。"""
from __future__ import annotations
from dataclasses import dataclass, field, asdict
from typing import Any, Optional
import jsonschema

VALID_CATEGORIES = {"rename", "add_tests", "add_logging", "bug_fix"}
VALID_HARNESSES = {"claude_code", "codex", "opencode", "hermes"}


@dataclass
class ToolCall:
    step: int
    tool_name: str
    args_summary: str
    ts: Optional[str]  # ISO8601 或 None（部分 harness 無逐工具時間戳）


@dataclass
class NormalizedTrace:
    run_id: str
    config_id: int
    harness: str
    harness_version: str
    model: str
    model_snapshot: str
    task_id: str
    task_category: str
    repeat_index: int
    reasoning_effort: str
    tool_calls: list[ToolCall]
    reasoning_steps: list[dict[str, Any]]
    decision_points: list[dict[str, Any]]
    outcome: dict[str, Any]            # {success: bool, grader_detail: str, final_diff_path: str|None}
    tokens: dict[str, Optional[int]]   # {input, cached_input, output}
    wall_time_s: Optional[float]
    turns: Optional[int]
    runtime_budget: dict[str, Any]     # {max_output_tokens, thinking_budget_tokens, context_window_tokens, effort_source}
    raw_log_path: str
    env_lock_ref: str
    timestamp: str
    # 跨 harness 誠實標註：每欄位的證據等級（見 dossier M4：direct/source-derived/inferred/unknown）
    evidence_levels: dict[str, str] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        d = asdict(self)
        d["tool_calls"] = sorted(d["tool_calls"], key=lambda tc: tc["step"])
        return d


_SCHEMA = {
    "type": "object",
    "required": [
        "run_id", "config_id", "harness", "harness_version", "model", "model_snapshot",
        "task_id", "task_category", "repeat_index", "reasoning_effort", "tool_calls",
        "reasoning_steps", "decision_points", "outcome", "tokens", "runtime_budget",
        "raw_log_path", "env_lock_ref", "timestamp",
    ],
    "properties": {
        "harness": {"enum": sorted(VALID_HARNESSES)},
        "task_category": {"enum": sorted(VALID_CATEGORIES)},
        "reasoning_effort": {"const": "high"},
        "tool_calls": {
            "type": "array",
            "items": {
                "type": "object",
                "required": ["step", "tool_name", "args_summary", "ts"],
                "properties": {"step": {"type": "integer"}, "tool_name": {"type": "string"}},
            },
        },
        "outcome": {"type": "object", "required": ["success", "grader_detail"]},
        "runtime_budget": {"type": "object", "required": ["effort_source"]},
    },
}


def validate_trace(d: dict[str, Any]) -> None:
    jsonschema.validate(instance=d, schema=_SCHEMA)
