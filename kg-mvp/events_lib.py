# -*- coding: utf-8 -*-
"""事件日志读写 + 活跃事件过滤(时间系统的核心工程落点,见 SPEC §4.4)。"""
from datetime import date, datetime, timedelta
from pathlib import Path

import yaml

from build_graph import LAG_MONTHS

DATA = Path(__file__).parent / "data"
EVENTS_FILE = {"copper": DATA / "copper_events.yaml"}


def parse_date(s) -> date:
    return datetime.strptime(str(s)[:10], "%Y-%m-%d").date()


def load_events(commodity: str = "copper") -> list[dict]:
    p = EVENTS_FILE[commodity]
    if not p.exists():
        return []
    doc = yaml.safe_load(p.read_text(encoding="utf-8")) or {}
    return doc.get("events", []) or []


def window_months(window: str) -> float | None:
    """事件窗口 → 月数;「待反转」返回 None(保持到反向事件)。"""
    if window == "待反转":
        return None
    if window in LAG_MONTHS:
        return LAG_MONTHS[window]
    raise ValueError(f"未知事件窗口: {window}(需登记到 build_graph.LAG_MONTHS 或用 待反转)")


def active_events(events: list[dict], today: date) -> list[dict]:
    """SPEC §4.4:被同根因更晚的反向事件反转 → 失效;待反转 → 持续;否则按窗口到期。"""
    out = []
    for e in events:
        t = parse_date(e["time"])
        if t > today:
            continue  # point-in-time:未来事件不可见
        reversed_ = any(
            e2 is not e
            and e2["root_cause"] == e["root_cause"]
            and parse_date(e2["time"]) <= today
            and parse_date(e2["time"]) > t
            and e2["direction"] == -e["direction"]
            for e2 in events)
        if reversed_:
            continue
        w = window_months(e.get("window", "待反转"))
        if w is None or t + timedelta(days=round(w * 30.44)) >= today:
            out.append(e)
    return out


def current_shocks(events: list[dict], today: date) -> dict[str, int]:
    """每根因取最新活跃事件的方向 → propagate 的输入。"""
    shocks: dict[str, tuple[date, int]] = {}
    for e in active_events(events, today):
        t = parse_date(e["time"])
        if e["root_cause"] not in shocks or t > shocks[e["root_cause"]][0]:
            shocks[e["root_cause"]] = (t, e["direction"])
    return {k: v[1] for k, v in shocks.items()}


def format_event_line(e: dict) -> str:
    """按仓库既有风格生成一条 flow-style 事件(追加用)。"""
    mag = str(e.get("magnitude", "中"))
    mag_repr = mag if mag in ("强", "中", "弱") else f'"{mag}"'
    parts = [f'time: "{e["time"]}"', f'root_cause: {e["root_cause"]}',
             f'direction: {"+1" if e["direction"] > 0 else "-1"}',
             f'magnitude: {mag_repr}']
    parts += [f'window: {e.get("window", "待反转")}',
              f'active: {str(e.get("active", True)).lower()}',
              f'auto: {str(e.get("auto", False)).lower()}']
    src = str(e.get("source", "")).replace('"', "'")
    parts.append(f'source: "{src}"')
    return "  - {" + ", ".join(parts) + "}"


def append_events(commodity: str, new_events: list[dict]) -> int:
    """幂等追加:同 (time, root_cause, direction) 的已有事件跳过。"""
    p = EVENTS_FILE[commodity]
    existing = {(str(e["time"]), e["root_cause"], e["direction"]) for e in load_events(commodity)}
    lines = []
    for e in new_events:
        key = (str(e["time"]), e["root_cause"], e["direction"])
        if key in existing:
            continue
        existing.add(key)
        lines.append(format_event_line(e))
    if lines:
        text = p.read_text(encoding="utf-8").rstrip("\n")
        p.write_text(text + "\n" + "\n".join(lines) + "\n", encoding="utf-8")
    return len(lines)
