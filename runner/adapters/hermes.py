"""Hermes Agent adapter for session JSON traces."""
from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any

from runner import paths
from runner.adapters.base import HarnessAdapter


def _loads_args(raw: Any) -> Any:
    if not isinstance(raw, str):
        return raw
    try:
        return json.loads(raw)
    except json.JSONDecodeError:
        return raw


def _summarize_args(args: Any) -> str:
    if not isinstance(args, dict):
        return str(args)[:160]
    parts: list[str] = []
    for key in ("path", "mode", "offset", "limit", "old_string", "new_string", "command"):
        if key in args:
            val = str(args[key]).replace("\n", "\\n")
            parts.append(f"{key}={val[:120]}")
    if parts:
        return ",".join(parts)
    return ",".join(list(args.keys())[:4])


class HermesAdapter(HarnessAdapter):
    name = "hermes"
    version = "0.13.0"

    def env(self, secrets: dict, model_snapshot: str) -> dict:
        env = {
            "HOME": str(paths.LAB_HOME),
            "HERMES_HOME": str(paths.LAB_HOME / ".hermes"),
            "PATH": f"{paths.LAB_BIN}:" + os.environ.get("PATH", ""),
        }
        if "ANTHROPIC_API_KEY" in secrets:
            env["ANTHROPIC_API_KEY"] = secrets["ANTHROPIC_API_KEY"]
        if "OPENAI_API_KEY" in secrets:
            env["OPENAI_API_KEY"] = secrets["OPENAI_API_KEY"]
        return env

    def command(self, prompt: str, model_snapshot: str, provider: str, workdir: Path | None = None) -> list[str]:
        return [
            str(paths.HERMES_BIN),
            "-z",
            prompt,
            "-m",
            model_snapshot,
            "--provider",
            provider,
            "--yolo",
        ]

    def raw_artifacts(self, workdir: Path) -> dict[str, Path]:
        arts: dict[str, Path] = {}
        session = workdir / "trace.session.json"
        if session.exists():
            arts["session_json"] = session
        log = workdir / "hermes.log"
        if log.exists():
            arts["stdout_log"] = log
        return arts

    def normalize(self, workdir: Path) -> dict:
        arts = self.raw_artifacts(workdir)
        session = arts.get("session_json")
        tool_calls: list[dict[str, Any]] = []
        reasoning_steps: list[dict[str, Any]] = []
        system_present = False
        turns = None

        if session:
            data = json.loads(session.read_text())
            system_present = bool(data.get("system_prompt"))
            turns = sum(1 for msg in data.get("messages", []) if msg.get("role") == "assistant")
            for idx, msg in enumerate(data.get("messages", [])):
                if msg.get("role") == "assistant":
                    if msg.get("reasoning") or msg.get("reasoning_content") or msg.get("codex_reasoning_items"):
                        reasoning_steps.append({"type": "reasoning", "message_index": idx, "present": True})
                for call in msg.get("tool_calls") or []:
                    fn = call.get("function") or {}
                    args = _loads_args(fn.get("arguments"))
                    tool_calls.append({
                        "step": len(tool_calls) + 1,
                        "tool_name": fn.get("name") or "?",
                        "args_summary": _summarize_args(args),
                        "ts": None,
                    })

        return {
            "tool_calls": tool_calls,
            "reasoning_steps": reasoning_steps,
            "decision_points": [],
            "tokens": {"input": None, "cached_input": None, "output": None},
            "turns": turns,
            "runtime_budget": {
                "max_output_tokens": None,
                "thinking_budget_tokens": None,
                "context_window_tokens": None,
                "effort_source": "hermes -z -m MODEL --provider PROVIDER --yolo; no explicit effort flag",
            },
            "system_present": system_present,
            "evidence_levels": {
                "tool_calls": "direct",
                "system_present": "direct" if session else "unknown",
                "reasoning_steps": "direct" if reasoning_steps else "unknown",
                "tokens": "unknown",
            },
        }
