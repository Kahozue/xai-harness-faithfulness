# Codex CLI dossier

## 1. 版本與安裝

Codex CLI 在 Phase 0 釘死為 `@openai/codex@0.136.0`。安裝腳本使用 lab-local prefix `/data/harness-lab/codex/prefix`，建立 `/data/harness-lab/bin/codex` symlink，並在 `$LAB_HOME/.codex/config.toml` 寫入模型與 reasoning effort，見 `/data/repos/xai-harness-faithfulness/infra/install-codex.sh:3` 到 `:17`。實際版本由 `/data/harness-lab/bin/codex --version` 驗證為 `codex-cli 0.136.0`。

npm package manifest 顯示此 package 名稱為 `@openai/codex`、版本 `0.136.0`，bin 入口是 `bin/codex.js`，描述為 OpenAI 在本機執行的 coding agent，見 `/data/harness-lab/codex/prefix/node_modules/@openai/codex/package.json:1` 到 `:8`。同一 manifest 也列出各平台 optional dependency，Linux arm64 對應 `@openai/codex@0.136.0-linux-arm64`，見 `package.json:22` 到 `:29`。平台包 manifest 進一步確認 target 是 `aarch64-unknown-linux-musl`，entrypoint 是 `bin/codex`，見 `/data/harness-lab/codex/prefix/node_modules/@openai/codex-linux-arm64/vendor/aarch64-unknown-linux-musl/codex-package.json:1` 到 `:8`。

`bin/codex.js` 是 Node wrapper。它依 `process.platform` 與 `process.arch` 選 target triple，Linux arm64 走 `aarch64-unknown-linux-musl`，見 `/data/harness-lab/codex/prefix/node_modules/@openai/codex/bin/codex.js:24` 到 `:67`；接著解析 native package，並以 `spawn(binaryPath, process.argv.slice(2), { stdio: "inherit", env })` 交給靜態 linked native binary，見 `bin/codex.js:73` 到 `:127` 與 `:170` 到 `:187`。因此此 dossier 對 wrapper/安裝可白箱，對 native agent loop 則以 CLI help、session JSONL 與 smoke trace 作為可觀察證據。

## 2. system prompt 結構與關鍵段落

Codex 的 session JSONL 暴露了實際 base instructions。`/data/harness-lab/home/.codex/sessions/2026/06/03/rollout-2026-06-03T20-42-51-019e8d82-0f4e-74d3-9de7-07c0cc9e6cd7.jsonl:1` 的 `session_meta.payload.base_instructions.text` 以「You are Codex, a coding agent based on GPT-5」開頭，接著分成 Personality、General、Editing constraints、Special user requests、Autonomy and persistence、Frontend tasks、Working with the user、Formatting rules、Intermediary updates、Final answer instructions 等段落。

同一 session 後續 lines 也顯示 system prompt 並非只有 base instructions。`rollout-...jsonl:3` 記錄 developer role，包含本次 exec 的權限設定與技能列表；`rollout-...jsonl:4` 記錄 environment context，包含 cwd、shell、日期、timezone、filesystem 權限；`rollout-...jsonl:5` 記錄 user prompt。這個結構表示 Codex 的 prompt 是「base instructions + developer/config context + environment context + user task」的分層組合。

關鍵段落與本 smoke 行為直接相符：base instructions 要求先檢查 codebase、優先用 `rg` 搜尋、平行讀檔、手動程式碼修改使用 `apply_patch`、完整處理到驗證與結果回報。smoke session 中 agent 先發 commentary 說要定位 `hello.py`，再呼叫 `exec_command` 搜尋與讀檔，最後以 `apply_patch` 修改並再次讀檔驗證，見 `rollout-...jsonl:9` 到 `:31` 的 response/function/tool-output 事件序列。

## 3. tool 集合與定義/docstring

Codex CLI help 顯示主要執行介面包含 `exec`、`review`、`login`、`mcp`、`plugin`、`mcp-server`、`app-server`、`completion`、`doctor`、`sandbox`、`apply`、`resume`、`cloud` 等 subcommands。非互動任務使用 `codex exec`；其 help 顯示可傳入 prompt、`--model`、`--sandbox`、`--ask-for-approval`、`--dangerously-bypass-approvals-and-sandbox`、`--cd`、`--skip-git-repo-check`、`--ephemeral`、`--output-schema` 與 `--json`。

