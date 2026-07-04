import { useCallback, useEffect, useMemo, useState } from "react";
import {
  ReactFlow, Background, Controls, MiniMap, useNodesState, useEdgesState,
} from "@xyflow/react";
import { fetchGraph, fetchNode, fetchEdge, reason } from "./api.js";
import { layoutGraph } from "./layout.js";
import KgNode from "./KgNode.jsx";

const nodeTypes = { kg: KgNode };
const today = "2026-07-06"; // 样例数据当前日期(point-in-time)

export default function App() {
  const [nodes, setNodes, onNodesChange] = useNodesState([]);
  const [edges, setEdges, onEdgesChange] = useEdgesState([]);
  const [target, setTarget] = useState("");
  const [detail, setDetail] = useState(null); // {kind:'node'|'edge', data}
  const [scenario, setScenario] = useState(null); // reason 结果
  const [mode, setMode] = useState("browse"); // browse | reason
  const [manualShocks, setManualShocks] = useState({}); // {node: 1|-1}

  // 初次加载:拉图 + elk 布局
  useEffect(() => {
    (async () => {
      const g = await fetchGraph();
      setTarget(g.target);
      const laid = await layoutGraph(g);
      setNodes(laid.nodes);
      setEdges(laid.edges);
    })().catch((e) => alert("加载图谱失败:" + e.message));
  }, [setNodes, setEdges]);

  const rootCauses = useMemo(
    () => nodes.filter((n) => n.data.isRoot).map((n) => n.id).sort(),
    [nodes]
  );

  const onNodeClick = useCallback(async (_, node) => {
    setDetail({ kind: "loading" });
    try {
      const d = await fetchNode(node.id);
      setDetail({ kind: "node", data: d });
    } catch (e) {
      setDetail(null);
    }
  }, []);

  const onEdgeClick = useCallback(async (_, edge) => {
    setDetail({ kind: "loading" });
    try {
      const d = await fetchEdge(edge.id);
      setDetail({ kind: "edge", data: d });
    } catch (e) {
      setDetail(null);
    }
  }, []);

  // 应用推演结果:给节点染色 + 高亮路径边
  const applyScenario = useCallback((res) => {
    setScenario(res);
    const shockSet = new Set(Object.keys(res.shocks));
    setNodes((ns) =>
      ns.map((n) => {
        let sign;
        if (shockSet.has(n.id)) sign = "shock";
        else if (n.id in res.node_signs) sign = res.node_signs[n.id];
        return { ...n, data: { ...n.data, sign } };
      })
    );
    const onPath = new Set(res.edges_on_paths.map(([s, t]) => s + "→" + t));
    setEdges((es) =>
      es.map((e) => {
        const active = onPath.has(e.source + "→" + e.target);
        return {
          ...e,
          animated: active,
          style: {
            ...e.style,
            strokeWidth: active ? e.data.width + 2 : e.data.width,
            opacity: active ? 1 : 0.15,
          },
        };
      })
    );
  }, [setNodes, setEdges]);

  const clearScenario = useCallback(() => {
    setScenario(null);
    setNodes((ns) => ns.map((n) => ({ ...n, data: { ...n.data, sign: undefined } })));
    setEdges((es) =>
      es.map((e) => ({ ...e, animated: false, style: { stroke: e.data.color, strokeWidth: e.data.width, opacity: 1 } }))
    );
  }, [setNodes, setEdges]);

  const runActiveEvents = useCallback(async () => {
    const res = await reason({ use_active_events: true, date: today });
    applyScenario(res);
  }, [applyScenario]);

  const runManual = useCallback(async () => {
    if (Object.keys(manualShocks).length === 0) return alert("先在下方勾选至少一个根因的方向");
    const res = await reason({ shocks: manualShocks });
    applyScenario(res);
  }, [manualShocks, applyScenario]);

  return (
    <div className="app">
      <div className="canvas">
        <ReactFlow
          nodes={nodes}
          edges={edges}
          onNodesChange={onNodesChange}
          onEdgesChange={onEdgesChange}
          onNodeClick={onNodeClick}
          onEdgeClick={onEdgeClick}
          nodeTypes={nodeTypes}
          fitView
          minZoom={0.2}
          proOptions={{ hideAttribution: true }}
        >
          <Background color="#1e293b" gap={20} />
          <Controls />
          <MiniMap pannable zoomable nodeColor={(n) => n.data.color} />
        </ReactFlow>
        <div className="legend">
          <b>沪铜根因图谱</b> · 目标:{target}
          <div>圆角=根因 · 金框=目标价 · 蓝边=同向(+) 红边=反向(−)</div>
          <div>推演染色:<span style={{ color: "#ef4444" }}>↑红=利多量</span> · <span style={{ color: "#22c55e" }}>↓绿=利空量</span> · <span style={{ color: "#3b82f6" }}>⚡蓝框=冲击</span></div>
        </div>
      </div>

      <aside className="panel">
        <div className="tabs">
          <button className={mode === "browse" ? "on" : ""} onClick={() => setMode("browse")}>🔍 浏览/解释</button>
          <button className={mode === "reason" ? "on" : ""} onClick={() => setMode("reason")}>🧮 情景推演</button>
        </div>

        {mode === "browse" && (
          <div className="pad">
            {!detail && <p className="hint">点击左图任意<b>节点</b>看含义与利好利空判定,点击<b>连线</b>看两端相互作用与"为什么这个强度"。</p>}
            {detail?.kind === "loading" && <p className="hint">加载中…</p>}
            {detail?.kind === "node" && <NodeDetail d={detail.data} />}
            {detail?.kind === "edge" && <EdgeDetail d={detail.data} />}
          </div>
        )}

        {mode === "reason" && (
          <div className="pad">
            <button className="primary" onClick={runActiveEvents}>▶ 用当前活跃事件推演({today})</button>
            <details className="manual">
              <summary>或手动选根因冲击</summary>
              {rootCauses.map((rc) => (
                <div key={rc} className="shock-row">
                  <span>{rc}</span>
                  <span>
                    <button className={manualShocks[rc] === 1 ? "up on" : "up"} onClick={() => setManualShocks((s) => ({ ...s, [rc]: 1 }))}>+1</button>
                    <button className={manualShocks[rc] === -1 ? "dn on" : "dn"} onClick={() => setManualShocks((s) => ({ ...s, [rc]: -1 }))}>−1</button>
                    <button onClick={() => setManualShocks((s) => { const c = { ...s }; delete c[rc]; return c; })}>×</button>
                  </span>
                </div>
              ))}
              <button className="primary" onClick={runManual}>▶ 用勾选的冲击推演</button>
            </details>
            {scenario && <button className="ghost" onClick={clearScenario}>清除高亮</button>}
            {scenario && <ScenarioResult res={scenario} target={target} />}
          </div>
        )}
      </aside>
    </div>
  );
}

