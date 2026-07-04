# 操作手册(RUNBOOK)

> 面向日常使用者。设计与契约见 `SPEC.md`。

## 环境

```powershell
# 仅需一次
pip install networkx pyyaml
# dashboard 重建才需要:node(npx 调 mermaid-cli)
```

所有命令在 `kg-mvp/` 目录下执行;Windows 控制台先设 `$env:PYTHONIOENCODING='utf-8'`。

## 日常节律

### 每天(交易日早晨,约 5 分钟)

```powershell
python cli.py ingest-data  --today 2026-07-06   # 数据型事件自动入库(z-score)
python cli.py ingest-news  --today 2026-07-06   # 新闻→待审队列 + 未归属队列
python cli.py approve --list                     # 看队列
python cli.py approve --approve 1 --direction +1 # 确认第 1 条(方向由人定)
python cli.py morning --today 2026-07-06         # 生成晨报 → out/morning_report.md
python cli.py conflicts --today 2026-07-06       # 冲突仪表盘 → out/conflict_dashboard.md
python cli.py anomaly --today 2026-07-06         # 收盘后跑:行情异常检测
```

### 每周

```powershell
python cli.py themes --today 2026-07-06   # 主题热度建议(按事件密度)→ 人工秒批后改 YAML
```

### 每月

```powershell
python cli.py reviews                      # 边保质期扫描 → 超期清单
```

### 随时(研究员)

```powershell
# 写观点前:让图谱当魔鬼代言人
python cli.py advocate --stance 多         # 列出所有与"看多"相反的传导路径
python cli.py advocate --stance 空 --structural   # 含未激活的结构性反方路径
```

### 边表变更后

```powershell
python cli.py ci          # 质量门(schema + golden tests),必须绿
python cli.py dashboard   # 重建 copper dashboard(需 node/npx)
```

## 知识修改流程(人和 AI 相同)

1. 改 `kg-mvp/data/*.yaml`(一行一个事实)
2. `python cli.py ci` 本地过门
3. 提交 PR(或直接 commit,小团队阶段);变更分级见 SPEC §与 kg-ops-design 页:
   L1 补证据/关键词/theme 状态 → 快批;L2 强度/条件/新边 → 单人审;L3 新根因/极性翻转 → 双人审
4. merge 后跑 `python cli.py dashboard`

## 常见问题

- **事件的 direction 为什么要人来定?** 冲击型新闻的方向判断是卡口(LLM 桩未接);数据型事件方向由 z 符号自动得出。
- **--today 是干嘛的?** point-in-time 纪律:回放历史/测试时必须显式传日期,禁止未来信息。
- **待反转窗口何时结束?** 同一根因出现反向事件时自动失效(events_lib.active_events 计算)。
