# -*- coding: utf-8 -*-
"""统一入口(SPEC §5)。用法:python cli.py <子命令> [参数];详见 docs/RUNBOOK.md"""
import argparse
import subprocess
import sys
from datetime import date, datetime
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")
ROOT = Path(__file__).parent


def parse_today(s: str | None) -> date:
    return datetime.strptime(s, "%Y-%m-%d").date() if s else date.today()


def main():
    ap = argparse.ArgumentParser(description="商品根因知识图谱 · 运维与使用 CLI")
    ap.add_argument("command", choices=[
        "ingest-data", "ingest-news", "approve", "morning", "conflicts",
        "advocate", "anomaly", "themes", "reviews", "ci", "dashboard"])
    ap.add_argument("--commodity", default="copper", choices=["copper"])
    ap.add_argument("--today", default=None, help="YYYY-MM-DD(point-in-time,回放历史必传)")
    # approve 专用
    ap.add_argument("--list", action="store_true")
    ap.add_argument("--approve", type=int, metavar="N")
    ap.add_argument("--direction", type=int, choices=[1, -1])
    ap.add_argument("--magnitude", default="中")
    ap.add_argument("--window", default="待反转")
    ap.add_argument("--root-cause", default=None, help="覆盖队列默认归属节点")
    # advocate 专用
    ap.add_argument("--stance", choices=["多", "空"])
    ap.add_argument("--structural", action="store_true", help="加列未激活的结构性反方路径")
    ap.add_argument("--target", default=None)
    a = ap.parse_args()
    today = parse_today(a.today)

    if a.command == "ingest-data":
        import pipeline_data_events as m
        out = m.run(a.commodity, str(today))
    elif a.command == "ingest-news":
        import pipeline_news_events as m
        out = m.run(a.commodity, str(today))
    elif a.command == "approve":
        import approve_events as m
        if a.approve:
            if a.direction is None:
                sys.exit("--approve 需要 --direction +1|-1(方向由人定,这是卡口)")
            out = m.approve(a.commodity, a.approve, a.direction, a.magnitude,
                            a.window, a.root_cause)
        else:
            out = m.list_queue()
    elif a.command == "morning":
        import morning_report as m
        out = m.run(a.commodity, today)
    elif a.command == "conflicts":
        import conflict_dashboard as m
        out = m.run(a.commodity, today)
    elif a.command == "advocate":
        if not a.stance:
            sys.exit("advocate 需要 --stance 多|空")
        import devils_advocate as m
        out = m.run(a.commodity, today, a.stance, a.structural, a.target)
    elif a.command == "anomaly":
        import detect_anomaly as m
        out = m.run(a.commodity, today)
    elif a.command == "themes":
        import refresh_themes as m
        out = m.run(a.commodity, today)
    elif a.command == "reviews":
        import scan_reviews as m
        out = m.run(a.commodity, today)
    elif a.command == "ci":
        import ci_checks
        sys.exit(ci_checks.main())
    elif a.command == "dashboard":
        steps = [
            [sys.executable, "ask_copper.py"],
            [sys.executable, "gen_panel.py", "data/copper.yaml", "SHFE铜价格", "out/cu_panel.html"],
            [sys.executable, "gen_explore.py", "data/copper.yaml", "SHFE铜价格", "out/cu_explore.json"],
            [sys.executable, "gen_layers.py", "data/copper.yaml", "data/copper_events.yaml",
             "SHFE铜价格", "out/cu_layers"],
            [sys.executable, "gen_mermaid.py", "data/copper.yaml", "out/cu_graph.mmd"],
        ]
        for cmd in steps:
            subprocess.run(cmd, cwd=ROOT, check=True)
        out = ["dashboard 数据产物已重建(SVG 渲染与注入见 RUNBOOK:需 npx mermaid-cli)"]

    print("\n".join(out))


if __name__ == "__main__":
    main()
