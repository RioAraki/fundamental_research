# -*- coding: utf-8 -*-
"""冲突仪表盘(SPEC §5 conflicts):多空同时被活跃事件激活的节点 + 裁决信号。"""
from pathlib import Path

from build_graph import load
from events_lib import current_shocks, load_events
from propagate import propagate

GRAPH = {"copper": ("data/copper.yaml", "SHFE铜价格"),
         "palm": ("data/palm_oil.yaml", "DCE棕榈油价格")}


def run(commodity: str, today) -> list[str]:
    gpath, target = GRAPH[commodity]
    G = load(Path(__file__).parent / gpath)
    shocks = current_shocks(load_events(commodity), today)
    res = propagate(G, shocks, max_hops=9) if shocks else {}
    res.pop("__feedback__", None)

    md = [f"# 冲突仪表盘 · {commodity} · {today}",
          "", "> 多空路径同时被当前活跃事件激活的节点 = 今天行情的分歧点。冲突期观望,等裁决信号。", ""]
    n_conf = 0
    for node, paths in sorted(res.items(), key=lambda kv: -len(kv[1])):
        bull = [p for p in paths if p.signs[-1] > 0]
        bear = [p for p in paths if p.signs[-1] < 0]
        bs, rs = sum(p.strength for p in bull), sum(p.strength for p in bear)
        if not (bull and bear and min(bs, rs) / max(bs, rs) > 0.34):
            continue
        n_conf += 1
        md.append(f"## ⚠️ {node}(多 {bs:.2f} vs 空 {rs:.2f})")
        md.append(f"- 最强利多:{max(bull, key=lambda p: p.strength).render()}")
        md.append(f"- 最强利空:{max(bear, key=lambda p: p.strength).render()}")
        srcs = {p.nodes[0] for p in bull} | {p.nodes[0] for p in bear}
        md.append("- **裁决信号**(双方源头根因的数据入口):")
        for s in sorted(srcs):
            data = (G.nodes[s].get("signals") or {}).get("data", [])
            if data:
                md.append(f"  - {s} → {' | '.join(data)}")
        md.append("")
    if n_conf == 0:
        md.append("当前活跃事件下无显著多空冲突节点。")
    out = Path(__file__).parent / "out" / "conflict_dashboard.md"
    out.write_text("\n".join(md), encoding="utf-8")
    return [f"冲突仪表盘 → {out}(冲突节点 {n_conf} 个)"]
