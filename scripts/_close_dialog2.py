# -*- coding: utf-8 -*-
"""Close the modal alert. Loosens the DOM search and falls back to clicking
the '确定' button's measured position.

The alert in the captured screenshot: a centered white card ~ (405..685, 180..345)
in the 1092-wide render of a 1920-wide device shot, with a blue '确定' button
around display (645, 310) -> css (~907, ~436).
"""
import os
import sys
import time

sys.path.insert(0, os.path.dirname(__file__))
from cdp import get_page_ws, CDP  # noqa: E402
from sheet_ui import click, snap  # noqa: E402

FIND_BTN = """
(() => {
  const all = [...document.querySelectorAll('*')];
  const hits = [];
  for (const e of all) {
    const t = (e.textContent || '').trim();
    if (t !== '确定' && t !== 'OK') continue;
    const r = e.getBoundingClientRect();
    if (r.width > 0 && r.height > 0) {
      hits.push({x: Math.round(r.x + r.width/2), y: Math.round(r.y + r.height/2),
                 w: Math.round(r.width), h: Math.round(r.height), tag: e.tagName});
    }
  }
  // prefer the smallest matching element (the actual button, not a wrapper)
  hits.sort((a,b) => (a.w*a.h) - (b.w*b.h));
  return hits.slice(0, 5);
})()
"""


def main():
    ws, tab = get_page_ws()
    if not ws:
        print("NO_TAB")
        return 1
    print("Driving:", tab["title"])
    c = CDP(ws)
    out = os.path.dirname(__file__)

    hits = c.eval(FIND_BTN)
    print("candidates:", hits)
    if hits:
        t = hits[0]
        click(c, t["x"], t["y"])
        time.sleep(1.0)
        snap(c, os.path.join(out, "closed2_dom.png"))
        print("clicked DOM candidate", t, "-> closed2_dom.png")
    else:
        click(c, 907, 436)
        time.sleep(1.0)
        snap(c, os.path.join(out, "closed2_coord.png"))
        print("clicked fallback (907,436) -> closed2_coord.png")

    c.close()
    return 0


if __name__ == "__main__":
    sys.exit(main())
