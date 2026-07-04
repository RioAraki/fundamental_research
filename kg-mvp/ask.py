# -*- coding: utf-8 -*-
"""MVP 演示:5 个真实问题,验证图谱推理能做什么。输出同时写入 out/demo_output.txt"""
import io
import sys
from pathlib import Path

from build_graph import load
from propagate import report, explain_drivers

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")

G = load(Path(__file__).parent / "data" / "olive_oil.yaml")
out = []


def q(title, body):
    block = f"\n{'='*72}\n【问题】{title}\n{'='*72}\n{body}\n"
    print(block)
    out.append(block)


# Q1 正向单事件:2022/23 真实主线
q("西班牙发生严重生长期干旱,对橄榄油价格意味着什么?",
  report(G, {"生长期干旱": +1}, targets=["橄榄油价格", "期末库存", "橄榄油消费量"]))

# Q2 政策事件:2023.8 真实事件
q("土耳其宣布散装出口禁令,影响如何传导?",
  report(G, {"土耳其出口禁令": +1}))

# Q3 反馈环:价格已暴涨,系统接下来怎么演化?
q("价格已经暴涨(如 2024 初),接下来图谱预测会发生什么?",
  report(G, {"橄榄油价格": +1}, targets=["橄榄油消费量", "期末库存", "EU私人仓储援助", "囤货投机"]))

# Q4 多事件叠加 → 多空冲突演示:2024/25 真实情形
q("丰产年遇上土耳其禁令延续 + 乌克兰战争推高葵油价,价格怎么走?(多空对照)",
  report(G, {"全球产量": +1, "土耳其出口禁令": +1, "乌克兰战争": +1},
         targets=["橄榄油价格"], top=4))

# Q5 反向问法:全景归因
q("有哪些根因会影响橄榄油价格?(反向查询)",
  explain_drivers(G, "橄榄油价格"))

(Path(__file__).parent / "out").mkdir(exist_ok=True)
(Path(__file__).parent / "out" / "demo_output.txt").write_text("".join(out), encoding="utf-8")
print("已写入 out/demo_output.txt")
