# -*- coding: utf-8 -*-
"""晨报(SPEC §5 morning):活跃事件叠加 → 分时段结论 → 待验证信号。输出 out/morning_report.md"""
from datetime import timedelta
from pathlib import Path

from build_graph import load
from events_lib import active_events, current_shocks, load_events, parse_date
from propagate import propagate, SIGN_TXT

GRAPH = {"copper": ("data/copper.yaml", "SHFE铜价格")}
BUCKETS = [("0-1 月", 0, 1), ("1-6 月", 1, 6), ("6 月以上", 6, 10 ** 9)]


def run(commodity: str, today) -> list[str]:
    gpath, target = GRAPH[commodity]
    G = load(Path(__file__).parent / gpath)
    events = load_events(commodity)
    act = active_events(events, today)
    shocks = current_shocks(events, today)
    new_today = [e for e in act if parse_date(e["time"]) >= today - timedelta(days=3)]

    md = [f"# 晨报 · {commodity} · {today}", ""]
    md.append(f"## 一、近三日新事件({len(new_today)} 条)")
    for e in sorted(new_today, key=lambda x: x["time"], reverse=True):
        md.append(f"- **{e['time']}** {e['root_cause']} {SIGN_TXT[e['direction']]}"
                  f"({e.get('magnitude', '')},窗口 {e.get('window', '')}) — {e.get('source', '')}")
    if not new_today:
        md.append("- 无")

    md.append(f"\n## 二、当前生效事件叠加({len(act)} 条活跃,{len(shocks)} 个根因)")
    md.append("冲击输入:" + " · ".join(f"{k}{SIGN_TXT[v]}" for k, v in shocks.items()))

    res = propagate(G, shocks, max_hops=9) if shocks else {}
    res.pop("__feedback__", None)
    paths = res.get(target, [])
    md.append(f"\n## 三、对 {target} 的分时段结论")
    watch_nodes = set(shocks)
    for label, lo, hi in BUCKETS:
        ps = [p for p in paths if lo <= p.lag_months < hi]
        bull = sum(p.strength for p in ps if p.signs[-1] > 0)
        bear = sum(p.strength for p in ps if p.signs[-1] < 0)
        tag = ("**多空拉锯 ⚠️(冲突期,观望等裁决)**" if bull and bear and min(bull, bear) / max(bull, bear) > 0.5
               else ("偏多" if bull > bear else ("偏空" if bear > bull else "无信号")))
        md.append(f"\n### 【{label}】{tag}(多 {bull:.2f} vs 空 {bear:.2f})")
        for p in sorted(ps, key=lambda x: -x.strength)[:3]:
            md.append(f"- [{'多' if p.signs[-1] > 0 else '空'} {p.strength:.2f}] {p.render()}")
            for c in dict.fromkeys(p.conditions):
                md.append(f"  - 条件:{c}")

    md.append("\n## 四、今日待验证信号(涉事根因的数据入口)")
    for n in sorted(watch_nodes):
        sig = (G.nodes[n].get("signals") or {})
        if sig.get("data"):
            md.append(f"- **{n}**:{' | '.join(sig['data'])}")

    out = Path(__file__).parent / "out" / "morning_report.md"
    out.parent.mkdir(exist_ok=True)
    out.write_text("\n".join(md), encoding="utf-8")
    return [f"晨报已生成 → {out}", f"活跃事件 {len(act)} 条 / 路径 {len(paths)} 条"]
