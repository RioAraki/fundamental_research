# -*- coding: utf-8 -*-
"""给 palm-mvp.html 插入「交互探索」页,并同步面板/全景图/计数/Q6 文本。"""
import html as H
import re
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")
root = Path(__file__).parent
page_path = root.parent / ".lavish" / "palm-mvp.html"
page = page_path.read_text(encoding="utf-8")

# 1) 计数
page = page.replace("43 节点", "45 节点").replace("53 边", "55 边").replace("23 个", "25 个")

# 2) 导航项 + 导读行
nav_anchor = '<li><a href="#graph" data-nav="graph">🕸️ 图谱全景</a></li>'
assert nav_anchor in page
page = page.replace(nav_anchor, nav_anchor +
    '\n        <li><a href="#explore" data-nav="explore">🖱️ 交互探索</a></li>')
guide_anchor = '<tr><td><a class="link" href="#demo">🔬 推理演示</a></td>'
page = page.replace(guide_anchor,
    '<tr><td><a class="link" href="#explore">🖱️ 交互探索</a></td><td><b>可解释性入口</b>:点任意节点看含义与利好利空判定,点任意边看两端相互作用与"为什么是这个强度"</td></tr>\n              ' + guide_anchor)

# 3) 交互探索 section(数据内联)
data = (root / "out" / "explore_data.json").read_text(encoding="utf-8")
SECTION = """      <!-- ============ EXPLORE ============ -->
      <section data-page="explore" class="hidden space-y-6">
        <h1 class="text-2xl font-bold">🖱️ 交互探索:点节点看含义,点边看相互作用</h1>
        <div class="alert alert-info"><span><b>用法</b>:左图可拖拽/缩放。<b>点击节点</b>→右侧显示该量含义、+/− 方向语义、<b>利好利空判定</b>(该量↑对 P 的方向、最强路径、是否存在异号路径)、监测信号与案例;<b>点击连线</b>→显示两端相互作用的机制解释、时滞/强度及"为什么配这个强度"(rationale)。蓝边=同向(+),红边=反向(−),线越粗强度越高;椭圆=根因,金框=目标变量 DCE P。</span></div>
        <div class="card card-border bg-base-100"><div class="card-body cell">
          <div class="flex flex-col lg:flex-row gap-4">
            <div id="kg-canvas" class="rounded-box border border-base-content/10" style="height:74vh; flex:1 1 58%; min-width:0; background:#0b0a08"></div>
            <div id="kg-panel" class="rounded-box bg-base-200 p-4 overflow-y-auto text-sm cell" style="height:74vh; flex:1 1 42%; min-width:0">
              <p class="text-base-content/60">👈 点击左图任意<b>节点</b>或<b>连线</b>,这里会显示解释。<br/><br/>试试:点「原油价格 → DCE棕榈油价格」那条细蓝线,看看为什么它只是"弱"影响;再点「油脂化工需求」,看看下游油化需求为什么对 P 影响有限。</p>
            </div>
          </div>
        </div></div>
      </section>

      <script src="https://cdn.jsdelivr.net/npm/vis-network@9.1.9/standalone/umd/vis-network.min.js"></script>
      <script>
      const KG = /*DATA*/;
      let kgNet = null;
      function kgEsc(s){ return String(s||'').replace(/&/g,'&amp;').replace(/</g,'&lt;'); }
      function badge(t, cls){ return '<span class="badge badge-sm '+cls+' mr-1">'+kgEsc(t)+'</span>'; }
      function nodeHtml(n){
        let h = '<h3 class="font-bold text-base mb-1">'+kgEsc(n.label)+'</h3>';
        h += badge(n.type, 'badge-outline');
        if (n.id === KG.target) h += badge('目标变量:全图收敛于此', 'badge-warning');
        if (n.note) h += '<div class="mt-2"><b>含义</b>:'+kgEsc(n.note)+'</div>';
        if (n.direction) h += '<div class="mt-2 rounded bg-base-300 p-2"><b>方向语义</b>:'+kgEsc(n.direction)+'</div>';
        if (n.id !== KG.target && n.effect){
          const e = n.effect;
          h += '<div class="mt-2 rounded bg-base-300 p-2"><b>利好利空判定</b>:该量<b>上升(↑)</b> ⇒ 对 DCE P <b>'
             + (e.sign==='利多' ? '<span class="text-error">利多</span>' : '<span class="text-success">利空</span>')
             + '</b>(最强路径强度 '+e.strength+',时滞 ≈'+e.lag+' 月);<b>下降(↓)</b>则反向。';
          h += '<br/>共 '+e.n_paths+' 条传导路径(利多 '+e.n_bull+' / 利空 '+e.n_bear+')';
          if (e.n_bull>0 && e.n_bear>0) h += ' <b>⚠️ 存在异号路径,净方向依赖情形(时滞不同,常为"短多长空"或反之)</b>';
          h += '<div class="text-xs mt-1 opacity-80">最强路径:'+kgEsc(e.path)+'</div></div>';
        }
        const sig = n.signals || {};
        if ((sig.news||[]).length || (sig.data||[]).length){
          h += '<div class="mt-2"><b>📡 监测信号</b>';
          if ((sig.news||[]).length) h += '<div class="text-xs mt-1">新闻关键词:'+kgEsc(sig.news.join(' / '))+'</div>';
          if ((sig.data||[]).length) h += '<div class="text-xs mt-1">数据源:'+kgEsc(sig.data.join(' | '))+'</div>';
          h += '</div>';
        }
        if (n.case) h += '<div class="mt-2 text-xs text-warning/90"><b>历史案例</b>:'+kgEsc(n.case)+'</div>';
        return h;
      }
      function edgeHtml(e){
        let h = '<h3 class="font-bold text-base mb-1">'+kgEsc(e.from)+' <span class="'+(e.polarity==='+'?'text-info':'text-error')+'">─'+e.polarity+'→</span> '+kgEsc(e.to)+'</h3>';
        h += badge('机制'+(e.polarity==='+'?'同向 +':'反向 −'), e.polarity==='+'?'badge-info':'badge-error');
        h += badge('时滞 '+e.lag, 'badge-outline') + badge('强度 '+e.strength, 'badge-outline');
        h += '<div class="mt-2"><b>相互作用</b>:'+kgEsc(e.sentence)+'</div>';
        if (e.rationale) h += '<div class="mt-2 rounded bg-base-300 p-2"><b>机制详解 / 为什么是这个强度</b>:'+kgEsc(e.rationale)+'</div>';
        if (e.condition) h += '<div class="mt-2"><b>生效条件</b>:'+kgEsc(e.condition)+'</div>';
        if (e.evidence) h += '<div class="mt-2 text-xs text-warning/90"><b>证据/案例</b>:'+kgEsc(e.evidence)+'</div>';
        if (!e.rationale) h += '<div class="mt-2 text-xs opacity-60">(此边暂无人工 rationale,以上为按五要素自动生成的解释;可在 palm_oil.yaml 补充)</div>';
        return h;
      }
      function initExplore(){
        if (kgNet) return;
        const nodes = new vis.DataSet(KG.nodes.map(n => ({
          id: n.id, label: n.label, shape: n.shape,
          color: {background: n.color, border: n.id===KG.target ? '#fbbf24' : 'rgba(255,255,255,.25)',
                  highlight: {background: n.color, border: '#fde047'}},
          borderWidth: n.id===KG.target ? 4 : 1,
          font: {color:'#fff', size:15}, margin: 8
        })));
        const edges = new vis.DataSet(KG.edges.map(e => ({
          id: e.id, from: e.from, to: e.to, arrows: 'to',
          color: {color: e.color, highlight: '#fde047'}, width: e.width,
          label: e.label, font: {size: 9, color:'#94a3b8', strokeWidth: 0},
          smooth: {type:'dynamic'}
        })));
        kgNet = new vis.Network(document.getElementById('kg-canvas'), {nodes, edges}, {
          physics: {solver:'forceAtlas2Based',
                    forceAtlas2Based:{gravitationalConstant:-90, springLength:150, avoidOverlap:0.7},
                    stabilization:{iterations:300}},
          interaction: {hover:true, tooltipDelay:99999}
        });
        const nmap = Object.fromEntries(KG.nodes.map(n=>[n.id,n]));
        const emap = Object.fromEntries(KG.edges.map(e=>[e.id,e]));
        kgNet.on('click', p => {
          const panel = document.getElementById('kg-panel');
          if (p.nodes.length) panel.innerHTML = nodeHtml(nmap[p.nodes[0]]);
          else if (p.edges.length) panel.innerHTML = edgeHtml(emap[p.edges[0]]);
        });
      }
      </script>

"""
SECTION = SECTION.replace("/*DATA*/", data)
method_marker = "      <!-- ============ METHOD ============ -->"
assert method_marker in page
page = page.replace(method_marker, SECTION + method_marker)

