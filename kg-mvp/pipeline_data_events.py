# -*- coding: utf-8 -*-
"""数据型事件流水线(SPEC §5 ingest-data):
feeds CSV → 预期差 z-score → |z|≥1.5 自动生成事件 → 幂等追加到事件日志。
CSV 列:date,node,value,expected,sigma,source
"""
import csv
from pathlib import Path

from build_graph import load
from events_lib import append_events

Z_THRESHOLD = 1.5
FEED = {"copper": Path(__file__).parent / "data" / "feeds" / "cu_indicators.csv"}
GRAPH = {"copper": Path(__file__).parent / "data" / "copper.yaml",
         "palm": Path(__file__).parent / "data" / "palm_oil.yaml"}


def run(commodity: str, today: str) -> list[str]:
    G = load(GRAPH[commodity])
    lines = []
    new_events = []
    with open(FEED[commodity], encoding="utf-8-sig", newline="") as f:
        for row in csv.DictReader(f):
            if row["date"] > today:
                continue  # point-in-time
            node = row["node"].strip()
            if node not in G.nodes:
                lines.append(f"⚠️ 跳过:节点不存在 {node}(feeds 配置错误)")
                continue
            z = (float(row["value"]) - float(row["expected"])) / float(row["sigma"])
            if abs(z) < Z_THRESHOLD:
                lines.append(f"·  {row['date']} {node}: z={z:+.2f} 未达阈值({Z_THRESHOLD}),不生成事件")
                continue
            new_events.append({
                "time": row["date"], "root_cause": node,
                "direction": 1 if z > 0 else -1,
                "magnitude": f"z={z:+.1f}", "window": "数周",
                "active": True, "auto": True,
                "source": f"{row['source']}:实际 {row['value']} vs 预期 {row['expected']}",
            })
            lines.append(f"✅ {row['date']} {node}: z={z:+.2f} → 事件 direction={'+1' if z > 0 else '-1'}")
    n = append_events(commodity, new_events)
    lines.append(f"入库 {n} 条(候选 {len(new_events)} 条,幂等去重 {len(new_events) - n} 条)")
    return lines
