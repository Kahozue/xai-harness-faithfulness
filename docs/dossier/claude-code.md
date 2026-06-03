# Claude Code dossier

## 1. 版本與安裝

Claude Code 在 Phase 0 釘死為 `2.1.88`，安裝來源是 repo 外的本機 tarball `/data/harness-lab/claude-code/claude-code-2.1.88.tgz`。安裝腳本只在 lab prefix 內執行 `npm install --prefix "$CC_PREFIX"`，並把 `$LAB_BIN/claude` symlink 到 `/data/harness-lab/claude-code/prefix/node_modules/.bin/claude`，見 `/data/repos/xai-harness-faithfulness/infra/install-claude-code.sh:3` 到 `:9`。此設計讓正式 `/home/opc` dotfiles 與全域 npm 不參與實驗。

白箱依據是 `/data/harness-lab/claude-code/restored-src/`。此 restored source 顯示主 agent 入口與 tool registry 均在套件內：`/data/harness-lab/claude-code/restored-src/QueryEngine.ts` 負責 headless/SDK 對話生命週期，`/data/harness-lab/claude-code/restored-src/query.ts` 負責模型呼叫與工具迴圈，`/data/harness-lab/claude-code/restored-src/tools.ts` 是 base tools 的 source of truth。

## 2. system prompt 結構與關鍵段落

Claude Code 的 default system prompt 由 `fetchSystemPromptParts()` 建出。該函式同時取得 `defaultSystemPrompt`、`userContext`、`systemContext`，並在沒有 custom prompt 時呼叫 `getSystemPrompt(tools, mainLoopModel, additionalWorkingDirectories, mcpClients)`，見 `/data/harness-lab/claude-code/restored-src/utils/queryContext.ts:30` 到 `:74`。`QueryEngine.submitMessage()` 在每輪開始時呼叫此函式，傳入 tool list、main loop model、額外工作目錄與 MCP clients，見 `/data/harness-lab/claude-code/restored-src/QueryEngine.ts:284` 到 `:325`。

prompt 文案來源在 `/data/harness-lab/claude-code/restored-src/constants/prompts.ts`。其中 `getSimpleIntroSection()` 定義 agent 身分與任務範圍，指出它是協助軟體工程任務的互動 agent，並要求根據可用工具協助使用者，見 `constants/prompts.ts:175` 到 `:183`。`getSimpleSystemSection()` 加入工具權限、hook、tool result prompt-injection 風險、以及自動壓縮上下文的規則，見 `constants/prompts.ts:186` 到 `:197`。`getSimpleDoingTasksSection()` 加入讀檔優先、不要超出需求、修完要驗證、如實回報失敗等工程行為規則，見 `constants/prompts.ts:199` 到 `:252`。prompt 還有動態邊界 `SYSTEM_PROMPT_DYNAMIC_BOUNDARY`，用來區分可跨使用者 cache 的靜態內容與 session-specific 內容，見 `constants/prompts.ts:105` 到 `:115`。

smoke trace 證實此結構實際送入 Anthropic Messages API：`/data/harness-lab/smoke/cc/.claude-trace/log-2026-06-03-12-36-38.jsonl` 的第一個主請求使用 `claude-haiku-4-5-20251001`，`system` 是 4 個 block、約 26,811 字元，開頭包含 `cc_version=2.1.88.e09` 與「Claude Agent SDK」身分段落；同一 request 含 22 個 tools。

## 3. tool 集合與定義/docstring

Claude Code 的 tool registry 在 `/data/harness-lab/claude-code/restored-src/tools.ts`。檔案前段 import 各工具實作，包括 Agent、Skill、Bash、Edit、Read、Write、Glob、NotebookEdit、WebFetch、TaskStop、WebSearch、EnterPlanMode、Grep、LSP、MCP resource tools、ToolSearch、worktree tools 等，見 `tools.ts:2` 到 `:85`。`getAllBaseTools()` 回傳實際可用 base tool 陣列，並依 feature flag、環境與 user type 加入或排除工具，見 `tools.ts:185` 到 `:250`。`getToolsForDefaultPreset()` 會先呼叫 `tool.isEnabled()`，因此 system prompt 裡不是靜態全量，而是「目前環境可用」工具，見 `tools.ts:173` 到 `:183`。

