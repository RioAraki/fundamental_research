// 后端 API 封装。开发时经 vite 代理到 :8000;生产时同源。
const COMMODITY = "copper";

async function get(path) {
  const r = await fetch(path);
  if (!r.ok) throw new Error(`${path} -> ${r.status}`);
  return r.json();
}

export const fetchGraph = () => get(`/api/graph?commodity=${COMMODITY}`);
export const fetchNode = (id) =>
  get(`/api/node/${encodeURIComponent(id)}?commodity=${COMMODITY}`);
export const fetchEdge = (id) =>
  get(`/api/edge/${encodeURIComponent(id)}?commodity=${COMMODITY}`);

export async function reason(body) {
  const r = await fetch("/api/reason", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ commodity: COMMODITY, ...body }),
  });
  if (!r.ok) throw new Error(`/api/reason -> ${r.status}`);
  return r.json();
}
