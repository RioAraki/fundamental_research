# -*- coding: utf-8 -*-
"""L1 覆盖度体检:把「先验完整的平衡表科目表」与「图谱实际建了什么」做 diff。

方法论(METHODOLOGY.md §L1):定性研究不需要平衡表的数字,但需要它的**科目空间**。
科目空间是封闭的,所以"我漏了什么"从不可回答变成可枚举:

  科目表 ⊖ 图谱 = 结构盲点

七项检查:
  1. 科目未建模         balance.yaml 中 node: null 的科目(must 优先)
  2. 映射失效           node 指向的 id 在图中不存在(改名/删节点造成)
  3. 科目无驱动         科目节点入度为 0 且非根因 —— 建了但从没研究过它为什么变
  4. 悬空根因           根因走不到任何科目/通道节点 —— 影响不了任何量,也就影响不了价格
  5. 库存池缺口         五池加总校验的前提是五池都有节点
  6. 通道缺口           L0/L2/L3/L4 中已知却未建模的指标
  7. 文字-结构背离      在 rationale/evidence/condition 里被反复引用、却没有节点的名词
"""
import re
import sys
from collections import Counter
from pathlib import Path

import networkx as nx
import yaml

import build_graph

ROOT = Path(__file__).parent
MAX_HOPS = 9  # 与 CI golden test 的 9 跳可达性保持一致


def _load_balance(commodity: str) -> dict:
    return yaml.safe_load((ROOT / "data" / f"{commodity}_balance.yaml").read_text(encoding="utf-8"))


def _load_scope(commodity: str) -> dict:
    p = ROOT / "data" / f"{commodity}_scope.yaml"
    return yaml.safe_load(p.read_text(encoding="utf-8")) if p.exists() else {}


def _accounts(bal: dict):
    """展平所有科目 + 库存池,统一成 (来源表, 科目 dict)。"""
    for t in bal.get("tables", []):
        for a in t.get("accounts", []):
            yield t["id"], a
    for p in bal.get("inventory_pools", []):
        yield "库存池", p


def _mapped_nodes(bal: dict) -> set:
    """科目表 + 通道声明中,所有已经指向图节点的 id。"""
    ids = {a.get("node") for _, a in _accounts(bal) if a.get("node")}
    for c in bal.get("channels", []):
        ids |= set(c.get("nodes", []))
    return ids


