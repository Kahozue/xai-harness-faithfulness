# Phase 5 — xAI 期末簡報結構與敘事主線

- 文件版本：v1（2026-06-04）
- 課程：xAI 期末專題（Faithfulness of the Harness）
- 狀態：簡報骨架與敘事主線已定，待逐頁填內容、再生 .pptx
- 範圍：**只做 xAI**。HCI human study 與信任校準等評估頁刻意排除，留給之後 HCI 那份。
- 對齊依據：`HCI_REPORT_NOON_REQUIREMENTS.md`（其中通用報告品質要求 xAI 全做到；HCI 評估專屬條目正確延後）
- 資料/圖表來源：`analysis/phase4/*.json`、`analysis/phase4/figures/*.svg`、`docs/verification/2026-06-04-phase4-analysis-report.md`

> 本文件定義簡報的「結構」與「說故事的邏輯」，不含實際數據文字；填內容時逐頁引用上列 Phase 4 產物。

---

## 0. 目的與範圍

xAI 這份簡報的任務：讓非實作者（資管所同學與老師）看懂——同一模型、同一任務、只換 harness，工具路徑就分岔；這差異是誰造成的、重不重要、能不能治理。

「完全對齊 `HCI_REPORT_NOON_REQUIREMENTS.md`」在這裡的定義：
- **通用報告品質要求**（背景→方法→結果、環境固定頁、token/thinking/context 寫清楚、標來源、多圖表、非過度宣稱、benchmark/受控分開、限制+未來、具體案例）→ xAI 全部滿足。
- **HCI 評估專屬**（human study、信任校準、安全感/清楚性評估、互動設計理念）→ 不放進 xAI，延後到 HCI 那份。這也符合「xai 做完再做 hci、別混用」。

---

## 1. 一句話主線與 ABT

**Logline**：同一個模型、同一個任務，只是換了 harness，工具路徑就不一樣——這差異是誰造成的、重不重要、能不能治理？我們用白箱方法把它拆開、量出來、變成一張可檢查的卡片。

**ABT throughline（全場骨幹）**
- **And（現況）**：Agent 都靠 harness 在跑，大家比的是成功率。
- **But（衝突）**：但固定模型、只換 harness，行為就分岔——黑箱跑分答不出「為什麼」。
- **Therefore（所以）**：所以我們做白箱歸因，把分歧拆成 harness／model／交互，並濃縮成 agent-card。

---

## 2. 讓「引導感」成立的三個機制

1. **拋問—回收**：RQ1–4（頁3）一次拋出，在結果區（頁15–19）一頁回收一個。觀眾全程知道「還欠哪個答案」。
2. **每頁結尾留鉤子**：每頁最後一句是下一頁的問題（見各頁承接句），頁與頁是因果而非並列。
3. **一個案例貫穿**：頁2 先用它當鉤子，頁20 用同一案例收束，首尾呼應、故事閉環。

★ = 建議口報核心路徑（若時間受限可只講 ★）。老師未鎖死時間，預設可走完整 24 頁；★ 僅作壓縮備案。

---

## 3. 五幕敘事結構（驅動問題 + 幕間承接 + 逐頁角色）

### 第一幕｜鉤子與問題：「這現象正常嗎？會出事嗎？」
- **1 封面** — 拋出主線一句話當副標，先給畫面。
- **2 ★ 背景與動機** — 現象示範：同模型換 harness → 路徑分岔；點出風險（信任、可重現、治理）。鉤子：那這差異能不能歸因？
- **3 ★ 研究問題 RQ1–4** — 把模糊焦慮收斂成四個明確問題。承諾：這四題稍後一一回收。

> 幕間承接：「要回答『差異是誰造成的』，只看成功率不夠——需要一套能拆開來看的方法。」

