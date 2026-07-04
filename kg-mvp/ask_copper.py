# -*- coding: utf-8 -*-
"""沪铜(SHFE CU)图谱推理演示:5+1 个真实问题(含双向)。输出 out/copper_demo.txt"""
import io
import sys
from pathlib import Path

from build_graph import load
from propagate import report, explain_drivers, signal_block

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")

G = load(Path(__file__).parent / "data" / "copper.yaml")
out = []


def q(title, body, watch=None):
    block = f"\n{'='*72}\n【问题】{title}\n{'='*72}\n{body}\n"
    if watch:
        block += "\n" + signal_block(G, watch) + "\n"
    print(block)
    out.append(block)


# Q1 矿端冲击:两段行情(对应 2025.9 Grasberg / 2023.11 巴拿马)
q("大型铜矿突发事故/关停(矿端供给扰动率 +1)→ ?(注意两段行情)",
  report(G, {"矿端供给扰动率": +1},
         targets=["SHFE铜价格", "TC/RC加工费", "中国精铜产量"], top=4, max_hops=9),
  watch=["矿端供给扰动率"])

# Q2 宏观双向:美联储(对应 2022 加息暴跌 / 降息周期)
q("美联储转向:紧缩(+1,2022 剧本)vs 宽松(−1)双向演示",
  "──情景 A:紧缩 +1(2022.3-7)──\n"
  + report(G, {"美联储政策立场": +1}, targets=["SHFE铜价格", "LME铜价格"])
  + "\n\n──情景 B:宽松 −1(降息周期)──\n"
  + report(G, {"美联储政策立场": -1}, targets=["SHFE铜价格"]),
  watch=["美联储政策立场"])

# Q3 贸易政策双向:232 关税(2025 全程:预期→搬库→豁免证伪)
q("美国 232 铜关税:扩大征税(+1)vs 精炼铜豁免(−1)——2025 年真实剧本",
  "──情景 A:关税预期升温 +1(2025.2-7)──\n"
  + report(G, {"美国铜进口关税": +1},
           targets=["SHFE铜价格", "全球显性库存", "COMEX-LME价差"])
  + "\n\n──情景 B:精炼铜豁免 −1(2025.7.30)──\n"
  + report(G, {"美国铜进口关税": -1}, targets=["SHFE铜价格", "COMEX-LME价差"]),
  watch=["美国铜进口关税"])

# Q4 需求侧:电网投资(中国铜需求第一大项)
q("国网年度投资计划大幅上调(中国电网投资 +1)→ ?",
  report(G, {"中国电网投资": +1},
         targets=["SHFE铜价格", "中国社会库存", "沪伦比值"]),
  watch=["中国电网投资"])

# Q5 反馈环:铜价已大涨,系统如何自我修复?(对应 2024.5 新高后 Q3 回落)
q("沪铜已创历史新高(SHFE铜价格 +1),接下来会发生什么?(反馈环识别)",
  report(G, {"SHFE铜价格": +1},
         targets=["中国下游开工率", "再生铜替代", "进口流入", "中国社会库存"]),
  watch=[])

# Q6 反向全景归因
q("有哪些根因会影响沪铜价格?(反向全景归因,+1 冲击口径)",
  explain_drivers(G, "SHFE铜价格", max_hops=9))

(Path(__file__).parent / "out").mkdir(exist_ok=True)
(Path(__file__).parent / "out" / "copper_demo.txt").write_text("".join(out), encoding="utf-8")
print("已写入 out/copper_demo.txt")
