# xAI Faithfulness Harness v2_5 HTML deck

Generated: 2026-06-05 (v2_5 — 基於 v2 版型修訂；原 v2 保留未動)

Canonical entry:
- `xAI-faithfulness-harness-v2_5.html`

Open Design sources used:
- `/Users/kahokozue/Desktop/AI/open-design/templates/deck-framework.html`
- `/Users/kahokozue/Desktop/AI/open-design/skills/simple-deck/SKILL.md`
- `/Users/kahokozue/Desktop/AI/open-design/craft/anti-ai-slop.md`
- `/Users/kahokozue/Desktop/AI/open-design/craft/color.md`
- `/Users/kahokozue/Desktop/AI/open-design/craft/typography.md`
- `/Users/kahokozue/Desktop/AI/open-design/design-systems/x-ai/DESIGN.md`

Hard checks designed into the build:
- 28 slides (v2 的 27 頁 + 新增「案例分析總覽」第 22 頁).
- Traditional Chinese primary copy; technical terms remain English.
- Structural slides are HTML/CSS, not pasted SVG.
- Data charts are copied from source SVG files.
- Screenshots are inserted with `object-fit: contain`.
- Slide 22 = 6-case gallery (case-candidates.csv); slide 23 = XAI-C03 deep dive.
- RQ recovery: RQ3 on 18/19, RQ2 on 20, RQ1 on 21, RQ4 on 24.

v2_5 修訂重點（基於 VPS 證據徹查）:
- Slide 03 邊界改寫（據 VPS 實 trace 徹查）：Anthropic/Haiku 的 thinking 可讀（Claude Code claude-trace 已擷取完整原文）；OpenAI/GPT-5.4-mini 的 reasoning 由 OpenAI 加密只回 summary+token；OpenCode 完整 prompt 不在 export 但可攔截 provider 請求取得。
- Slide 11 env matrix：Output/Thinking/Context 不再留白，填入實查的 harness/模型窗口並標 ✦pin / ○default / effort / —。
- Slide 22 新增案例總覽（6 組高分歧案例的左右對照、路徑、成敗、M1–M4）。
