# -*- coding: utf-8 -*-
"""把 graph.svg 与 demo_output.txt 注入 .lavish/olive-mvp.html 的占位符。"""
import html
import re
from pathlib import Path

root = Path(__file__).parent
report = root.parent / ".lavish" / "olive-mvp.html"

page = report.read_text(encoding="utf-8")

svg = (root / "out" / "graph.svg").read_text(encoding="utf-8")
svg = svg.replace('id="my-svg"', 'id="svg-graph"').replace("#my-svg", "#svg-graph")
page = page.replace("<!--GRAPH-SVG-->", svg)

demo = (root / "out" / "demo_output.txt").read_text(encoding="utf-8")
blocks = re.split(r"={72}\n【问题】.*?\n={72}\n", demo)[1:]  # 按分隔符切 5 段
assert len(blocks) == 5, f"期望 5 段,实际 {len(blocks)}"
for i, b in enumerate(blocks, 1):
    page = page.replace(f"<!--DEMO:{i}-->", html.escape(b.strip()))

assert "<!--" not in page or not re.search(r"<!--(GRAPH|DEMO)", page), "有占位符未替换"
report.write_text(page, encoding="utf-8")
print(f"注入完成,页面 {len(page)//1024} KB")