def run(commodity: str = "copper", today=None) -> list[str]:
    G = build_graph.load(ROOT / "data" / f"{commodity}.yaml")
    bal = _load_balance(commodity)
    scope = _load_scope(commodity)
    lines, summary = [], []

    lines.append(f"# L1 覆盖度体检 · {bal['meta']['commodity']}")
    lines.append("")
    lines.append(f"> 科目表版本 {bal['meta']['version']} · 图谱 {G.number_of_nodes()} 节点 / "
                 f"{G.number_of_edges()} 边 · 定性口径")
    lines.append("")

    # ── 1/2. 科目未建模 与 映射失效 ──
    missing_must, missing_opt, broken, modeled = [], [], [], []
    for table, a in _accounts(bal):
        node = a.get("node")
        if node is None:
            (missing_must if a.get("must") else missing_opt).append((table, a))
        elif node not in G:
            broken.append((table, a))
        else:
            modeled.append((table, a))

    total = len(missing_must) + len(missing_opt) + len(broken) + len(modeled)
    must_total = len([1 for _, a in _accounts(bal) if a.get("must")])
    must_ok = len([1 for _, a in modeled if a.get("must")])

    lines.append("## 一、科目覆盖")
    lines.append("")
    lines.append(f"- 全部科目:**{len(modeled)}/{total}** 已建模")
    lines.append(f"- 必备科目(must):**{must_ok}/{must_total}** 已建模")
    lines.append("")
    summary.append(f"科目覆盖 {len(modeled)}/{total} · 必备 {must_ok}/{must_total}")

    if missing_must:
        lines.append("### ★ 必备科目缺口(结构盲点)")
        lines.append("")
        lines.append("| 所属表 | 科目 | 侧 | 为什么重要 |")
        lines.append("|---|---|---|---|")
        for table, a in missing_must:
            why = (a.get("gap") or a.get("note") or "").replace("\n", " ")
            lines.append(f"| {table} | **{a['id']}** | {a.get('side', a.get('visibility', ''))} | {why} |")
        lines.append("")
    if missing_opt:
        lines.append("### 次要科目缺口")
        lines.append("")
        for table, a in missing_opt:
            lines.append(f"- {table} · {a['id']} —— {(a.get('gap') or a.get('note') or '')}")
        lines.append("")
    if broken:
        lines.append("### 映射失效(科目指向的节点在图中不存在)")
        lines.append("")
        for table, a in broken:
            lines.append(f"- {table} · {a['id']} → 找不到节点 `{a['node']}`")
        lines.append("")

    # ── 3. 已建模科目无驱动 ──
    no_driver = [(t, a) for t, a in modeled
                 if G.in_degree(a["node"]) == 0 and not G.nodes[a["node"]].get("type", "").startswith("根因")]
    lines.append("## 二、已建模但无驱动的科目")
    lines.append("")
    if no_driver:
        lines.append("这些科目在图里存在,但没有任何边解释它为什么会变——等于摆了个空盒子。")
        lines.append("")
        for t, a in no_driver:
            lines.append(f"- {t} · **{a['id']}**(节点 `{a['node']}` 入度 0)")
    else:
        lines.append("无。所有已建模科目都至少有一条驱动边。")
    lines.append("")
    summary.append(f"无驱动科目 {len(no_driver)}")

    # ── 4. 悬空根因 ──
    targets = {n for n in _mapped_nodes(bal) if n in G}
    roots = [n for n in G.nodes if G.nodes[n].get("type", "").startswith("根因")]
    dangling = []
    for r in roots:
        reach = nx.single_source_shortest_path_length(G, r, cutoff=MAX_HOPS)
        if not (set(reach) & targets):
            dangling.append(r)
    lines.append("## 三、悬空根因")
    lines.append("")
    lines.append(f"判据:根因在 {MAX_HOPS} 跳内走不到任何平衡表科目、也走不到任何已声明的 L2/L3/L4 通道节点。")
    lines.append("这类根因既改不了量、也改不了估值/结构/预期,属于修辞而非机制。")
    lines.append("")
    if dangling:
        for r in dangling:
            lines.append(f"- **{r}**")
    else:
        lines.append("无。全部根因都能落到科目或通道上。")
    lines.append("")
    summary.append(f"悬空根因 {len(dangling)}/{len(roots)}")

    # ── 5. 库存池 ──
    pools = bal.get("inventory_pools", [])
    pool_ok = [p for p in pools if p.get("node") and p["node"] in G]
    lines.append("## 四、库存分池(加总校验的前提)")
    lines.append("")
    lines.append(f"**{len(pool_ok)}/{len(pools)}** 池已建模。定性用法:总库存方向变化,必须能被至少一池解释;")
    lines.append("说不出是哪一池 → 该池未建模。")
    lines.append("")
    lines.append("| 池 | 可见性 | 状态 | 说明 |")
    lines.append("|---|---|---|---|")
    for p in pools:
        ok = p.get("node") and p["node"] in G
        state = f"✅ `{p['node']}`" if ok else ("★ 缺失" if p.get("must") else "缺失")
        note = (p.get("gap") or p.get("note") or "").replace("\n", " ")
        lines.append(f"| {p['id']} | {p.get('visibility','')} | {state} | {note} |")
    lines.append("")
    summary.append(f"库存池 {len(pool_ok)}/{len(pools)}")

    # ── 6. 通道缺口 ──
    lines.append("## 五、非平衡表通道(L0/L2/L3/L4)")
    lines.append("")
    chan_missing = 0
    for c in bal.get("channels", []):
        have = [n for n in c.get("nodes", []) if n in G]
        miss = c.get("missing", [])
        chan_missing += len(miss)
        lines.append(f"### {c['id']}({c['layer']})")
        lines.append("")
        lines.append(f"*{c['meaning']}*")
        lines.append("")
        lines.append(f"- 已建模:{', '.join(f'`{n}`' for n in have) if have else '(无)'}")
        for m in miss:
            lines.append(f"- 缺失 · **{m['id']}** —— {m['gap']}")
        lines.append("")
    summary.append(f"通道缺口 {chan_missing}")

    # ── 7. 文字-结构背离 ──
    text = " ".join(
        f"{d.get('rationale','')} {d.get('evidence','')} {d.get('condition','')}"
        for _, _, d in G.edges(data=True))
    text += " ".join(f"{d.get('note','')} {d.get('case','')}" for _, d in G.nodes(data=True))
    # 精确到"能唯一指向一个候选节点"的词;避免"出口"这类会被「家电产销出口」误命中的宽泛词
    watch = ["人民币", "汇率", "洋山", "保税", "运费", "海运", "船期", "季节", "旺季", "淡季",
             "注销仓单", "交割品牌", "铜材出口", "在途", "升贴水", "成本曲线", "现金成本"]
    hits = Counter()
    for w in watch:
        n = len(re.findall(re.escape(w), text))
        if n:
            hits[w] = n
    lines.append("## 六、文字-结构背离扫描")
    lines.append("")
    lines.append("在 rationale / evidence / condition / note 里被反复提到,却没有对应节点的名词。")
    lines.append("机制写在文字里而没有建成结构,是最隐蔽的一类盲点:读的人以为考虑过了,推理引擎其实看不见。")
    lines.append("")
    lines.append("| 关键词 | 文中出现 | 图中有节点? |")
    lines.append("|---|---|---|")
    node_text = " ".join(G.nodes)
    for w, n in hits.most_common():
        has = "✅" if w in node_text else "❌ **无节点**"
        lines.append(f"| {w} | {n} | {has} |")
    lines.append("")
    orphan_words = [w for w in hits if w not in node_text]
    summary.append(f"文字提及无节点 {len(orphan_words)} 词")

    # ── L0 断点 ──
    chain = scope.get("translation_chain", [])
    if chain:
        lines.append("## 七、L0 定价链断点")
        lines.append("")
        lines.append("| 从 | 到 | 途经 | 状态 |")
        lines.append("|---|---|---|---|")
        for s in chain:
            lines.append(f"| {s['step']} | {s['to']} | {', '.join(s['via'])} | {s['status']} |")
        lines.append("")

    out_path = ROOT / "out" / "coverage_report.md"
    out_path.parent.mkdir(exist_ok=True)
    out_path.write_text("\n".join(lines), encoding="utf-8")

    head = [f"L1 覆盖度体检 · {bal['meta']['commodity']}", "  " + " | ".join(summary), ""]
    if missing_must:
        head.append("必备科目缺口:")
        head += [f"  ★ {a['id']}（{t}）" for t, a in missing_must]
    if dangling:
        head.append("悬空根因:" + "、".join(dangling))
    head.append("")
    head.append(f"完整报告:{out_path.relative_to(ROOT)}")
    return head


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8")
    print("\n".join(run("copper")))
