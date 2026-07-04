# -*- coding: utf-8 -*-
"""为每个推理演示生成传导子图 mermaid:
只画本次冲击实际走过的路径;节点标注 ↑/↓(红涨绿跌,冲突为琥珀 ⚠);冲击节点加粗边框。
输出 out/demo1.mmd ... demoN.mmd
"""
import sys
from pathlib import Path

from build_graph import load
from propagate import propagate

sys.stdout.reconfigure(encoding="utf-8")
G = load(Path(__file__).parent / "data" / "palm_oil.yaml")

SCENARIOS = [
    ("demo1", {"MPOB库存预期差": +1}, ["DCE棕榈油价格", "进口利润", "中国买船", "中国港口库存"]),
    ("demo2", {"印尼生柴掺混率": +1}, ["DCE棕榈油价格", "全球可出口供给", "豆棕价差", "印尼生柴需求"]),
    ("demo3", {"产区干旱程度": +1}, ["DCE棕榈油价格", "天气升水情绪", "FFB单产", "MPOB库存", "全球可出口供给"]),
    ("demo4", {"印尼出口限制力度": +1}, ["DCE棕榈油价格", "印尼国内库存", "FCPO价格", "全球可出口供给"]),
    ("demo5", {"美国生柴掺混义务": +1}, ["DCE棕榈油价格", "豆棕价差", "棕油替代需求", "中国港口库存"]),
]

for name, shocks, targets in SCENARIOS:
    res = propagate(G, shocks, max_hops=7)
    loops = res.pop("__feedback__")
    node_signs: dict[str, set] = {n: {s} for n, s in shocks.items()}
    edges: dict[tuple, dict] = {}

    def absorb(path):
        for i in range(1, len(path.nodes)):
            u, v, s = path.nodes[i - 1], path.nodes[i], path.signs[i]
            node_signs.setdefault(v, set()).add(s)
            edges[(u, v)] = path.edges[i - 1]

    for t in targets:
        for p in res.get(t, [])[:4]:
            absorb(p)
    for p in loops[:3]:
        absorb(p)

    INIT = ('%%{init: {"theme":"dark","themeVariables":{"lineColor":"#38bdf8",'
            '"edgeLabelBackground":"#0f172a","primaryTextColor":"#e2e8f0"}}}%%')
    ids = {n: f"n{i}" for i, n in enumerate(node_signs)}
    lines = [INIT, "flowchart LR"]
    for n, signs in node_signs.items():
        mark = "⚠↑↓" if len(signs) > 1 else ("↑" if 1 in signs else "↓")
        cls = "conf" if len(signs) > 1 else ("up" if 1 in signs else "down")
        if n in shocks:
            cls = "shock"
            mark = "↑" if shocks[n] > 0 else "↓"
        lines.append(f'  {ids[n]}["{n} {mark}"]:::{cls}')
    neg = []
    for i, ((u, v), e) in enumerate(edges.items()):
        lines.append(f'  {ids[u]} -->|"{e["polarity_str"]}·{e["lag"]}·{e["strength"]}"| {ids[v]}')
        if e["polarity"] < 0:
            neg.append(i)
    lines += [
        "  classDef shock fill:#1d4ed8,color:#fff,stroke:#93c5fd,stroke-width:4px",
        "  classDef up fill:#b91c1c,color:#fff",
        "  classDef down fill:#15803d,color:#fff",
        "  classDef conf fill:#b45309,color:#fff,stroke:#fde68a,stroke-width:2px",
    ]
    lines.append("  linkStyle default stroke:#38bdf8,stroke-width:2px")
    if neg:
        lines.append(f"  linkStyle {','.join(map(str, neg))} stroke:#f87171,stroke-width:2px")
    out = Path(__file__).parent / "out" / f"{name}.mmd"
    out.write_text("\n".join(lines), encoding="utf-8")
    print(f"{name}: {len(node_signs)} 节点 {len(edges)} 边 → {out}")
