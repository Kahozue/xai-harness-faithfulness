# xai-harness-faithfulness 設計規格（Design Spec）

- 文件版本：v1（2026-06-03）
- 作者：陳政顯　7114029018
- 課程：xAI 期末專題
- 狀態：已通過 brainstorming 設計核准，待 writing-plans 產出實作計畫
- 對應 repo：`xai-harness-faithfulness`（GitHub: `anonymous/xai-harness-faithfulness`）
- 下游依賴：`hci-agent-attribution` 以本專案產出的 factorial trace 為 ground truth

> 本文件為實驗的單一事實來源（single source of truth）。所有過程與數據皆保留作報告之用；任何偏離 proposal 之處都在「決策紀錄」與「風險與限制」中明確交代。

---

## 0. 研究問題與摘要

**題目**：Faithfulness of the Harness — 歸因 Agent 的工具選擇分歧。

LLM Agent 在不同 harness（Claude Code、Codex CLI、OpenCode、Hermes）下對同一任務產生的 tool 序列差異，有多少來自 **harness 設計**（system prompt、tool 定義、skills 調用邏輯、memory），多少來自**模型**，多少來自**交互作用或雜訊**？本研究在隔離環境用 4 種白箱 xAI 方法（M1–M4）＋ 2×3 partial factorial 進行歸因。

**研究問題**

| RQ | 問題 |
|----|------|
| RQ1 | 4 種 xAI 方法對同一 decision point 的 attribution 是否一致？不一致比例與 pattern？ |
| RQ2 | 高 disagreement 是否與任務失敗正向關聯？可否作 governance trigger？ |
| RQ3 | harness 主效應、model 主效應、交互作用對 tool 選擇差異各解釋多少？ |
| RQ4 | 能否轉化為 agent-card 模板（fidelity / stability / robustness / actionability / governability）？ |

---

## 1. 範圍與保真度決策

採**完整執行**（全做），不縮減 proposal：4 harness、2 模型、6 configs、20 tasks、M1–M4 四法皆做、四 harness 皆做、全部指標與 agent-card。

唯二的「方法學增補」而非縮減：
1. **Pilot 驗證關**（2 configs × 3 tasks 跑通）先驗證管線、grader 與成本/時間，再放大全量。屬風險控制，不影響最終全量。
2. **重複次數 = 3**（每 config×task），用以估計 Noise（proposal 的 Noise pair 型別即「同配置重跑」）。

執行順序固定：**xAI →（產出 trace）→ HCI**。HCI 需要本專案的 ground-truth trace 才能進行。

---

## 2. 系統架構總覽

實驗引擎由四個可獨立理解、以明確介面溝通的單元組成：

```
            ┌────────────────────────────────────────────────┐
            │ 環境與版本鎖 ENVIRONMENT.lock.md（§3）          │
            └────────────────────────────────────────────────┘
 任務套件(§6) ──► 統一 Runner(§6) ──► 各 harness 介面卡(§6) ──► 正規化 Trace(§6)
   20 tasks        provision/launch       CC/Codex/OpenCode/Hermes     JSON + raw logs
   (受控+benchmark)  /capture/grade         (model 與 effort 注入)        (不可變、committed)
                                                   │
                                                   ▼
                              白箱 M1–M4 ablation(§8) ──► 指標與分析(§9) ──► agent-card(§9)
```

- **任務套件**：定義「做什麼」（20 個受控、可自動評分的 agentic task）。
- **統一 Runner**：定義「怎麼跑一次」（對 (harness, model, task) 開乾淨副本、注入模型與 high effort、固定 timeout、擷取 trace、評分）。
- **harness 介面卡**：把四個 harness 的差異封裝在一致介面後（啟動方式、模型注入、trace 擷取各不同）。
- **正規化 Trace**：定義「輸出長怎樣」（跨 harness 可比的 JSON schema）。

每個單元都能單獨測試：任務套件可用一個 mock harness 驗證 grader；Runner 可用單一 config 跑通；介面卡可逐一驗證能擷取到 tool 序列。