在 agent 內部，本次 smoke 實際可見的工具有兩類。第一類是 shell command tool：session JSONL 中 `response_item` 的 `function_call` 名稱是 `exec_command`，arguments 包含 `cmd`、`workdir`、`login`、`tty`、`max_output_tokens`，見 `rollout-...jsonl:12`、`:13`、`:21`、`:29`。stdout trace 對同一類工具抽象成 `command_execution` item，見 `/data/harness-lab/smoke/codex/codex.log` 的 `item_1`、`item_2`、`item_4`、`item_8`。

第二類是 patch/edit tool：session JSONL 中 `response_item` 的 `custom_tool_call` 名稱是 `apply_patch`，input 是標準 unified patch，見 `rollout-...jsonl:25`；stdout trace 對同一動作抽象成 `file_change` item，見 `/data/harness-lab/smoke/codex/codex.log` 的 `item_6`。native binary 的 strings 也顯示它有 tool/MCP/dynamic tool/approval 相關模組字串，如 `core/src/tools/code_mode/mod.rs`、`mcp-server/src/codex_tool_runner.rs`、`dynamic tool`、`apply_patch approval` 等，這只佐證工具系統存在，不把不可見 Rust source 當成已讀白箱。

## 4. 工具選擇的理由與決策邏輯

Codex 的工具選擇由模型根據 base instructions、developer instructions、environment context 與可用工具 schema 產生 tool call。client/CLI 端再依 approval policy、sandbox policy、exec mode 約束與工具結果把 action 落地。`codex exec --help` 顯示 approvals 與 sandbox 可由 `--ask-for-approval`、`--sandbox`、`--dangerously-bypass-approvals-and-sandbox` 控制；本 smoke 腳本使用 bypass 與 `--skip-git-repo-check`，讓 headless 實驗不因本機 sandbox/approval 停住，見 `/data/repos/xai-harness-faithfulness/infra/smoke/smoke-codex.sh:11` 到 `:14`。

本次 smoke 的工具選擇理由可直接由 agent commentary 與 tool sequence 看出：先 `rg --files .` 找檔案，再 `pwd && rg -n "def add|add\\(" -S .` 確認符號位置，再 `nl -ba hello.py` 讀取內容，接著使用 `apply_patch` 修改一行，最後再次 `nl -ba hello.py` 驗證。這符合 base instructions 中的「先檢查 codebase、不做多餘改動、手動改檔用 apply_patch、完成後驗證」。stdout JSONL 以 `agent_message` 搭配 `command_execution`/`file_change` 呈現此決策過程，session JSONL 則保存更細的 function call arguments。

## 5. planning / agent loop 結構

Codex 在此 smoke 沒有輸出獨立 plan object，因任務是單檔最小修正；但 planning 以 commentary 形式存在。agent 先宣告「定位 `hello.py`、確認 `add`、直接 patch」，再於讀檔後宣告「更新該行」，最後宣告「驗證內容」，這些 commentary 分別出現在 `/data/harness-lab/smoke/codex/codex.log` 的 `item_0`、`item_3`、`item_5`、`item_7`。

agent loop 的可觀察週期是：assistant message 或 reasoning -> tool call -> tool output/file change -> 下一個 assistant step。session JSONL 以 `response_item` 記錄 reasoning、message、function_call、function_call_output、custom_tool_call、custom_tool_call_output，並穿插 `token_count`；stdout log 則將同一流程壓成 `thread.started`、`turn.started`、`item.started`、`item.completed`、`turn.completed`。最後 `turn.completed` usage 顯示 `input_tokens`、`cached_input_tokens`、`output_tokens` 與 `reasoning_output_tokens`，見 `/data/harness-lab/smoke/codex/codex.log` 最後一行。

native binary strings 中可見 `TurnPlanUpdatedNotification`、`explanation`、`plan` 等字串，表示 CLI 具備 plan update 事件類型；但此 smoke 未觸發此事件。因此本 dossier 對 planning 的結論限定為：簡單任務使用 inline commentary micro-plan，較複雜任務可能有 plan notification，但 Phase 0 未以此 smoke 證明其完整行為。

## 6. memory / 狀態機制

Codex 的隔離狀態在 `$LAB_HOME/.codex`。Phase 0 lab 內可見 `auth.json`、`config.toml`、`sessions/`、`state_5.sqlite`、`memories_1.sqlite`、`goals_1.sqlite`、`logs_2.sqlite`、`installation_id` 等檔案。這些都位於 `/data/harness-lab/home/.codex`，不在 repo 中，也不碰正式 `/home/opc`。

