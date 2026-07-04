# -*- coding: utf-8 -*-
"""待审队列的人工确认(SPEC §5 approve)。非交互式 CLI(方向由人显式给出)。"""
from pathlib import Path

import yaml

from events_lib import append_events

QUEUE = Path(__file__).parent / "out" / "review_queue.yaml"


def _load():
    doc = yaml.safe_load(QUEUE.read_text(encoding="utf-8")) if QUEUE.exists() else {}
    return (doc or {}).get("queue", []) or []


def list_queue() -> list[str]:
    q = _load()
    if not q:
        return ["队列为空。先运行 ingest-news。"]
    lines = []
    for i, item in enumerate(q, 1):
        lines.append(f"[{i}] {item['time']} · {item['title']}")
        lines.append(f"    命中节点: {item['matched_nodes']}(默认取 {item['root_cause']})")
    return lines


def approve(commodity: str, idx: int, direction: int, magnitude: str = "中",
            window: str = "待反转", root_cause: str | None = None) -> list[str]:
    q = _load()
    if not 1 <= idx <= len(q):
        return [f"序号 {idx} 不存在(共 {len(q)} 条)"]
    item = q.pop(idx - 1)
    e = {"time": item["time"], "root_cause": root_cause or item["root_cause"],
         "direction": direction, "magnitude": magnitude, "window": window,
         "active": True, "auto": False, "source": item["source"]}
    n = append_events(commodity, [e])
    QUEUE.write_text(yaml.safe_dump({"queue": q}, allow_unicode=True, sort_keys=False),
                     encoding="utf-8")
    return [f"✅ 已入库({n} 条): {e['root_cause']} direction={direction:+d} window={window}",
            f"   队列剩余 {len(q)} 条"]
