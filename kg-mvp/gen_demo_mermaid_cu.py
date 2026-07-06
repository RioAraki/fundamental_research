# -*- coding: utf-8 -*-
"""沪铜演示传导子图 mermaid:每个情景冲击只画实际走过的路径。输出 out/cu_demo1..5.mmd"""
import sys
from pathlib import Path

from build_graph import load
from propagate import propagate

sys.stdout.reconfigure(encoding="utf-8")
G = load(Path(__file__).parent / "data" / "copper.yaml")

SCENARIOS = [
    ("cu_demo1", {"矿端供给扰动率": +1}, ["SHFE铜价格", "TC/RC加工费", "中国精铜产量", "全球显性库存"]),
    ("cu_demo2", {"美联储政策立场": +1}, ["SHFE铜价格", "LME铜价格", "美元指数", "全球衰退预期"]),
    ("cu_demo3", {"美国铜进口关税": +1}, ["SHFE铜价格", "COMEX-LME价差", "全球显性库存", "LME铜价格"]),
    ("cu_demo4", {"中国电网投资": +1}, ["SHFE铜价格", "中国社会库存", "沪伦比值", "中国下游开工率"]),
    ("cu_demo5", {"SHFE铜价格": +1}, ["中国下游开工率", "再生铜替代", "进口流入", "中国社会库存", "精废价差", "沪伦比值"]),
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
    for p in loops[:4]:
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
        "  linkStyle default stroke:#38bdf8,stroke-width:2px",
    ]
    if neg:
        lines.append(f"  linkStyle {','.join(map(str, neg))} stroke:#f87171,stroke-width:2px")
    out = Path(__file__).parent / "out" / f"{name}.mmd"
    out.write_text("\n".join(lines), encoding="utf-8")
    print(f"{name}: {len(node_signs)} 节点 {len(edges)} 边 → {out}")
