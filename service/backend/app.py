# -*- coding: utf-8 -*-
"""沪铜根因图谱 · 后端 API(FastAPI)。
复用 kg-mvp 的现有引擎(build_graph / propagate / events_lib),只读 YAML,不写。
端点:GET /api/graph · GET /api/node/{id} · GET /api/edge/{id} · POST /api/reason
"""
import sys
from datetime import date
from pathlib import Path

# 把 kg-mvp 加入 import 路径(service/backend/ → 上两级是仓库根)
KG = Path(__file__).resolve().parents[2] / "kg-mvp"
sys.path.insert(0, str(KG))

from fastapi import FastAPI, HTTPException  # noqa: E402
from fastapi.middleware.cors import CORSMiddleware  # noqa: E402
from fastapi.staticfiles import StaticFiles  # noqa: E402
from pydantic import BaseModel  # noqa: E402

from build_graph import load  # noqa: E402
from propagate import propagate  # noqa: E402
from events_lib import load_events, current_shocks, active_events, parse_date  # noqa: E402

GRAPHS = {"copper": ("data/copper.yaml", "SHFE铜价格"),
          "palm": ("data/palm_oil.yaml", "DCE棕榈油价格")}

COLOR = {
    "根因·天气": "#7c2d12", "根因·结构": "#57534e", "根因·供给": "#7c2d12",
    "根因·政策": "#5b21b6", "根因·宏观": "#831843", "根因·需求": "#14532d",
    "根因·季节": "#0e7490", "根因·市场": "#a16207",
    "供给指标": "#1e3a5f", "需求指标": "#14532d", "替代品": "#14532d",
    "价差": "#3f6212", "情绪": "#a16207", "价格": "#b91c1c",
    # 橄榄油 schema 兼容
    "天气冲击": "#7c2d12", "结构因素": "#57534e", "成本": "#525252",
    "政策": "#5b21b6", "政策事件": "#5b21b6", "宏观事件": "#831843", "需求因素": "#14532d",
}
STRENGTH_W = {"强": 3, "中": 2, "弱": 1}
BUCKETS = [("0-1 月", 0, 1), ("1-6 月", 1, 6), ("6 月以上", 6, 10 ** 9)]

_cache: dict[str, tuple] = {}


def get_graph(commodity: str):
    if commodity not in GRAPHS:
        raise HTTPException(404, f"未知品种 {commodity}")
    if commodity not in _cache:
        gpath, target = GRAPHS[commodity]
        _cache[commodity] = (load(KG / gpath), target)
    return _cache[commodity]


def node_color(d: dict) -> str:
    return COLOR.get(d.get("type", ""), "#57534e")


def node_effect(G, node: str, target: str):
    """该量 +1 时对目标价的方向/最强路径/多空路径数(利好利空判定)。"""
    if node == target:
        return None
    res = propagate(G, {node: 1}, max_hops=9)
    res.pop("__feedback__", None)
    paths = res.get(target)
    if not paths:
        return None
    best = paths[0]
    bull = sum(1 for p in paths if p.signs[-1] > 0)
    return {"sign": "利多" if best.signs[-1] > 0 else "利空",
            "strength": round(best.strength, 2), "lag": round(best.lag_months, 1),
            "path": best.render(), "n_paths": len(paths),
            "n_bull": bull, "n_bear": len(paths) - bull}


app = FastAPI(title="根因图谱 API", version="1.0")
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])


@app.get("/api/graph")
def api_graph(commodity: str = "copper"):
    G, target = get_graph(commodity)
    nodes = [{"id": n, "label": n, "type": d.get("type", ""),
              "isRoot": G.in_degree(n) == 0, "isTarget": n == target,
              "color": node_color(d)} for n, d in G.nodes(data=True)]
    edges = []
    for i, (u, v, d) in enumerate(G.edges(data=True)):
        edges.append({"id": f"e{i}", "source": u, "target": v,
                      "polarity": d["polarity_str"], "strength": d["strength"],
                      "color": "#38bdf8" if d["polarity"] > 0 else "#f87171",
                      "width": STRENGTH_W.get(d["strength"], 1),
                      "label": f'{d["polarity_str"]}·{d["strength"]}'})
    return {"commodity": commodity, "target": target, "nodes": nodes, "edges": edges}


@app.get("/api/node/{node_id}")
def api_node(node_id: str, commodity: str = "copper"):
    G, target = get_graph(commodity)
    if node_id not in G.nodes:
        raise HTTPException(404, f"节点不存在 {node_id}")
    d = G.nodes[node_id]
    return {"id": node_id, "type": d.get("type", ""), "note": d.get("note", ""),
            "direction": d.get("direction", ""), "case": d.get("case", ""),
            "signals": d.get("signals") or {}, "temporal": d.get("temporal") or {},
            "isRoot": G.in_degree(node_id) == 0, "isTarget": node_id == target,
            "effect": node_effect(G, node_id, target)}


