"""Spike: Chromium renders a newspaper-style HTML page to PDF; measure time and check layout features."""
import time
from pathlib import Path

from playwright.sync_api import sync_playwright

HTML = """<!doctype html><html><head><meta charset="utf-8"><style>
@page { size: A4; margin: 14mm; }
body { font-family: Georgia, serif; color:#111; }
.mast { text-align:center; border-bottom:3px double #111; margin-bottom:8px; }
.mast h1 { font-size:42px; margin:0; letter-spacing:1px; }
.cols { column-count:3; column-gap:16px; column-rule:1px solid #bbb; }
.lead { column-span: all; border-bottom:1px solid #111; padding-bottom:8px; margin-bottom:8px; }
.lead h2 { font-size:28px; margin:4px 0; }
article { break-inside: avoid; margin-bottom:10px; }
img { width:100%; }
</style></head><body>
<div class="mast"><h1>The Ayesha Morning</h1><div>Saturday, 17 October 2026 · Live edition</div></div>
<div class="cols"><div class="lead"><h2>Lead story headline</h2><p>Lead synthesis text. """ + "Lorem ipsum dolor sit amet. " * 40 + """</p></div>
""" + "".join(f"<article><h3>Brief {i}</h3><p>{'Summary text with citation [1]. ' * 12}</p></article>" for i in range(14)) + """
</div></body></html>"""

out = Path("spikes/out")
out.mkdir(parents=True, exist_ok=True)
t0 = time.perf_counter()
with sync_playwright() as p:
    b = p.chromium.launch()
    page = b.new_page()
    page.set_content(HTML, wait_until="networkidle")
    page.pdf(path=str(out / "edition.pdf"), format="A4", print_background=True)
    b.close()
pdf = (out / "edition.pdf").read_bytes()
print(f"pdf bytes {len(pdf)} pages~{pdf.count(b'/Type /Page') - pdf.count(b'/Type /Pages')} seconds {time.perf_counter() - t0:.2f}")
