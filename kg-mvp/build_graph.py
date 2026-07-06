# -*- coding: utf-8 -*-
"""把 YAML 边表编译成 networkx 有向图,并做 schema 校验。图 = 可再生构建产物。"""
import sys
from pathlib import Path

import networkx as nx
import yaml

VALID_POLARITY = {"+", "-"}
VALID_STRENGTH = {"强", "中", "弱"}
STRENGTH_W = {"强": 0.9, "中": 0.6, "弱": 0.3}
# 时滞的粗略月份中值,用于沿路径累计
LAG_MONTHS = {
    "即时": 0, "当日": 0, "数日": 0.15, "数周": 0.75, "1月内": 0.5, "当月": 0.25,
    "2-8周": 1.25, "2周-2月": 1.25, "6-10周": 2, "节前1-2月": 1.5,
    "1-2月": 1.5, "1-3月": 2, "0-3月": 1.5, "数月": 3, "当季": 3, "1季": 3,
    "3-6月": 4.5, "1-6月": 3.5, "榨季初": 3, "中期": 6, "6-12月": 9, "3-12月": 7.5,
    "1年": 12, "12-24月": 18, "6-24月": 15, "多年": 36, "3-5年": 48, "3-10年": 78,
}


def load(path: str | Path) -> nx.DiGraph:
    data = yaml.safe_load(Path(path).read_text(encoding="utf-8"))
    node_ids = {n["id"] for n in data["nodes"]}
    errors = []
    if len(node_ids) != len(data["nodes"]):
        errors.append("存在重复节点 id")

    G = nx.DiGraph(meta=data.get("meta", {}))
    for n in data["nodes"]:
        G.add_node(n["id"], type=n.get("type", ""), note=n.get("note", ""),
                   case=n.get("case", ""), signals=n.get("signals", {}),
                   direction=n.get("direction", ""), temporal=n.get("temporal", {}))

    seen = set()
    for i, e in enumerate(data["edges"]):
        for k in ("from", "to", "polarity", "lag", "strength"):
            if k not in e:
                errors.append(f"边 #{i} 缺少字段 {k}: {e}")
        u, v = e.get("from"), e.get("to")
        if u not in node_ids:
            errors.append(f"边 #{i} 起点未声明: {u}")
        if v not in node_ids:
            errors.append(f"边 #{i} 终点未声明: {v}")
        if e.get("polarity") not in VALID_POLARITY:
            errors.append(f"边 #{i} polarity 非法: {e.get('polarity')}")
        if e.get("strength") not in VALID_STRENGTH:
            errors.append(f"边 #{i} strength 非法: {e.get('strength')}")
        if e.get("lag") not in LAG_MONTHS:
            errors.append(f"边 #{i} lag 未登记换算表: {e.get('lag')}")
        if (u, v) in seen:
            errors.append(f"重复边: {u} -> {v}")
        seen.add((u, v))
        G.add_edge(
            u, v,
            polarity=1 if e["polarity"] == "+" else -1,
            polarity_str=e["polarity"],
            lag=e["lag"],
            lag_months=LAG_MONTHS.get(e["lag"], 0),
            strength=e["strength"],
            weight=STRENGTH_W.get(e["strength"], 0.3),
            condition=e.get("condition", ""),
            evidence=e.get("evidence", ""),
            rationale=e.get("rationale", ""),
        )

    if errors:
        for msg in errors:
            print("[校验失败]", msg)
        sys.exit(1)
    return G


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8")
    g = load(Path(__file__).parent / "data" / "copper.yaml")
    print(f"校验通过:{g.number_of_nodes()} 节点 / {g.number_of_edges()} 边")
    roots = [n for n in g.nodes if g.in_degree(n) == 0]
    print("根因节点(入度0):", ", ".join(roots))
    cycles = list(nx.simple_cycles(g))
    print(f"反馈环 {len(cycles)} 个:")
    for c in cycles:
        print("  ↻", " → ".join(c))