function Badge({ children, tone }) {
  return <span className={"badge " + (tone || "")}>{children}</span>;
}

function NodeDetail({ d }) {
  const th = d.temporal?.theme || {};
  return (
    <div>
      <h3>{d.id}</h3>
      <Badge>{d.type}</Badge>
      {d.isTarget && <Badge tone="warn">目标变量</Badge>}
      {d.temporal?.reversion && <Badge tone="accent">回归:{d.temporal.reversion}</Badge>}
      {th.status && <Badge tone={th.status === "活跃" ? "err" : th.status === "降温" ? "warn" : "muted"}>主题:{th.name} · {th.status}</Badge>}
      {d.note && <p><b>含义:</b>{d.note}</p>}
      {d.direction && <div className="box"><b>方向语义:</b>{d.direction}</div>}
      {d.effect && (
        <div className="box">
          <b>利好利空判定:</b>该量<b>上升↑</b> ⇒ 对目标价 <b className={d.effect.sign === "利多" ? "red" : "green"}>{d.effect.sign}</b>
          (最强路径强度 {d.effect.strength},时滞≈{d.effect.lag} 月);下降↓则反向。
          <div>共 {d.effect.n_paths} 条路径(利多 {d.effect.n_bull}/利空 {d.effect.n_bear})
            {d.effect.n_bull > 0 && d.effect.n_bear > 0 ? " ⚠️ 存在异号路径,净方向依情形" : ""}</div>
          <div className="path">最强路径:{d.effect.path}</div>
        </div>
      )}
      {(d.signals?.news?.length || d.signals?.data?.length) ? (
        <div className="box">
          <b>📡 监测信号</b>
          {d.signals.news?.length ? <div className="sm">新闻关键词:{d.signals.news.join(" / ")}</div> : null}
          {d.signals.data?.length ? <div className="sm">数据源:{d.signals.data.join(" | ")}</div> : null}
        </div>
      ) : null}
      {th.note && <p className="sm muted-t">主题备注:{th.note}</p>}
      {d.case && <p className="sm warn-t">历史案例:{d.case}</p>}
    </div>
  );
}

function EdgeDetail({ d }) {
  return (
    <div>
      <h3>{d.source} <span className={d.polarity === "+" ? "blue" : "red"}>─{d.polarity}→</span> {d.target}</h3>
      <Badge tone={d.polarity === "+" ? "info" : "err"}>机制{d.polarity === "+" ? "同向 +" : "反向 −"}</Badge>
      <Badge>时滞 {d.lag}</Badge>
      <Badge>强度 {d.strength}</Badge>
      <p><b>相互作用:</b>{d.sentence}</p>
      {d.rationale && <div className="box"><b>机制详解 / 为什么这个强度:</b>{d.rationale}</div>}
      {d.condition && <p className="sm"><b>生效条件:</b>{d.condition}</p>}
      {d.evidence && <p className="sm warn-t"><b>证据/案例:</b>{d.evidence}</p>}
      {!d.rationale && <p className="sm muted-t">(此边暂无人工 rationale,以上为按五要素自动生成的解释)</p>}
    </div>
  );
}

function ScenarioResult({ res, target }) {
  return (
    <div className="scenario">
      <h3>对 {target} 的分时段结论</h3>
      <div className="sm muted-t">冲击:{Object.entries(res.shocks).map(([k, v]) => `${k}${v > 0 ? "↑" : "↓"}`).join(" · ") || "无"}
        {res.n_feedback_loops ? ` · 反馈环 ${res.n_feedback_loops} 个` : ""}</div>
      {res.buckets.map((b) => (
        <div key={b.label} className="bucket">
          <b>【{b.label}】{b.tag}</b> <span className="sm muted-t">多 {b.bull} vs 空 {b.bear}</span>
          {b.top.map((p, i) => (
            <div key={i} className={"path " + (p.sign === "多" ? "red" : "green")}>[{p.sign} {p.strength}] {p.render}</div>
          ))}
        </div>
      ))}
      {res.active_events?.length ? (
        <details className="manual">
          <summary>当前活跃事件({res.active_events.length} 条)</summary>
          {res.active_events.map((e, i) => (
            <div key={i} className="sm">{e.time} {e.root_cause} {e.direction > 0 ? "↑" : "↓"} — {e.source}</div>
          ))}
        </details>
      ) : null}
    </div>
  );
}
