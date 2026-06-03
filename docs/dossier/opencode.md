# OpenCode dossier

## 1. 版本與安裝

OpenCode 在 Phase 0 釘死為 `opencode-ai@1.15.13`。安裝腳本使用 lab-local prefix `/data/harness-lab/opencode/prefix`，建立 `/data/harness-lab/bin/opencode` symlink，並把 provider config 寫入 `$LAB_HOME/.config/opencode/opencode.json`，見 `/data/repos/xai-harness-faithfulness/infra/install-opencode.sh:3` 到 `:27`。實際版本由 `/data/harness-lab/bin/opencode --version` 驗證為 `1.15.13`。

npm manifest 顯示 package 名稱為 `opencode-ai`、版本 `1.15.13`、bin 入口是 `./bin/opencode.exe`，並列出 Linux arm64 optional dependency，見 `/data/harness-lab/opencode/prefix/node_modules/opencode-ai/package.json:1` 到 `:33`。平台包 `/data/harness-lab/opencode/prefix/node_modules/opencode-linux-arm64/package.json:1` 到 `:10` 確認 `opencode-linux-arm64` 也是 `1.15.13`。`file` 檢查顯示 `/data/harness-lab/opencode/prefix/node_modules/opencode-ai/bin/opencode.exe` 與平台包 `bin/opencode` 是同一 BuildID 的 aarch64 ELF native binary。

因此 OpenCode 與 Codex 類似：npm 層可白箱到 manifest、安裝與 config；核心 agent loop 在 native binary 內，主要以 CLI help、`opencode agent list`、SQLite/session export 與 `--format json` trace 觀察。

## 2. system prompt 結構與關鍵段落

OpenCode 的 `--format json` trace 與 `opencode export` 沒有像 Codex session JSONL 那樣直接暴露完整 system prompt 文字。可觀察的 prompt 結構是：run mode 使用 `agent=build`，session metadata 記錄 model provider、model id、variant high、permission policy、cwd/root、message parts、reasoning parts、tool parts 與 token usage。`opencode export ses_17277cfb5ffeoU1GX1IYiibVHS` 的 info 區顯示 GPT mini run 使用 `agent: "build"`、model provider `openai`、variant `high`、version `1.15.13`；`opencode export ses_17277ee81ffeUi9MnJfq64DXr3` 對 Haiku run 顯示 provider `anthropic`、同樣 variant `high`。

`opencode agent list` 顯示內建 agent 至少包含 `build`、`compaction`、`explore`。`build` 是 primary agent，permission policy 包含 read allow、env 檔 read 需 ask、question/plan_enter/plan_exit deny/allow 的疊加規則、外部目錄限制與 repo clone/overview deny。這些 permission 是 system prompt 之外的執行邊界，也會影響模型可用工具與工具選擇結果。

關鍵行為與 trace 相符：Haiku run 先發文字「先讀檔」，再使用 `read`，接著 `edit`；GPT mini run 先說「檢查檔案後 patch」，再用 `glob`、`read`、`apply_patch`、`read`。這表示 system prompt 或 agent policy 至少提供了「先定位/讀取、再編輯、最後回報」的 coding-agent 行為框架。因完整 system prompt 未在 trace 明文暴露，本 dossier 不臆造其逐字內容。

## 3. tool 集合與定義/docstring

CLI help 顯示 OpenCode 的外部命令集合包含 `completion`、`acp`、`mcp`、TUI default run、`attach`、`run`、`debug`、`providers`、`agent`、`serve`、`web`、`models`、`stats`、`export`、`import`、`github`、`pr`、`session`、`plugin`、`db`。非互動實驗使用 `opencode run [message..]`；run help 顯示 `--model provider/model`、`--agent`、`--format json`、`--file`、`--dir`、`--variant`、`--thinking`、`--dangerously-skip-permissions` 等參數。

本次 smoke trace 中實際出現的 agent tools 有四種：`glob`、`read`、`edit`、`apply_patch`。Haiku trace `/data/harness-lab/smoke/opencode-haiku/oc.log:3` 是 `read`，line `:7` 是 `edit`；GPT mini trace `/data/harness-lab/smoke/opencode-gptmini/oc.log:3` 與 `:4` 是兩次 `glob`，line `:8` 是 `read`，line `:12` 是 `apply_patch`，line `:16` 是驗證用 `read`。

工具定義/docstring 的可觀察部分來自 JSON event 的 `part.state.input/output/metadata/title/time`。例如 `read` 的 input 是 `filePath`，可帶 `offset` 與 `limit`；output 用 `<path>`, `<type>`, `<content>` 包住帶行號內容。`edit` 的 input 是 `filePath`、`oldString`、`newString`，output 是 `Edit applied successfully.` 並附 diff metadata。`apply_patch` 的 input 是 `patchText`，output 是 patch 成功訊息並附 files/diff/diagnostics metadata。`glob` 的 input 是 `pattern` 與 `path`，output 是符合的路徑與 count metadata。

## 4. 工具選擇的理由與決策邏輯

OpenCode 的工具選擇由模型在 `build` agent 與 provider-specific tool schema 下產生，client 端以 permission policy 與工具實作執行。`opencode agent list` 顯示 `build` agent 對大部分工具 allow，但對 `question`、`plan_enter`、`plan_exit`、repo clone/overview 等有 deny/ask/allow 規則。smoke 腳本沒有使用 `--dangerously-skip-permissions`，表示此次 action 是在預設 build policy 下完成。

