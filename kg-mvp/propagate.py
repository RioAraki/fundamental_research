# -*- coding: utf-8 -*-
"""QPN 式符号传播推理器(~200 行,可解释)。

核心语义:
- 冲击 shock:某节点"增加/发生"(+1)或"减少"(-1)
- 路径符号 = 各边 polarity 相乘;路径强度 = 各边权重相乘(弱边衰减);时滞 = 各边累计
- 环路处理:单条路径内不允许重访节点(时间展开的一步近似);源节点自环单独识别为"反馈回路"
- 冲突消解:不强行裁决,同一目标节点同时给出利多/利空路径对照
"""
from dataclasses import dataclass, field

import networkx as nx

SIGN_TXT = {1: "↑", -1: "↓"}


@dataclass
class Path:
    nodes: list
    signs: list          # 每个节点的方向(含起点)
    edges: list          # 边属性 dict 列表
    strength: float
    lag_months: float
    conditions: list = field(default_factory=list)

    def render(self) -> str:
        parts = [f"{self.nodes[0]}{SIGN_TXT[self.signs[0]]}"]
        for e, node, s in zip(self.edges, self.nodes[1:], self.signs[1:]):
            parts.append(f" ─{e['polarity_str']}/{e['lag']}/{e['strength']}→ {node}{SIGN_TXT[s]}")
        return "".join(parts)


def propagate(G: nx.DiGraph, shocks: dict[str, int], max_hops: int = 7,
              min_strength: float = 0.02) -> dict[str, list[Path]]:
    """从冲击节点前向传播,返回 {目标节点: [Path, ...]}(不含冲击节点自身)。"""
    results: dict[str, list[Path]] = {}
    feedback_loops: list[Path] = []

    def dfs(path: Path):
        cur = path.nodes[-1]
        if len(path.nodes) > max_hops:
            return
        for _, nxt, attr in G.out_edges(cur, data=True):
            new_sign = path.signs[-1] * attr["polarity"]
            new_strength = path.strength * attr["weight"]
            if new_strength < min_strength:
                continue
            if nxt == path.nodes[0]:  # 回到源点 → 反馈回路
                feedback_loops.append(Path(
                    path.nodes + [nxt], path.signs + [new_sign], path.edges + [attr],
                    new_strength, path.lag_months + attr["lag_months"],
                    path.conditions + ([attr["condition"]] if attr["condition"] else [])))
                continue
            if nxt in path.nodes:  # 非源点重访:掐断(消环)
                continue
            new_path = Path(
                path.nodes + [nxt], path.signs + [new_sign], path.edges + [attr],
                new_strength, path.lag_months + attr["lag_months"],
                path.conditions + ([attr["condition"]] if attr["condition"] else []))
            results.setdefault(nxt, []).append(new_path)
            dfs(new_path)

    for node, direction in shocks.items():
        if node not in G:
            raise KeyError(f"冲击节点不在图中: {node}")
        dfs(Path([node], [direction], [], 1.0, 0.0))

    for paths in results.values():
        paths.sort(key=lambda p: -p.strength)
    results["__feedback__"] = feedback_loops
    return results


def verdict(paths: list[Path]) -> dict:
    """对单个目标节点做多空汇总:输出净倾向 + 多空路径对照(不裁决冲突)。"""
    bull = [p for p in paths if p.signs[-1] > 0]
    bear = [p for p in paths if p.signs[-1] < 0]
    b, r = sum(p.strength for p in bull), sum(p.strength for p in bear)
    if b > 0 and r > 0:
        tag = "⚠️ 多空冲突" if min(b, r) / max(b, r) > 0.34 else ("偏多(有反向路径)" if b > r else "偏空(有反向路径)")
    else:
        tag = "利多" if b > r else "利空"
    return {"bull": bull, "bear": bear, "bull_score": round(b, 3),
            "bear_score": round(r, 3), "tag": tag}


def report(G, shocks, targets=None, top=3, max_hops=7) -> str:
    """生成一次推理的完整文字报告。targets=None 时输出全部受影响节点。"""
    res = propagate(G, shocks, max_hops=max_hops)
    loops = res.pop("__feedback__")
    lines = []
    shock_txt = ", ".join(f"{k}{SIGN_TXT[v]}" for k, v in shocks.items())
    lines.append(f"◆ 情景冲击:{shock_txt}")

    order = targets if targets else sorted(res, key=lambda n: -max(p.strength for p in res[n]))
    for t in order:
        if t not in res:
            lines.append(f"\n▶ {t}:图上无从冲击出发的传导路径")
            continue
        v = verdict(res[t])
        lines.append(f"\n▶ {t} —— {v['tag']}(利多分 {v['bull_score']} vs 利空分 {v['bear_score']})")
        for label, group in (("利多路径", v["bull"]), ("利空路径", v["bear"])):
            for p in group[:top]:
                lines.append(f"   [{label} 强度{p.strength:.2f} 时滞≈{p.lag_months:.0f}月] {p.render()}")
                for c in dict.fromkeys(p.conditions):
                    lines.append(f"      └ 条件:{c}")
            if len(group) > top:
                lines.append(f"   … 另有 {len(group)-top} 条{label}略")
    if loops:
        lines.append("\n↻ 检测到经过冲击节点的反馈回路:")
        for p in sorted(loops, key=lambda x: -x.strength)[:5]:
            kind = "自我强化(正反馈)" if p.signs[-1] == p.signs[0] else "自我修复(负反馈)"
            lines.append(f"   [{kind} 强度{p.strength:.2f} 周期≈{p.lag_months:.0f}月] {p.render()}")
    return "\n".join(lines)


def signal_block(G: nx.DiGraph, nodes) -> str:
    """输出若干节点的监测信号(新闻关键词 + 数据源),即'根因定性、新闻数据定量'的定量端。"""
    lines = []
    for n in nodes:
        sig = G.nodes[n].get("signals") or {}
        if not sig:
            continue
        lines.append(f"📡 「{n}」的监测信号:")
        if sig.get("news"):
            lines.append(f"   新闻关键词:{' / '.join(sig['news'])}")
        if sig.get("data"):
            lines.append(f"   数据源:{' | '.join(sig['data'])}")
        if G.nodes[n].get("case"):
            lines.append(f"   历史案例:{G.nodes[n]['case']}")
    return "\n".join(lines)


def explain_drivers(G: nx.DiGraph, target: str, max_hops: int = 6, top_show: int = 40) -> str:
    """反向问法:哪些根因会影响 target?对每个根因节点做一次 +1 冲击,汇总到 target 的最强路径。"""
    roots = [n for n in G.nodes if G.in_degree(n) == 0]
    rows = []
    for r in roots:
        res = propagate(G, {r: 1}, max_hops=max_hops)
        res.pop("__feedback__", None)
        if target in res:
            best = res[target][0]
            rows.append((best.strength, r, best))
    rows.sort(reverse=True, key=lambda x: x[0])
    lines = [f"◆ 影响「{target}」的根因全景(按最强路径强度排序)"]
    for s, r, p in rows[:top_show]:
        lines.append(f"  {SIGN_TXT[p.signs[-1]]} {r}(强度{s:.2f}, 时滞≈{p.lag_months:.0f}月): {p.render()}")
    return "\n".join(lines)
