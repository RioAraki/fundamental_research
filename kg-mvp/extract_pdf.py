# -*- coding: utf-8 -*-
"""提取甲醇 PDF 全文文本到 out/methanol_pdf.txt"""
import sys
from pathlib import Path

import fitz

sys.stdout.reconfigure(encoding="utf-8")
doc = fitz.open(r"D:\github\fundamental_research\reference\甲醇基本面研究.pdf")
parts = []
for i, page in enumerate(doc):
    parts.append(f"\n===== 第 {i+1} 页 =====\n" + page.get_text("text"))
out = Path(__file__).parent / "out" / "methanol_pdf.txt"
out.write_text("".join(parts), encoding="utf-8")
print(f"{doc.page_count} 页 → {out},共 {sum(len(p) for p in parts)//1000}k 字符")
