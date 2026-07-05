# -*- coding: utf-8 -*-
"""列出 fundamental_research 下所有活跃 lavish 会话的文件路径(供批量关闭)。"""
import json
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")
state = json.loads((Path.home() / ".lavish-axi" / "state.json").read_text(encoding="utf-8"))
for s in state["sessions"].values():
    f = s["file"]
    if "fundamental_research" in f and ".lavish" in f and s.get("status") != "ended":
        print(f)