---

## 3. 可重現性骨幹（版本全釘死）

每個 repo 一份 `ENVIRONMENT.lock.md`，為第一級交付物。釘死並記錄下列全部：

| 項目 | 釘死值 / 釘死方式 |
|------|------|
| Claude Code | **2.1.88**，以本機 `claude-code-2.1.88.tgz` 離線安裝（不從 npm 抓最新）；以 restored-src（同版）作白箱參照 |
| claude-trace | `@loki-zhou/claude-trace` **1.0.4**（攔截 Claude Code API 流量，擷取 system prompt / tool 定義 / tool 序列 / thinking） |
| Codex CLI | 安裝時釘死一個明確版本號（記錄於 lock） |
| OpenCode | 安裝時釘死一個明確版本號（記錄於 lock） |
| Hermes | **0.13.0**，全新乾淨實例（與正式服務隔離）；自動更新已於 2026-05-14 暫停，狀態穩定，另存快照 |
| Haiku 4.5 模型 | `claude-haiku-4-5-20251001`（Anthropic 原生 `api.anthropic.com`） |
| GPT-5.4-mini 模型 | `gpt-5.4-mini-2026-03-17`（OpenAI 原生 `api.openai.com`） |
| reasoning effort | 全部 `high`（依 proposal 設計取捨；低 effort 會讓失敗來源混入 model under-utilization 而非 harness 設計）。Claude Code / Haiku 4.5 經 SDK/source 查核後另固定 `CLAUDE_CODE_MAX_OUTPUT_TOKENS=64000` 與 `MAX_THINKING_TOKENS=63999`，trace 必須證明 request 真的送出 `max_tokens=64000` / `thinking.budget_tokens=63999`。 |
| 執行環境 | node v22.22.2、Python 3.11.13、OS = Oracle Linux（aarch64）、各 harness 的 commit/版本、安裝日期，全寫入 lock |
| 閘道路由 | 同一模型固定走同一後端（見 §4），控制 provider 混淆變數 |

**為何釘死**：harness 與模型版本若浮動，trace 不可重現、跨配置比較失去基準，HCI 的 ground truth 也會漂移。版本鎖同時滿足 HCI 注意事項對「測試環境固定版本＋環境介紹」的要求。

---

## 4. 閘道、認證與隔離

**模型路由（控制變數）**

| 模型 | 後端 | 使用此模型的 harness |
|------|------|------|
| Haiku 4.5（`claude-haiku-4-5-20251001`） | Anthropic 原生 | Claude Code、OpenCode、Hermes |
| GPT-5.4-mini（`gpt-5.4-mini-2026-03-17`） | OpenAI 原生 | OpenCode、Hermes、Codex CLI |

同一模型在不同 harness 一律走同一後端 → 跨 harness 是「同一個模型」，harness 效應才乾淨。Claude Code 因原生講 Anthropic API 格式，使用 Anthropic 原生即零轉譯、最忠實；WorldRouter 退為備援、不進主實驗。

**6 configs**

| # | harness | model | 角色 |
|---|---------|-------|------|
| 1 | Claude Code | Haiku 4.5 | anchor（橫向 harness 基準） |
| 2 | OpenCode | Haiku 4.5 | |
| 3 | Hermes | Haiku 4.5 | |
| 4 | OpenCode | GPT-5.4-mini | |
| 5 | Hermes | GPT-5.4-mini | |
| 6 | Codex CLI | GPT-5.4-mini | anchor |

橫向＝harness 效應、縱向＝model 效應、OpenCode/Hermes 兩列分離交互作用。

