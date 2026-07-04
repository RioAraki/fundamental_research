# -*- coding: utf-8 -*-
"""生成 cu_price.csv 样例(确定性,seed 固定):2026-01-02 起工作日序列,
内嵌两天异动:2026-02-05 +3.5%(国储收储次日,应判"有解释"),
2026-05-20 -3.2%(活跃事件皆偏多,应判"方向失灵")。"""
import csv
import random
from datetime import date, timedelta
from pathlib import Path

random.seed(42)
rows, px, d = [], 78000.0, date(2025, 11, 3)
SPIKES = {date(2026, 2, 5): 0.035, date(2026, 5, 20): -0.032}
while d <= date(2026, 7, 6):
    if d.weekday() < 5:
        r = SPIKES.get(d, random.gauss(0, 0.008))
        px *= 1 + r
        rows.append({"date": d.isoformat(), "close": f"{px:.0f}"})
    d += timedelta(days=1)
out = Path(__file__).parent / "cu_price.csv"
with open(out, "w", encoding="utf-8", newline="") as f:
    w = csv.DictWriter(f, fieldnames=["date", "close"])
    w.writeheader()
    w.writerows(rows)
print(f"{len(rows)} 行 → {out}")
