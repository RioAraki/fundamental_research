# 商品基本面根因知识图谱 · 工程规格书(SPEC)

> 版本 1.0 · 2026-07-04 · 以沪铜(SHFE CU)为参考实现
> 本文是全部设计讨论的工程化沉淀,目标读者:coding agent 与工程师。
> 设计讨论原文:`.lavish/kg-inference-report.html`(调研)、`time-dimension-design.html`(三层本体)、
> `kg-ops-design.html`(运维协作)、`methanol-methodology.html`(定量验证方法)。

## 1. 我们要干什么

把研究员脑中的商品供需传导逻辑,建成**可推理、可维护、可审计的知识图谱**,并围绕它建立
交易员/研究员/AI agent/工程师四角色的日常协作系统。

核心原则(全部有设计讨论背书,不可随意推翻):

1. **KG-as-code**:图谱的唯一事实源是 git 仓库里的 YAML 文本;图数据库/dashboard 都是可再生的构建产物。
2. **根因中性化**:根因节点是永续存在的中性状态量(如「印度进口关税」),名字里不许有方向词;
   `direction` 字段说明 +/− 各代表什么现实事件。
3. **图存机制、新闻定方向**:边的极性是传导机制(起点↑ → 终点如何);事件以 ±1 冲击输入。
4. **三层本体**:变量(根因,进图)/ 主题(市场注意力标签,挂在节点上)/ 事件(带时间戳的赋值,进事件日志不进图)。
   判据:把新闻的时间和方向剥掉,剩下的名词才是根因。
5. **冲突不裁决**:多空路径并列输出;行动语义 = 冲突期观望,并给出裁决信号(甲醇报告实证)。
6. **传导绝不让 LLM 裸推**:LLM 只管两端(新闻→事件解析、结论→自然语言),中间由符号引擎执行。
7. **一切修改 = PR**:人改与 AI 改走同一通道,PR review 就是审批系统(用户确认的设计共识)。

## 2. 三层本体(正式定义摘要)

| 层 | 定义 | 判定标准 | 时间属性 |
|---|---|---|---|
| 🧱 变量(根因) | 可测量、持续存在的中性状态量;图谱节点 | ①可测量(任何时刻有读数,可为0)②中性命名③机制独立④实质性 | 回归特性五类:快速重置/事件回收/状态保持/趋势累积/季节周期 |
| ⚡ 事件 | 对某变量的一次带时间戳 ± 赋值;进事件日志 | ①有时间戳②有方向(±,可带幅度)③可归属(受控词表);归属失败→未归属队列=新根因候选 | 事件窗口;影响窗口=min(事件窗口, 变量回归期) |
| 🔥 主题 | 一个或多个变量在某段时期的市场注意力状态;节点上的标签 | ①依附性②时段性③注意力可观测(事件密度/价格敏感度) | 生灭由监测判定,不预言;休眠=打折不删除 |

## 3. 文件架构(现状即规范)

```
fundamental_research/                ← git 仓库
├── kg-mvp/
│   ├── data/                        ★ 唯一需要人审的层
│   │   ├── copper.yaml              ← 图谱本体:41 节点(23 根因带 temporal)/55 边(五要素+rationale)
│   │   ├── copper_events.yaml       ← 事件日志:一个文件多条事件,append-only
│   │   ├── palm_oil.yaml / palm_events.yaml(棕榈油,三层待套用)
│   │   ├── olive_oil.yaml           ← MVP 1.0,保留作教学
│   │   └── feeds/                   ← 数据/新闻输入样例(真实数据源接入前的桩)
│   ├── docs/SPEC.md(本文)· RUNBOOK.md(操作手册)
│   ├── build_graph.py               ← YAML→networkx+校验(引擎,品种无关)
│   ├── propagate.py                 ← QPN 符号传播推理器
│   ├── events_lib.py                ← 事件日志读写 + 活跃事件过滤函数
│   ├── cli.py                       ← 统一入口(见 §5)
│   ├── pipeline_data_events.py      ← 数据型事件流水线(z-score)
│   ├── pipeline_news_events.py      ← 冲击型事件流水线(关键词+LLM桩→待审队列)
│   ├── approve_events.py            ← 待审队列的人工确认 CLI
│   ├── morning_report.py            ← 晨报(活跃事件叠加→分时段结论)
│   ├── conflict_dashboard.py        ← 冲突仪表盘
│   ├── devils_advocate.py           ← 反方路径(魔鬼代言人)
│   ├── detect_anomaly.py            ← 行情驱动异常检测
│   ├── refresh_themes.py            ← 主题热度刷新(事件密度)
│   ├── scan_reviews.py              ← 边保质期扫描
│   ├── ci_checks.py                 ← CI 质量门(schema+golden tests+跨品种一致性)
│   ├── gen_*.py / ask_*.py / inject_*.py ← dashboard 生成链(既有)
│   └── out/                         ← 构建产物,git 忽略
├── .lavish/*.html                   ← dashboard(可批注交付物)
└── .github/workflows/ci.yml         ← CI
```

