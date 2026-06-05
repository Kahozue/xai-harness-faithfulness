# PPT 製作交付包（handoff）

給 AI 簡報工具用的完整素材包。內容對應唯一基準稿 `content-outline.md`（= 27 頁 v3），所有圖表/資料檔名與該稿一致。

## 資料夾
- `content-outline.md` — 唯一內容來源（27 頁逐頁講稿 + 每頁圖表 + 理由）。
- `charts/` — 21 張向量圖（SVG，matplotlib publication 風格；含 phase4 5 張）。
- `tables/` — 14 個資料表（CSV）。
- `screenshots/` — 2 張真實去敏截圖（PNG）。

## headline 數字（給標題/big-stat 用）
- formal traces：360（6 config × 20 task × 3 repeat）；整體成功率 295/360 = 81.9%。
- controlled 267/288 = 92.7%；benchmark 28/72 = 38.9%。
- disagreement vs success-gap：Pearson r ≈ 0.003（n=300，近乎無關）。
- M1–M4 完全一致：10/20 = 50%；label 分布 harness=6 / interaction=8 / model=6。

## 逐頁素材對應（27 頁）
| 頁 | 主題 | 圖（charts/ 或 screenshots/） | 表（tables/） |
|---:|---|---|---|
| 1 | 封面 | — | — |
| 2 | 背景與動機 | xai-case-card-01.svg | — |
| 3 | Faithfulness 定義 + RQ1–4 | — | — |
| 4 | 什麼是 harness / 為何這四個 | — | harness-overview.csv |
| 5 | 四 harness 機制對照 | — | harness-mechanism-comparison.csv |
| 6 | 為何白箱 + M1–M4 | method-evidence-ladder.svg | — |
| 7 | 研究設計總覽 | research-design-pipeline.svg | headline-stats.csv |
| 8 | 6 configs 路由 | config-routing-grid.svg | — |
| 9 | 設計取捨 | — | design-tradeoffs.csv |
| 10 | 管線詳細流程 | pipeline-flow.svg | — |
| 11 | 環境鎖與可重現性 | environment-controls-matrix.svg | environment-controls.csv |
| 12 | 隔離與污染防護 | isolation-hierarchy.svg | — |
| 13 | 任務套件 + 評分機制 | task-suite-composition.svg, grader-flow.svg | — |
| 14 | Trace schema + 證據強度 | trace-schema-evidence.svg, method-evidence-ladder.svg | — |
| 15 | 執行實況 | runner-cli-execution.png, claude-trace-system-prompt.png | — |
| 16 | 資料規模 | trace-inventory.svg | headline-stats.csv |
| 17 | controlled vs benchmark | controlled-vs-benchmark.svg, factorial-by-split.svg | — |
| 18 | Jaccard / disagreement（RQ3 前哨） | jaccard-matrix.svg | — |
| 19 | Factorial 對比（RQ3） | factorial-contrast-bars.svg | factorial-summary.csv |
| 20 | 分歧 vs 成敗（RQ2） | disagreement-success-scatter.svg | success-association.csv |
| 21 | M1–M4 一致性（RQ1） | method-consistency.svg, phase3-label-summary.svg | — |
| 22 | 案例深度走查 XAI-C03（核心） | xai-case-card-03.svg | case-candidates.csv（取 XAI-C03 列） |
| 23 | Agent-card 五維（RQ4） | agent-card-matrix.svg | agent-card-matrix.csv |
| 24 | 從歸因到行動 | attribution-action-map.svg | action-implications.csv |
| 25 | 限制與非過度宣稱 | — | limitations.csv |
| 26 | 未來展望 | — | future-work.csv |
| 27 | 收束（附錄） | — | source-index.csv, chart-manifest.csv |

## 本次新建的 5 個素材（原稿標「待補/可重畫」，已補齊）
- `tables/harness-overview.csv`（頁4）、`tables/harness-mechanism-comparison.csv`（頁5）— 由 dossier 事實整理。
- `charts/pipeline-flow.svg`（頁10）、`charts/isolation-hierarchy.svg`（頁12）、`charts/grader-flow.svg`（頁13）— matplotlib 同風格新繪。

## 給 AI 工具的提醒
- 主要語言繁體中文、禁 emoji；圖表內英文軸標保留即可。
- 每頁先講「這頁如何幫我解釋差異從何而來」，不要只貼數據（見 content-outline.md 各頁「要講的內容」）。
- 邊界務必就地呈現：anchor 未完全交叉、model effect = model+provider route、M1/M2 為 source/dossier evidence、agent-card 為描述性 proxy、hidden CoT omitted。
