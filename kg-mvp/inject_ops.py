# -*- coding: utf-8 -*-
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")
root = Path(__file__).parent
p = root.parent / ".lavish" / "kg-ops-design.html"
page = p.read_text(encoding="utf-8")
svg = (root / "out" / "ops_loop.svg").read_text(encoding="utf-8")
svg = svg.replace('id="my-svg"', 'id="svg-ops"').replace("#my-svg", "#svg-ops")
assert "<!--OPS-SVG-->" in page
page = page.replace("<!--OPS-SVG-->", svg)
p.write_text(page, encoding="utf-8")
print("注入完成", len(page) // 1024, "KB")