## 4. 数据模式(schema)

### 4.1 图谱节点(copper.yaml `nodes[]`)

```yaml
- id: 矿端供给扰动率          # 中性状态量命名
  type: 根因·供给              # 根因·{供给|结构|政策|宏观|需求|季节|市场} 或 供给指标/需求指标/价差/价格/情绪/替代品
  direction: "+ = 扰动加剧(...) / − = 平息"   # 根因必填
  temporal:                    # 根因必填
    reversion: 事件回收型       # 快速重置型|事件回收型|状态保持型|趋势累积型|季节周期型
    theme: {name: 2026供给缺口, status: 活跃, since: "2025.9", note: "..."}  # status: 活跃|降温|休眠
  note: "..."                  # 含义(交互页解释用)
  case: "..."                  # 历史案例(校准锚)
  signals:                     # 根因必填:定量入口
    news: [罢工, "force majeure", ...]       # 新闻关键词(中英)
    data: ["公司公告", "ICSG 月度矿产量", ...] # 数据源
```

### 4.2 边(copper.yaml `edges[]`)

```yaml
- {from: A, to: B,
   polarity: "+",              # +|-:A 上升时 B 的方向(机制,非当下判断)
   lag: 1-3月,                 # 词表见 build_graph.LAG_MONTHS
   strength: 强,               # 强0.9|中0.6|弱0.3(先验,待回测校准)
   condition: "...",           # 生效条件(未来参与剪枝)
   evidence: "...",            # 证据/案例(强制溯源)
   rationale: "...",           # 机制详解/为什么是这个强度(关键边必填)
   review: {last: "2026-07", note: "..."},        # 保质期(可选,scan_reviews 消费)
   factor_rule: "...",         # 可回测因子规则原型(可选,甲醇方法)
   validation: {status: 未回测, corr: null, win_rate: null}}  # 回测结果(可选)
```

### 4.3 事件(copper_events.yaml `events[]`)

```yaml
- {time: "2026-07-06",         # 信息可得时刻(point-in-time),非事实发生时刻
   root_cause: 矿端供给扰动率,  # 必须命中图中已有节点(含中间变量;受控词表)
   direction: +1,              # ±1
   magnitude: 中,              # 强|中|弱 或 "z=-2.1"(数据型)
   window: 待反转,             # 词表同 lag;"待反转"=保持到同根因出现反向事件
   active: true,               # 记录字段;运行时以 events_lib.active_events 计算为准
   auto: true,                 # 是否流水线自动生成
   source: "..."}              # 来源(新闻标题/数据说明),强制
```

### 4.4 活跃事件过滤函数(时间系统的核心工程落点)

```
active(e, today) =
  若日志中存在同 root_cause 且 time 更晚且 direction 相反的事件 e' → False(被反转)
  否则若 e.window == 待反转 → True
  否则 → e.time + window_months(e.window) >= today
shocks(today) = {root_cause: 最新活跃事件的 direction}
```

## 5. 模块规格(I/O 契约)

统一入口:`python cli.py <子命令> [参数]`,所有子命令支持 `--commodity copper|palm`(默认 copper)
与 `--today YYYY-MM-DD`(point-in-time 纪律:回放历史时必传)。

