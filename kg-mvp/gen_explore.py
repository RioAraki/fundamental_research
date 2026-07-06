# -*- coding: utf-8 -*-
"""生成交互探索页数据(JSON):
- 每个节点:含义、direction、signals、case + 预计算「该量↑对 DCE P 的方向与最强路径」(利好利空判定)
- 每条边:五要素 + rationale + 自动生成的机制解释句
用法: python gen_explore.py data/copper.yaml SHFE铜价格 out/explore_data.json
"""
import json
import sys
from pathlib import Path

from build_graph import load
from propagate import propagate

sys.stdout.reconfigure(encoding="utf-8")
src, target, dst = sys.argv[1], sys.argv[2], Path(sys.argv[3])
G = load(src)

COLOR = {
    "根因·天气": "#7c2d12", "根因·结构": "#57534e", "根因·供给": "#7c2d12",
    "根因·政策": "#5b21b6", "根因·宏观": "#831843", "根因·需求": "#14532d",
    "根因·季节": "#0e7490", "根因·市场": "#a16207",
    "供给指标": "#1e3a5f", "需求指标": "#14532d", "替代品": "#14532d",
    "价差": "#3f6212", "情绪": "#a16207", "价格": "#b91c1c",
}

nodes, edges = [], []
for n, d in G.nodes(data=True):
    eff = None
    if n != target:
        res = propagate(G, {n: 1}, max_hops=9)
        res.pop("__feedback__", None)
        if target in res:
            best = res[target][0]
            n_paths = len(res[target])
            bull = sum(1 for p in res[target] if p.signs[-1] > 0)
            eff = {
                "sign": "利多" if best.signs[-1] > 0 else "利空",
                "strength": round(best.strength, 2),
                "lag": round(best.lag_months, 1),
                "path": best.render(),
                "n_paths": n_paths, "n_bull": bull, "n_bear": n_paths - bull,
            }
    is_root = d["type"].startswith("根因")
    nodes.append({
        "id": n, "label": n, "type": d["type"],
        "shape": "ellipse" if is_root else "box",
        "color": COLOR.get(d["type"], "#57534e"),
        "borderWidth": 4 if n == target else 1,
        "note": d.get("note", ""), "direction": d.get("direction", ""),
        "case": d.get("case", ""), "signals": d.get("signals") or {},
        "temporal": d.get("temporal") or {},
        "isRoot": is_root, "effect": eff,
    })

for i, (u, v, d) in enumerate(G.edges(data=True)):
    verb = "上升" if d["polarity"] > 0 else "下降"
    sent = (f"当「{u}」上升时,「{v}」趋于{verb}"
            f"(机制{'同向 +' if d['polarity'] > 0 else '反向 −'});"
            f"传导时滞约 {d['lag']},强度「{d['strength']}」。"
            f"反之,「{u}」下降则「{v}」趋于{'下降' if d['polarity'] > 0 else '上升'}。")
    edges.append({
        "id": f"e{i}", "from": u, "to": v,
        "polarity": d["polarity_str"], "lag": d["lag"], "strength": d["strength"],
        "condition": d.get("condition", ""), "evidence": d.get("evidence", ""),
        "rationale": d.get("rationale", ""), "sentence": sent,
        "color": "#38bdf8" if d["polarity"] > 0 else "#f87171",
        "width": {"强": 3, "中": 2, "弱": 1}[d["strength"]],
        "label": f"{d['polarity_str']}·{d['lag']}·{d['strength']}",
    })

dst.write_text(json.dumps({"nodes": nodes, "edges": edges, "target": target},
                          ensure_ascii=False), encoding="utf-8")
print(f"explore 数据:{len(nodes)} 节点 / {len(edges)} 边 → {dst}")
