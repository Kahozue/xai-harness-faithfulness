# Hermes Agent 機制 dossier

本章目標是把 Hermes 在本次 smoke 中「模型到底看見什麼、如何決定工具、loop 如何收斂」整理成可交叉比較的白箱資料。證據只取自 lab 隔離安裝、來源碼與 smoke session JSON；未啟動或重啟 production `/data/hermes-agent`。

## 觀察範圍

- production source（只讀）：`/data/hermes-agent`
- lab home：`/data/harness-lab/home/.hermes`
- lab smoke：`/data/harness-lab/smoke/hermes-haiku`、`/data/harness-lab/smoke/hermes-gptmini`
- harness repo：`/data/repos/xai-harness-faithfulness`

`infra/install-hermes-clean.sh` 把 `HOME` 與 `HERMES_HOME` 指到 lab sandbox，並寫入 lab 專用 `config.yaml`；腳本明確以 clean isolated Hermes 取樣，不讀 `/home/opc/.hermes`。`infra/smoke/smoke-hermes.sh` 使用 production binary 路徑，但同樣以 lab `HOME/HERMES_HOME` 執行，且把最新 `session_*.json` 複製成 trace。

## system prompt 組裝

Hermes 的 system prompt 不是單一硬編碼字串，而是 `run_agent.py` 透過 `agent/prompt_builder.py` 建出多層 prompt：

1. `stable` 層：`SOUL.md` 或預設 identity、Hermes help guidance、memory/session/skills guidance、工具使用 enforcement、skills index、environment hints、platform hints。
2. `context` 層：caller-supplied `system_message` 與 cwd context files，例如 `AGENTS.md`、`.cursorrules`、`.hermes.md`、`HERMES.md`。
3. `volatile` 層：`MEMORY.md`、`USER.md`、external memory provider block、conversation timestamp、session id、model、provider。

來源依據：

- `agent/prompt_builder.py:134-142` 定義預設 Hermes identity。
- `agent/prompt_builder.py:150-170` 定義 memory guidance，要求記憶為 compact durable facts，避免存短期任務進度。
- `run_agent.py:5804-5820` 把 prompt parts 分成 stable/context/volatile，並註明為了 prefix cache，session 內不重繪。
- `run_agent.py:5825-5838` 優先載入 `SOUL.md`，否則使用預設 identity。
- `run_agent.py:5842-5857` 依可用工具追加 memory、session_search、skills、kanban guidance。
- `run_agent.py:5953-5970` 載入 cwd context files。
- `run_agent.py:5972-6004` 注入 memory/user/external memory/timestamp/model/provider。
- `run_agent.py:6012-6029` 將三層合併成單一 system prompt。

在 smoke trace 中可觀察到：

| run | model | provider host | system prompt 長度 | message count |
| --- | --- | --- | ---: | ---: |
| Hermes Haiku | `claude-haiku-4-5-20251001` | `api.anthropic.com` | 3,477 chars | 6 |
| Hermes GPT mini | `gpt-5.4-mini-2026-03-17` | `api.openai.com` | 6,996 chars | 7 |

兩個 trace 的 prompt 開頭皆為預設 Hermes identity。GPT mini 較長，原因是 OpenAI/GPT execution guidance 會依 model family 追加，Haiku 走 Anthropic messages transport，不會追加同一塊 GPT guidance。

## 工具選擇

Hermes 工具 surface 由 `model_tools.py` 和 tool registry 組合而成：

- `model_tools.py:180-199` import built-in tools 與 plugins，讓各 tool module 以 registry 自註冊。
- `model_tools.py:271-332` 提供 `get_tool_definitions()`，支援 quiet-mode cache，避免 gateway 長期程序累積重複 schema。
- `model_tools.py:335-390` 依 enabled/disabled toolsets 決定可見工具，並由 registry 回傳通過 `check_fn` 的 schema。
- `run_agent.py:1832-1845` 在 `AIAgent.__init__` 載入工具並記錄 `valid_tool_names`。
- `run_agent.py:2050-2069` 將 external memory provider 的 tool schemas 加到同一個 tool surface，並用名稱去重。
- `run_agent.py:2340-2355` 同樣把 context engine tool schemas 加入 tool surface。

本次 lab config 啟用 `toolsets: hermes-cli`，兩個 Hermes smoke trace 都有 18 個工具 schema。Trace 中可見的工具名稱包含檔案、terminal、patch、search、session recall、memory、skills、clarify、delegate、vision、speech、image 等；任務清單工具也在 schema 中，但本文件刻意以描述代稱，避免佔位字掃描器把工具名誤判成未完成標記。

工具選擇在模型側發生，但 Hermes 在 host 側加上幾個控制點：

- `run_agent.py:328-355` 定義不可併行、可併行讀取、path-scoped 工具與最大 worker 數。
- `run_agent.py:392-433` 只在工具 batch 安全時併行。
- `run_agent.py:10452-10471` 依 batch 安全性走 sequential 或 concurrent tool execution。
- `run_agent.py:10494-10579` agent-level 工具先在 agent loop 內處理；其他工具才交給 registry `handle_function_call()`。
- `model_tools.py:697-805` dispatch 前會做參數 coercion、plugin pre-hook、registry dispatch、post hook 與 latency metadata。

## planning 與 loop

