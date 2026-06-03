"""Plaintext private audit summaries for full local/VPS records.

The committed trace JSON remains a sanitized summary. This module writes a
non-committed Markdown companion under /data/harness-lab/private-audits with
tool inputs/outputs, visible agent messages, errors, and raw artifact paths.

Claude/Anthropic thinking deltas are deliberately not transcribed. The audit
records presence/count and uses visible messages plus tool behavior instead.
"""
from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any, Iterable


MAX_TEXT = 6000


def _clip(value: Any, limit: int = MAX_TEXT) -> str:
    text = "" if value is None else str(value)
    text = text.replace("\r", "")
    if len(text) > limit:
        return text[:limit] + f"\n...[truncated {len(text) - limit} chars]"
    return text


def _one_line(value: Any, limit: int = 220) -> str:
    text = re.sub(r"\s+", " ", _clip(value, limit)).strip()
    return text


def _jsonl(path: str | None) -> Iterable[dict[str, Any]]:
    if not path:
        return
    p = Path(path)
    if not p.exists():
        return
    for line in p.read_text(errors="replace").splitlines():
        line = line.strip()
        if not line:
            continue
        try:
            yield json.loads(line)
        except json.JSONDecodeError:
            continue


def _fenced(text: Any, lang: str = "text") -> list[str]:
    return [f"```{lang}", _clip(text), "```"]


def _parse_claude_sse(body_raw: str) -> list[dict[str, Any]]:
    blocks: dict[int, dict[str, Any]] = {}
    order: list[int] = []
    for line in body_raw.splitlines():
        if not line.startswith("data:"):
            continue
        payload = line[len("data:"):].strip()
        if not payload or payload == "[DONE]":
            continue
        try:
            ev = json.loads(payload)
        except json.JSONDecodeError:
            continue
        typ = ev.get("type")
        if typ == "content_block_start":
            idx = ev.get("index")
            cb = ev.get("content_block") or {}
            blocks[idx] = {
                "type": cb.get("type"),
                "id": cb.get("id"),
                "name": cb.get("name"),
                "text": "",
                "input_json": "",
            }
            order.append(idx)
        elif typ == "content_block_delta":
            idx = ev.get("index")
            if idx not in blocks:
                continue
            delta = ev.get("delta") or {}
            dtyp = delta.get("type")
            if dtyp == "text_delta":
                blocks[idx]["text"] += delta.get("text", "")
            elif dtyp == "input_json_delta":
                blocks[idx]["input_json"] += delta.get("partial_json", "")
            elif dtyp in {"thinking_delta", "signature_delta"}:
                continue
    return [blocks[idx] for idx in order]


