# service — 沪铜根因图谱 web 服务(v1)

把 `kg-mvp/` 的引擎包成前后端服务:**FastAPI 后端(读现有 YAML)+ React Flow 前端(交互图谱 + 情景推演)**。
设计见 `.lavish/service-arch-design.html`。v1 只读、无数据库、无部署层。

```
service/
├── backend/    FastAPI(app.py)· 复用 kg-mvp 的 build_graph/propagate/events_lib
└── frontend/   React + Vite + @xyflow/react(React Flow) + elkjs 自动布局
```

## 后端 API(4 端点)

| 端点 | 说明 |
|---|---|
| `GET /api/graph?commodity=copper` | 节点+边(前端画图) |
| `GET /api/node/{id}` | 点节点:含义/方向语义/利好利空判定/监测信号/主题/回归特性 |
| `GET /api/edge/{id}` | 点边:相互作用句 + rationale(为什么这个强度) |
| `POST /api/reason` | 情景推演:`{use_active_events:true,date}` 用某日活跃事件,或 `{shocks:{根因:±1}}` 手动;返回分时段结论 + 节点方向 + 高亮路径 |

## 怎么跑起来

前置:Python(`pip install -r backend/requirements.txt`,含 fastapi/uvicorn/networkx/pyyaml)、Node ≥18。

### 方式 A:开发模式(前后端分开,热更新)

```powershell
# 终端 1 — 后端(8000)
cd service/backend
python -m uvicorn app:app --reload --port 8000

# 终端 2 — 前端(5173,/api 自动代理到 8000)
cd service/frontend
npm install        # 仅首次
npm run dev
# 浏览器打开 http://localhost:5173
```

### 方式 B:单进程模式(部署/服务器用,一个端口)

```powershell
cd service/frontend
npm install && npm run build      # 产出 frontend/dist
cd ../backend
python -m uvicorn app:app --port 8000
# 浏览器打开 http://localhost:8000  (后端自动托管前端 dist + API)
```

跑在服务器上就是方式 B 换成 `--host 0.0.0.0`,同样两条命令,无需额外设施。

## 怎么用

- **浏览/解释**:点节点看利好利空判定与监测信号,点边看机制与"为什么这个强度"。
- **情景推演**:切到「🧮 情景推演」→「用当前活跃事件推演」(读 copper_events.yaml 里 2026-07-06 的活跃事件),或展开手动勾选根因 ±1。图上节点按方向染色(↑红/↓绿/⚡蓝框冲击)、传导路径高亮,右侧给 0-1月/1-6月/6月+ 三段结论。

## 数据来源

只读 `kg-mvp/data/copper.yaml`(图谱本体)与 `copper_events.yaml`(事件)。改知识仍走 kg-mvp 的 YAML + CLI(`python cli.py ci` 过门),本服务重启即加载最新(或后续加热重载)。

## v1 明确不含(推到 v2+)

数据库、数据管道/调度、反向代理/认证、网页改图生成 PR、监测面板/晨报/冲突等页面(后端逻辑已在 kg-mvp,加端点即可)。
