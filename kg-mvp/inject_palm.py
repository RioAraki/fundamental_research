# -*- coding: utf-8 -*-
"""把 palm_graph.svg / demo1-5.svg / panel.html / palm_demo.txt 注入 .lavish/palm-mvp.html"""
import html
import re
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")
root = Path(__file__).parent
report = root.parent / ".lavish" / "palm-mvp.html"

page = report.read_text(encoding="utf-8")


def load_svg(name, uid):
    svg = (root / "out" / f"{name}.svg").read_text(encoding="utf-8")
    return svg.replace('id="my-svg"', f'id="{uid}"').replace("#my-svg", f"#{uid}")


page = page.replace("<!--GRAPH-SVG-->", load_svg("palm_graph", "svg-palm"))
for i in range(1, 6):
    page = page.replace(f"<!--DEMOSVG:{i}-->", load_svg(f"demo{i}", f"svg-demo{i}"))

panel = (root / "out" / "panel.html").read_text(encoding="utf-8")
page = page.replace("<!--PANEL-->", panel)

demo = (root / "out" / "palm_demo.txt").read_text(encoding="utf-8")
blocks = re.split(r"={72}\n【问题】.*?\n={72}\n", demo)[1:]
assert len(blocks) == 6, f"期望 6 段,实际 {len(blocks)}"
for i, b in enumerate(blocks, 1):
    page = page.replace(f"<!--DEMO:{i}-->", html.escape(b.strip()))

assert not re.search(r"<!--(GRAPH|DEMO|PANEL)", page), "有占位符未替换"
report.write_text(page, encoding="utf-8")
print(f"注入完成,页面 {len(page)//1024} KB")
