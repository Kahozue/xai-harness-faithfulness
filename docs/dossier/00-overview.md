# Dossier 總覽

這組 dossier 是 Phase 0 的白箱入口文件，整理四個 coding-agent harness 在同一個最小 smoke 任務中可觀察到的 prompt、tools、agent loop、memory/state 與 trace 行為。目的不是評分模型好壞，也不是正式實驗；它是後續 M1-M4 分析前的 evidence map。

## 文件清單

| 文件 | 內容 |
| --- | --- |
| `claude-code.md` | Claude Code CLI 的 system prompt、工具定義、hook/state、trace 與 smoke 對照。 |
| `codex-cli.md` | OpenAI Codex CLI 的 base instructions、developer/env/user 注入、shell/edit 工具、session JSONL。 |
| `opencode.md` | OpenCode 的 provider/agent 設定、export trace、tool schema、Haiku/GPT mini smoke。 |
| `hermes.md` | Hermes Agent 的 prompt layers、tool registry、provider transports、memory injection、smoke trace。 |
| `hermes-memory.md` | Hermes SOUL、內建 memory、external provider、context compression 與收斂機制。 |
| `cross-harness-comparison.md` | 四 harness 的 white-box entrypoints 與 M1-M4 映射。 |

## 觀察原則

- 只使用既有 smoke、source、install/config scripts、session traces。
- 不讀取或引用 credential values、headers、API keys。
- production Hermes 只讀 source，不啟動、不重啟、不修改。
- UI 與文件輸出維持繁體中文。
- 每個 task 完成後獨立 commit/push，降低後續 review 的切片成本。

## 共用 smoke 任務

四個 harness 都以隔離 lab HOME 執行同型態 smoke：讓 agent 修正一個簡單 Python function，使 `add(a, b)` 回傳 `a + b`。這個任務刻意小到不測 benchmark，而是專注觀察：

- 模型看到的 system/developer/user/context 層。
- host 暴露哪些工具 schema。
- 模型是否直接用 edit/patch，或先 read/search。
- tool result 如何回到下一輪模型輸入。
- trace 是否保存 prompt、tool call、usage/reasoning tokens。

## 主要產物

| harness | smoke trace 類型 | 主要可觀察面 |
| --- | --- | --- |
| Claude Code | `.claude-trace` JSONL | system blocks、22 tools、`Read -> Edit`、model/usage；已用遠端 `@loki-zhou/claude-trace@1.0.4` 二次解析。 |
| Codex CLI | Codex session JSONL + stdout events | base instructions、developer/env/user items、`exec_command`/`apply_patch`、reasoning tokens。 |
| OpenCode | `opencode export` + stdout | agent/provider config、tool calls、provider usage、OpenCode system prompt 不完整可見。 |
| Hermes Agent | `session_*.json` | cached system prompt、18 tools、messages/tool_calls、provider/model/session metadata。 |

## 後續使用方式

- M1：把每個 harness 的 system prompt 來源、注入順序、可變層與 cache 行為對齊。
- M2：比較工具 schema 的來源、工具名稱、host-side guardrails、parallel/sequential execution。
- M3：比較 agent loop 如何處理 context pressure、retry、state persistence。
- M4：比較 trace 與模型可見輸入的差距，特別是 compression summary、memory fence、ephemeral context 與 hidden host decisions。

## 已知限制

- 這批文件不包含 formal experiment、統計結果或顯著性檢定。
- OpenCode export 沒有完整 system prompt，因此只能把 observable metadata 與 trace 行為分開記錄。
- Hermes request dumps 未引用內容，以免誤曝 credentials；session JSON 已足以完成本階段 mapping。
- Claude Code restored source 是安裝包層級的白箱 evidence，不等於 provider raw request dump。
