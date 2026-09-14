# -*- coding: utf-8 -*-
"""Locate the row expand/collapse icons (▼/▲) in the row-header column.

策略: 不要遍历 document.querySelectorAll('*') —— 腾讯文档 DOM 巨大, 那个
操作能卡死好几分钟. 这里只在行号列附近查找带 fold/expand/svg 候选的元素,
且加上尺寸 / 坐标过滤避免误中.
"""
import os
import sys
import time

sys.path.insert(0, os.path.dirname(__file__))
from cdp import get_page_ws, CDP  # noqa: E402

JS = """
(() => {
  const out = [];
  const X_LIM = 80;     // row-header column is ~50px wide on 1536 viewport
  const Y_LO = 100, Y_HI = 720;
  const seen = new Set();
  // 1. SVG / icons
  for (const e of document.querySelectorAll('svg, [class*="icon"]')) {
    const r = e.getBoundingClientRect();
    if (r.width < 6 || r.width > 32) continue;
    if (r.height < 6 || r.height > 32) continue;
    if (r.x > X_LIM) continue;
    if (r.y < Y_LO || r.y > Y_HI) continue;
    const key = r.x.toFixed(0) + ',' + r.y.toFixed(0);
    if (seen.has(key)) continue;
    seen.add(key);
    out.push({x: Math.round(r.x+r.width/2), y: Math.round(r.y+r.height/2),
              w: Math.round(r.width), h: Math.round(r.height),
              tag: e.tagName, cls: String(e.className?.baseVal || e.className || '').slice(0,80),
              txt: (e.textContent||'').trim().slice(0,30)});
  }
  return out;
})()
"""


def main():
    ws, tab = get_page_ws()
    if not ws:
        print("NO_TAB")
        return 1
    print("Driving:", tab["title"], flush=True)
    c = CDP(ws)
    out = os.path.dirname(__file__)

    hits = c.eval(JS)
    print(f"found {len(hits)} icon candidates:", flush=True)
    for h in hits:
        print("  ", h, flush=True)

    # Save the hits for the next step to use.
    import json
    open(os.path.join(out, "_icons.json"), "w").write(json.dumps(hits))

    c.close()
    return 0


if __name__ == "__main__":
    sys.exit(main())