@app.get("/api/edge/{edge_id}")
def api_edge(edge_id: str, commodity: str = "copper"):
    G, _ = get_graph(commodity)
    try:
        idx = int(edge_id[1:])
    except (ValueError, IndexError):
        raise HTTPException(400, "边 id 格式应为 e<数字>")
    edges = list(G.edges(data=True))
    if not 0 <= idx < len(edges):
        raise HTTPException(404, f"边不存在 {edge_id}")
    u, v, d = edges[idx]
    verb = "上升" if d["polarity"] > 0 else "下降"
    sentence = (f"当「{u}」上升时,「{v}」趋于{verb}(机制{'同向 +' if d['polarity'] > 0 else '反向 −'});"
                f"传导时滞约 {d['lag']},强度「{d['strength']}」。"
                f"反之「{u}」下降则「{v}」趋于{'下降' if d['polarity'] > 0 else '上升'}。")
    return {"id": edge_id, "source": u, "target": v, "polarity": d["polarity_str"],
            "lag": d["lag"], "strength": d["strength"], "condition": d.get("condition", ""),
            "evidence": d.get("evidence", ""), "rationale": d.get("rationale", ""),
            "sentence": sentence}


class ReasonReq(BaseModel):
    commodity: str = "copper"
    shocks: dict[str, int] | None = None
    use_active_events: bool = False
    date: str | None = None


@app.post("/api/reason")
def api_reason(req: ReasonReq):
    G, target = get_graph(req.commodity)
    if req.use_active_events:
        today = parse_date(req.date) if req.date else date.today()
        events = load_events(req.commodity)
        shocks = current_shocks(events, today)
        active = [{"time": str(e["time"]), "root_cause": e["root_cause"],
                   "direction": e["direction"], "magnitude": str(e.get("magnitude", "")),
                   "source": e.get("source", "")} for e in active_events(events, today)]
    else:
        shocks = {k: int(v) for k, v in (req.shocks or {}).items()}
        active = []

    res = propagate(G, shocks, max_hops=9) if shocks else {"__feedback__": []}
    loops = res.pop("__feedback__", [])
    paths = res.get(target, [])

    buckets = []
    for label, lo, hi in BUCKETS:
        ps = [p for p in paths if lo <= p.lag_months < hi]
        bull = sum(p.strength for p in ps if p.signs[-1] > 0)
        bear = sum(p.strength for p in ps if p.signs[-1] < 0)
        if bull and bear and min(bull, bear) / max(bull, bear) > 0.5:
            tag = "多空拉锯"
        elif bull > bear:
            tag = "偏多"
        elif bear > bull:
            tag = "偏空"
        else:
            tag = "无信号"
        top = [{"sign": "多" if p.signs[-1] > 0 else "空", "strength": round(p.strength, 2),
                "lag": round(p.lag_months, 1), "render": p.render()}
               for p in sorted(ps, key=lambda x: -x.strength)[:3]]
        buckets.append({"label": label, "tag": tag, "bull": round(bull, 2),
                        "bear": round(bear, 2), "n_paths": len(ps), "top": top})

    # 每个受影响节点的净方向(供前端染色)
    node_signs = {}
    for n, plist in res.items():
        b = sum(p.strength for p in plist if p.signs[-1] > 0)
        r = sum(p.strength for p in plist if p.signs[-1] < 0)
        node_signs[n] = 1 if b > r else (-1 if r > b else 0)
    for n, s in shocks.items():
        node_signs[n] = s
    # 传导路径经过的边(source,target)供前端高亮
    edge_pairs = set()
    for p in paths:
        for i in range(1, len(p.nodes)):
            edge_pairs.add((p.nodes[i - 1], p.nodes[i]))

    return {"target": target, "shocks": shocks, "active_events": active,
            "buckets": buckets, "node_signs": node_signs,
            "edges_on_paths": [list(pair) for pair in edge_pairs],
            "n_feedback_loops": len(loops)}


@app.get("/api/health")
def health():
    return {"ok": True, "commodities": list(GRAPHS)}


# 生产模式:若前端已构建到 ../frontend/dist,则由后端一并托管(单进程起服务)
_dist = Path(__file__).resolve().parents[1] / "frontend" / "dist"
if _dist.exists():
    app.mount("/", StaticFiles(directory=str(_dist), html=True), name="frontend")
