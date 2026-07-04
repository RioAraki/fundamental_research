# -*- coding: utf-8 -*-
"""生成「根因监测面板」HTML 表格行。
根因是中性状态量:面板对每个根因给出双向定性(+1 时对目标的方向;−1 反之),
方向语义(+/− 各代表什么现实事件)来自节点 direction 字段。
用法: python gen_panel.py data/palm_oil.yaml DCE棕榈油价格 out/panel.html
"""
import html
import sys
from pathlib import Path

from build_graph import load
from propagate import propagate

sys.stdout.reconfigure(encoding="utf-8")

src, target, dst = sys.argv[1], sys.argv[2], Path(sys.argv[3])
G = load(src)

rows = []
for r in [n for n in G.nodes if G.in_degree(n) == 0]:
    res = propagate(G, {r: 1}, max_hops=9)
    res.pop("__feedback__", None)
    if target not in res:
        continue
    best = res[target][0]
    rows.append((best.strength, r, best, G.nodes[r]))

rows.sort(reverse=True, key=lambda x: x[0])
out = []
for s, r, p, d in rows:
    up_bull = p.signs[-1] > 0  # 根因 +1 时目标 ↑?
    both = (('<span class="badge badge-error badge-sm">↑ 利多</span>' if up_bull
             else '<span class="badge badge-success badge-sm">↑ 利空</span>')
            + '<br/>'
            + ('<span class="badge badge-success badge-sm mt-1">↓ 利空</span>' if up_bull
               else '<span class="badge badge-error badge-sm mt-1">↓ 利多</span>'))
    sig = d.get("signals") or {}
    news = " / ".join(sig.get("news", [])) or "—"
    data = "<br/>".join(sig.get("data", [])) or "—"
    case = d.get("case", "")
    direction = d.get("direction", "")
    tmp = d.get("temporal") or {}
    theme = tmp.get("theme") or {}
    st = theme.get("status", "")
    st_cls = {"活跃": "badge-error", "降温": "badge-warning", "休眠": "badge-ghost"}.get(st, "badge-ghost")
    tbadges = ""
    if tmp.get("reversion"):
        tbadges += f'<span class="badge badge-xs badge-outline badge-accent mr-1">{html.escape(tmp["reversion"])}</span>'
    if st:
        tbadges += f'<span class="badge badge-xs {st_cls}">主题·{html.escape(theme.get("name",""))} {st}</span>'
    out.append(f"""<tr>
<td><b>{html.escape(r)}</b><div class="mt-1">{tbadges}</div><div class="text-xs text-warning/90 mt-1">{html.escape(direction)}</div><div class="text-xs text-base-content/50">{html.escape(d.get('note','')[:60])}</div></td>
<td>{both}<div class="text-xs mt-1">强度 {s:.2f}<br/>时滞 ≈{p.lag_months:.0f} 月</div></td>
<td class="text-xs">{html.escape(news)}</td>
<td class="text-xs">{data}</td>
<td class="text-xs">{html.escape(p.render())}{('<div class="text-warning/80 mt-1">案例: ' + html.escape(case) + '</div>') if case else ''}</td>
</tr>""")

dst.write_text("\n".join(out), encoding="utf-8")
print(f"面板 {len(rows)} 个根因 → {dst}")
