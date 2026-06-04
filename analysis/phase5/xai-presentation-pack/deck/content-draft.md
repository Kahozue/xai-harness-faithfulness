# xAI 期末簡報 — 27 頁唯一基準稿 v3

狀態：canonical outline（2026-06-05）。舊 24 頁 HTML deck / index.html 不再作為基準；後續若到其他工具製作 PPT，請以本文件為唯一內容來源。

本版採納 2026-06-05 審稿修正：
- 案例頁改用資料表真實對齊的 `XAI-C03 / bugfix-t2-03 / OpenCode vs Hermes`，不再誤寫 Hermes vs Codex。
- 全部資料映射改以 27 頁為準，不再沿用 24 頁 slide map。
- 表格檔名以實際 pack 檔名為準（hyphen，例如 `case-candidates.csv`）。
- 明確定義本研究的 faithfulness / explain target。
- M1/M2 統一為 source/dossier/tool-surface evidence，不宣稱 uniform runtime ablation。
- 限制補上 model/provider route confound、effort 對齊非完全等價、agent-card 部分維度只作 coverage gate、描述性統計非因果推論。

定位：聽眾是資管所同學與老師。主線是 xAI，不做 HCI human-study claim。每頁都要回答「這一頁如何幫我解釋 agent 行為差異從何而來」。

---

# 第一幕｜鉤子與問題

## 1 · 封面
**要講的內容**：題目「Faithfulness of the Harness — 歸因 Agent 的工具選擇分歧」。副標：「固定同一個任務與可控環境，只換 harness / model route，agent 的工具路徑就分岔；我們用白箱證據把差異歸因到 harness、model+provider route 與交互。」一句定位：這是 pipeline-level 的 xAI 研究，不是 agent 排行榜。

**圖表/資料**：無。

## 2 · 研究背景與動機 ★
**要講的內容**：LLM coding agent 不是只有模型本身，還有外層 harness：system prompt、tool schema、planning loop、memory、session state、執行限制。業界常看成功率，但成功率會遮住過程分歧：兩個 agent 都 pass，工具路徑可能完全不同；一個 fail，也可能是 harness 沒給對工具、不是模型能力不足。若不能解釋分歧來源，就很難談信任、重現與治理。

**圖表/資料**：用 `charts/xai-case-card-01.svg` 作為同任務分歧鉤子即可；口頭說它只是示例，不是結論。

## 3 · Faithfulness 定義與 RQ1–RQ4 ★
**要講的內容**：先定義 explain target。這裡的 faithfulness 不是讀取 hidden chain-of-thought，也不是宣稱知道模型「心裡真正原因」；而是問：**可觀測 trace、prompt/tool 表面、counterfactual rerun 是否能忠實支持我們對工具路徑分歧的歸因**。四個 RQ：
- RQ1：M1–M4 對同一 decision point 的歸因是否一致？
- RQ2：高 tool-sequence disagreement 是否與任務失敗相關，能不能當 governance trigger？
- RQ3：分歧主要來自 harness、model+provider route，還是兩者交互？
- RQ4：能否把歸因結果濃縮成有邊界的 agent-card？

**圖表/資料**：四格 RQ；頁腳註明 hidden CoT omitted。

---

# 第二幕｜認識研究對象：harness

## 4 · 什麼是 harness？為何是這四個 ★
**要講的內容**：harness 是模型外面決定「收到什麼指令、能用什麼工具、怎麼規劃、怎麼記憶、怎麼執行」的 scaffolding。選 Claude Code、Codex CLI、OpenCode、Hermes，是因為它們橫跨閉源原生、可觀測黑箱、多 provider、開源通用 agent，剛好能觀察 harness 差異。

**圖表/資料**：四 harness 一覽表：來源、版本、開放程度、白箱可見度。

## 5 · 四個 harness 的機制對照 ★
**要講的內容**：四者的 prompt/tool/planning/memory 本來就不同：
- Claude Code：Anthropic 原生、2.1.88、可用 claude-trace 觀察 API request；rich tool surface。
- Codex CLI：OpenAI 原生、0.136.0；外層可觀測、核心原生 binary；工具主要是 `exec_command` / `apply_patch`。
- OpenCode：多 provider，npm 層可讀，部分 prompt 不完全外露；tool surface 較小。
- Hermes：Nous Research、0.13.0、Python 開源，memory/context 機制最豐富。

重點：這些差異就是 M1/M2 能歸因的來源，但它們不是「公平化後消失的雜訊」，而是 agent 產品本身的一部分。

**圖表/資料**：harness 機制對照表；來源可連到 dossier / environment controls。

