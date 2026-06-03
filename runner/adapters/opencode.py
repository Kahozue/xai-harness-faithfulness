"""OpenCode adapter for `opencode run --format json` traces."""
from __future__ import annotations

import json
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable

from runner import paths
from runner.adapters.base import HarnessAdapter


def _jsonl(path: Path) -> Iterable[dict[str, Any]]:
    for line in path.read_text().splitlines():
        line = line.strip()
        if not line:
            continue
        try:
            yield json.loads(line)
        except json.JSONDecodeError:
            continue


def _ts(ms: int | float | None) -> str | None:
    if ms is None:
        return None
    return datetime.fromtimestamp(ms / 1000, tz=timezone.utc).isoformat().replace("+00:00", "Z")


def _summarize_input(inp: Any) -> str:
    if not isinstance(inp, dict):
        return str(inp)[:160]
    parts: list[str] = []
    for key in ("filePath", "path", "pattern", "patchText", "oldString", "newString"):
        if key in inp:
            val = str(inp[key]).replace("\n", "\\n")
            parts.append(f"{key}={val[:120]}")
    if parts:
        return ",".join(parts)
    return ",".join(list(inp.keys())[:4])


class OpenCodeAdapter(HarnessAdapter):
    name = "opencode"
    version = "1.15.13"

    def env(self, secrets: dict, model_snapshot: str) -> dict:
        env = {
            "HOME": str(paths.LAB_HOME),
            "PATH": f"{paths.LAB_BIN}:" + os.environ.get("PATH", ""),
        }
        if "ANTHROPIC_API_KEY" in secrets:
            env["ANTHROPIC_API_KEY"] = secrets["ANTHROPIC_API_KEY"]
        if "OPENAI_API_KEY" in secrets:
            env["OPENAI_API_KEY"] = secrets["OPENAI_API_KEY"]
        return env

    def command(self, prompt: str, model_snapshot: str, provider: str) -> list[str]:
        return [
            str(paths.LAB_BIN / "opencode"),
            "run",
            "--model",
            f"{provider}/{model_snapshot}",
            "--variant",
            "high",
            "--format",
            "json",
            prompt,
        ]

    def raw_artifacts(self, workdir: Path) -> dict[str, Path]:
        for name in ("oc.log", "opencode.log", "opencode-haiku.smoke.log", "opencode-gptmini.smoke.log"):
            p = workdir / name
            if p.exists():
                return {"stdout_jsonl": p}
        return {}

    def normalize(self, workdir: Path) -> dict:
        arts = self.raw_artifacts(workdir)
        tool_calls: list[dict[str, Any]] = []
        reasoning_steps: list[dict[str, Any]] = []
        tokens = {"input": 0, "cached_input": 0, "output": 0}
        saw_tokens = False
        reasoning_tokens = 0
        turns = 0

        stdout = arts.get("stdout_jsonl")
        if stdout:
            for rec in _jsonl(stdout):
                typ = rec.get("type")
                part = rec.get("part") or {}
                if typ == "step_start":
                    turns += 1
                elif typ == "tool_use":
                    state = part.get("state") or {}
                    tool_calls.append({
                        "step": len(tool_calls) + 1,
                        "tool_name": part.get("tool") or "?",
                        "args_summary": _summarize_input(state.get("input")),
                        "ts": _ts(rec.get("timestamp")),
                    })
                elif typ == "reasoning":
                    reasoning_steps.append({"type": "reasoning", "present": True, "ts": _ts(rec.get("timestamp"))})
                elif typ == "step_finish":
                    t = part.get("tokens") or {}
                    cache = t.get("cache") or {}
                    tokens["input"] += int(t.get("input") or 0)
                    tokens["cached_input"] += int(cache.get("read") or 0)
                    tokens["output"] += int(t.get("output") or 0)
                    reasoning_tokens += int(t.get("reasoning") or 0)
                    saw_tokens = True

        if reasoning_tokens:
            reasoning_steps.append({"type": "reasoning_tokens", "tokens": reasoning_tokens})

        if not saw_tokens:
            tokens = {"input": None, "cached_input": None, "output": None}

        return {
            "tool_calls": tool_calls,
            "reasoning_steps": reasoning_steps,
            "decision_points": [],
            "tokens": tokens,
            "turns": turns or None,
            "runtime_budget": {
                "max_output_tokens": None,
                "thinking_budget_tokens": None,
                "context_window_tokens": None,
                "effort_source": "opencode run --variant high",
            },
            "system_present": False,
            "evidence_levels": {
                "tool_calls": "direct",
                "system_present": "unknown",
                "reasoning_steps": "direct" if reasoning_steps else "unknown",
                "tokens": "direct" if saw_tokens else "unknown",
            },
        }
