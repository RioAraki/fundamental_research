# kg-mvp · 沪铜根因知识图谱 + 推理 + 运维系统

> 引擎 + 知识 + 运维。品种:**沪铜(SHFE CU)**。事实源是 `data/copper.yaml`(41 节点 / 55 边 /
> 23 个带监测信号的根因)+ `data/copper_events.yaml`(事件日志)。
> 方法论见仓库根 `METHODOLOGY.md`,工程规格见 `docs/SPEC.md`,命令见 `docs/RUNBOOK.md`。

## 快速上手

```powershell
pip install networkx pyyaml
python cli.py ci                          # 质量门(schema + golden tests),应全绿
python cli.py ingest-data --today 2026-07-06   # 数据→事件(z-score)
python cli.py ingest-news --today 2026-07-06   # 新闻→待审队列
python cli.py morning     --today 2026-07-06   # 晨报(分时段结论)
python cli.py advocate    --stance 多           # 反方路径(魔鬼代言人)
python cli.py conflicts   --today 2026-07-06   # 冲突仪表盘
python cli.py anomaly     --today 2026-07-06   # 行情异常检测
```

## 核心文件

```
kg-mvp/
├── data/copper.yaml          # ⭐ 事实源:根因 + 中间节点 + 因果边(五要素+rationale)+ 主题/回归特性
├── data/copper_events.yaml   # 事件日志(带时间戳的 ±赋值)
├── data/feeds/               # 数据/新闻输入(样例桩;进公司换真实源)
├── build_graph.py            # YAML → networkx + 校验(非法极性/悬空节点/重复边/反馈环)
├── propagate.py              # QPN 符号传播推理器(前向传播/多空对照/反馈环/反向归因)
├── events_lib.py             # 事件读写 + 活跃事件过滤(待反转语义)
├── pipeline_data_events.py   # 数据型事件流水线(z-score)
├── pipeline_news_events.py   # 新闻型流水线(含 llm_parse 桩)
├── cli.py                    # 统一运维入口
├── ci_checks.py              # CI 质量门(schema + golden tests + 事件校验)
└── docs/SPEC.md · RUNBOOK.md # 工程规格 + 操作手册
```

## 推理器能回答的问题类型

| 类型 | 例子 | 机制 |
|------|------|------|
| 正向传导 | 矿端事故 → 铜价? | 从冲击节点 DFS,符号相乘、强度相乘、时滞累计 |
| 全景涟漪 | 某事件影响哪些东西? | 输出全部受影响节点排序 |
| 系统演化 | 价格暴涨之后会怎样? | 检测经过冲击节点的反馈回路(正反馈/负反馈) |
| 多空对照 | 多个冲击叠加,价格怎么走? | 冲突不裁决,输出利多 vs 利空路径 + 分时段 |
| 反向归因 | 什么因素影响价格? | 对每个根因做单位冲击,汇总最强路径排序 |

## 设计要点

- **图是构建产物,YAML 是事实源**:知识变更走 PR review。
- **推理器与存储分离**:今天是 networkx,以后换存储不动边表。
- **冲突不裁决**:多空同时存在时输出两边路径,冲突本身是研究信号。
- **环路**用"单路径不重访 + 回到源点记为反馈环"消解。
- **强度是先验**(强0.9/中0.6/弱0.3),后续用历史行情回测校准。

> 新品种扩展:新增 `data/<品种>.yaml` + `<品种>_events.yaml`,并更新各模块的 commodity→路径映射(见 `AGENTS.md` §6 已知粗糙点)。
