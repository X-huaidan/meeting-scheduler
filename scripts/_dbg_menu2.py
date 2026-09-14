# -*- coding: utf-8 -*-
"""Debug: what menu appears for a row-header selection, and does x matter?"""
import json
import os
import sys
import time

sys.path.insert(0, os.path.dirname(__file__))
from cdp import get_page_ws, CDP                                     # noqa: E402
from sheet_ui import click, key, key_up, mouse_move, mouse_down, mouse_up, SHIFT   # noqa: E402

BAR = "document.querySelector('.bar-label') ? document.querySelector('.bar-label').value : ''"
DUMP = """
(() => {
  const root = document.querySelector('.context-menu_contextmenu__2Aa6v')
            || document.querySelector('[class*="contextmenu"]');
  if (!root) return 'NO_MENU';
  const r = root.getBoundingClientRect();
  const items = [];
  for (const e of root.querySelectorAll('*')) {
    if (e.children.length) continue;
    const t = (e.textContent || '').trim();
    if (!t) continue;
    const b = e.getBoundingClientRect();
    if (b.width <= 0) continue;
    items.push([Math.round(b.x + b.width/2), Math.round(b.y + b.height/2), t]);
  }
  return {menu: [Math.round(r.x), Math.round(r.y), Math.round(r.width), Math.round(r.height)], items: items};
})()
"""


def wheel(c, dy, x=500, y=400):
    c.send("Input.dispatchMouseEvent", {"type": "mouseWheel", "x": x, "y": y,
                                        "deltaX": 0, "deltaY": dy, "button": "none"})
    time.sleep(0.3)


def fast_click(c, x, y):
    c.send("Input.dispatchMouseEvent", {"type": "mouseMoved", "x": x, "y": y, "button": "none"})
    c.send("Input.dispatchMouseEvent", {"type": "mousePressed", "x": x, "y": y,
                                        "button": "left", "clickCount": 1})
    c.send("Input.dispatchMouseEvent", {"type": "mouseReleased", "x": x, "y": y,
                                        "button": "left", "clickCount": 1})
    time.sleep(0.03)


def parse_row(v):
    if not isinstance(v, str) or not v:
        return -1
    v = v.replace("$", "")
    if ":" in v:
        v = v.split(":")[0]
    d = "".join(ch for ch in v if ch.isdigit())
    return int(d) if d else -1


def scan(c, x=18, lo=185, hi=645, step=6):
    vis = {}
    for y in range(lo, hi, step):
        fast_click(c, x, y)
        r = parse_row(c.eval(BAR))
        if r > 0 and r not in vis:
            vis[r] = y
    return vis


def shift_click(c, x, y, send_key=True):
    if send_key:
        key(c, "Shift", "ShiftLeft", 16, SHIFT)
        time.sleep(0.05)
    mouse_move(c, x, y)
    time.sleep(0.05)
    mouse_down(c, x, y, "left", 1, SHIFT)
    time.sleep(0.05)
    mouse_up(c, x, y, "left", 1, SHIFT)
    time.sleep(0.05)
    if send_key:
        key_up(c, "Shift", "ShiftLeft", 16, 0)
    time.sleep(0.45)


def right_click(c, x, y):
    mouse_move(c, x, y)
    time.sleep(0.15)
    mouse_down(c, x, y, "right", 1)
    time.sleep(0.12)
    mouse_up(c, x, y, "right", 1)
    time.sleep(1.1)


def trial(c, x, label):
    vis = scan(c, x)
    if 40 not in vis or 47 not in vis:
        print(f"  [{label}] x={x}: rows 40/47 not both visible ({sorted(vis)})", flush=True)
        return
    click(c, x, vis[40])
    time.sleep(0.5)
    after_first = c.eval(BAR)
    shift_click(c, x, vis[47])
    after_shift = c.eval(BAR)
    right_click(c, x, vis[47])
    d = c.eval(DUMP)
    key(c, "Escape", "Escape", 27)
    time.sleep(0.5)
    print(f"  [{label}] x={x} y40={vis[40]} y47={vis[47]} "
          f"first={after_first!r} shift={after_shift!r}", flush=True)
    if isinstance(d, dict):
        print(f"    menu={d['menu']}", flush=True)
        for it in d["items"]:
            print(f"      {it[0]:4d},{it[1]:4d}  {it[2]}", flush=True)
    else:
        print("    ", d, flush=True)


ws, tab = get_page_ws()
c = CDP(ws)
print("tab:", tab.get("title"), flush=True)
key(c, "Escape", "Escape", 27)
time.sleep(0.4)

for _ in range(25):
    wheel(c, -900)
time.sleep(0.4)
# bring rows ~36..51 into view
for _ in range(4):
    wheel(c, 420)
time.sleep(0.4)

trial(c, 28, "row-header x=28")
for _ in range(25):
    wheel(c, -900)
time.sleep(0.3)
for _ in range(4):
    wheel(c, 420)
time.sleep(0.4)
trial(c, 18, "x=18")

c.close()