def _claude_sections(trace_jsonl: str | None) -> list[str]:
    if not trace_jsonl:
        return ["No Claude trace JSONL artifact was saved."]

    texts: list[str] = []
    calls: list[dict[str, Any]] = []
    results: dict[str, dict[str, Any]] = {}
    thinking_blocks = 0
    tool_surface: set[str] = set()

    for rec in _jsonl(trace_jsonl):
        req = rec.get("request") or {}
        if "/v1/messages" not in str(req.get("url") or ""):
            continue
        body = req.get("body") or {}
        for tool in body.get("tools") or []:
            if isinstance(tool, dict) and tool.get("name"):
                tool_surface.add(str(tool["name"]))
        messages = body.get("messages") or []
        if messages:
            last = messages[-1]
            if last.get("role") == "user" and isinstance(last.get("content"), list):
                for block in last["content"]:
                    if block.get("type") == "tool_result":
                        results[str(block.get("tool_use_id"))] = {
                            "is_error": bool(block.get("is_error")),
                            "content": block.get("content", ""),
                        }
        for block in _parse_claude_sse((rec.get("response") or {}).get("body_raw") or ""):
            if block["type"] == "thinking":
                thinking_blocks += 1
            elif block["type"] == "text" and block["text"].strip():
                texts.append(block["text"].strip())
            elif block["type"] == "tool_use":
                raw = block.get("input_json") or "{}"
                try:
                    inp = json.loads(raw)
                except json.JSONDecodeError:
                    inp = {"_raw": raw}
                calls.append({
                    "id": block.get("id"),
                    "tool": block.get("name"),
                    "input": inp,
                })

    lines = [
        "### Claude Code detailed timeline",
        "",
        f"- thinking blocks present: {thinking_blocks}",
        f"- available tool surface: {', '.join(sorted(tool_surface)) if tool_surface else 'unknown'}",
        "- hidden thinking text: omitted by policy",
        "",
    ]
    if texts:
        lines += ["#### Visible model messages", ""]
        for i, text in enumerate(texts, 1):
            lines += [f"{i}. {_one_line(text, 1200)}"]
        lines.append("")

    lines += ["#### Tool calls", ""]
    for i, call in enumerate(calls, 1):
        result = results.get(str(call.get("id"))) or {}
        status = "ERROR" if result.get("is_error") else "OK"
        lines += [
            f"{i}. `{call.get('tool')}`",
            "",
            "Input:",
            *_fenced(json.dumps(call.get("input"), ensure_ascii=False, indent=2), "json"),
            f"Result status: {status}",
            *_fenced(result.get("content", "")),
            "",
        ]
    return lines


def _codex_sections(stdout_jsonl: str | None, stderr_log: str | None) -> list[str]:
    if not stdout_jsonl:
        return ["No Codex stdout JSONL artifact was saved."]
    lines = ["### Codex detailed timeline", ""]
    step = 0
    for rec in _jsonl(stdout_jsonl):
        if rec.get("type") != "item.completed":
            continue
        item = rec.get("item") or {}
        typ = item.get("type")
        if typ == "agent_message":
            lines += ["Visible model message:", *_fenced(item.get("text", "")), ""]
        elif typ == "command_execution":
            step += 1
            lines += [
                f"{step}. `command_execution` exit={item.get('exit_code')} status={item.get('status')}",
                "Command:",
                *_fenced(item.get("command", "")),
                "Output:",
                *_fenced(item.get("aggregated_output", "")),
                "",
            ]
        elif typ == "file_change":
            step += 1
            changes = item.get("changes") or []
            lines += [
                f"{step}. `file_change` status={item.get('status')}",
                *_fenced(json.dumps(changes, ensure_ascii=False, indent=2), "json"),
                "",
            ]
    if stderr_log and Path(stderr_log).exists():
        err = Path(stderr_log).read_text(errors="replace").strip()
        if err:
            lines += ["#### Stderr", *_fenced(err), ""]
    return lines


def _opencode_sections(stdout_jsonl: str | None) -> list[str]:
    if not stdout_jsonl:
        return ["No OpenCode stdout JSONL artifact was saved."]
    lines = ["### OpenCode detailed timeline", ""]
    step = 0
    for rec in _jsonl(stdout_jsonl):
        typ = rec.get("type")
        part = rec.get("part") or {}
        if typ == "message" and part.get("text"):
            lines += ["Visible model message:", *_fenced(part.get("text", "")), ""]
        elif typ == "reasoning":
            lines += ["Reasoning marker: present (raw reasoning text omitted if provided).", ""]
        elif typ == "tool_use":
            step += 1
            state = part.get("state") or {}
            lines += [
                f"{step}. `{part.get('tool') or '?'}`",
                "Input:",
                *_fenced(json.dumps(state.get("input"), ensure_ascii=False, indent=2), "json"),
                "Output/state:",
                *_fenced(json.dumps(state, ensure_ascii=False, indent=2), "json"),
                "",
            ]
    return lines


