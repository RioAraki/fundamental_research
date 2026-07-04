// 用 elkjs 做自动布局(layered,从左到右);把后端 graph 转成 React Flow 的 nodes/edges。
import ELK from "elkjs/lib/elk.bundled.js";

const elk = new ELK();

export async function layoutGraph(graph) {
  const elkGraph = {
    id: "root",
    layoutOptions: {
      "elk.algorithm": "layered",
      "elk.direction": "RIGHT",
      "elk.layered.spacing.nodeNodeBetweenLayers": "110",
      "elk.spacing.nodeNode": "45",
      "elk.layered.nodePlacement.strategy": "NETWORK_SIMPLEX",
    },
    children: graph.nodes.map((n) => ({ id: n.id, width: 150, height: 46 })),
    edges: graph.edges.map((e) => ({ id: e.id, sources: [e.source], targets: [e.target] })),
  };
  const laid = await elk.layout(elkGraph);
  const pos = {};
  laid.children.forEach((c) => (pos[c.id] = { x: c.x, y: c.y }));

  const nodes = graph.nodes.map((n) => ({
    id: n.id,
    type: "kg",
    position: pos[n.id] || { x: 0, y: 0 },
    data: { ...n },
  }));
  const edges = graph.edges.map((e) => ({
    id: e.id,
    source: e.source,
    target: e.target,
    data: { ...e },
    style: { stroke: e.color, strokeWidth: e.width },
    animated: false,
  }));
  return { nodes, edges };
}
