# -*- coding: utf-8 -*-
"""棕榈油(DCE P)图谱推理演示。
根因是中性状态量,冲击方向(±1)由当下新闻决定——同一根因两个方向都演示。
输出写入 out/palm_demo.txt
"""
import io
import sys
from pathlib import Path

from build_graph import load
from propagate import report, explain_drivers, signal_block

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")

G = load(Path(__file__).parent / "data" / "palm_oil.yaml")
out = []


def q(title, body, watch=None):
    block = f"\n{'='*72}\n【问题】{title}\n{'='*72}\n{body}\n"
    if watch:
        block += "\n" + signal_block(G, watch) + "\n"
    print(block)
    out.append(block)


# Q1 市场侧根因 · 双向演示:同一节点,新闻决定方向
q("MPOB 月报公布,库存 vs 调查预期有偏差 → ?(中性根因双向演示)",
  "──情景 A:库存高于预期(冲击 +1)──\n"
  + report(G, {"MPOB库存预期差": +1}, targets=["DCE棕榈油价格", "进口利润"])
  + "\n\n──情景 B:库存低于预期(冲击 −1)──\n"
  + report(G, {"MPOB库存预期差": -1}, targets=["DCE棕榈油价格", "进口利润"]),
  watch=["MPOB库存预期差"])

# Q2 政策根因:B50 预期
q("印尼宣布推进 B50(生柴掺混率上调,冲击 +1)→ ?",
  report(G, {"印尼生柴掺混率": +1}, targets=["DCE棕榈油价格", "全球可出口供给", "豆棕价差"]),
  watch=["印尼生柴掺混率"])

# Q3 天气根因:双时滞
q("NOAA 宣布强厄尔尼诺,产区干旱预期加剧(冲击 +1)→ ?(注意两段行情)",
  report(G, {"产区干旱程度": +1}, targets=["DCE棕榈油价格"], top=5),
  watch=["产区干旱程度"])

# Q4 政策根因 · 双向演示:2022 上下半场完整剧本
q("印尼出口限制:收紧(禁令)与放开(flush out)各会发生什么?(2022 上下半场)",
  "──情景 A:收紧/禁令(冲击 +1,2022.4)──\n"
  + report(G, {"印尼出口限制力度": +1},
           targets=["DCE棕榈油价格", "印尼国内库存", "FCPO价格"])
  + "\n\n──情景 B:放开/flush out(冲击 −1,2022.6-7)──\n"
  + report(G, {"印尼出口限制力度": -1},
           targets=["DCE棕榈油价格", "FCPO价格"]),
  watch=["印尼出口限制力度"])

# Q5 跨品种传导
q("美国 EPA 大幅上调生柴掺混义务(冲击 +1)→ 对棕榈油是利多吗?",
  report(G, {"美国生柴掺混义务": +1},
         targets=["DCE棕榈油价格", "豆棕价差", "棕油替代需求"]),
  watch=["美国生柴掺混义务"])

# Q6 反向全景归因
q("有哪些根因会影响 DCE 棕榈油价格?(反向全景归因,+1 冲击口径)",
  explain_drivers(G, "DCE棕榈油价格", max_hops=7))

(Path(__file__).parent / "out").mkdir(exist_ok=True)
(Path(__file__).parent / "out" / "palm_demo.txt").write_text("".join(out), encoding="utf-8")
print("已写入 out/palm_demo.txt")
