# xAI 期末簡報（HTML deck）

`index.html` — 單檔橫向 swipe HTML 投影片，共 24 頁，主要語言繁體中文。

## 怎麼放
- 瀏覽器開 `index.html`，按 F 全螢幕；`← / →`、空白鍵、捲動或滑動翻頁。
- 需與 `../charts/`、`../screenshots/`、`../../../phase4/figures/` 同在 repo 內（用相對路徑引用圖表），請勿單獨搬移此檔。
- 字型走 Google Fonts（Poppins / Roboto / Noto Sans TC / Inconsolata），離線時退回系統 CJK（PingFang TC）。

## 怎麼做的
- 用 open-design 的 `simple-deck` seed（驗證過的 iframe 導覽 script，未改寫）。
- 套用 `design-systems/clean`（minimal）視覺：主色 `#3b82f6`、文字 `#111827`、留白優先、display 用 Poppins。
- 24 頁對齊 `../../../../docs/specs/2026-06-04-phase5-xai-presentation-structure.md` 的五幕問題鏈與 `../slide-data-map.json`。
- light/dark 交替換氣；圖表內標籤維持英文（學術可接受），slide 標題與說明為中文，數據取自 `../../phase4/metrics-summary.json` 等已驗證產物。

## 後續可選
- 用 headless 瀏覽器把每頁匯出成 PDF / 圖片，再組成 .pptx（open-design 另有 `pptx-html-fidelity-audit` 流程）。
- 內容文字若要逐頁微調，直接改 `index.html` 對應 `<section data-screen-label="...">`。