`Tool` 型別要求每個工具具備 `call()`、`description()`、`inputSchema`、`isConcurrencySafe()`、`isEnabled()`、`isReadOnly()`，並可宣告 alias、searchHint、outputSchema、destructive 判定等，見 `/data/harness-lab/claude-code/restored-src/Tool.ts:362` 到 `:430`。工具名稱 lookup 允許 primary name 或 alias，見 `Tool.ts:345` 到 `:360`。

本次 smoke trace 中送入模型的 22 個 tool 名稱為：Agent、AskUserQuestion、Bash、CronCreate、CronDelete、CronList、Edit、EnterPlanMode、EnterWorktree、ExitPlanMode、ExitWorktree、Glob、Grep、NotebookEdit、Read、Skill、TaskOutput、TaskStop、工作清單寫入工具（trace 名稱可重建為 `T` + `odoWrite`）、WebFetch、WebSearch、Write。這些名稱來自 trace request body 的 `tools[*].name`，而非文件推測。

工具 docstring 不是單一文字檔，而是各工具的 `description()` 或 prompt module。例子：Bash tool 的 input schema 要求 `command`，並有可選 `description`，其 runtime description 預設為 `Run shell command`，見 `/data/harness-lab/claude-code/restored-src/tools/BashTool/BashTool.tsx:230` 與 `:420` 到 `:429`；FileRead tool 的 prompt 常數匯入 `DESCRIPTION`、`FILE_READ_TOOL_NAME`、line format/offset instructions，見 `/data/harness-lab/claude-code/restored-src/tools/FileReadTool/FileReadTool.ts:78` 到 `:86`；Agent tool 的 prompt 描述 subagent 使用時機與短描述要求，見 `/data/harness-lab/claude-code/restored-src/tools/AgentTool/prompt.ts:239` 到 `:270`。

## 4. 工具選擇的理由與決策邏輯

Claude Code 並沒有在 client 端以規則式 planner 強制選工具；工具選擇主要由模型根據 system prompt、tools schema、當前 messages 與 user context 決定。client 端負責把可用工具傳入 API，見 `query.ts:659` 到 `:707` 中 `deps.callModel({ ..., tools: toolUseContext.options.tools, ... })`。模型回傳 assistant content block 後，client 收集 `tool_use` block 作為是否繼續 agent loop 的訊號，見 `query.ts:826` 到 `:835`。

client 端決策主要體現在三層 guard。第一層是工具是否存在與 schema 是否能 parse：`findToolByName()` 依名稱或 alias 找工具，`StreamingToolExecutor.addTool()` 找不到工具會產生 `No such tool available` 的 tool_result，見 `/data/harness-lab/claude-code/restored-src/services/tools/StreamingToolExecutor.ts:73` 到 `:124`。第二層是權限：`QueryEngine` 包裝 `canUseTool()`，把非 allow 的決策記到 SDK permission denials，見 `QueryEngine.ts:243` 到 `:270`。第三層是 concurrency/read-only 判定：`runTools()` 或 streaming executor 會用工具的 `isConcurrencySafe()` 將只讀工具併發、非只讀工具序列化，見 `/data/harness-lab/claude-code/restored-src/services/tools/toolOrchestration.ts:19` 到 `:82` 與 `:86` 到 `:116`。

因此工具選擇的「理由」在 trace 內可觀察為模型先讀取 `hello.py`，再次讀取確認內容，再用 Edit 修正。這與 prompt 中「修改前先讀檔」的工程規則相符，也與 client 端的 read-only 先併發、edit 類工具需權限/序列化的執行策略相容。

## 5. planning / agent loop 結構

