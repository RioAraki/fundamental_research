# -*- coding: utf-8 -*-
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")
p = Path(__file__).parent.parent / ".lavish" / "kg-inference-report.html"
page = p.read_text(encoding="utf-8")
sec = (Path(__file__).parent / "out" / "concepts_section.html").read_text(encoding="utf-8")

marker = "<!-- ============ REFS ============ -->"
assert page.count(marker) == 1, "marker 异常"
page = page.replace(marker, sec)

nav_old = '<li><a href="#refs" data-nav="refs">📚 参考文献</a></li>'
assert nav_old in page, "nav 未找到"
page = page.replace(nav_old, '<li><a href="#concepts" data-nav="concepts">🎓 概念详解</a></li>\n        ' + nav_old)

p.write_text(page, encoding="utf-8")
print(f"概念页插入完成, 页面 {len(page)//1024} KB")
