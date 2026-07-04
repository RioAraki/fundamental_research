# -*- coding: utf-8 -*-
"""从 YAML 边表生成 mermaid 图源码(节点按类型着色,边按极性着色)。
用法: python gen_mermaid.py [data/xxx.yaml] [out/xxx.mmd]
"""
import sys
from pathlib import Path

from build_graph import load

sys.stdout.reconfigure(encoding="utf-8")

TYPE_CLASS = {
    # 橄榄油 schema
    "天气冲击": "weather", "结构因素": "struct", "成本": "cost",
    "政策": "policy", "政策事件": "policy", "宏观事件": "macro",
    "需求因素": "demand",
    # 棕榈油 schema(根因带 · 前缀)
    "根因·天气": "weather", "根因·结构": "struct", "根因·供给": "weather",
    "根因·政策": "policy", "根因·宏观": "macro", "根因·需求": "demand",
    "根因·季节": "season", "根因·市场": "senti",
    # 共用
    "供给指标": "supply", "需求指标": "demand", "替代品": "demand",
    "价差": "spread", "情绪": "senti", "价格": "price",
}

src = Path(sys.argv[1]) if len(sys.argv) > 1 else Path(__file__).parent / "data" / "olive_oil.yaml"
dst = Path(sys.argv[2]) if len(sys.argv) > 2 else Path(__file__).parent / "out" / "graph.mmd"

INIT = ('%%{init: {"theme":"dark","themeVariables":{"lineColor":"#38bdf8",'
        '"edgeLabelBackground":"#0f172a","primaryTextColor":"#e2e8f0"}}}%%')

G = load(src)
ids = {n: f"n{i}" for i, n in enumerate(G.nodes)}
lines = [INIT, "flowchart LR"]
for n, d in G.nodes(data=True):
    shape = f'(["{n}"])' if d["type"].startswith("根因") else f'["{n}"]'
    lines.append(f'  {ids[n]}{shape}:::{TYPE_CLASS.get(d["type"], "struct")}')
neg_idx = []
for i, (u, v, d) in enumerate(G.edges(data=True)):
    label = f"{d['polarity_str']}·{d['strength']}"
    lines.append(f'  {ids[u]} -->|"{label}"| {ids[v]}')
    if d["polarity"] < 0:
        neg_idx.append(i)
lines += [
    "  classDef weather fill:#7c2d12,color:#fff",
    "  classDef struct fill:#57534e,color:#fff",
    "  classDef supply fill:#1e3a5f,color:#fff",
    "  classDef cost fill:#525252,color:#fff",
    "  classDef policy fill:#5b21b6,color:#fff",
    "  classDef macro fill:#831843,color:#fff",
    "  classDef demand fill:#14532d,color:#fff",
    "  classDef senti fill:#a16207,color:#fff",
    "  classDef season fill:#0e7490,color:#fff",
    "  classDef spread fill:#3f6212,color:#fff",
    "  classDef price fill:#b91c1c,color:#fff,stroke:#fbbf24,stroke-width:3px",
]
lines.append("  linkStyle default stroke:#38bdf8,stroke-width:2px")
if neg_idx:
    lines.append(f"  linkStyle {','.join(map(str, neg_idx))} stroke:#f87171,stroke-width:2px")

dst.parent.mkdir(exist_ok=True)
dst.write_text("\n".join(lines), encoding="utf-8")
print(f"已生成 {dst}: {G.number_of_nodes()} 节点 {G.number_of_edges()} 边")
