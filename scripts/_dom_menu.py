# -*- coding: utf-8 -*-
"""1) Probe the DOM for the context-menu container (bounded query).
   2) Re-test the name box jump with the correct Enter key name.
"""
import json
import os
import sys
import time

sys.path.insert(0, os.path.dirname(__file__))
from cdp import get_page_ws, CDP                                    # noqa: E402
from sheet_ui import click, key, key_up, chord, CTRL, mouse_move, mouse_down, mouse_up  # noqa: E402

OUT = os.path.dirname(__file__)
PROBE = """
(() => {
  const sels = ['[class*="menu"]','[class*="Menu"]','[class*="popup"]','[class*="Popup"]',
                '[class*="dropdown"]','[class*="Dropdown"]','[class*="context"]','[class*="Context"]'];
  const seen = new Set(); const out = [];
  for (const s of sels) {
    for (const e of document.querySelectorAll(s)) {
      if (seen.has(e)) continue; seen.add(e);
      const r = e.getBoundingClientRect();
      if (r.width < 60 || r.height < 40) continue;
      const n = e.querySelectorAll('*').length;
      if (n > 4000) continue;
      out.push({cls: String(e.className).slice(0,90),
                x: Math.round(r.x), y: Math.round(r.y), w: Math.round(r.width), h: Math.round(r.height),
                n: n});
    }
  }
  return out.slice(0, 30);
})()
"""


def rclick(c, x, y):
    mouse_move(c, x, y)
    time.sleep(0.15)
    mouse_down(c, x, y, "right", 1)
    time.sleep(0.12)
    mouse_up(c, x, y, "right", 1)
    time.sleep(1.1)


ws, tab = get_page_ws()
c = CDP(ws)
print("tab:", tab.get("title"), flush=True)

print("--- menu containers currently in DOM ---", flush=True)
print(json.dumps(c.eval(PROBE), ensure_ascii=False), flush=True)

# force a menu open and probe again
key(c, "Escape", "Escape", 27)
time.sleep(0.3)
rclick(c, 18, 300)
print("--- after right-click on row header ---", flush=True)
print(json.dumps(c.eval(PROBE), ensure_ascii=False), flush=True)
key(c, "Escape", "Escape", 27)
time.sleep(0.3)

# --- name box jump test (key name must be "Enter", and send keyUp) ---
print("--- name box test ---", flush=True)
click(c, 30, 111)
time.sleep(0.3)
chord(c, "a", "KeyA", 65, CTRL)
time.sleep(0.1)
key(c, "Delete", "Delete", 46, 0)
time.sleep(0.15)
c.send("Input.insertText", {"text": "A47"})
time.sleep(0.3)
key(c, "Enter", "Enter", 13, 0)
time.sleep(0.1)
key_up(c, "Enter", "Enter", 13, 0)
time.sleep(1.0)
print("bar-label now:", c.eval("document.querySelector('.bar-label').value"), flush=True)

c.close()
