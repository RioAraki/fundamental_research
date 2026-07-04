# -*- coding: utf-8 -*-
"""边保质期扫描(SPEC §5 reviews):review.last 超 12 个月或缺失的边 → 清单。"""
from datetime import date
from pathlib import Path

from build_graph import load

GRAPH = {"copper": "data/copper.yaml", "palm": "data/palm_oil.yaml"}
OVERDUE_MONTHS = 12


def run(commodity: str, today: date) -> list[str]:
    G = load(Path(__file__).parent / GRAPH[commodity])
    never, overdue = [], []
    for u, v, d in G.edges(data=True):
        rv = d.get("review") or {}
        last = rv.get("last")
        if not last:
            never.append((u, v))
            continue
        y, m = int(str(last)[:4]), int(str(last)[5:7])
        age = (today.year - y) * 12 + (today.month - m)
        if age > OVERDUE_MONTHS:
            overdue.append((u, v, last, age))

    md = [f"# 边保质期扫描 · {commodity} · {today}", "",
          f"共 {G.number_of_edges()} 条边;从未审校 {len(never)} 条;超期(>{OVERDUE_MONTHS}月){len(overdue)} 条", ""]
    if overdue:
        md.append("## ⏰ 超期待审")
        md += [f"- {u} → {v}(上次 {last},已 {age} 个月)" for u, v, last, age in overdue]
    if never:
        md.append("\n## 📋 从未审校(首轮全量审校时补 review.last 字段)")
        md += [f"- {u} → {v}" for u, v in never[:60]]
    out = Path(__file__).parent / "out" / "review_overdue.md"
    out.write_text("\n".join(md), encoding="utf-8")
    return [f"保质期扫描 → {out}(未审 {len(never)} / 超期 {len(overdue)})"]
