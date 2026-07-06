# -*- coding: utf-8 -*-
"""冲击型事件流水线(SPEC §5 ingest-news):
新闻 JSONL → 按 signals.news 关键词粗过滤 → 命中入待审队列(方向由人定)/ 未命中入未归属队列。
LLM 解析留桩:接入真实 LLM 时实现 llm_parse(),产出 direction/magnitude/window 建议供人确认。
JSONL 行:{"date": "...", "title": "...", "text": "..."}
"""
import json
from pathlib import Path

import yaml

from build_graph import load

ROOT = Path(__file__).parent
FEED = {"copper": ROOT / "data" / "feeds" / "news_sample.jsonl"}
GRAPH = {"copper": ROOT / "data" / "copper.yaml"}
QUEUE = ROOT / "out" / "review_queue.yaml"
UNATTR = ROOT / "out" / "unattributed.yaml"


def llm_parse(news: dict, candidates: list[str]):
    """LLM 解析桩(SPEC §8 明确本期不接):
    接入点——传入新闻全文与受控词表 candidates,要求 LLM 输出
    {root_cause(只能选 candidates), direction, magnitude, window, quote}。
    未接入时返回 None,方向交由人工在 approve 时决定。"""
    return None


def run(commodity: str, today: str) -> list[str]:
    G = load(GRAPH[commodity])
    kw_index = []  # (keyword_lower, node)
    for n, d in G.nodes(data=True):
        for kw in (d.get("signals") or {}).get("news", []):
            kw_index.append((str(kw).lower(), n))

    queue, unattributed, lines = [], [], []
    for raw in FEED[commodity].read_text(encoding="utf-8").splitlines():
        if not raw.strip():
            continue
        news = json.loads(raw)
        if news["date"] > today:
            continue  # point-in-time
        blob = (news["title"] + " " + news.get("text", "")).lower()
        hits = sorted({node for kw, node in kw_index if kw in blob})
        if hits:
            item = {"time": news["date"], "title": news["title"],
                    "matched_nodes": hits, "root_cause": hits[0],
                    "direction": None, "source": news["title"],
                    "llm": llm_parse(news, hits)}
            queue.append(item)
            lines.append(f"📥 待审: [{news['date']}] {news['title']} → 命中 {hits}")
        else:
            unattributed.append({"time": news["date"], "title": news["title"],
                                 "text": news.get("text", "")[:120]})
            lines.append(f"❓ 未归属: [{news['date']}] {news['title']}(新根因候选信号)")

    QUEUE.parent.mkdir(exist_ok=True)
    QUEUE.write_text(yaml.safe_dump({"queue": queue}, allow_unicode=True, sort_keys=False),
                     encoding="utf-8")
    UNATTR.write_text(yaml.safe_dump({"unattributed": unattributed}, allow_unicode=True,
                                     sort_keys=False), encoding="utf-8")
    lines.append(f"待审 {len(queue)} 条 → {QUEUE.name};未归属 {len(unattributed)} 条 → {UNATTR.name}")
    return lines
