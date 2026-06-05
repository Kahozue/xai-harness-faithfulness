#!/usr/bin/env python3
"""把 v2_7 HTML 的指定頁（1-based）渲染成 1920x1080 PNG。

用系統 Chrome（channel=chrome）以對齊 macOS 字型，確保重渲染的單頁與
原 preview 其餘頁面風格一致。

用法: python3 render-slide.py <slide_no> <out.png>
"""
import sys
from pathlib import Path
from playwright.sync_api import sync_playwright

HERE = Path(__file__).resolve().parent
HTML = (HERE / "xAI-faithfulness-harness-v2_7.html").as_uri()

n = int(sys.argv[1])
out = sys.argv[2]

with sync_playwright() as p:
    b = p.chromium.launch(channel="chrome")
    pg = b.new_page(viewport={"width": 1920, "height": 1080}, device_scale_factor=1)
    pg.goto(HTML)
    pg.evaluate(
        """(n)=>{
            document.documentElement.style.setProperty('--deck-scale','1');
            const s=[...document.querySelectorAll('.slide')];
            s.forEach((el,i)=>el.classList.toggle('active', i===n-1));
        }""",
        n,
    )
    pg.wait_for_timeout(400)
    el = pg.query_selector(".slide.active")
    el.screenshot(path=out)
    b.close()
print(f"rendered slide {n} -> {out}")