**隔離與安全**
- 實驗 harness 安裝於獨立執行根（如 `/data/harness-lab/`），各自獨立 config 與 HOME 樣資料夾，與正式服務（花帆 Discord bot、正式 Hermes、open-design 等）完全分離。
- **Hermes 用全新乾淨實例**（乾淨 memory、乾淨設定），絕不使用 VPS 上正在跑的那台；避免既有累積記憶污染實驗。
- 所有 secrets（Anthropic / OpenAI key）放於 repo 之外（`~/.harness-exp/*.env`，chmod 600），**永不進 git、永不推 GitHub**；repo 內 `.gitignore` 另排除 `.env`。

---

## 5. Phase 0 — 乾淨隔離建置 + harness 機制研究（不跑實驗，書面 dossier 經審閱才放行）

**目的**：在跑任何實驗前，把四個 harness 的機制與配置徹底搞懂，作為實驗嚴謹性與報告論述的「底」。

**交付物**
1. **乾淨隔離安裝**四 harness（版本全釘死，見 §3），各自獨立 config/HOME；全新乾淨 Hermes，不碰花帆。
2. **harness 機制 dossier**（書面，逐 harness）：
   - system prompt 結構與關鍵段落
   - tool 集合、tool 定義與 docstring
   - **工具選擇的理由與決策邏輯**（agent 如何決定下一步用哪個 tool）
   - planning / agent loop 結構
   - memory / 狀態機制
3. **Hermes 記憶機制專章**：記憶在什麼條件下收斂／濃縮／成長變強、觸發條件、SOUL 與 memory 的邊界（直接讀 `/data/hermes-agent` 源碼確認）。
4. **跨 harness 對照表**：四者在 system prompt 規模、tool 數量與種類、planning 風格、memory 機制上的異同。
5. **配置文件化**：每個 harness 如何指定模型、如何設定 high effort、如何掛 trace/hook，皆寫成可重跑的步驟。

**放行條件（Gate）**：dossier 與 `ENVIRONMENT.lock.md` 經使用者審閱通過後，才進入 Phase 1。

---

## 6. Phase 1 — 任務套件、統一 Runner、Trace schema、Pilot

### 6.1 任務套件（20 tasks，受控外殼 + benchmark 取材）

四類任務（依 proposal）：**rename / add tests / add logging / simple bug fix**，各 5 題、共 20。

雙層取材：

| 層 | 來源 | 數量 | 說明 |
|---|---|---|---|
| Tier 1 錨點 | SWE-bench **Verified** 易題子集（人工篩過可解、model-card 標準，自帶 hidden-test verifier） | 逐類各 1，共約 4 | 逐字真實任務 + 可引用 provenance + 自動評分 |
| Tier 2 受控主體 | 一個釘死的受控 target repo，依 **DeepSWE 風格**（contamination-free + behavior verifier）自撰 | 其餘約 16 | 四類均衡、難度可調、grader 好寫 |

**難度校準（必要）**：兩個模型皆為小模型；Tier 1 僅取易題、Tier 2 難度調到小模型能完成一部分，避免「全失敗、無分歧訊號、success 觸底」。所有來源在 repo 與報告標註出處。

每個 task 規格：固定初始 repo 狀態（pinned）、明確任務 prompt、**自動 grader**（Tier 1 用 hidden tests；Tier 2 用 behavior 驗證腳本），輸出 pass/fail 與細節。

### 6.2 統一 Runner

對每個 (harness, model, task)：
1. provision 一份乾淨的 target repo 副本。
2. 以非互動模式啟動該 harness，注入指定 model 與 `reasoning_effort=high`，並在該 harness 可控範圍內固定輸出/token/thinking 預算；Claude Code / Haiku 4.5 必須固定 `CLAUDE_CODE_MAX_OUTPUT_TOKENS=64000` 與 `MAX_THINKING_TOKENS=63999`，餵入 task prompt。
3. 固定 timeout 與資源限制。
4. 擷取完整 trace（見 6.3）。
5. 跑 grader，記錄結果。
6. 全部存成不可變檔並 git commit。

各 harness 以**介面卡**封裝差異：
- Claude Code：經 claude-trace 啟動並攔截 API 流量取得 tool 序列、system prompt、tool 定義、thinking。
- Codex CLI：以其原生 log／exec 輸出取 trace。
- OpenCode：以其原生 log／事件取 trace。
- Hermes：以其 hook／trace 機制取 reasoning 與 tool 序列。

