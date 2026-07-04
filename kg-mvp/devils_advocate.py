# -*- coding: utf-8 -*-
"""反方路径/魔鬼代言人(SPEC §5 advocate):
给定立场(多/空),列出图上方向相反的传导路径——活跃事件驱动的优先,--structural 加列结构性反方。
"""
from pathlib import Path

from build_graph import load
from events_lib import current_shocks, load_events
from propagate import propagate

GRAPH = {"copper": ("data/copper.yaml", "SHFE铜价格"),
         "palm": ("data/palm_oil.yaml", "DCE棕榈油价格")}


def run(commodity: str, today, stance: str, structural: bool = False,
        target: str | None = None) -> list[str]:
    gpath, default_target = GRAPH[commodity]
    target = target or default_target
    G = load(Path(__file__).parent / gpath)
    against = -1 if stance == "多" else 1  # 看多 → 找利空路径

    lines = [f"◆ 你的立场:看{stance} {target};以下是图上的反方证据", ""]

    # 1) 当前活跃事件中的反方路径
    shocks = current_shocks(load_events(commodity), today)
    res = propagate(G, shocks, max_hops=9) if shocks else {}
    res.pop("__feedback__", None)
    opp = [p for p in res.get(target, []) if p.signs[-1] == against]
    lines.append(f"【当前活跃事件已在驱动的反方路径】{len(opp)} 条")
    for p in sorted(opp, key=lambda x: -x.strength)[:5]:
        lines.append(f"  [{p.strength:.2f} 时滞≈{p.lag_months:.0f}月] {p.render()}")
        for c in dict.fromkeys(p.conditions):
            lines.append(f"     └ 前提:{c}")
        sig = (G.nodes[p.nodes[0]].get("signals") or {}).get("data", [])
        if sig:
            lines.append(f"     └ 验证信号:{' | '.join(sig)}")
    if not opp:
        lines.append("  (无——注意:没有反方事件 ≠ 没有反方机制,看下节)")

    # 2) 结构性反方(任一根因 ±1 都可能触发的反向机制)
    if structural:
        lines.append(f"\n【结构性反方机制(当前未被事件激活,但机制存在)】")
        seen = set()
        rows = []
        for r in [n for n in G.nodes if G.in_degree(n) == 0]:
            rr = propagate(G, {r: 1}, max_hops=9)
            rr.pop("__feedback__", None)
            for p in rr.get(target, []):
                if p.signs[-1] == against and p.nodes[0] not in seen:
                    seen.add(p.nodes[0])
                    rows.append(p)
                    break
        for p in sorted(rows, key=lambda x: -x.strength)[:8]:
            lines.append(f"  [{p.strength:.2f}] {p.render()}")
    lines.append("\n提示:反方路径不是让你放弃观点,而是你的观点成立所必须压过的东西——逐条给出压过的理由,观点才完整。")
    return lines
