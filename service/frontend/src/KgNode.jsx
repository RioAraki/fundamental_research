import { Handle, Position } from "@xyflow/react";

// 情景推演时的方向染色
const SIGN_STYLE = {
  1: { boxShadow: "0 0 0 3px #b91c1c", tip: "↑" },
  "-1": { boxShadow: "0 0 0 3px #15803d", tip: "↓" },
  shock: { boxShadow: "0 0 0 4px #1d4ed8", tip: "⚡" },
};

export default function KgNode({ data, selected }) {
  const isRoot = data.isRoot;
  const isTarget = data.isTarget;
  const sign = data.sign; // 由 App 在推演时注入:1 / -1 / "shock" / undefined
  const hi = sign !== undefined ? SIGN_STYLE[sign] : null;

  return (
    <div
      title={data.type}
      style={{
        background: data.color,
        color: "#fff",
        borderRadius: isRoot ? 20 : 6,
        border: isTarget ? "3px solid #fbbf24" : "1px solid rgba(255,255,255,.35)",
        padding: "8px 12px",
        width: 150,
        fontSize: 12,
        textAlign: "center",
        lineHeight: 1.25,
        cursor: "pointer",
        opacity: sign === 0 ? 0.4 : 1,
        outline: selected ? "2px solid #fde047" : "none",
        ...(hi ? { boxShadow: hi.boxShadow } : {}),
      }}
    >
      <Handle type="target" position={Position.Left} style={{ opacity: 0 }} />
      <div style={{ fontWeight: 700 }}>
        {hi?.tip ? <span style={{ marginRight: 4 }}>{hi.tip}</span> : null}
        {data.label}
      </div>
      <div style={{ fontSize: 9, opacity: 0.8, marginTop: 2 }}>
        {isTarget ? "◎ 目标价格" : isRoot ? "根因" : data.type.replace("根因·", "")}
      </div>
      <Handle type="source" position={Position.Right} style={{ opacity: 0 }} />
    </div>
  );
}