### 第二幕｜方法為回答問題而生：「那要怎麼才能可信地回答？」
- **4 ★ 研究設計總覽** — 答案骨架：固定任務、變 harness/model、白箱拆解（pipeline 圖）。
- **5 ★ 為何用白箱歸因** — 為什麼不能只看成功率：黑箱答不出「誰造成」。
- **6 決策紀錄／取捨**（輔）— 每個設計選擇的理由，讓老師知道不是隨便定（對應 design spec §14）。
- **7 ★ 環境鎖與可重現性** — 「比較」要有意義，前提是條件一致 → 釘死版本/snapshot/route/effort/`max_tokens=64000`/`thinking=63999`/200k context/raw-log 證據鏈（可信度地基）。
- **8 6 configs 與路由／隔離** — 固定環境下，6 格怎麼擺才能分離 harness 效應與 model 效應。
- **9 ★ 任務套件** — 拿什麼去問：20 題（5 類×4）、Tier1/Tier2、難度校準、可自動評分（標 provenance）。
- **10 Runner + 正規化 Trace schema**（輔）— 怎麼跑一次、怎麼把四種 harness 變成可比的同一格式（紀錄方法）。
- **11 ★ M1–M4 歸因方法** — 核心武器：四法各看一層，並標清楚證據邊界（M1/M2 source-derived、M3 direct-run、M4 trace；hidden CoT omitted）。
- **12 執行實況**（輔）— 不是紙上談兵：它真的在跑、trace 真的被擷取的樣子（claude-trace HTML、trace JSON、runner CLI 截圖）。

> 幕間承接：「方法到位、資料跑完——現在讓資料自己說話。」

### 第三幕｜結果，逐一回收 RQ：「那資料說了什麼？」
- **13 ★ 資料規模** — 手上有多少證據：360 條 formal trace（6×20×3）。
- **14 controlled vs benchmark 分開** — 先分流，免得結論被混淆。
- **15 ★ Jaccard 矩陣** — 差異**多大**？〔回收 RQ3 前半〕`figures/jaccard-matrix.svg`
- **16 ★ Factorial 分解** — 差異是**誰造成**：harness／model／交互（標 anchor-cell 邊界）。〔回收 RQ3〕`figures/factorial-contrast-bars.svg`
- **17 ★ 分歧 vs 成敗散點** — 這些分歧**重不重要**？〔回收 RQ2——誠實說目前近乎無關，這反而是亮點〕`figures/disagreement-success-scatter.svg`
- **18 M1–M4 一致性** — 四法**看法一致**嗎？〔回收 RQ1〕`figures/method-consistency.svg`
- **19 ★ Agent-card 五維矩陣** — 把上面全部**濃縮成卡片**（標描述性 proxy 邊界）。〔回收 RQ4〕`figures/agent-card-matrix.svg`
- **20 具體案例走查** — 用一個真實 decision point（含 M3 修改前後）把「分歧→歸因→卡片」整條串起來，抽象變具體（結果區收束高潮）。

> 幕間承接：「看懂差異從哪來——那這對『用 agent 的人』有什麼用？」

### 第四幕｜所以呢：「歸因完，能做什麼？」
- **21 ★ 從歸因到行動** — 歸因不是終點：轉成 prompt/tool-surface 設計建議與治理卡片。

> 幕間承接：「這些主張站得住腳嗎？我先自己劃清界線。」

### 第五幕｜穩健性與未來：「結論多穩？下一步？」
- **22 ★ 限制與非過度宣稱** — 只在這 20 題成立、benchmark/受控分開、小模型天花板、harness affinity 偏誤、跨語言·大型 repo 缺口、子集偏誤、M1/M2 邊界。
- **23 ★ 未來展望** — 怎麼補、釘死舊版未含新機制（如 /goal）的影響、這份 trace 的下游用途（一行帶過）。
- **24 附錄**（備援）— 相關工作（Artificial Analysis / DeepSWE / SWE-bench）、環境細節、引用來源清單、（可選）HTML 儀表板。

---

## 4. 24 頁完整結構表（交叉對照）

