# -*- coding: utf-8 -*-
"""Probe what element sits at the row-header marker pixels (DOM vs canvas)."""
import json
import re
import sys
import time

sys.path.insert(0, r"C:\Users\changan\.workbuddy\skills\meeting-scheduler\scripts")
from cdp import get_page_ws, CDP          # noqa: E402
from sheet_ui import snap, click, key, key_up, chord, CTRL, ALT, SHIFT   # noqa: E402

ws, tab = get_page_ws()
c = CDP(ws)
print("tab:", tab.get("title"), flush=True)

# ---- jump to A3 so the scroll position is deterministic ----
click(c, 30, 111)                 # name box
time.sleep(0.2)
chord(c, "a", "KeyA", 65, CTRL)   # select all text in the box
key(c, "3", "Digit3", 51, 0, text="3")
key(c, "Return", "Enter", 13)
time.sleep(0.8)
print("jumped to A3", flush=True)

pts = [(10, 300), (10, 315), (18, 300), (18, 315), (28, 300),
       (10, 477), (10, 487), (10, 535), (10, 547)]
js = """(function(pts){
  return pts.map(function(p){
    var els = document.elementsFromPoint(p[0], p[1]);
    if (els === undefined) return {p:p, els:'undefined'};
    return {p: p, n: els.length, els: els.slice(0,5).map(function(e){
      var cl = '';
      try { cl = (e.className && e.className.toString) ? e.className.toString().slice(0,70) : ''; } catch(err) { cl = '?'; }
      return (e.tagName || '') + '|' + cl;
    })};
  });
})(%s)""" % json.dumps(pts)
print(json.dumps(c.eval(js), ensure_ascii=False, indent=1), flush=True)

snap(c, r"C:\Users\changan\.workbuddy\skills\meeting-scheduler\scripts\probe_page.png")
print("saved probe_page.png", flush=True)
c.close()
