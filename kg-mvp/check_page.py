# -*- coding: utf-8 -*-
import re
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")
h = (Path(__file__).parent.parent / ".lavish" / "copper-mvp.html").read_text(encoding="utf-8")
print("layers 页:", 'data-page="layers"' in h)
print("主题看板:", "主题看板" in h)
print("事件日志『待反转』:", len(re.findall("待反转", h)), "处")
print("temporal 徽章 JS:", "badge('回归:'" in h)
print("新名:", len(re.findall("数据中心算力基建需求", h)), "处 / 旧名残留:",
      len(re.findall("AI数据中心扩建", h)), "处")
print("占位残留:", any(x in h for x in ("<!--THEMES-->", "<!--EVENTS-->", "<!--STACKED-->")))
print("叠加推理:", "当前生效事件叠加" in h)
