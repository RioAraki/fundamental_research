# -*- coding: utf-8 -*-
"""把铜的 SVG/面板/演示/交互数据注入 .lavish/copper-mvp.html"""
import html
import re
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")
root = Path(__file__).parent
report = root.parent / ".lavish" / "copper-mvp.html"
page = report.read_text(encoding="utf-8")


def load_svg(name, uid):
    svg = (root / "out" / f"{name}.svg").read_text(encoding="utf-8")
    return svg.replace('id="my-svg"', f'id="{uid}"').replace("#my-svg", f"#{uid}")


page = page.replace("<!--GRAPH-SVG-->", load_svg("cu_graph", "svg-cu"))
for i in range(1, 6):
    page = page.replace(f"<!--DEMOSVG:{i}-->", load_svg(f"cu_demo{i}", f"svg-cudemo{i}"))

page = page.replace("<!--PANEL-->", (root / "out" / "cu_panel.html").read_text(encoding="utf-8"))
page = page.replace("/*DATA*/", (root / "out" / "cu_explore.json").read_text(encoding="utf-8"))

demo = (root / "out" / "copper_demo.txt").read_text(encoding="utf-8")
blocks = re.split(r"={72}\n【问题】.*?\n={72}\n", demo)[1:]
assert len(blocks) == 6, f"期望 6 段,实际 {len(blocks)}"
for i, b in enumerate(blocks, 1):
    page = page.replace(f"<!--DEMO:{i}-->", html.escape(b.strip()))

assert not re.search(r"<!--(GRAPH|DEMO|PANEL)", page) and "/*DATA*/" not in page, "有占位符未替换"
report.write_text(page, encoding="utf-8")
print(f"注入完成,页面 {len(page)//1024} KB")