planning 入口存在兩種層次。第一種是 prompt 層：`constants/prompts.ts` 告訴模型遇到不清楚需求要先理解上下文、讀相關檔案、不要超出需求、必要時再詢問。第二種是工具層：`tools.ts` 讓 EnterPlanMode、ExitPlanMode、Agent、TaskStop 等工具可供模型使用，見 `tools.ts:202`、`:210` 到 `:213`。

真正的 agent loop 在 `query.ts`。每輪建立 `messagesForQuery`，先處理 snip、microcompact、context collapse、autocompact，再把 `systemPrompt` 與 `systemContext` 合成 `fullSystemPrompt`，見 `query.ts:365` 到 `:467`。接著 `deps.callModel()` 送出 messages、system prompt、thinking config、tools、model 與 effortValue，見 `query.ts:650` 到 `:707`。串流過程中只要 assistant message 含 `tool_use` block，就把它放入 `toolUseBlocks` 並設定 `needsFollowUp = true`，見 `query.ts:826` 到 `:835`。

工具結果會被 normalize 成 user-side tool result，再接回 messages。若沒有 tool use，loop 進入終止/stop-hook 路徑；若有 tool use，client 消費工具結果並在後續 state 中繼續下一輪。`query.ts:551` 到 `:558` 明確說 `toolUseBlocks` 是 loop exit signal，`query.ts:1011` 到 `:1052` 處理 streaming abort 時補齊 synthetic tool_result，避免 API 對話出現 tool_use 無對應 result 的不合法狀態。`QueryEngine` 本身則維持 conversation 級 state：`mutableMessages`、`readFileState`、usage、permission denials、已載入 nested memory path 等跨 turn 狀態，見 `QueryEngine.ts:175` 到 `:207`。

## 6. memory / 狀態機制

Claude Code 有兩類與本 dossier 有關的 memory/狀態。第一類是對話內狀態：`QueryEngine` 在一個 conversation 中保存 `mutableMessages`、`readFileState`、`totalUsage`、`permissionDenials`、`discoveredSkillNames`、`loadedNestedMemoryPaths`，見 `QueryEngine.ts:184` 到 `:207`。每次 submitMessage 會把新 user messages push 進 `mutableMessages`，並在進入 query 前寫 transcript，使中途停止後仍可 resume，見 `QueryEngine.ts:430` 到 `:463`。

第二類是 file-based auto memory。`memdir/paths.ts` 表示 auto-memory 預設啟用，但可由 `CLAUDE_CODE_DISABLE_AUTO_MEMORY`、bare/simple mode、remote storage 缺失或 settings 關閉，見 `/data/harness-lab/claude-code/restored-src/memdir/paths.ts:21` 到 `:55`。memory base dir 來自 `CLAUDE_CODE_REMOTE_MEMORY_DIR` 或 Claude config home，見 `memdir/paths.ts:79` 到 `:90`；auto memory 目錄解析順序是 env override、trusted settings、再到 `<memoryBase>/projects/<sanitized-git-root>/memory/`，見 `memdir/paths.ts:207` 到 `:220`。

memory prompt 在 `memdir/memdir.ts` 建立。`ENTRYPOINT_NAME` 是 `MEMORY.md`，entrypoint 有 200 行與 25,000 bytes 上限，見 `/data/harness-lab/claude-code/restored-src/memdir/memdir.ts:34` 到 `:39`。`buildMemoryLines()` 要求模型把 memory 建成持久、file-based 系統，並規定記憶要分類、去重、更新或移除過期內容，見 `memdir.ts:187` 到 `:266`。`buildMemoryPrompt()` 讀取現有 `MEMORY.md`，如果存在則 truncate 後注入 prompt，否則宣告目前為空，見 `memdir.ts:268` 到 `:315`。