---

# 第三幕｜方法與管線

## 6 · 為何用白箱歸因 + M1–M4 ★
**要講的內容**：黑箱 success rate 只回答「有沒有過」，不能回答「為什麼走這條路」。本研究用四種互補證據：
- M1 system prompt evidence：source / dossier / captured request 中可見的 prompt 結構。
- M2 tool-surface evidence：工具集合、工具描述、可用 affordance。
- M3 behavioral counterfactual：真的改寫 task input 後重跑，觀察工具路徑/成敗是否位移。
- M4 planning-loop trace：比較可見 trace、tool-call sequence、reasoning markers。

重要邊界：M1/M2 不是四個 harness 都做了完全一樣的 runtime ablation；閉源/原生工具可 patch 程度不同，所以只宣稱 source-derived / dossier-derived / tool-surface attribution。

**圖表/資料**：`charts/method-evidence-ladder.svg`。

## 7 · 研究設計總覽 ★
**要講的內容**：設計骨架：固定 task suite、固定版本、固定可控 route/effort，變動 harness 與 model route，收集 360 條 formal trace。流程先 pilot，確認 runner、grader、trace schema、成本時間，再跑 6 configs × 20 tasks × 3 repeats。Phase 3 counterfactual 只當案例/方法證據，不混進 baseline statistics。

**圖表/資料**：`charts/research-design-pipeline.svg`、`headline-stats.csv`。

## 8 · 6 configs：怎麼分清楚來源 ★
**要講的內容**：6 格不是隨便擺。OpenCode/Hermes 同時搭 Haiku 與 GPT-mini，是 crossed cells，可估交互；Claude Code 只搭 Haiku、Codex 只搭 GPT-mini，是 anchor cells。橫向看同 model 換 harness，縱向看同 harness 換 model route。限制先講清楚：Haiku 經 Anthropic，GPT-mini 經 OpenAI，所以 model effect 在本研究中更精確地說是 **model+provider route effect**。

**圖表/資料**：`charts/config-routing-grid.svg`。

## 9 · 設計取捨：排除什麼、為何
**要講的內容**：
- 不納入 Antigravity CLI：版本時點太新、harness 不成熟，會引入不穩定變因。
- 不用反代理硬改 route：官方 harness 搭官方預設路由是產品行為的一部分；反代理格式轉換會引入額外變因。
- 不用 SWE-bench Verified：aarch64/docker/舊依賴與 oracle 漂移成本太高，且它更偏 patch correctness，不直接對準 tool-path divergence。
- 選 Aider-polyglot / Exercism 純 Python benchmark：可追 provenance，可自動評分，小模型有足夠通過率避免全失敗。

**圖表/資料**：`tables/design-tradeoffs.csv`；內容需補上本頁四條，不只原始五條。

## 10 · 實驗管線詳細流程 ★
**要講的內容**：一次 run 的流程：provision 乾淨 target repo → 剝掉 hidden graders → 建全新 HOME → 非互動啟動 harness → 注入 model/route/可控 effort → timeout=900s → capture raw/private/public trace → repo mutation guard → hidden pytest grader → normalize trace → immutable public trace + private audit。這頁要讓觀眾知道不是在唬爛，是可重現 pipeline。

**圖表/資料**：完整 8 步流程圖，可從 `charts/research-design-pipeline.svg` 延伸或重畫。

## 11 · 環境鎖與可重現性 ★
**要講的內容**：固定 harness 版本、model snapshot、provider route、可控 budget。Claude Code 用 2.1.88 tarball 離線安裝；claude-trace 1.0.4 攔截 request，直接驗證 system prompt、tool definitions、`max_tokens=64000`、`thinking_budget=63999`、Haiku 200k context。OpenCode/Codex/Hermes 也記錄版本與 route。語氣要精準：不是所有 harness 都有完全等價的 token/thinking 控制；表裡空值代表該 harness 沒有相同可觀測欄位。

**圖表/資料**：`charts/environment-controls-matrix.svg`、`tables/environment-controls.csv`。

## 12 · 隔離與污染／越界防護
**要講的內容**：每次 run 都用新的 HOME，不共用 session/history/memory/log。Hermes 用獨立 `HERMES_HOME`，不碰生產 Hermes。hidden tests 不進工作目錄；grader 用完即刪；repo baseline 被改動會被偵測、隔離、還原。第一批 Phase 2 因 shared HOME 風險整批作廢重跑，這件事可口頭帶，證明實驗不是粉飾。

**圖表/資料**：隔離層次圖；可補在 PPT 裡重畫。

