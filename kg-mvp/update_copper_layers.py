# -*- coding: utf-8 -*-
"""把三层方法论(根因徽章/主题看板/事件日志/叠加分时段推理)注入 copper-mvp.html"""
import html as H
import re
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")
root = Path(__file__).parent
page_path = root.parent / ".lavish" / "copper-mvp.html"
page = page_path.read_text(encoding="utf-8")

out = root / "out"
themes = (out / "cu_layers_themes.html").read_text(encoding="utf-8")
events = (out / "cu_layers_events.html").read_text(encoding="utf-8")
stacked = (out / "cu_layers_stacked.html").read_text(encoding="utf-8")

# 1) 导航 + 导读
nav_anchor = '<li><a href="#explore" data-nav="explore">🖱️ 交互探索</a></li>'
assert nav_anchor in page
page = page.replace(nav_anchor, nav_anchor +
    '\n        <li><a href="#layers" data-nav="layers">⏳ 三层·事件日志</a></li>')
guide_anchor = '<tr><td><a class="link" href="#demo">🔬 推理演示</a></td>'
page = page.replace(guide_anchor,
    '<tr><td><a class="link" href="#layers">⏳ 三层·事件日志</a></td><td><b>时间维度方法论落地</b>:主题看板(活跃/降温/休眠)· 真实事件日志(2021-2026)· 当前生效事件叠加的分时段推理</td></tr>\n              ' + guide_anchor, 1)

# 2) 新 section
SECTION = """      <!-- ============ LAYERS ============ -->
      <section data-page="layers" class="hidden space-y-6">
        <h1 class="text-2xl font-bold">⏳ 三层方法论落地:变量 · 主题 · 事件</h1>
        <div class="alert alert-info"><span><b>三层分工</b>(方法论详见 time-dimension-design.html):🧱 <b>变量(根因)</b>=永续中性状态量,在图里,带「回归特性」;🔥 <b>主题</b>=变量在某段时期的市场注意力状态,是挂在节点上的标签(不新建节点);⚡ <b>事件</b>=对变量的一次带时间戳 ±赋值,不进图、进事件日志(<code class="text-xs">data/copper_events.yaml</code>)。推理的完整输入 = 图给结构 + 事件给激活 + 主题给计价强度提示。</span></div>

        <div class="card card-border bg-base-100"><div class="card-body cell">
          <h2 class="card-title">🔥 主题看板(23 个根因的当前市场地位)</h2>
          <p class="text-sm text-base-content/70">主题 ≠ 根因:机制(边)一直在,主题决定市场当下"看不看它"。休眠主题的机制照常运转,只是不被计价——直到退场信号反转(事件密度回升/价格重新响应)。冷启动为人工标注,接新闻监控后由事件密度自动接管。</p>
          <div class="mt-2">
<!--THEMES-->
          </div>
        </div></div>

        <div class="card card-border bg-base-100"><div class="card-body cell">
          <h2 class="card-title">⚡ 事件日志(2021-2026 真实事件,append-only)</h2>
          <p class="text-sm text-base-content/70">每条事件 = 时间 + 根因 + 方向(±)+ 幅度 + 影响窗口 + 来源。「待反转」= 状态保持到出现反向事件(如 232 关税的 +1 被 7.30 豁免的 −1 回收)。注意 2025.7 的 232 三连事件:同一根因 22 天内走完 +1→−1,这正是中性根因建模的价值。</p>
          <div class="overflow-x-auto mt-2"><table class="table table-sm">
            <thead><tr><th>时间</th><th>根因(回归特性)</th><th>方向·幅度</th><th>影响窗口</th><th>状态</th><th>事件与来源</th></tr></thead>
            <tbody>
<!--EVENTS-->
            </tbody>
          </table></div>
        </div></div>

        <div class="card card-border bg-base-100"><div class="card-body cell">
          <h2 class="card-title">🧮 当前生效事件叠加 → 分时段综合研判(方法论跑起来的样子)</h2>
          <p class="text-sm text-base-content/70">推理输入不再是手写的单一冲击,而是<b>事件日志中所有仍在生效的事件叠加</b>(同一根因取最新方向);输出按路径累计时滞分三桶,每桶独立汇总多空——回答"现在这些事同时在起作用,近端和远端分别怎么看"。此为构建时快照,边表或事件更新后重跑 <code class="text-xs">gen_layers.py</code> 即刷新。</p>
          <div class="mt-2 cell">
<!--STACKED-->
          </div>
          <p class="text-xs text-base-content/50 mt-2">读法提示:6 月以上桶同时出现多头路径(冶炼减产→精铜紧)与空头路径(硫酸走强→延缓减产→供给不减)——这正是当下市场关于"减产会不会兑现"的真实分歧,图谱把分歧的结构摆了出来,验证信号见各根因的监测面板。</p>
        </div></div>
      </section>

"""
SECTION = SECTION.replace("<!--THEMES-->", themes).replace("<!--EVENTS-->", events).replace("<!--STACKED-->", stacked)
demo_marker = "      <!-- ============ DEMO ============ -->"
assert demo_marker in page
page = page.replace(demo_marker, SECTION + demo_marker, 1)

