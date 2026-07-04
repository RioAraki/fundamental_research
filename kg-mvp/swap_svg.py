# -*- coding: utf-8 -*-
"""按 id 把 palm-mvp.html 里已注入的 SVG 替换为新渲染版本(lavish 会热重载)。"""
import re
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")
root = Path(__file__).parent
report = root.parent / ".lavish" / "palm-mvp.html"
page = report.read_text(encoding="utf-8")

PAIRS = [("palm_graph", "svg-palm")] + [(f"demo{i}", f"svg-demo{i}") for i in range(1, 6)]
for name, uid in PAIRS:
    svg = (root / "out" / f"{name}.svg").read_text(encoding="utf-8")
    svg = svg.replace('id="my-svg"', f'id="{uid}"').replace("#my-svg", f"#{uid}")
    pattern = re.compile(f'<svg id="{uid}".*?</svg>', re.DOTALL)
    assert pattern.search(page), f"未找到 {uid}"
    page = pattern.sub(lambda m: svg, page, count=1)
    print(f"{uid} 已替换")

report.write_text(page, encoding="utf-8")
print(f"完成,页面 {len(page)//1024} KB")