## 13 · 任務套件與評分機制 ★
**要講的內容**：20 題，5 類 × 4：bug_fix、rename、add_tests、add_logging、benchmark。Tier 1 是 benchmark provenance，Tier 2 是自撰受控 repo。評分不用更強模型當裁判，而是 hidden pytest / unittest：全綠才 pass；Tier 2 驗 behavior property，不比 patch 字串。難度目的不是排行榜，而是讓小模型有成功也有失敗，保留可分析訊號。

**圖表/資料**：`charts/task-suite-composition.svg`；可另畫 grader flow。

## 14 · Trace schema 與證據強度 ★
**要講的內容**：四個 harness 各有不同 log 形式，所以統一成 normalized trace：tool-call sequence、tool family、success、tokens/budget metadata、raw/private refs、evidence levels。每個欄位標 direct / source-derived / inferred / unknown，避免把不可見的東西講成看見了。

**圖表/資料**：`charts/trace-schema-evidence.svg`、`charts/method-evidence-ladder.svg`。

## 15 · 執行實況
**要講的內容**：展示 runner CLI 與 claude-trace 截圖。重點不要講「raw log 在伺服器不進 git」這種瑣事，而是說：原檔有留存、public trace 可重跑驗證、private audit 可追溯，公開層做了去敏。

**圖表/資料**：`screenshots/runner-cli-execution.png`、`screenshots/claude-trace-system-prompt.png`。

---

# 第四幕｜結果：回收 RQ

## 16 · 資料規模 ★
**要講的內容**：formal baseline 是 360 traces = 6 configs × 20 tasks × 3 repeats，整體成功率 295/360 = 81.9%。另有 pilot 和 Phase 3 counterfactual，但不混入 baseline。資料完整性 gate 通過。

**圖表/資料**：`charts/trace-inventory.svg`、`tables/headline-stats.csv`。

## 17 · Controlled vs Benchmark 分流
**要講的內容**：controlled success 267/288 = 92.7%，benchmark success 28/72 = 38.9%。這兩類難度與 provenance 不同，pooled 平均會誤導，所以結果解讀要分開。

**圖表/資料**：`charts/controlled-vs-benchmark.svg`、`charts/factorial-by-split.svg`。

## 18 · 怎麼量分歧：Jaccard + sequence disagreement ★
**要講的內容**：先講量法再講圖。我們把 tool name canonicalize 成 tool family，計算 tool-set Jaccard，也用 normalized edit distance 混合成 sequence disagreement。這避免不同 harness 的工具命名差異直接支配結果，但仍保留路徑差異。結果顯示 Codex anchor 與其他 config 的工具集合重疊較低，分歧是結構化的，不像純隨機。

**圖表/資料**：`analysis/phase4/figures/jaccard-matrix.svg`；補一句 selection score 來自 `sequence_divergence + 0.25 * success_gap`。

## 19 · 分歧來自誰：Factorial 對比（RQ3）★
**要講的內容**：描述性對比：同 model 換 harness、同 harness 換 model+provider route、兩者都換。結果可說「mixed 對比的 sequence disagreement 較高」，但不要下強因果。因 Claude Code/Codex 是 anchor cells，交互只能靠 OpenCode/Hermes crossed cells 支持。

**圖表/資料**：`analysis/phase4/figures/factorial-contrast-bars.svg`、`tables/factorial-summary.csv`。

## 20 · 分歧重要嗎：分歧 vs 成敗（RQ2）★
**要講的內容**：資料中 sequence disagreement 與 success gap 的描述性 Pearson r ≈ 0.003，近乎無關。這不是證明分歧沒有風險，而是說：在這個 20-task suite 裡，不能單靠「路徑分歧高」當 fail/gov trigger；治理要看 evidence path、任務類型、case-level diagnosis。

**圖表/資料**：`analysis/phase4/figures/disagreement-success-scatter.svg`、`tables/success-association.csv`。

## 21 · M1–M4 一致性（RQ1）★
**要講的內容**：在 20 個高分歧 decision labels 中，M1–M4 完全一致 10/20；標籤分布 harness_main_effect=6、interaction=8、model_main_effect=6。解讀：很多分歧不是單一來源，而是 harness 與 model+route 的交互。限制要就地說：這是 selected high-divergence subset，不是全體 prevalence。

**圖表/資料**：`analysis/phase4/figures/method-consistency.svg`、`charts/phase3-label-summary.svg`。

