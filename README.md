# 商品基本面根因知识图谱(沪铜)

> 把研究员的供需传导逻辑,建成**可推理、可维护、可解释**的知识图谱,并配套推理引擎、事件系统、
> 运维 CLI 与 web 服务。当前落地品种:**沪铜(SHFE CU)**。

## 交接文档(English handoff docs)

- [`AGENTS.md`](./AGENTS.md) — **接手的 coding agent 先读这个**:接着怎么干、规则、读研报的第一步任务
- [`METHODOLOGY.md`](./METHODOLOGY.md) — 方法论总纲(why)· interactive: `.lavish/01-methodology-en.html`
- [`ENGINEERING.md`](./ENGINEERING.md) — 工程落地 + 公司环境准备(how)· interactive: `.lavish/02-engineering-en.html`

## 目录结构

| 目录 | 内容 |
|---|---|
| **`kg-mvp/`** | 引擎 + 知识 + 运维:图谱本体 YAML(`data/copper.yaml`)、推理引擎、事件流水线、运维 CLI、CI 质量门;见 `docs/SPEC.md` 与 `docs/RUNBOOK.md` |
| **`service/`** | web 服务:FastAPI 后端 + React Flow 前端(沪铜交互图谱与情景推演);见其 `README.md` |
| `.lavish/` | 交互式 dashboard 与设计文档(可批注 HTML) |

## 快速开始

```powershell
pip install networkx pyyaml fastapi "uvicorn[standard]"
cd kg-mvp && python cli.py ci            # 质量门,应全绿
python cli.py morning --today 2026-07-06 # 晨报(分时段结论)

# web 服务
cd service/frontend && npm install && npm run build
cd ../backend && python -m uvicorn app:app --port 8000   # 打开 http://localhost:8000
```

详见 `AGENTS.md`(接手指南)、`kg-mvp/docs/RUNBOOK.md`(命令)、`service/README.md`(服务)。