| 子命令 | 模块 | 输入 | 输出 | 说明 |
|---|---|---|---|---|
| `ingest-data` | pipeline_data_events | `data/feeds/cu_indicators.csv`(date,node,value,expected,sigma,source) | 追加事件到 `copper_events.yaml`(z≥阈值 1.5,auto:true);stdout 摘要 | 幂等:同 (date,node) 不重复入库 |
| `ingest-news` | pipeline_news_events | `data/feeds/news_sample.jsonl`(date,title,text) | `out/review_queue.yaml`(命中,方向待人定)+ `out/unattributed.yaml`(未归属) | LLM 解析留桩(`--llm` 提示接入点);关键词命中即入队 |
| `approve` | approve_events | `--list` / `--approve <序号> --direction ±1 [--magnitude 中] [--window 待反转]` | 入库 events.yaml 并从队列移除 | 人工确认卡口 |
| `morning` | morning_report | 图 + 事件日志(活跃过滤) | `out/morning_report.md`:活跃事件清单→叠加推理分时段(0-1/1-6/6+月)→冲突提示→今日待验证信号 | 交易员每日入口 |
| `conflicts` | conflict_dashboard | 同上 | `out/conflict_dashboard.md`:多空同时激活的节点+双方路径+裁决信号 | 冲突=观望+等裁决 |
| `advocate` | devils_advocate | `--stance 多\|空 [--target SHFE铜价格]` | stdout:与立场相反的传导路径(活跃事件优先,其次结构性),各附条件与验证信号 | 研究员写观点前必跑 |
| `anomaly` | detect_anomaly | `data/feeds/cu_price.csv`(date,close)+ 事件日志 | `out/anomaly_report.md` + `out/event_price_pairs.csv` | 触发\|r\|>2.5σ(60日);三分类:一致(记配对)/无解释(issue)/方向失灵(边待校准);反向:大事件无反应→计价死亡建议 |
| `themes` | refresh_themes | 事件日志(90 天窗口) | `out/theme_suggestions.md`:事件密度 vs 当前 status 的升降档建议(L1 级,人秒批) | 每周 |
| `reviews` | scan_reviews | 图 | `out/review_overdue.md`:无 review 字段或超 12 个月未审的边清单 | 每月 |
| `ci` | ci_checks | 两份图+两份事件日志 | 退出码 0/1;stdout 报告 | 见 §6 |
| `dashboard` | 既有 gen 链 | 图+事件 | 重建 copper dashboard 全部产物并注入 | 边表变更后运行 |

## 6. CI 质量门(ci_checks.py,每个 PR 必过)

1. **Schema**:两份图谱 build 通过(悬空节点/非法枚举/重复边);事件日志全部 root_cause 命中图节点、window/时间可解析。
2. **Golden tests(推理回归)**——保护结构性知识不被误删:
   - 铜:`矿端供给扰动率+1 ⇒ SHFE 净利多`;`美联储政策立场+1 ⇒ SHFE 净利空`;
     `全部入度0根因在9跳内可达 SHFE铜价格`;存在含「沪伦比值→进口流入→中国社会库存」的负反馈环(R3);存在含「精废价差」的环(R1)。
   - 棕榈油:`产区干旱程度+1 ⇒ DCE 净利多`;存在「印尼出口限制力度⇄印尼国内库存」政策自反环。
3. **跨品种一致性**:同名共享根因(如 原油价格)在各品种图中 type 必须一致。
4. **保质期警告**(不阻塞):超期边数量输出。

## 7. 验收标准

- `python cli.py ci` 退出码 0,golden 全绿。
- `ingest-data` 对样例 feed 生成 ≥2 条 z 事件且幂等(重跑不重复)。
- `ingest-news` 对样例新闻:≥3 条入待审队列、≥1 条入未归属队列;`approve` 能将队列项入库。
- `morning` 产出含三时段结论与活跃事件清单的 markdown。
- `advocate --stance 多` 至少列出一条含「硫酸价格」的反方路径(2026 年真实分歧)。
- `anomaly` 对样例价格:识别出 ≥2 天超阈值异动并给出正确分类与解释事件(三分类代码路径均存在;样例数据当前两天均为"有解释",因事件日志补全了美联储 2024.9 降息反转与 232 豁免两条真实事件)。
- push 到 GitHub 后,Actions 的 CI 运行通过(或本地等效运行通过)。

## 8. 明确不在本期(防 scope creep)

- 真实数据源 API 接入(feeds/ 是桩,接口契约已定即 §5 输入格式)
- LLM 新闻解析的真实调用(pipeline_news_events 留 `llm_parse()` 桩)
- condition 参与推理剪枝、事件幅度进入传播权重
- MCP server 封装(CLI 即当前 agent 接口)
- 回测校准框架(factor_rule/validation 字段已预留,方法论见甲醇报告页)