### 6.3 正規化 Trace schema（跨 harness 可比）

每次 run 一筆 JSON，欄位至少：

```
run_id, config_id, harness, harness_version, model, model_snapshot,
task_id, task_category, repeat_index, reasoning_effort,
tool_calls: [ {step, tool_name, args_summary, ts} ... ],   # 有序 tool 序列
reasoning_steps: [ ... ],                                   # planning/思考（可得者）
decision_points: [ {id, context, chosen_tool, alternatives} ... ],
outcome: { success: bool, grader_detail, final_diff_path },
tokens: { input, cached_input, output }, wall_time_s, turns,
runtime_budget: { max_output_tokens, thinking_budget_tokens, context_window_tokens, effort_source },
raw_log_path, env_lock_ref, timestamp
```

`raw_log_path` 指向該次原始 log（claude-trace jsonl/html、codex/opencode/hermes log），可回溯。

### 6.4 Pilot 驗證關

先跑 2 configs × 3 tasks 端到端，驗證：介面卡能擷取 tool 序列、grader 正確、trace 正規化無遺漏、成本/時間在預期內。Pilot 報告經確認後才放大 Phase 2。

---

## 7. Phase 2 — Baseline Factorial（6 configs × 20 tasks × 3 重複）

- 全量 6×20×3 ≈ 360 次 baseline run，產出正規化 trace 資料庫（不可變、committed）。
- 此資料庫即 **HCI 的 ground truth**（§11）。
- 同 config×task 的 3 次重複 → 估計 Noise（隨機誤差）。

---

## 8. Phase 3 — M1–M4 白箱歸因（四法 × 四 harness）

四法皆做、四 harness 皆做；每法跑在**有分歧的 decision-point 子集**（歸因最重要之處），而非機械式全 20×6，以兼顧忠於 proposal 與期限可完成。

| 方法 | 內容 | 各 harness 實作途徑 |
|------|------|------|
| M1 system prompt ablation | 移除／替換 system prompt 段落 | CC：依 2.1.88 restored-src 定位段落，patch 安裝後 cli.js 或用支援的覆寫機制；OpenCode/Codex/Hermes：改其 prompt 來源 |
| M2 tool 定義擾動 | rename、改 docstring、移除特定 tool | 各 harness 改其 tool registry / 定義（CC 可經 MCP 工具覆寫 + restored-src 參照） |
| M3 行為 counterfactual swap | 改寫 task input | harness-agnostic，統一在 task 層改寫 |
| M4 planning-loop trace | hook 攔截 reasoning step | CC：claude-trace 擷取；OpenCode/Codex/Hermes：各自 hook/trace |

每個方法 × decision point 量測 attribution 如何位移；交叉比較四法是否對同一 decision point 給出一致歸因（→ RQ1）。

---

## 9. Phase 4 — 指標與分析

**核心指標**
- **Jaccard 相似度**：兩 config 在同 task 的 tool 集合重疊。
- **Disagreement rate**：tool 序列分歧程度。
- **Success 關聯**：disagreement 與任務成敗的相關（→ RQ2，governance trigger 假說）。
- **2×3 factorial 分解**：harness 主效應、model 主效應、交互作用各解釋多少 tool 選擇差異（→ RQ3）。
- **方法一致性**：M1–M4 對同一 decision point 的 attribution 一致性與不一致 pattern（→ RQ1）。

**Agent-card 五維矩陣**（→ RQ4）：fidelity / stability / robustness / actionability / governability，由上述指標彙整為每個 harness 的卡片。

所有圖表（factorial 長條/熱圖、Jaccard 矩陣、disagreement-vs-failure 散點、方法一致性混淆圖、agent-card）皆程式產生並 committed，作為報告素材與稽核軌跡。

---

## 10. Phase 5 — 交付物