# 3) 面板 tbody 替换
panel_rows = (out / "cu_panel.html").read_text(encoding="utf-8")
pat = re.compile(r"(最强传导路径\(\+1 口径\)/ 历史案例</th></tr></thead>\s*<tbody>\n)(.*?)(\n            </tbody>)", re.DOTALL)
assert pat.search(page), "面板 tbody 未定位"
page = pat.sub(lambda m: m.group(1) + panel_rows + m.group(3), page, count=1)

# 4) KG JSON 替换(单行)
data = (out / "cu_explore.json").read_text(encoding="utf-8")
assert re.search(r"const KG = .*;", page)
page = re.sub(r"const KG = .*", "const KG = " + data + ";", page, count=1)

# 5) nodeHtml 增加 temporal 徽章
js_anchor = "h += badge(n.type, 'badge-outline');"
assert js_anchor in page
page = page.replace(js_anchor, js_anchor + """
        const tmp = n.temporal || {};
        if (tmp.reversion) h += badge('回归:'+tmp.reversion, 'badge-outline badge-accent');
        const th = tmp.theme || {};
        if (th.status) h += badge('主题:'+(th.name||'')+' · '+th.status,
          th.status==='活跃' ? 'badge-error' : (th.status==='降温' ? 'badge-warning' : 'badge-ghost'));
        if (th.note) h += '<div class="text-xs opacity-60 mt-1">主题备注:'+kgEsc(th.note)+'</div>';""", 1)

# 6) 全景 SVG 替换(节点已改名)
svg = (out / "cu_graph.svg").read_text(encoding="utf-8")
svg = svg.replace('id="my-svg"', 'id="svg-cu"').replace("#my-svg", "#svg-cu")
pat2 = re.compile(r'<svg id="svg-cu".*?</svg>', re.DOTALL)
assert pat2.search(page)
page = pat2.sub(lambda m: svg, page, count=1)

# 7) Q6 演示文本更新(含改名后的根因)
demo = (out / "copper_demo.txt").read_text(encoding="utf-8")
blocks = re.split(r"={72}\n【问题】.*?\n={72}\n", demo)[1:]
q6 = H.escape(blocks[5].strip())
pat3 = re.compile(r"◆ 影响「SHFE铜价格」的根因全景.*?(?=</pre>)", re.DOTALL)
assert pat3.search(page), "Q6 未定位"
page = pat3.sub(lambda m: q6, page, count=1)

# 8) 页面上残留的旧名(交互页提示语等)
page = page.replace("AI数据中心扩建", "数据中心算力基建需求(主题:AI算力扩建)")

page_path.write_text(page, encoding="utf-8")
print(f"完成:{len(page)//1024} KB")
