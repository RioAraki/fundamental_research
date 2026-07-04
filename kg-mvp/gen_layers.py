# -*- coding: utf-8 -*-
"""三层方法论页面内容生成器:
① 主题看板(活跃/降温/休眠) ② 事件日志时间线 ③ 当前活跃事件叠加 → 分时段推理
用法: python gen_layers.py data/copper.yaml data/copper_events.yaml SHFE铜价格 out/cu_layers
输出: <prefix>_themes.html / <prefix>_events.html / <prefix>_stacked.html
"""
import html as H
import sys
from pathlib import Path

import yaml

from build_graph import load
from propagate import propagate, SIGN_TXT

sys.stdout.reconfigure(encoding="utf-8")
graph_src, events_src, target, prefix = sys.argv[1], sys.argv[2], sys.argv[3], sys.argv[4]
G = load(graph_src)
events = yaml.safe_load(Path(events_src).read_text(encoding="utf-8"))["events"]

# ── ① 主题看板 ──
board = {"活跃": [], "降温": [], "休眠": []}
for n, d in G.nodes(data=True):
    theme = (d.get("temporal") or {}).get("theme") or {}
    if theme.get("status") in board:
        board[theme["status"]].append((theme, n, d))

cols = []
STYLE = {"活跃": ("🔥 活跃", "border-error/60"), "降温": ("🌡️ 降温", "border-warning/60"),
         "休眠": ("💤 休眠", "border-base-content/20")}
for status, (label, border) in STYLE.items():
    cards = []
    for theme, n, d in board[status]:
        since = f'<span class="text-xs opacity-60">since {H.escape(str(theme.get("since","")))}</span>' if theme.get("since") else ""
        cards.append(
            f'<div class="rounded-box border {border} bg-base-100 p-3 mb-2">'
            f'<b>{H.escape(theme.get("name",""))}</b> {since}'
            f'<div class="text-xs mt-1">挂载根因:<span class="badge badge-xs badge-outline">{H.escape(n)}</span>'
            f' <span class="badge badge-xs badge-outline badge-accent">{H.escape((d.get("temporal") or {}).get("reversion",""))}</span></div>'
            f'<div class="text-xs text-base-content/60 mt-1">{H.escape(theme.get("note",""))}</div></div>')
    cols.append(f'<div class="cell"><h3 class="font-bold mb-2">{label}({len(board[status])})</h3>{"".join(cards)}</div>')
(Path(f"{prefix}_themes.html")).write_text(
    f'<div class="grid gap-4 lg:grid-cols-3 cell">{"".join(cols)}</div>', encoding="utf-8")

# ── ② 事件时间线(倒序)──
rows = []
for e in sorted(events, key=lambda x: x["time"], reverse=True):
    dir_badge = ('<span class="badge badge-sm badge-error">+1</span>' if e["direction"] > 0
                 else '<span class="badge badge-sm badge-success">−1</span>')
    act = '<span class="badge badge-sm badge-warning">生效中</span>' if e.get("active") else '<span class="badge badge-sm badge-ghost">已过期/被反转</span>'
    rev = (G.nodes[e["root_cause"]].get("temporal") or {}).get("reversion", "") if e["root_cause"] in G.nodes else "⚠️根因不存在"
    rows.append(f"""<tr>
<td class="text-xs whitespace-nowrap">{e['time']}</td>
<td><b>{H.escape(e['root_cause'])}</b><div class="text-xs opacity-60">{H.escape(rev)}</div></td>
<td>{dir_badge}<div class="text-xs mt-1">{H.escape(e.get('magnitude',''))}</div></td>
<td class="text-xs">{H.escape(e.get('window',''))}</td>
<td>{act}</td>
<td class="text-xs">{H.escape(e.get('source',''))}</td></tr>""")
(Path(f"{prefix}_events.html")).write_text("\n".join(rows), encoding="utf-8")

# ── ③ 活跃事件叠加 → 分时段推理 ──
W = {"强": 1.0, "中": 0.66, "弱": 0.33}
active = [e for e in events if e.get("active")]
# 同一根因取最新事件方向
shocks = {}
for e in sorted(active, key=lambda x: x["time"]):
    shocks[e["root_cause"]] = e["direction"]
res = propagate(G, shocks, max_hops=9)
res.pop("__feedback__", None)
paths = res.get(target, [])
BUCKETS = [("0-1 月", 0, 1), ("1-6 月", 1, 6), ("6 月以上", 6, 10**9)]
sections = []
for label, lo, hi in BUCKETS:
    ps = [p for p in paths if lo <= p.lag_months < hi]
    bull = sum(p.strength for p in ps if p.signs[-1] > 0)
    bear = sum(p.strength for p in ps if p.signs[-1] < 0)
    tag = ("多空拉锯 ⚠️" if bull and bear and min(bull, bear) / max(bull, bear) > 0.5
           else ("偏多" if bull > bear else ("偏空" if bear > bull else "无信号")))
    top = sorted(ps, key=lambda p: -p.strength)[:3]
    lines = "".join(
        f'<div class="text-xs mt-1 {"text-error" if p.signs[-1] > 0 else "text-success"}">'
        f'[{"多" if p.signs[-1] > 0 else "空"} {p.strength:.2f}] {H.escape(p.render())}</div>' for p in top)
    sections.append(
        f'<div class="rounded-box bg-base-200 p-3 mb-2"><b>【{label}】{tag}</b>'
        f'<span class="text-xs opacity-70">(多 {bull:.2f} vs 空 {bear:.2f},路径 {len(ps)} 条)</span>{lines}</div>')
shock_txt = " · ".join(f"{k}{SIGN_TXT[v]}" for k, v in shocks.items())
head = (f'<div class="text-sm mb-2">当前生效事件叠加(共 {len(active)} 条,取每根因最新方向):'
        f'<b>{H.escape(shock_txt)}</b></div>')
(Path(f"{prefix}_stacked.html")).write_text(head + "".join(sections), encoding="utf-8")
print(f"主题 {sum(len(v) for v in board.values())} 个 / 事件 {len(events)} 条(生效 {len(active)})/ "
      f"叠加推理路径 {len(paths)} 条 → {prefix}_*.html")
