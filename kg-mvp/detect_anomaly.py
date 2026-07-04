# -*- coding: utf-8 -*-
"""行情驱动异常检测(SPEC §5 anomaly,kg-ops-design §2-①的实现):
|日收益| > 2.5×(60日σ) 触发 → 查活跃事件的传导方向是否解释价格 → 三分类。
输入 data/feeds/cu_price.csv(date,close);输出 out/anomaly_report.md + out/event_price_pairs.csv
"""
import csv
import statistics
from pathlib import Path

from build_graph import load
from events_lib import active_events, load_events, parse_date
from propagate import propagate

GRAPH = {"copper": ("data/copper.yaml", "SHFE铜价格", "data/feeds/cu_price.csv")}
TRIGGER_SIGMA, WINDOW = 2.5, 60


def _event_direction_on(G, e, target):
    res = propagate(G, {e["root_cause"]: e["direction"]}, max_hops=9)
    res.pop("__feedback__", None)
    paths = res.get(target, [])
    if not paths:
        return 0, 0.0
    best = paths[0]
    return best.signs[-1], best.strength


def run(commodity: str, today) -> list[str]:
    gpath, target, feed = GRAPH[commodity]
    root = Path(__file__).parent
    G = load(root / gpath)
    events = load_events(commodity)

    rows = list(csv.DictReader(open(root / feed, encoding="utf-8-sig", newline="")))
    rows = [r for r in rows if parse_date(r["date"]) <= today]
    closes = [float(r["close"]) for r in rows]
    rets = [(closes[i] - closes[i - 1]) / closes[i - 1] for i in range(1, len(closes))]

    md = [f"# 行情异常检测 · {commodity} · 截至 {today}", ""]
    pairs, n_flag = [], 0
    for i in range(WINDOW, len(rets)):
        sigma = statistics.pstdev(rets[i - WINDOW:i])
        r = rets[i]
        if abs(r) <= TRIGGER_SIGMA * sigma:
            continue
        n_flag += 1
        day = rows[i + 1]["date"]
        move = 1 if r > 0 else -1
        acts = active_events(events, parse_date(day))
        consistent, contrary = [], []
        for e in acts:
            sign, strength = _event_direction_on(G, e, target)
            if strength < 0.3 or sign == 0:
                continue
            (consistent if sign == move else contrary).append((e, strength))
        md.append(f"## {day}:收益 {r:+.2%}(阈值 ±{TRIGGER_SIGMA * sigma:.2%})")
        if consistent:
            e, s = max(consistent, key=lambda x: x[1])
            md.append(f"- ✅ **有解释**:{e['root_cause']}({e['time']},强度 {s:.2f})方向一致 → 记入事件-价格配对库")
            pairs.append({"date": day, "return": f"{r:+.4f}", "event_time": e["time"],
                          "root_cause": e["root_cause"], "direction": e["direction"],
                          "path_strength": f"{s:.2f}"})
        elif contrary:
            e, s = max(contrary, key=lambda x: x[1])
            md.append(f"- 🔴 **方向失灵**:最强活跃事件 {e['root_cause']} 指向相反 → 涉事路径标记待校准(issue)")
        else:
            md.append("- 🟠 **无解释**:无足够强度的活跃事件 → issue「疑似漏事件/缺根因/纯资金」,请对照当日新闻排查")
    if n_flag == 0:
        md.append("样本期内无超阈值异动。")

    out_md = root / "out" / "anomaly_report.md"
    out_md.write_text("\n".join(md), encoding="utf-8")
    out_csv = root / "out" / "event_price_pairs.csv"
    with open(out_csv, "w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=["date", "return", "event_time", "root_cause",
                                          "direction", "path_strength"])
        w.writeheader()
        w.writerows(pairs)
    return [f"异常检测 → {out_md}(触发 {n_flag} 天;配对库 {len(pairs)} 条 → {out_csv.name})"]