def _hermes_sections(session_json: str | None, stdout_log: str | None) -> list[str]:
    lines = ["### Hermes detailed timeline", ""]
    if not session_json or not Path(session_json).exists():
        lines.append("No Hermes session JSON artifact was saved.")
    else:
        data = json.loads(Path(session_json).read_text(errors="replace"))
        lines += [
            f"- system prompt present: {bool(data.get('system_prompt'))}",
            f"- messages: {len(data.get('messages', []))}",
            "",
        ]
        step = 0
        for idx, msg in enumerate(data.get("messages", [])):
            if msg.get("role") == "assistant" and (
                msg.get("reasoning") or msg.get("reasoning_content") or msg.get("codex_reasoning_items")
            ):
                lines += [f"Assistant message {idx}: reasoning marker present; raw reasoning omitted.", ""]
            content = msg.get("content")
            if msg.get("role") == "assistant" and content:
                lines += [f"Assistant message {idx} visible content:", *_fenced(content), ""]
            for call in msg.get("tool_calls") or []:
                step += 1
                fn = call.get("function") or {}
                lines += [
                    f"{step}. `{fn.get('name') or '?'}`",
                    "Arguments:",
                    *_fenced(fn.get("arguments", "")),
                    "",
                ]
    if stdout_log and Path(stdout_log).exists():
        out = Path(stdout_log).read_text(errors="replace").strip()
        if out:
            lines += ["#### Stdout log", *_fenced(out), ""]
    return lines


def build_private_audit(trace: dict[str, Any]) -> str:
    raw_artifacts = trace.get("raw_artifacts") or {}
    lines = [
        f"# Private full run audit: {trace['run_id']}",
        "",
        "This plaintext file is intentionally not committed to git/GitHub.",
        "It is stored on the VPS/Mac private artifact layer for detailed replay.",
        "Secrets and raw hidden chain-of-thought must not be copied into committed docs.",
        "",
        "## Summary",
        "",
        f"- config: {trace['config_id']}",
        f"- harness: {trace['harness']} {trace.get('harness_version')}",
        f"- model: {trace.get('model')}",
        f"- task: {trace['task_id']} ({trace.get('task_category')})",
        f"- repeat: {trace['repeat_index']}",
        f"- timestamp: {trace.get('timestamp')}",
        f"- success: {trace.get('outcome', {}).get('success')}",
        f"- wall_time_s: {trace.get('wall_time_s')}",
        f"- raw_log_path: {trace.get('raw_log_path')}",
        "",
        "## Normalized tool sequence",
        "",
    ]
    for tc in trace.get("tool_calls") or []:
        lines.append(f"- {tc.get('step')}. `{tc.get('tool_name')}`: {tc.get('args_summary')}")
    lines += [
        "",
        "## Outcome",
        "",
        *_fenced(json.dumps(trace.get("outcome"), ensure_ascii=False, indent=2), "json"),
        "## Tokens / budget",
        "",
        *_fenced(json.dumps({
            "tokens": trace.get("tokens"),
            "runtime_budget": trace.get("runtime_budget"),
            "evidence_levels": trace.get("evidence_levels"),
        }, ensure_ascii=False, indent=2), "json"),
        "## Raw artifacts",
        "",
    ]
    for name, path in sorted(raw_artifacts.items()):
        lines.append(f"- `{name}`: `{path}`")
    lines.append("")

    harness = trace.get("harness")
    if harness == "claude_code":
        lines += _claude_sections(raw_artifacts.get("trace_jsonl"))
    elif harness == "codex":
        lines += _codex_sections(raw_artifacts.get("stdout_jsonl"), raw_artifacts.get("stderr_log"))
    elif harness == "opencode":
        lines += _opencode_sections(raw_artifacts.get("stdout_jsonl"))
    elif harness == "hermes":
        lines += _hermes_sections(raw_artifacts.get("session_json"), raw_artifacts.get("stdout_log"))
    else:
        lines.append(f"No detailed parser for harness={harness}.")

    return "\n".join(lines).rstrip() + "\n"