上下文壓縮也是狀態機制的一部分。`services/compact/autoCompact.ts` 以模型 context window 扣掉 summary output buffer 得到 effective window，並在 token usage 超過 threshold 時觸發 auto compact，見 `/data/harness-lab/claude-code/restored-src/services/compact/autoCompact.ts:28` 到 `:90` 與 `:160` 到 `:239`。`query.ts` 在每輪模型呼叫前執行 microcompact/autocompact，成功後用 summary messages 取代原 messages 並繼續本輪，見 `query.ts:412` 到 `:543`。

## 7. 模型、high effort 與 claude-trace 注入

Phase 0 的 Claude Code smoke 只使用 Haiku：`infra/00-paths.sh:8` 將 `ANTHROPIC_MODEL` 固定為 `claude-haiku-4-5-20251001`。smoke 腳本把 `HOME` 設為 `$LAB_HOME`、匯出 `ANTHROPIC_API_KEY`，並把 `$LAB_BIN` 放進 PATH，確保 `claude-trace --run-with` 解析到 lab-local 的 Claude Code 2.1.88，見 `/data/repos/xai-harness-faithfulness/infra/smoke/smoke-claude-code.sh:9` 到 `:16`。

trace 掛載方式是 `/data/harness-lab/bin/claude-trace --include-all-requests --run-with -p ... --model "$ANTHROPIC_MODEL" --permission-mode acceptEdits`，見 `smoke-claude-code.sh:14` 到 `:16`。`claude-trace` 本身釘在 `@loki-zhou/claude-trace@1.0.4`，見 `/data/repos/xai-harness-faithfulness/infra/install-claude-trace.sh:3` 到 `:8`。模型 high effort 在 Claude Code 這一階段不是像 Codex/OpenCode 那樣由單一 CLI flag 注入；`QueryEngine` 預設在沒有關閉 thinking 時使用 `{ type: 'adaptive' }`，見 `QueryEngine.ts:278` 到 `:282`，而 Phase 1 runner 會再固定 effort 控制。ENVIRONMENT.lock 也記錄 Claude Code high effort 為「預設 thinking；effort 於 runner 設定」，見 `/data/repos/xai-harness-faithfulness/ENVIRONMENT.lock.md:38`。

## 8. 與 smoke trace 對照

實際 trace：`/data/harness-lab/smoke/cc/.claude-trace/log-2026-06-03-12-36-38.jsonl`。遠端 lab 內的 `@loki-zhou/claude-trace@1.0.4` 可重新解析此 JSONL 並生成 `secondary-verify.html`；JSONL 共 14 筆 captured request/response，其中主模型 `/v1/messages` request 有 3 筆，`model` 皆是 `claude-haiku-4-5-20251001`，`max_tokens` 皆是 `32000`，`system` 約 26,811 字元，tools 皆有 22 個。這直接佐證 `QueryEngine` 在呼叫 `deps.callModel()` 時傳入 system prompt、thinking config 與 tool list，而不是僅靠 CLI stdout 推斷。

smoke 工作目錄是 `/data/harness-lab/smoke/cc`，初始 `hello.py` 由腳本寫成 `return a - b`，見 `smoke-claude-code.sh:4` 到 `:8`。二次驗證解析 SSE response 的 `content_block_start` event 後，assistant tool sequence 是 `Read -> Edit`；三次主模型呼叫的 stop reasons 依序為 `tool_use`、`tool_use`、`end_turn`。最後 `/data/harness-lab/smoke/cc/hello.py` 被修正為 `return a + b`。此序列對上 system prompt 的「讀檔理解後再修改」要求、tool registry 中 Read/Edit 的可用性，以及 query loop 對 `tool_use` block 的 follow-up 機制。

結論：Claude Code 2.1.88 在本實驗中是可白箱分析的 harness。可控點包含 `--model` 模型注入、runner/狀態設定中的 thinking/effort、tool registry 與 system prompt 組裝；可觀察點包含 claude-trace JSONL 的 `system`、`tools`、`messages[].content[].tool_use`。Phase 1 可用此 trace schema 直接比對各 harness 的 prompt/tool/action trajectory。
