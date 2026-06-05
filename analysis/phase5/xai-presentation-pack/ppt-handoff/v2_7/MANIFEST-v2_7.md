# xAI Faithfulness Harness v2_7 HTML deck

Generated: 2026-06-05 (v2_7; wording compressed for formal presentation)

Canonical entry:
- `xAI-faithfulness-harness-v2_7.html`

Design sources used:
- Open Design deck framework
- simple-deck skill guidance
- anti-slop, color, and typography craft notes
- x-ai design system

Hard checks designed into the build:
- 28 slides (v2 的 27 頁 + 新增「案例分析總覽」第 22 頁).
- Traditional Chinese primary copy; technical terms remain English.
- Structural slides are HTML/CSS, not pasted SVG.
- Data charts are copied from source SVG files.
- Screenshots are inserted with `object-fit: contain`.
- Slide 22 = 6-case gallery (case-candidates.csv); slide 23 = XAI-C03 deep dive.
- RQ recovery: RQ3 on 18/19, RQ2 on 20, RQ1 on 21, RQ4 on 24.

v2_7 修訂重點:
- Slide 02 改寫動機案例，移除需預先知道 XAI-C01 的說法。
- Slide 03 與 Slide 11 壓縮邊界文字，只保留 provider 可見度與欄位控制。
- Slide 05、07、09、11、12、13、16、17、22、27、28 改為正式簡報語氣。
- Slide 07 補上 20 題任務類型；Slide 27 加入平均 token 用量分析。
- 可見文字移除長破折號與 en dash。
- Slide 09 新增第六張取捨卡「reasoning effort 全部固定為 high」，補上 proposal 取捨③理由（低 effort 會把失敗誤歸因到模型 under-utilization 而非 harness），版面改為均衡 2x3。

PPTX 交付:
- `../xAI-faithfulness-harness-v2_7.pptx`（28 頁、16:9）由 `build-pptx-v2_7.py` 把 `preview/slide-01..28.png` 每頁整頁鋪滿生成；單頁重渲染用 `render-slide.py`（系統 Chrome，對齊 macOS 字型）。