## 22 · 案例深度走查：XAI-C03（核心頁）★
**要講的內容**：用真實對齊資料的 `XAI-C03 / bugfix-t2-03 / OpenCode vs Hermes / Haiku`。現象：OpenCode dominant path 是 `shell -> read -> read -> read -> plan -> edit -> read -> shell...`，Hermes 是 `read -> edit`，兩者 baseline 都 0/3，但路徑與語意 convention 不同。M1：OpenCode system prompt partial visibility，Hermes 三層 prompt/memory 可讀，起始策略不同。M2：OpenCode tool surface 小，Hermes 有 search/memory/context affordance。M3：semantic counterfactual repeat 401 實際重跑，檢查 task wording convention 改變後是否位移。M4：比對 baseline/counterfactual visible trace。結論：此例標為 interaction / semantic_output_convention，4/4 agreement，高 confidence。

**圖表/資料**：`charts/xai-case-card-03.svg`、`tables/case-candidates.csv` 第 `XAI-C03`。備援可用 `XAI-C06 / addlog-t2-03 / Hermes vs Codex` 講 harness_main_effect，但不要混成同一案例。

## 23 · Agent-card 五維（RQ4）★
**要講的內容**：五維：fidelity、stability、robustness、actionability、governability。務必說清楚：這是本 suite 的 descriptive proxy，不是通用能力分數。尤其 actionability/governability 在目前資料表全是 1.0，應解釋為「trace coverage / diagnosability gate 全通」，不是可區分的能力排名；若要做更強治理卡，未來要換成可見度、可改動性、ablation 支援度等更有差異的指標。

**圖表/資料**：`analysis/phase4/figures/agent-card-matrix.svg`、`tables/agent-card-matrix.csv`。

---

# 第五幕｜所以呢 + 穩健性與未來

## 24 · 從歸因到行動 ★
**要講的內容**：把 finding 轉成治理建議：
- 只報 pass/fail 不夠，要揭露 evidence path。
- first-tool strategy 因 harness 而異，若治理重要，要標準化或揭露初始探索方式。
- benchmark 與 controlled 要分流，不要 pooled 後過度解讀。
- M1–M4 只部分一致，所以 agent-card 必須帶 confidence/caveat。

**圖表/資料**：`charts/attribution-action-map.svg`、`tables/action-implications.csv`。

## 25 · 限制與非過度宣稱 ★
**要講的內容**：
- 20-task Python suite，不代表所有 coding-agent 工作。
- controlled 與 benchmark provenance/難度不同，需分開解讀。
- Hermes 是通用 agent，Claude Code/Codex 更偏 coding agent，專用 vs 通用可比性有限。
- Claude Code/Codex 是 anchor cells，未完全 crossed。
- model effect 更精確是 model+provider route effect。
- effort/budget 只能在各 harness 可控範圍內對齊，非完全等價。
- Phase 3 labels 是高分歧選樣，不是 prevalence。
- M1/M2 多為 source/dossier/tool-surface evidence，非 uniform runtime ablation。
- hidden CoT omitted。
- 結果是描述性統計與案例歸因，不是廣義因果宣稱。

**圖表/資料**：`tables/limitations.csv`；這張不要只念清單，要說「我知道我的證據邊界在哪」。

## 26 · 未來展望 ★
**要講的內容**：下一步：擴到非 Python、大型 repo、long-horizon；在新版 harness 上重跑；對 `/goal`、memory、plan mode 做開/關對照；讓 agent-card 的 actionability/governability 改成真正有差異的可見度/可干預性指標；把 trace/case pack 轉給後續 HCI study 當 ground truth，但 HCI 結論要另做 human study。

**圖表/資料**：`tables/future-work.csv`。

## 27 · 收束
**要講的內容**：呼應開場：「換個 harness，路徑就不同；重點不是誰比較強，而是我們能不能說清楚差異從何而來。」總結三句：第一，harness 會系統性塑造 tool path；第二，分歧未必等於失敗，所以要 evidence-based governance；第三，faithful xAI 不是讀心，而是把可觀測證據、反事實重跑與邊界說清楚。

**圖表/資料**：結語大字；附錄放 source index、chart manifest、環境細節。

---

## 27 頁檢查清單

1. 舊 24 頁 HTML deck 不再作為內容來源。
2. `slide-data-map.json` 必須有 27 筆，且 table filenames 必須對得上實際 hyphen CSV。
3. 案例頁必須使用 `XAI-C03` + `xai-case-card-03.svg`，不可再寫 Hermes vs Codex。
4. 每個 RQ 都在結果區回收：RQ3=18/19，RQ2=20，RQ1=21，RQ4=23。
5. 每個限制要就地出現一次，25 頁再集中收束。
