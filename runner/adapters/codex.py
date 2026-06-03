"""Codex CLI adapter.

`codex exec --json` writes a JSONL event stream to stdout. The first line may
be non-JSON status text, then events look like:

  {"type":"item.completed","item":{"type":"command_execution", ...}}
  {"type":"item.completed","item":{"type":"file_change", ...}}
  {"type":"turn.completed","usage":{...}}

The richer rollout session under $LAB_HOME/.codex/sessions is used only as a
supplement for system-prompt presence, reasoning markers, and context budget.
"""
from __future__ import annotations

import json
import os
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


def _safe_rel_to(path: Path, parent: Path) -> bool:
    try:
        path.resolve().relative_to(parent.resolve())
    except ValueError:
        return False
    return True


def _latest_rollout() -> Path | None:
    root = paths.LAB_HOME / ".codex" / "sessions"
    if not root.exists():
        return None
    files = list(root.rglob("rollout-*.jsonl"))
    if not files:
        return None
    return max(files, key=lambda p: (p.stat().st_mtime, str(p)))


def _summarize_command(item: dict[str, Any]) -> str:
    cmd = str(item.get("command") or "")
    return f"command={cmd[:160]}"


def _summarize_file_change(item: dict[str, Any]) -> str:
    changes = item.get("changes") or []
    parts = []
    for change in changes[:3]:
        if not isinstance(change, dict):
            continue
        path = str(change.get("path") or "")
        kind = str(change.get("kind") or "")
        parts.append(f"{path}:{kind}" if kind else path)
    return "changes=" + ",".join(parts)


def _session_tool_summary(payload: dict[str, Any]) -> str:
    if payload.get("type") == "function_call":
        raw = payload.get("arguments") or ""
        try:
            args = json.loads(raw)
        except (TypeError, json.JSONDecodeError):
            return str(raw)[:160]
        if isinstance(args, dict):
            if "cmd" in args:
                return f"cmd={str(args['cmd'])[:160]}"
            return ",".join(list(args.keys())[:4])
    return str(payload.get("input") or "")[:160]


class CodexAdapter(HarnessAdapter):
    name = "codex"
    version = "0.136.0"

    def env(self, secrets: dict, model_snapshot: str) -> dict:
        return {
            "HOME": str(paths.LAB_HOME),
            "PATH": f"{paths.LAB_BIN}:" + os.environ.get("PATH", ""),
            "OPENAI_API_KEY": secrets["OPENAI_API_KEY"],
        }

    def command(self, prompt: str, model_snapshot: str, provider: str) -> list[str]:
        return [
            str(paths.LAB_BIN / "codex"),
            "exec",
            "--skip-git-repo-check",
            "--dangerously-bypass-approvals-and-sandbox",
            "--json",
            prompt,
        ]

    def raw_artifacts(self, workdir: Path) -> dict[str, Path]:
        arts: dict[str, Path] = {}
        for name in ("codex.log", "codex.smoke.log"):
            p = workdir / name
            if p.exists():
                arts["stdout_jsonl"] = p
                break

        local_sessions = [
            workdir / "codex.session.jsonl",
            workdir / "trace.session.jsonl",
            *sorted(workdir.glob("rollout-*.jsonl")),
        ]
        for p in local_sessions:
            if p.exists():
                arts["session_jsonl"] = p
                return arts

        if _safe_rel_to(workdir, paths.LAB):
            latest = _latest_rollout()
            if latest is not None:
                arts["session_jsonl"] = latest
        return arts

    def normalize(self, workdir: Path) -> dict:
        arts = self.raw_artifacts(workdir)
        tool_calls: list[dict[str, Any]] = []
        reasoning_steps: list[dict[str, Any]] = []
        tokens = {"input": None, "cached_input": None, "output": None}
        turns = 0
        system_present = False
        context_window_tokens = None
        reasoning_tokens = None

        stdout = arts.get("stdout_jsonl")
        if stdout:
            step = 0
            for rec in _jsonl(stdout):
                typ = rec.get("type")
                if typ == "turn.started":
                    turns += 1
                elif typ == "item.completed":
                    item = rec.get("item") or {}
                    item_type = item.get("type")
                    if item_type == "command_execution":
                        step += 1
                        tool_calls.append({
                            "step": step,
                            "tool_name": "command_execution",
                            "args_summary": _summarize_command(item),
                            "ts": None,
                        })
                    elif item_type == "file_change":
                        step += 1
                        tool_calls.append({
                            "step": step,
                            "tool_name": "file_change",
                            "args_summary": _summarize_file_change(item),
                            "ts": None,
                        })
                elif typ == "turn.completed":
                    usage = rec.get("usage") or {}
                    tokens["input"] = usage.get("input_tokens")
                    tokens["cached_input"] = usage.get("cached_input_tokens")
                    tokens["output"] = usage.get("output_tokens")
                    reasoning_tokens = usage.get("reasoning_output_tokens")

        session = arts.get("session_jsonl")
        if session:
            session_step = 0
            for rec in _jsonl(session):
                typ = rec.get("type")
                payload = rec.get("payload") or {}
                if typ == "session_meta":
                    base = payload.get("base_instructions") or {}
                    system_present = bool(base.get("text"))
                elif typ == "turn_context":
                    context_window_tokens = context_window_tokens or payload.get("model_context_window")
                elif typ == "event_msg":
                    ptyp = payload.get("type")
                    if ptyp == "task_started":
                        context_window_tokens = context_window_tokens or payload.get("model_context_window")
                        if turns == 0:
                            turns = 1
                    elif ptyp == "token_count":
                        info = payload.get("info") or {}
                        total = info.get("total_token_usage") or {}
                        context_window_tokens = context_window_tokens or info.get("model_context_window")
                        tokens["input"] = tokens["input"] if tokens["input"] is not None else total.get("input_tokens")
                        tokens["cached_input"] = (
                            tokens["cached_input"]
                            if tokens["cached_input"] is not None
                            else total.get("cached_input_tokens")
                        )
                        tokens["output"] = tokens["output"] if tokens["output"] is not None else total.get("output_tokens")
                        if reasoning_tokens is None:
                            reasoning_tokens = total.get("reasoning_output_tokens")
                elif typ == "response_item":
                    ptyp = payload.get("type")
                    if ptyp == "reasoning":
                        reasoning_steps.append({"type": "reasoning", "present": True, "ts": rec.get("timestamp")})
                    elif not tool_calls and ptyp in {"function_call", "custom_tool_call"}:
                        session_step += 1
                        tool_calls.append({
                            "step": session_step,
                            "tool_name": payload.get("name") or ptyp,
                            "args_summary": _session_tool_summary(payload),
                            "ts": rec.get("timestamp"),
                        })

        if reasoning_tokens:
            reasoning_steps.append({"type": "reasoning_tokens", "tokens": reasoning_tokens})

        return {
            "tool_calls": tool_calls,
            "reasoning_steps": reasoning_steps,
            "decision_points": [],
            "tokens": tokens,
            "turns": turns or None,
            "runtime_budget": {
                "max_output_tokens": None,
                "thinking_budget_tokens": None,
                "context_window_tokens": context_window_tokens,
                "effort_source": "$LAB_HOME/.codex/config.toml reasoning_effort=high",
            },
            "system_present": system_present,
            "evidence_levels": {
                "tool_calls": "direct",
                "system_present": "source-derived" if session else "unknown",
                "reasoning_steps": "direct" if reasoning_steps else "unknown",
                "tokens": "direct" if any(v is not None for v in tokens.values()) else "unknown",
            },
        }