| 頁 | 幕 | 頁名 | 核心 | RQ | 產物／figure | 對應 doc 需求 |
|---:|---|---|:--:|---|---|---|
| 1 | 一 | 封面 |  |  |  |  |
| 2 | 一 | 研究背景與動機 | ★ |  |  | §2.1 |
| 3 | 一 | 研究問題 RQ1–4 | ★ | 全 |  | §1 理解性 |
| 4 | 二 | 研究設計總覽 + pipeline | ★ |  |  | §2.2 |
| 5 | 二 | 為何用白箱歸因 | ★ |  |  | §2.2 |
| 6 | 二 | 決策紀錄／取捨 |  |  |  | §3 設計取捨 |
| 7 | 二 | 環境鎖與可重現性 | ★ |  | metrics-summary（environment_controls） | §2.3, §2.4, §3 token |
| 8 | 二 | 6 configs、路由與隔離 |  |  |  | §2.4 |
| 9 | 二 | 任務套件 | ★ |  | registry.yaml、graders | §3 抽樣/校準/來源 |
| 10 | 二 | Runner + Trace schema |  |  | trace_schema | §6 紀錄方法 |
| 11 | 二 | M1–M4 歸因方法 | ★ |  | attribution-results | §2.2 |
| 12 | 二 | 執行實況（截圖） |  |  | claude-trace/CLI 截圖 | §2.5, §3.5 |
| 13 | 三 | 資料規模 | ★ |  | metrics-summary（overall） |  |
| 14 | 三 | controlled vs benchmark 分開 |  |  | metrics-summary（task_splits） | §3 分開 |
| 15 | 三 | Jaccard 矩陣 | ★ | RQ3 | jaccard-matrix.svg | §2.7 |
| 16 | 三 | Factorial 分解 | ★ | RQ3 | factorial-contrast-bars.svg | §2.7 |
| 17 | 三 | 分歧 vs 成敗散點 | ★ | RQ2 | disagreement-success-scatter.svg | §2.7 |
| 18 | 三 | M1–M4 一致性 |  | RQ1 | method-consistency.svg | §2.7 |
| 19 | 三 | Agent-card 五維矩陣 | ★ | RQ4 | agent-card-matrix.svg | §2.7 |
| 20 | 三 | 具體案例走查 |  |  | hci-case-pack、m3 counterfactual | §5 案例, §2.5 前後比較 |
| 21 | 四 | 從歸因到行動 | ★ |  | agent_cards | §5 提解法 |
| 22 | 五 | 限制與非過度宣稱 | ★ |  |  | §3 多條 |
| 23 | 五 | 未來展望 | ★ |  |  | §2 收尾 |
| 24 | 五 | 附錄 |  |  | 來源清單、（可選）dashboard | §2.6, §2 dashboard |

---

## 5. 與 HCI_REPORT_NOON_REQUIREMENTS.md 的對齊稽核

### 5.1 通用要求（xAI 全覆蓋）

| doc 條目 | 對應頁 |
|---|---|
| §2.1 前段研究背景（不喧賓奪主） | 2 |
| §2.2 先講方法、為何用、如何對應目標 | 4、5 |
| §2.3 測試環境固定版本 + 環境介紹 | 7 |
| §2.4 / §3 環境頁寫清 token/thinking/context/route/raw-log 證據鏈（不可只寫 high effort） | 7 |
| §2.5 / §3 過程截圖、操作流程、修改前後比較 | 12、20 |
| §2.6 / §3 引用來源在頁面或附錄標註 | 跨頁 footnote + 24 |
| §2.7 多用圖表/流程圖/比較圖 | 15–19、4 |
| §2 收尾未來展望（擴充/限制/下一步） | 22、23 |
| §2（可選）HTML 儀表板加分項 | 24（optional） |
| §3 benchmark 與受控題分開呈現 | 14 |
| §3 抽樣/難度校準/harness affinity 偏誤/跨語言·大型 repo 缺口 | 9、22 |
| §3 非過度宣稱（只支持這 20 題 suite） | 22 |
| §3 每個選擇對應設計取捨 | 6 |
| §5 補入具體案例、多種風險案例分析 | 20 |
| §5 用結果提出改善方向/解法 | 21 |
| §5 呈現欄位間依賴與關聯 | 結果頁敘事 |
| §6 數據解釋要講「為什麼」 | 跨頁慣例 |

### 5.2 HCI 評估專屬（xAI 不放，延後到 HCI 那份）

- human study：參與者來源、任務、比較條件、開放回饋、匿名與自願（§1、§3）。
- human study 指標：clarity、trust calibration、verification/action choice、perceived safety/control、cognitive load（§3）。
- 信任校準討論、介面信任/安全感/清楚性評估、針對哪些群體（§6）。
- human-in-the-loop 互動設計理念、「扣回 HCI」的 framing（§2、§6）。

> 素材銜接：頁19 agent-card、頁20 案例、`analysis/phase4/hci-case-pack.json` 之後可直接餵給 HCI 那份當證據素材，但 HCI 評估本身不在 xAI 簡報內。

---

## 6. 跨頁慣例（套用全簡報，非單頁）

1. 每頁底標資料來源（文獻/規格/工具/產物路徑）。
2. 每張結果頁附一句「為什麼會這樣」的成因解釋，不只放數值。
3. 圖表/表格/流程圖優先於長段文字。

---

## 7. 下一步

1. 逐頁填內容（spoken script 骨架 → 正式內容），承接句直接當講稿轉場。
2. 內容定稿後生 .pptx（介面語言繁中、禁 emoji）。
3. xAI 簡報完成後，再依本文件 §5.2 進 HCI 那份。