session persistence 的主要可讀證據是 `/data/harness-lab/home/.codex/sessions/2026/06/03/rollout-2026-06-03T20-42-51-019e8d82-0f4e-74d3-9de7-07c0cc9e6cd7.jsonl`。line 1 的 `session_meta` 記錄 cwd、originator、cli_version、source、thread_source、model_provider 與 base instructions；後續 lines 保存 developer/user context、reasoning encrypted content、tool calls、tool outputs、token counts、final answer 與 task completion。這提供 trace 之外的 session replay/state ground truth。

`memories_1.sqlite` 與 native binary strings 中的 `memory mode`、`memories db`、`Cleared memory state` 等字串顯示 Codex CLI 有記憶資料庫與 memory mode 機制；但本 smoke 是乾淨單輪 bug fix，未觀察到 memory citation 或 memory write。對本實驗而言，Codex memory 的重要控制是把 `HOME` 設為 `$LAB_HOME`，使 memory/session/auth/config 均隔離在 lab，見 `/data/repos/xai-harness-faithfulness/infra/smoke/smoke-codex.sh:9`。

## 7. 模型、high effort 與 trace 注入

模型與 high effort 在 `$LAB_HOME/.codex/config.toml` 中注入：line 1 是 `model = "gpt-5.4-mini-2026-03-17"`，line 2 是 `model_reasoning_effort = "high"`；安裝腳本負責寫入這兩行，見 `/data/repos/xai-harness-faithfulness/infra/install-codex.sh:8` 到 `:13`。認證不是單純依賴環境變數；Phase 0 校正後使用 `printenv OPENAI_API_KEY | HOME="$LAB_HOME" "$LAB_BIN/codex" login --with-api-key`，把 auth 寫到 `$LAB_HOME/.codex/auth.json`，見 `install-codex.sh:14` 到 `:17`。dossier 不讀取或貼出 auth 內容。

trace 掛載方式是 `codex exec --json`。smoke 腳本在 `/data/harness-lab/smoke/codex` 內執行 `/data/harness-lab/bin/codex exec --skip-git-repo-check --dangerously-bypass-approvals-and-sandbox --json "Fix the bug..."`，並用 `tee "$WORK/codex.log"` 保存 stdout JSONL，見 `/data/repos/xai-harness-faithfulness/infra/smoke/smoke-codex.sh:10` 到 `:15`。`codex.log` 的最終 usage 顯示 `reasoning_output_tokens: 75`，佐證本次 gpt-5.4-mini run 有 reasoning token 輸出。

## 8. 與 smoke trace 對照

stdout trace：`/data/harness-lab/smoke/codex/codex.log`。事件序列為 `thread.started` -> `turn.started` -> 多個 `agent_message`、`command_execution`、`file_change` item -> `turn.completed`。工具/action trajectory 是：`rg --files .`、`pwd && rg -n ...`、`nl -ba hello.py`、`apply_patch` 對 `/data/harness-lab/smoke/codex/hello.py` 做 update、再 `nl -ba hello.py` 驗證。

session trace：`/data/harness-lab/home/.codex/sessions/2026/06/03/rollout-2026-06-03T20-42-51-019e8d82-0f4e-74d3-9de7-07c0cc9e6cd7.jsonl`。它比 stdout trace 更完整，包含 base instructions、developer/environment context、function call arguments、custom patch input、tool output、token_count 與 final answer。兩份 trace 對同一輪 smoke 的結論一致：`hello.py` 從 `return a - b` 被修正為 `return a + b`。

結論：Codex CLI 在本實驗中的可控點是 npm/native binary 版本、`$LAB_HOME/.codex/config.toml` 的 model/effort、`codex login --with-api-key` 的隔離 auth、以及 `codex exec --json` trace；可觀察點是 stdout JSONL 與 session JSONL。相較 Claude Code，Codex 的完整 Rust agent loop 不在 npm wrapper 內展開，因此本 dossier 把 native 內部 prompt/工具實作視為可觀察黑箱，並用 session JSONL 作為 Phase 1 trace schema 的主證據。

## 模型推理可見性補正（2026-06-05）

Codex/GPT-5.4-mini 的 reasoning 由 OpenAI 加密：session JSONL 的 reasoning item 帶 `encrypted_content`（~1000-3200 字、不可解碼）＋ `reasoning_output_tokens`，原始 CoT 無法還原；可讀的只有 reasoning summary（部分 provider 才回）與 token 數。Codex model_family 的 context window 為 258400，與 OpenAI 對 GPT-5.4-mini 的 400000、OpenCode catalog 的 400000 不同（屬 harness 端設定）。詳見 `docs/verification/2026-06-05-thinking-capture-investigation.md`。