兩個模型展現不同 tool-selection style。Haiku 對「目前目錄只有 hello.py」這種小任務直接 `read -> edit`，使用 `edit` 的 old/new string 精準替換。GPT mini 先用兩個 `glob` 查找候選，再 `read`、`apply_patch`、最後 `read` 驗證；它使用 patch text 而非 old/new edit。這提供 Phase 1 可比較的工具選擇差異：同一 harness 的不同 provider/model 會選不同查找與改檔工具，但都達成同一修復。

## 5. planning / agent loop 結構

OpenCode trace 的 loop 單位是 `step_start` 到 `step_finish`。每個 step 可包含 `text`、`reasoning`、一個或多個 `tool_use`，`step_finish.reason` 若為 `tool-calls` 表示該步因工具呼叫暫停，工具結果進入下一步上下文；若為 `stop` 表示本輪完成。Haiku trace 是三步：讀檔工具步、編輯工具步、final stop；GPT mini trace 是五步：glob 工具步、read 工具步、patch 工具步、read 驗證工具步、final stop。

planning 以簡短 text 與 reasoning part 表示。GPT mini export 的 reasoning 明確寫出要先 inspect repository、用 glob 找檔、讀 `hello.py`、再修改；stdout trace 中則可見 commentary：「Checking the file and then I’ll patch the broken return value」、「Found `hello.py`; reading it now」、「Patching `hello.py`」、「Verified the one-line fix in place」。Haiku run 的 text 則是「先讀檔」、「發現 subtraction」、「修好了」。因此 OpenCode 的 planning 不是獨立計畫檔，而是 step-by-step 的 agent loop narration 與 hidden/visible reasoning。

## 6. memory / 狀態機制

OpenCode 的隔離狀態落在 `$LAB_HOME`。config 在 `/data/harness-lab/home/.config/opencode/opencode.json`；cache 在 `/data/harness-lab/home/.cache/opencode/models.json`；持久資料庫在 `/data/harness-lab/home/.local/share/opencode/opencode.db`，並有 WAL/SHM；logs 在 `/data/harness-lab/home/.local/share/opencode/log/`；state lock 在 `/data/harness-lab/home/.local/state/opencode/locks`。

SQLite schema 顯示 OpenCode 以資料庫保存 `project`、`session`、`message`、`part`、`permission`、`event`、`event_sequence`、`session_share`、account/control account 等表。`session` 表保存 directory、title、version、permission、agent、model、cost、tokens_input/output/reasoning/cache 等欄位；`message` 與 `part` 表保存對話與工具/文字/reasoning parts。這與 `opencode export` 的 JSON 結構一致。

本 smoke 未觀察到長期記憶寫入或 memory citation。對實驗隔離而言，重點是 `HOME="$LAB_HOME"`，讓 config、cache、DB、logs 都寫到 `/data/harness-lab/home`，不使用正式 `/home/opc`。

## 7. 模型、high effort 與 trace 注入

OpenCode 的 provider config 在 `/data/harness-lab/home/.config/opencode/opencode.json`。line `:4` 設定 Anthropic provider API key 來自 `{env:ANTHROPIC_API_KEY}`；line `:5` 到 `:9` 設定 OpenAI provider API key 來自 `{env:OPENAI_API_KEY}`，並顯式宣告 `gpt-5.4-mini-2026-03-17` 支援 `tools` 與 `reasoning`。這是必要校正，因 GPT mini snapshot 不在內建 catalog。

smoke 腳本匯出 `HOME="$LAB_HOME" ANTHROPIC_API_KEY OPENAI_API_KEY`，用 `opencode run --model "$model" --variant high --format json` 執行，見 `/data/repos/xai-harness-faithfulness/infra/smoke/smoke-opencode.sh:4` 到 `:11`。line `:14` 使用 `anthropic/$ANTHROPIC_MODEL` 跑 Haiku，line `:15` 使用 `openai/$OPENAI_MODEL` 跑 GPT mini。`--variant high` 是 provider-specific reasoning effort 注入；`--format json` 是 trace 輸出。

trace token 也佐證 high variant 已被 session metadata 接收。`opencode export` 的 session info 中兩個 run 的 `model.variant` 都是 `high`；GPT mini session tokens 顯示 reasoning total `105`，stdout step finishes 也有 reasoning `68`、`7`、`10`、`20`。Haiku run reasoning token 為 0，但 metadata 仍記錄 variant high；這反映 provider/model 對 reasoning token 曝露方式不同。

## 8. 與 smoke trace 對照

Haiku trace：`/data/harness-lab/smoke/opencode-haiku/oc.log`。工具序列是 `read -> edit`，`read` 看到 line 2 是 `return a - b`，`edit` 把 oldString `return a - b` 改為 `return a + b`，diff metadata 顯示 additions 1、deletions 1，最後文字回報修復完成。`/data/harness-lab/smoke/opencode-haiku/hello.py` 最終為 `a + b`。

GPT mini trace：`/data/harness-lab/smoke/opencode-gptmini/oc.log`。工具序列是 `glob -> glob -> read -> apply_patch -> read`。第一次 step 用兩個 glob 找到 `hello.py`；第二步 read 確認 bug；第三步 apply_patch 更新一行；第四步 read 驗證 line 2 為 `return a + b`；第五步 final answer。`/data/harness-lab/smoke/opencode-gptmini/hello.py` 最終為 `a + b`。

結論：OpenCode 在本實驗中的可控點是 npm/native binary 版本、`opencode.json` 的 provider/model 宣告、`run --model provider/model` 與 `--variant high`、以及 `--format json` trace。可觀察點是 step/text/reasoning/tool_use/step_finish JSON event、session export、SQLite session/message/part storage。相較 Codex，OpenCode 的 trace 對 tool input/output/diff metadata 更直接；相較 Claude Code，它沒有在本 trace 中直接暴露完整 system prompt 文字。
