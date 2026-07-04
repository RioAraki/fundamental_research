# -*- coding: utf-8 -*-
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")
p = Path(__file__).parent.parent / ".lavish" / "palm-mvp.html"
h = p.read_text(encoding="utf-8")
h = h.replace('<span class="badge badge-outline">红边 = 机制反向(−)</span>',
              '<span class="badge badge-outline">蓝边 = 机制同向(+) · 红边 = 反向(−)</span>')
h = h.replace('红色边 = 机制反向(−)。完整文字推理',
              '蓝色边 = 机制同向(+),红色边 = 反向(−)。完整文字推理')
p.write_text(h, encoding="utf-8")
print("图例已更新")
