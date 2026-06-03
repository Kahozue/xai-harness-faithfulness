# Cross-Harness Comparison

本文件把 Claude Code、Codex CLI、OpenCode、Hermes Agent 的白箱證據放到同一張比較表，並標出 M1-M4 可以直接使用的 white-box entrypoints。

## white-box entrypoints

| harness | Prompt entrypoints | Tool entrypoints | Loop/state entrypoints | Trace entrypoints |
| --- | --- | --- | --- | --- |
| Claude Code | restored source `constants/prompts.ts`、main trace system blocks | restored source `tools.ts`、`Tool.ts`、`QueryEngine.ts` | `query.ts`、auto compact、memory dir handling | `.claude-trace/log-*.jsonl` |
| Codex CLI | session JSONL `base_instructions`、developer/env/user items | tool list in session JSONL：shell command 與 patch edit | exec event stream、sandbox/approval metadata、session state under `.codex` | `rollout-*.jsonl`、stdout command/file-change events |
| OpenCode | package + config + export metadata；full system prompt 未由 export 完整暴露 | exported tool calls、agent/provider config、tool enablement | `opencode run` stdout、session export、provider usage | `opencode export` output、`oc.log` |
| Hermes Agent | `run_agent.py` prompt builder、`prompt_builder.py`、`SOUL.md`、context files、memory snapshot | `model_tools.py` registry/toolset、external memory/context engine schemas | `run_agent.py` tool loop、provider transports、ContextCompressor、MemoryManager | lab `session_*.json` copied to `trace.session.json` |

## M1: prompt 與 instruction stack

| harness | M1 觀察點 |
| --- | --- |
| Claude Code | system prompt 是多個 blocks；trace 可見 tool-selection guidance、memory instructions、model/permission/env context。 |
| Codex CLI | session JSONL 開頭完整保存 base instructions，另有 developer instructions、environment context、user message，層次最清楚。 |
| OpenCode | export 可見 provider/agent/config 與 message flow，但 full system prompt 不完整；需把「不可見」視為資料缺口，而非假設不存在。 |
| Hermes Agent | system prompt 由 stable/context/volatile 三層組成；SOUL、context files、memory snapshot、timestamp/model/provider 都可能進入 prompt。 |

M1 建議欄位：

- prompt layer name
- source file or trace path
- injected order
- session-stable 或 per-call
- cache behavior
- raw visibility level：full、partial、metadata-only、not visible

## M2: tool schema、工具選擇與 host guardrails

| harness | M2 觀察點 |
| --- | --- |
| Claude Code | trace 中 22 tools，smoke 走 `Read -> Read -> Edit`；source 中 tool definitions 與 query engine 可對應。 |
| Codex CLI | 本次 smoke 可見 `exec_command` 與 `apply_patch`；工具少但 environment/sandbox metadata 很強。 |
| OpenCode | Haiku 走 `read -> edit`；GPT mini 走 `glob -> glob -> read -> apply_patch -> read`，同任務不同模型工具路徑差異明顯。 |
| Hermes Agent | 18 tools 由 registry/toolset 過濾；Haiku 走 `read_file -> patch`，GPT mini 走 `read_file + search_files -> patch`；host 只在安全條件下併行。 |

M2 建議欄位：

- model-visible tool name
- host handler location
- schema source
- selection reason 是否 trace-visible
- sequential/parallel execution decision
- tool result 是否完整回灌

## M3: loop、retry、state 與 compression

| harness | Loop model | State/compression 特徵 |
| --- | --- | --- |
| Claude Code | query engine 驅動，多工具 loop，trace 記錄 request/response/tool events | 有 memory dir、auto compact 與 session/permission context。 |
| Codex CLI | exec mode 以 session items 保存 reasoning、tool call、stdout/file change | session state under `.codex`；reasoning tokens 可見。 |
| OpenCode | `opencode run` 執行到完成，export 能回放 tool path | config/state 分散在 `.config`、`.cache`、`.local/share`；usage 可見但 full prompt 受限。 |
| Hermes Agent | `run_conversation()` 迴圈直到 tool calls 結束或 budget/retry/compression 介入 | cached system prompt、MemoryManager、ContextCompressor；context pressure 會旋轉 session id 並寫 continuation lineage。 |

M3 在本階段只做機制整理，不下性能或可靠性結論。正式實驗前要先固定：同一 workspace、同一 prompt、同一模型、同一工具啟用面、同一 timeout/retry policy。

## M4: faithfulness 與 trace 可見性

| harness | Trace 對模型可見輸入的保真度 | 風險 |
| --- | --- | --- |
| Claude Code | trace 對 system blocks、tools、tool calls 可見度高 | restored source 與 runtime raw request 仍需分開；trace snippet 不應含 secrets。 |
| Codex CLI | session JSONL 對 instructions/items/tool events 很完整 | stdout event 與 JSONL 需合併讀，否則可能漏 file-change context。 |
| OpenCode | tool path 與 usage 可見，system prompt 不完整 | 不能把 export 沒顯示的 prompt 當成模型沒收到。 |
| Hermes Agent | session JSON 有 cached system prompt、tools、messages；source 可補足 injection rules | external memory prefetch 以 fenced user-message context 注入，UI scrubber 不代表模型沒看到；compression summary 會成為新的模型輸入。 |

M4 建議把 evidence 分成四級：

- Direct：trace 直接保存該 input 或 tool call。
- Source-derived：source 明確表示 runtime 會建出該 input。
- Inferred：由 config/source/trace 組合推論，但 raw payload 不可見。
- Unknown：目前資料不能確認。

## 機制差異摘要

| 面向 | Claude Code | Codex CLI | OpenCode | Hermes Agent |
| --- | --- | --- | --- | --- |
| prompt visibility | 高 | 高 | 中低 | 高 |
| tool schema visibility | 高 | 高 | 中 | 高 |
| host loop visibility | 中高 | 高 | 中 | 高 |
| memory visibility | 中 | 中 | 中 | 高，尤其 Hermes memory 章 |
| compression visibility | 中 | 低到中 | 低 | 高 |
| smoke tool diversity | 低到中 | 低 | 中 | 中 |
| provider abstraction | Anthropic-centered CLI | OpenAI Codex CLI | multi-provider | multi-provider transports |

## 結論

四個 harness 都能在 smoke 中完成簡單修補，但可解釋性資料面不同。Claude Code 與 Codex CLI 的 trace 對 instruction stack 較直接；OpenCode 對 tool path 可觀察但 prompt 有缺口；Hermes 的 source-level observability 最完整，尤其 memory、provider transport、compression 與 session lineage。後續 M1-M4 應避免把「trace 不可見」與「模型未接收」混為一談，並在比較表中明確標註 evidence level。
