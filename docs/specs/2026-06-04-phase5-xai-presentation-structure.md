# Phase 5 — xAI 期末簡報 27 頁 canonical structure

- 文件版本：v2（2026-06-05）
- 課程：xAI 期末專題（Faithfulness of the Harness）
- 狀態：**27 頁 canonical outline**。舊 24 頁 HTML deck 已廢棄，不再作為 PPT 來源。
- 唯一逐頁基準：`analysis/phase5/xai-presentation-pack/deck/content-draft.md`
- 資料/圖表來源：`analysis/phase5/xai-presentation-pack/slide-data-map.json`、`analysis/phase5/xai-presentation-pack/tables/`、`analysis/phase5/xai-presentation-pack/charts/`、`analysis/phase4/figures/`
- 範圍：只做 xAI。HCI human study、trust calibration、perceived safety、cognitive load 等評估延後到 HCI 報告。

## 1. 核心定義

**Logline**：同一任務、同一可控環境下，只要換 harness / model route，agent 工具路徑就會分岔；本研究用可觀測白箱證據，把分歧歸因到 harness、model+provider route 與交互。

**Faithfulness 定義**：本研究的 faithfulness 不是讀取 hidden chain-of-thought，也不是宣稱知道模型內心真正理由；而是檢查 **可觀測 trace、prompt/tool surface、source/dossier evidence、counterfactual rerun 是否足以忠實支持工具路徑分歧的歸因**。

**主要邊界**：

- M1/M2 是 source/dossier/captured-prompt/tool-surface evidence，不宣稱四個 harness 都做了 uniform runtime ablation。
- model effect 更精確是 model+provider route effect，因 Haiku 走 Anthropic、GPT-mini 走 OpenAI。
- reasoning effort 只在各 harness 可控範圍內對齊，不宣稱完全等價。
- Phase 3 labels 是 selected high-divergence subset，不是 prevalence。
- Agent-card 是本 suite 的 descriptive proxy；actionability/governability 目前作為 coverage gate，不是可區分能力排名。

## 2. 27 頁結構

| 頁 | 幕 | 頁名 | 核心 | RQ | 主要資料/圖表 | 必講邊界 |
|---:|---|---|:--:|---|---|---|
| 1 | 一 | 封面 | ★ |  |  | 舊 24 頁 deck 廢棄 |
| 2 | 一 | 背景與動機 | ★ |  | `xai-case-card-01.svg` | hook 不是 prevalence |
| 3 | 一 | Faithfulness 定義與 RQ1-RQ4 | ★ | 全 |  | hidden CoT omitted |
| 4 | 二 | 什麼是 harness？為何是這四個 | ★ |  | `config-summary.csv` | 先介紹研究對象 |
| 5 | 二 | 四個 harness 的機制對照 | ★ |  | `first-tool-family-stacked-by-config.svg` | prompt/tool/planning/memory 是 agent 行為的一部分 |
| 6 | 三 | 為何用白箱歸因 + M1-M4 | ★ | RQ1 | `method-evidence-ladder.svg` | M1/M2 非 uniform runtime ablation |
| 7 | 三 | 研究設計總覽 | ★ |  | `research-design-pipeline.svg` | baseline vs counterfactual 分開 |
| 8 | 三 | 6 configs：怎麼分清楚來源 | ★ | RQ3 | `config-routing-grid.svg` | model+provider route confound |
| 9 | 三 | 設計取捨 |  |  | `design-tradeoffs.csv` | Antigravity、反代理、benchmark、SWE-bench 取捨 |
| 10 | 三 | 實驗管線詳細流程 | ★ |  | pipeline flow | 8 步 pipeline、防污染 |
| 11 | 三 | 環境鎖與可重現性 | ★ |  | `environment-controls-matrix.svg` | effort/token/thinking 不完全等價 |
| 12 | 三 | 隔離與污染／越界防護 |  |  | trace/policy refs | per-run HOME、hidden tests、mutation guard |
| 13 | 三 | 任務套件與評分機制 | ★ |  | `task-suite-composition.svg` | hidden pytest/unittest，無 LLM judge |
| 14 | 三 | Trace schema 與證據強度 | ★ |  | `trace-schema-evidence.svg` | direct/source-derived/inferred/unknown |
| 15 | 三 | 執行實況 |  |  | screenshots | 原檔可追溯、public 層去敏 |
| 16 | 四 | 資料規模 | ★ |  | `trace-inventory.svg` | formal baseline 360，不是 public JSON 396 |
| 17 | 四 | Controlled vs Benchmark 分流 | ★ |  | `controlled-vs-benchmark.svg` | pooled 平均會誤導 |
| 18 | 四 | Jaccard + sequence disagreement | ★ | RQ3 | `jaccard-matrix.svg` | tool family canonicalization |
| 19 | 四 | Factorial 對比 | ★ | RQ3 | `factorial-contrast-bars.svg` | 描述性，不下強因果 |
| 20 | 四 | 分歧 vs 成敗 | ★ | RQ2 | `disagreement-success-scatter.svg` | r≈0.003 不是無風險證明 |
| 21 | 四 | M1-M4 一致性 | ★ | RQ1 | `method-consistency.svg` | high-divergence subset |
| 22 | 四 | 案例深度走查：XAI-C03 | ★ | RQ1/RQ3 | `xai-case-card-03.svg` | `bugfix-t2-03` 是 OpenCode vs Hermes，不是 Hermes vs Codex |
| 23 | 四 | Agent-card 五維 | ★ | RQ4 | `agent-card-matrix.svg` | descriptive proxy；兩維是 coverage gate |
| 24 | 五 | 從歸因到行動 | ★ | RQ4 | `attribution-action-map.svg` | evidence path > pass/fail |
| 25 | 五 | 限制與非過度宣稱 | ★ | 全 | `limitations.csv` | 集中收束所有證據邊界 |
| 26 | 五 | 未來展望 | ★ |  | `future-work.csv` | 新版 harness、/goal、memory、HCI study |
| 27 | 五 | 收束 | ★ |  | source index / appendix refs | faithful xAI 不是排行榜也不是讀心 |

## 3. RQ 回收路徑

- RQ1（方法一致性）：第 21 頁主回收，第 22 頁案例展示。
- RQ2（分歧與失敗）：第 20 頁主回收。
- RQ3（效應分解）：第 18、19 頁主回收，第 22 頁案例展示。
- RQ4（治理卡）：第 23、24 頁主回收。

## 4. Canonical artifact rules

1. PPT 製作只准讀 `content-draft.md` 與 `slide-data-map.json`。
2. 不准以已刪除的 24 頁 `deck/index.html` 作為頁碼、截圖或內容來源。
3. `slide-data-map.json` 必須維持 27 筆，且每個 table/chart path 必須可解析。
4. 案例頁的主案例固定為 `XAI-C03 / bugfix-t2-03 / OpenCode vs Hermes / xai-case-card-03.svg`。
5. HCI claim 只可在未來工作或邊界中提及，不可當 xAI 結果。

## 5. 下一步

1. 依 `content-draft.md` 到外部工具製作 PPT。
2. 製作時逐頁引用 `slide-data-map.json` 的資料/圖表。
3. 完成初版 PPT 後，再做一次頁碼、案例、邊界、圖表路徑一致性檢查。
