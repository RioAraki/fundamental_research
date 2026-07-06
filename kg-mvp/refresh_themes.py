# -*- coding: utf-8 -*-
"""主题热度刷新(SPEC §5 themes):90 天事件密度 → 升降档建议(L1 级,人秒批后改 YAML)。"""
from datetime import timedelta
from pathlib import Path

from build_graph import load
from events_lib import load_events, parse_date

GRAPH = {"copper": "data/copper.yaml"}


def suggest(count: int) -> str:
    return "活跃" if count >= 3 else ("降温" if count >= 1 else "休眠")


def run(commodity: str, today) -> list[str]:
    G = load(Path(__file__).parent / GRAPH[commodity])
    events = load_events(commodity)
    since = today - timedelta(days=90)
    density: dict[str, int] = {}
    for e in events:
        t = parse_date(e["time"])
        if since <= t <= today:
            density[e["root_cause"]] = density.get(e["root_cause"], 0) + 1

    md = [f"# 主题热度建议 · {commodity} · {today}(90 天事件密度)", "",
          "| 根因 | 主题 | 当前状态 | 90天事件数 | 建议 | 动作 |", "|---|---|---|---|---|---|"]
    n_change = 0
    for n, d in G.nodes(data=True):
        theme = (d.get("temporal") or {}).get("theme") or {}
        if not theme.get("status"):
            continue
        cnt = density.get(n, 0)
        sug = suggest(cnt)
        change = sug != theme["status"]
        n_change += change
        md.append(f"| {n} | {theme.get('name','')} | {theme['status']} | {cnt} | {sug} | "
                  f"{'⚠️ 建议改档(L1 PR)' if change else '维持'} |")
    md.append("")
    md.append("> 规则:90 天 ≥3 条事件=活跃,1-2 条=降温,0 条=休眠。改档是建议不是自动执行——"
              "人确认后修改 YAML 的 theme.status(注意滞后型主题可人工否决,如趋势借尸还魂型)。")
    out = Path(__file__).parent / "out" / "theme_suggestions.md"
    out.write_text("\n".join(md), encoding="utf-8")
    return [f"主题建议 → {out}(建议改档 {n_change} 个)"]
