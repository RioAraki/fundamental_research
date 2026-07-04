# -*- coding: utf-8 -*-
"""通用 SVG 注入:python inject_svg_generic.py <html相对.lavish路径> <svg文件> <占位符> <svg-id>"""
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")
html_path = Path(__file__).parent.parent / ".lavish" / sys.argv[1]
svg_path = Path(__file__).parent / sys.argv[2]
placeholder, svg_id = sys.argv[3], sys.argv[4]

page = html_path.read_text(encoding="utf-8")
svg = svg_path.read_text(encoding="utf-8").replace('id="my-svg"', f'id="{svg_id}"').replace("#my-svg", f"#{svg_id}")
assert placeholder in page, f"占位符 {placeholder} 未找到"
page = page.replace(placeholder, svg)
html_path.write_text(page, encoding="utf-8")
print(f"注入完成 {len(page)//1024} KB")