Hermes 的 planning 不是獨立 planner step；它表現在 system guidance、任務清單工具、skills guidance，以及 tool-calling loop 的反覆呼叫中。`run_agent.py:11679-11706` 定義 `run_conversation()`：輸入 user message、system override、history，回傳 final response、messages、api call count 等。

主要 loop：

1. `run_agent.py:11822-11890` 複製 history、hydrate session state，加入本輪 user message。
2. `run_agent.py:11898-11948` 首輪建立或沿用 cached system prompt；continuing session 會從 session DB 拿先前 prompt snapshot，避免 prefix cache 破掉。
3. `run_agent.py:11950-12017` preflight 粗估 system + messages + tool schemas token，超過 compression threshold 就先濃縮。
4. `run_agent.py:12089-12110` external memory provider 在 tool loop 前 prefetch 一次，結果 cache 起來，不會每次工具呼叫重查。
5. `run_agent.py:12256-12320` 建 API messages；external memory context 與 plugin user context 只注入本輪 user message，不改 system prompt。
6. `run_agent.py:12329-12340` 對 Anthropic 相關 provider 套用 prompt cache control。
7. `run_agent.py:12498-12528` 建 provider-specific API kwargs，必要時 dump request debug。
8. `run_agent.py:12549-12578` 優先走 streaming path，讓 stale-stream timeout 能生效。
9. `run_agent.py:13030-13158` 正規化 usage，更新 context compressor token 狀態與 session usage。
10. 若 assistant 回傳 tool calls，`run_agent.py:10452-10579` 執行工具並把 tool result 追加回 messages；若無 tool calls，收斂成 final response。

Hermes 對 provider 的 API shape 有 transport 層：

- `run_agent.py:9443-9467` Anthropic messages path 會把 OpenAI-style messages/tools 轉為 Anthropic kwargs。
- `agent/transports/anthropic.py:41-78` 呼叫 `build_anthropic_kwargs()`，並轉換 tool schemas。
- `agent/transports/anthropic.py:80-131` 把 text、thinking、tool_use blocks 正規化回 Hermes loop 的 `NormalizedResponse`。
- `run_agent.py:9513-9645` chat completions path 依 provider profile 或 legacy flags 建 kwargs。
- `agent/transports/chat_completions.py:160-220` 建 chat.completions kwargs；messages/tools 基本保持 OpenAI 格式，但會移除 strict providers 不接受的 Codex Responses fields。

## memory 進入模型的位置

Hermes 有兩層 memory：

1. 內建 curated memory：`MEMORY.md` 與 `USER.md`。它們在 session start 讀入，變成 system prompt snapshot。
2. external memory provider：透過 provider lifecycle 提供 system prompt block、prefetch context、sync、tool schemas、session switch hooks。

內建 memory：

- `tools/memory_tool.py:5-14` 說明 `MEMORY.md`/`USER.md` 是 file-backed persistent memory，session 中 snapshot 固定，mid-session writes 只更新檔案，不改 system prompt。
- `tools/memory_tool.py:118-124` 建立 live entries 與 frozen system prompt snapshot。
- `tools/memory_tool.py:126-142` load from disk 並 capture snapshot。
- `tools/memory_tool.py:361-372` system prompt 只讀 frozen snapshot。
- `tools/memory_tool.py:515-564` 定義 `memory` tool schema。

External provider：

- `agent/memory_provider.py:15-22` 定義 initialize、system_prompt_block、prefetch、sync_turn、get_tool_schemas、handle_tool_call、shutdown lifecycle。
- `agent/memory_provider.py:24-30` 定義可選 hooks：turn start、session end、session switch、pre-compress、memory write、delegation。
- `agent/memory_manager.py:190-249` 管理 provider 註冊，且只允許一個 external provider。
- `agent/memory_manager.py:285-302` 每輪 prefetch 合併 provider context。
- `agent/memory_manager.py:317-327` completed turn 會 sync 到 provider。
- `agent/memory_manager.py:438-455` compression 前 provider 可提供要保存到摘要的內容。

External memory prefetch 的注入不是 system prompt：`run_agent.py:12260-12277` 把 fenced memory context 附在本輪 user message API copy 後面；`messages` 原物件不被 mutate，不落 session persistence。

## smoke trace 對照

Haiku trace：

- session id：`20260603_210107_4071fe`
- model：`claude-haiku-4-5-20251001`
- provider host：`api.anthropic.com`
- tools count：18
- visible sequence：`read_file -> patch`
- final：修正完成

GPT mini trace：

- session id：`20260603_210118_a1b06e`
- model：`gpt-5.4-mini-2026-03-17`
- provider host：`api.openai.com`
- tools count：18
- visible sequence：`read_file + search_files -> patch`
- final：修正完成

兩者同樣在 lab sandbox 編輯同一型態的 `hello.py`，但工具路徑不同：Haiku 先讀檔再直接 patch；GPT mini 同一輪同時讀檔與搜尋，下一輪 patch。這表示 Hermes host 固定提供相同工具 surface，但工具選擇與 batch 組合由模型輸出決定，host 只負責安全調度與結果回灌。

## 可觀察限制

- session JSON 有 system prompt、tools、messages，但不是 provider raw HTTP payload。
- lab request dumps 存在於 isolated `$HERMES_HOME/sessions/request_dump_*.json` 時可做更細核對；本章不引用 dump 內容，以免誤曝 headers 或 credentials。
- 沒有 formal experiment；本章只總結既有 smoke 與來源碼白箱路徑。
- production Hermes 僅讀取來源碼，未做 process 操作。