# 4) show() 懒加载
hook = "document.getElementById('nav-toggle').checked = false;"
assert hook in page
page = page.replace(hook, "if(id==='explore'){ setTimeout(initExplore, 80); }\n  " + hook)

# 5) 面板 tbody 替换
panel_rows = (root / "out" / "panel.html").read_text(encoding="utf-8")
pat = re.compile(r"(最强传导路径\(\+1 口径\)/ 历史案例</th></tr></thead>\s*<tbody>\n)(.*?)(\n            </tbody>)", re.DOTALL)
assert pat.search(page), "面板 tbody 未定位到"
page = pat.sub(lambda m: m.group(1) + panel_rows + m.group(3), page, count=1)

# 6) 全景图 SVG 替换
svg = (root / "out" / "palm_graph.svg").read_text(encoding="utf-8")
svg = svg.replace('id="my-svg"', 'id="svg-palm"').replace("#my-svg", "#svg-palm")
pat2 = re.compile(r'<svg id="svg-palm".*?</svg>', re.DOTALL)
assert pat2.search(page)
page = pat2.sub(lambda m: svg, page, count=1)

# 7) Q6 文本更新(现在 25 个根因)
demo = (root / "out" / "palm_demo.txt").read_text(encoding="utf-8")
blocks = re.split(r"={72}\n【问题】.*?\n={72}\n", demo)[1:]
q6 = H.escape(blocks[5].strip())
pat3 = re.compile(r"◆ 影响「DCE棕榈油价格」的根因全景.*?(?=</pre>)", re.DOTALL)
assert pat3.search(page), "Q6 未定位到"
page = pat3.sub(lambda m: q6, page, count=1)

page_path.write_text(page, encoding="utf-8")
print(f"完成:{len(page)//1024} KB")
