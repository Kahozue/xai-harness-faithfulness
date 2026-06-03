"""Claude Code 2.1.88 介面卡：經 claude-trace 攔截 API 流量。

claude-trace 1.0.4 的 .claude-trace/*.jsonl 每行一筆：
  {request:{method,url,body:{model,max_tokens,thinking,system,tools,messages}},
   response:{status_code, body_raw:<SSE 串流字串>}, logged_at}
tool 序列＝response.body_raw（SSE）中的 content_block_start(type=tool_use) 事件，依序。
usage 在 SSE 的 message_start / message_delta。budgets 在 request.body。"""
from __future__ import annotations
import json
import os
from pathlib import Path
from runner import paths
from runner.adapters.base import HarnessAdapter


def _parse_sse(body_raw: str):
    """解析一段 Anthropic SSE 串流，回傳 (blocks, order, usage)。"""
    blocks: dict = {}
    order: list = []
    usage = {"input": None, "output": None, "cached_input": None}
    for line in body_raw.splitlines():
        line = line.strip()
        if not line.startswith("data:"):
            continue
        payload = line[len("data:"):].strip()
        if not payload or payload == "[DONE]":
            continue
        try:
            ev = json.loads(payload)
        except json.JSONDecodeError:
            continue
        t = ev.get("type")
        if t == "message_start":
            u = (ev.get("message") or {}).get("usage") or {}
            if u.get("input_tokens") is not None:
                usage["input"] = u.get("input_tokens")
            if u.get("cache_read_input_tokens") is not None:
                usage["cached_input"] = u.get("cache_read_input_tokens")
        elif t == "content_block_start":
            idx = ev.get("index")
            cb = ev.get("content_block") or {}
            blocks[idx] = {"type": cb.get("type"), "name": cb.get("name"), "parts": []}
            order.append(idx)
        elif t == "content_block_delta":
            idx = ev.get("index")
            d = ev.get("delta") or {}
            if d.get("type") == "input_json_delta" and idx in blocks:
                blocks[idx]["parts"].append(d.get("partial_json", ""))
        elif t == "message_delta":
            u = ev.get("usage") or {}
            if u.get("output_tokens") is not None:
                usage["output"] = u.get("output_tokens")
    return blocks, order, usage


def _summ_parts(parts: list[str]) -> str:
    raw = "".join(parts)
    if not raw:
        return ""
    try:
        inp = json.loads(raw)
    except json.JSONDecodeError:
        return raw[:80]
    if isinstance(inp, dict):
        for k in ("file_path", "path", "command", "pattern", "old_string"):
            if k in inp:
                return f"{k}={str(inp[k])[:80]}"
        return ",".join(list(inp.keys())[:4])
    return str(inp)[:80]


class ClaudeCodeAdapter(HarnessAdapter):
    name = "claude_code"
    version = "2.1.88"

    def env(self, secrets: dict, model_snapshot: str) -> dict:
        return {
            "HOME": str(paths.LAB_HOME),
            "PATH": f"{paths.LAB_BIN}:" + os.environ.get("PATH", ""),
            "ANTHROPIC_API_KEY": secrets["ANTHROPIC_API_KEY"],
            "CLAUDE_CODE_EFFORT_LEVEL": "high",
            "CLAUDE_CODE_MAX_OUTPUT_TOKENS": "64000",
            "MAX_THINKING_TOKENS": "63999",
        }

    def command(self, prompt: str, model_snapshot: str, provider: str) -> list[str]:
        return [
            str(paths.LAB_BIN / "claude-trace"), "--include-all-requests", "--run-with",
            "-p", prompt, "--model", model_snapshot,
            "--effort", "high", "--permission-mode", "acceptEdits",
        ]

    def raw_artifacts(self, workdir: Path) -> dict[str, Path]:
        td = workdir / ".claude-trace"
        jsonls = sorted(td.glob("*.jsonl")) if td.exists() else []
        return {"trace_jsonl": jsonls[-1]} if jsonls else {}

    def normalize(self, workdir: Path) -> dict:
        arts = self.raw_artifacts(workdir)
        tool_calls, reasoning_steps = [], []
        max_tokens = thinking_budget = None
        system_present = False
        in_tok = out_tok = cached = None
        turns = 0
        step = 0
        if "trace_jsonl" in arts:
            for line in arts["trace_jsonl"].read_text().splitlines():
                line = line.strip()
                if not line:
                    continue
                try:
                    rec = json.loads(line)
                except json.JSONDecodeError:
                    continue
                body = (rec.get("request") or {}).get("body")
                if isinstance(body, dict) and body.get("model"):
                    turns += 1
                    if max_tokens is None:
                        max_tokens = body.get("max_tokens")
                    th = body.get("thinking") or {}
                    if thinking_budget is None:
                        thinking_budget = th.get("budget_tokens")
                    if body.get("system"):
                        system_present = True
                braw = (rec.get("response") or {}).get("body_raw") or ""
                if not braw:
                    continue
                blocks, order, usage = _parse_sse(braw)
                if usage["input"] is not None:
                    in_tok = usage["input"]
                if usage["cached_input"] is not None:
                    cached = usage["cached_input"]
                if usage["output"] is not None:
                    out_tok = (out_tok or 0) + usage["output"]
                for idx in order:
                    blk = blocks[idx]
                    if blk["type"] == "tool_use":
                        step += 1
                        tool_calls.append({
                            "step": step, "tool_name": blk.get("name") or "?",
                            "args_summary": _summ_parts(blk["parts"]), "ts": None,
                        })
                    elif blk["type"] == "thinking":
                        reasoning_steps.append({"type": "thinking", "present": True})
        return {
            "tool_calls": tool_calls,
            "reasoning_steps": reasoning_steps,
            "decision_points": [],
            "tokens": {"input": in_tok, "cached_input": cached, "output": out_tok},
            "turns": turns,
            "runtime_budget": {
                "max_output_tokens": max_tokens, "thinking_budget_tokens": thinking_budget,
                "context_window_tokens": 200000, "effort_source": "cli --effort high + env budgets",
            },
            "system_present": system_present,
            "evidence_levels": {"tool_calls": "direct", "system_present": "direct",
                                "reasoning_steps": "direct", "tokens": "direct"},
        }