- 結果報告（含上述圖表）、agent-card 矩陣、PPT 錄影素材（依 proposal）。
- PPT/報告的環境設定頁必須揭露：harness 版本、模型 snapshot、provider route、reasoning effort、Claude Code 的 `max_tokens=64000` / `thinking.budget_tokens=63999` / 200k context window、以及 raw logs 不進 git 但 sanitized trace summary committed 的證據鏈。
- 完整 trace 資料庫、grader、runner、分析腳本，全 committed 並推上 GitHub。

---

## 11. 與 HCI 的介面

HCI（`hci-agent-attribution`）消費本專案的：
- 6 configs × 20 tasks（×重複）正規化 trace。
- 每個 decision point 的 ground-truth 歸因標籤（harness 主效應 / model 主效應 / 交互 / 雜訊），供 HCI 配 20 對 contrastive pair。

介面契約：HCI 只讀 trace JSON 與 ground-truth 標籤檔；不反向修改 xAI 任何產物。

---

## 12. 風險與限制

- **小模型難度天花板**：DeepSWE / SWE-Bench-Pro-Hard 對 Haiku 4.5、gpt-5.4-mini 偏難（gpt-5.4-mini 在 DeepSWE 僅 24% pass@1）。對策：Tier 1 取易題、Tier 2 難度校準。
- **Claude Code 白箱深度**：閉源 CLI，雖有 2.1.88 restored-src 與 claude-trace，M1/M2 的 ablation 仍可能受限於可 patch 的範圍；如有限制將如實標註。
- **樣本量**：重複 3 次對 Noise 估計仍偏小；factorial 分解的統計檢定力有限，結論以效應量與描述為主、避免過度推論。
- **decision-point 子集選取偏誤**：M1–M4 跑在高分歧子集，可能高估歸因清晰度；選取準則須預先定義並記錄。
- **provider 行為漂移**：原生 API 模型行為可能隨時間更新；以帶日期 snapshot 釘死降低風險，並記錄實驗日期。

## 13. 未來展望取向（報告用）

在「研究限制與未來展望」段落，討論釘死舊版未實裝的新功能（例如 Claude Code 後續版本的 `/goal` 等新機制）對 harness 行為與歸因可能造成的影響，以展現對時事的掌握與全盤考量，並指出後續可在新版本上重跑以驗證結論穩定性。仍須扣回本研究的歸因主軸。

## 14. 決策紀錄（brainstorming 結論）

| 決策 | 選擇 | 理由 |
|------|------|------|
| 保真度 | 全做 | 使用者指示；資源與可行性已確認 |
| Haiku 路由 | Anthropic 原生 | Claude Code 零轉譯、跨 harness 同後端、最忠實 |
| 目標程式庫 | 單一受控專案 + benchmark 取材 | 兼顧可控性、可引用 provenance、小模型可完成性 |
| 重複次數 | 3 | Noise 估計最穩、信心曲線最有本 |
| ablation 廣度 | 高分歧 decision-point 子集 | 忠於 proposal 且期限可完成 |
| Hermes 實例 | 全新乾淨、隔離 | 避免既有記憶污染、追求嚴謹 |
| Pilot | 先行 | 風險控制，非縮減範圍 |

## 15. 相關工作定位（report framing）

- **Artificial Analysis Coding Agents**：已做「固定模型、比 harness」的 Harness Comparison（Claude Code / Cursor / OpenCode），且明言不加自訂 relay header 以保代表性（與本研究設計取捨一致）。本研究在其黑箱跑分之上，新增白箱歸因（M1–M4）、模型軸、交互分解與 agent-card 治理。
- **DeepSWE（Datacurve）**：contamination-free、手寫 behavior verifier、long-horizon；採 mini-swe-agent 固定 harness 比模型——與本研究「固定任務、變 harness、做歸因」互為對照。
- **SWE-bench Verified**：model-card 級標準、hidden-test 評分，作為 Tier 1 任務錨點。
