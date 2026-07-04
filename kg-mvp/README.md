# kg-mvp · 商品基本面根因知识图谱 + 推理 + 运维系统

> **快速上手**:`pip install networkx pyyaml`,然后 `python cli.py ci` 验证环境;
> 日常用法见 **docs/RUNBOOK.md**,工程规格见 **docs/SPEC.md**。
> 一分钟体验(沪铜):
> ```powershell
> python cli.py ingest-data --today 2026-07-06   # 数据→事件(z-score)
> python cli.py ingest-news --today 2026-07-06   # 新闻→待审队列
> python cli.py morning     --today 2026-07-06   # 晨报(分时段结论)
> python cli.py advocate    --stance 多           # 反方路径(魔鬼代言人)
> ```

> **当前主线:棕榈油(DCE P)根因图谱(MVP 2.0)**——`data/palm_oil.yaml`(43 节点/53 边/23 个带监测信号的根因),
> 方法论:**根因定性、新闻和数据定量**。根因节点自带 signals(新闻关键词+数据源+历史案例)。
> 运行:`python ask_palm.py`(6 个推理演示)、`python gen_panel.py data/palm_oil.yaml DCE棕榈油价格 out/panel.html`(根因监测面板)。
> 橄榄油版(MVP 1.0)保留作为第一次验证,见下文。

# MVP 1.0 · 橄榄油基本面知识图谱 + 推理

> **一句话总结**:用「YAML 边表(事实源,git 管理)→ networkx 内存图 → 自写 QPN 符号传播推理器」
> 三件套,验证了"把供需因素结构化成因果图谱、再做规则演绎推理"这条路线端到端可行。
> 图谱内容来自公开橄榄油报告(IOC/USDA/EU/行业媒体),推理结果与 2022-2025 真实行情吻合。

## 文件结构

```
kg-mvp/
├── data/olive_oil.yaml   # ⭐ 核心资产:35 节点 / 41 条因果边(五要素:polarity/lag/strength/condition/evidence)
├── build_graph.py        # YAML → networkx,schema 校验(非法极性/悬空节点/重复边),报告反馈环
├── propagate.py          # QPN 符号传播推理器(~150 行):前向传播 / 多空路径对照 / 反馈环识别 / 反向归因
├── ask.py                # 5 个演示问题
├── gen_mermaid.py        # 从 YAML 生成 mermaid 图源码(节点按类型着色)
└── out/                  # 构建产物:demo_output.txt / graph.mmd / graph.svg
```

## 快速开始

```powershell
pip install networkx pyyaml
python build_graph.py   # 校验 + 图统计(35 节点/41 边/8 个反馈环)
python ask.py           # 跑 5 个推理演示,输出到 out/demo_output.txt
```

## 推理器能回答的问题类型

| 类型 | 例子 | 机制 |
|------|------|------|
| 正向传导 | 西班牙干旱→价格? | 从冲击节点 DFS,符号相乘、强度相乘、时滞累计 |
| 全景涟漪 | 土耳其禁令影响哪些东西? | 同上,输出全部受影响节点排序 |
| 系统演化 | 价格暴涨之后会怎样? | 检测经过冲击节点的反馈回路(正反馈=自我强化/负反馈=自我修复) |
| 多空对照 | 丰产+禁令+葵油涨,价格怎么走? | 多冲击叠加,冲突不裁决,输出利多 vs 利空路径对照 |
| 反向归因 | 什么因素影响价格? | 对每个根因做单位冲击,汇总最强路径排序 |

## 设计要点(为什么这么做)

- **图是构建产物,YAML 是事实源**:知识变更走 PR review,和 markdown 知识库同一套协作流程
- **推理器与存储分离**:今天是 networkx,以后换 Neo4j/PyReason 不动边表
- **冲突不裁决**:多空同时存在时输出两边路径,冲突本身是研究信号
- **环路用"单路径不重访 + 回到源点单独记为反馈环"消解**,等价于时间展开一步近似
- **强度是拍脑袋的先验**(强0.9/中0.6/弱0.3),之后用历史案例回验校准
