# -*- coding: utf-8 -*-
"""CI 质量门(SPEC §6):schema + golden tests + 事件日志校验 + 跨品种一致性。退出码 0/1。"""
import sys
from pathlib import Path

import networkx as nx

from build_graph import LAG_MONTHS, load
from events_lib import load_events, parse_date
from propagate import propagate, verdict

sys.stdout.reconfigure(encoding="utf-8")
ROOT = Path(__file__).parent
FAILURES = []


def check(name: str, ok: bool, detail: str = ""):
    print(f"{'✅' if ok else '❌'} {name}" + (f" — {detail}" if detail else ""))
    if not ok:
        FAILURES.append(name)


def net_sign(G, shocks, target):
    res = propagate(G, shocks, max_hops=9)
    res.pop("__feedback__", None)
    v = verdict(res.get(target, []))
    return v["bull_score"] - v["bear_score"]


def has_cycle_containing(G, must_nodes: set) -> bool:
    return any(must_nodes <= set(c) for c in nx.simple_cycles(G))


def main() -> int:
    # ── 1. Schema(load 内部 sys.exit(1) 即失败)──
    cu = load(ROOT / "data" / "copper.yaml")
    check("schema: copper.yaml", True, f"{cu.number_of_nodes()} 节点/{cu.number_of_edges()} 边")

    # ── 2. Golden tests · 铜 ──
    check("golden(cu): 矿端供给扰动率+1 ⇒ SHFE 净利多",
          net_sign(cu, {"矿端供给扰动率": 1}, "SHFE铜价格") > 0)
    check("golden(cu): 美联储政策立场+1 ⇒ SHFE 净利空",
          net_sign(cu, {"美联储政策立场": 1}, "SHFE铜价格") < 0)
    roots = [n for n in cu.nodes if cu.in_degree(n) == 0]
    unreachable = [r for r in roots
                   if "SHFE铜价格" not in {k for k in propagate(cu, {r: 1}, max_hops=9) if k != "__feedback__"}]
    check("golden(cu): 全部根因 9 跳内可达 SHFE", not unreachable, f"不可达: {unreachable}")
    check("golden(cu): R3 比值-进口负反馈环存在",
          has_cycle_containing(cu, {"沪伦比值", "进口流入", "中国社会库存"}))
    check("golden(cu): R1 精废替代环存在", has_cycle_containing(cu, {"精废价差"}))

    # ── 3. 事件日志校验 ──
    for commodity, G in (("copper", cu),):
        try:
            events = load_events(commodity)
        except FileNotFoundError:
            continue
        bad_node = [e["root_cause"] for e in events if e["root_cause"] not in G.nodes]
        bad_win = [e.get("window") for e in events
                   if e.get("window") not in LAG_MONTHS and e.get("window") != "待反转"]
        bad_dir = [e for e in events if e.get("direction") not in (1, -1)]
        ok = not (bad_node or bad_win or bad_dir)
        check(f"events({commodity}): 节点/窗口/方向合法({len(events)} 条)", ok,
              f"坏节点{bad_node} 坏窗口{bad_win} 坏方向{len(bad_dir)}" if not ok else "")
        try:
            for e in events:
                parse_date(e["time"])
            check(f"events({commodity}): 时间可解析", True)
        except Exception as ex:
            check(f"events({commodity}): 时间可解析", False, str(ex))

    # ── 4. L1 覆盖度(SPEC §L1)──
    # 硬失败:科目表指向了图中不存在的节点(两份事实源不一致,必须修)
    # 软告警:必备科目/库存池未建模(结构盲点,靠 PR 逐步补,不阻塞)
    import check_coverage as cov
    bal = cov._load_balance("copper")
    broken = [a["id"] for _, a in cov._accounts(bal)
              if a.get("node") and a["node"] not in cu]
    check("coverage(cu): 科目表与图谱映射一致", not broken, f"指向不存在的节点: {broken}")

    must = [(t, a) for t, a in cov._accounts(bal) if a.get("must")]
    must_gap = [a["id"] for _, a in must if not a.get("node")]
    pools = bal.get("inventory_pools", [])
    pool_ok = sum(1 for p in pools if p.get("node") and p["node"] in cu)
    print(f"ℹ️ 提醒(不阻塞): copper 必备科目覆盖 {len(must)-len(must_gap)}/{len(must)}"
          f",库存池 {pool_ok}/{len(pools)};缺口: {', '.join(must_gap) if must_gap else '无'}"
          f"(cli.py coverage 出完整报告)")

    # ── 5. 保质期警告(不阻塞)──
    never = sum(1 for _, _, d in cu.edges(data=True) if not d.get("review"))
    print(f"ℹ️ 提醒(不阻塞): copper 从未审校的边 {never}/{cu.number_of_edges()} 条(scan_reviews 出清单)")

    print("\n" + ("🎉 全部通过" if not FAILURES else f"💥 失败 {len(FAILURES)} 项: {FAILURES}"))
    return 0 if not FAILURES else 1


if __name__ == "__main__":
    sys.exit(main())
