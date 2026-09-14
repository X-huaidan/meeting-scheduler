# -*- coding: utf-8 -*-
"""Inspect the DOM of the 取消隐藏行 menu entry (its label text is not in textContent)."""
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
  const out = [];
  for (const e of root.querySelectorAll('*')) {
    const t = (e.textContent || '').trim();
    if (t !== 'Alt+Shift+9' && t !== 'Ctrl+Alt+9') continue;
    let p = e, chain = [];
    for (let i = 0; i < 4 && p; i++) {
      chain.push(p.tagName + '.' + String(p.className).slice(0, 70));
      p = p.parentElement;
    }
    const pe = e.parentElement;
    out.push({t: t, chain: chain,
              parentText: (pe ? (pe.textContent || '').trim().slice(0, 60) : ''),
              parentHTML: (pe ? pe.outerHTML.slice(0, 500) : ''),
              rect: (() => { const r = e.getBoundingClientRect();
                             return [Math.round(r.x), Math.round(r.y), Math.round(r.width), Math.round(r.height)]; })()});
  }
  return {root: root.outerHTML.length, items: out};
})()
"""


def wheel(c, dy, x=500, y=400):
    c.send("Input.dispatchMouseEvent", {"type": "mouseWheel", "x": x, "y": y,
                                        "deltaX": 0, "deltaY": dy, "button": "none"})
    time.sleep(0.3)


def fast_click(c, x, y):
    c.send("Input.dispatchMouseEvent", {"type": "mouseMoved", "x": x, "y": y, "button": "none"})
    c.send("Input.dispatchMouseEvent", {"type": "mousePressed", "x": x, "y": y, "button": "left", "clickCount": 1})
    c.send("Input.dispatchMouseEvent", {"type": "mouseReleased", "x": x, "y": y, "button": "left", "clickCount": 1})
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


def shift_click(c, x, y):
    key(c, "Shift", "ShiftLeft", 16, SHIFT)
    time.sleep(0.05)
    mouse_move(c, x, y)
    time.sleep(0.05)
    mouse_down(c, x, y, "left", 1, SHIFT)
    time.sleep(0.05)
    mouse_up(c, x, y, "left", 1, SHIFT)
    time.sleep(0.05)
    key_up(c, "Shift", "ShiftLeft", 16, 0)
    time.sleep(0.45)


def right_click(c, x, y):
    mouse_move(c, x, y)
    time.sleep(0.15)
    mouse_down(c, x, y, "right", 1)
    time.sleep(0.12)
    mouse_up(c, x, y, "right", 1)
    time.sleep(1.1)


ws, tab = get_page_ws()
c = CDP(ws)
print("tab:", tab.get("title"), flush=True)
key(c, "Escape", "Escape", 27)
time.sleep(0.4)
for _ in range(25):
    wheel(c, -900)
for _ in range(4):
    wheel(c, 420)
time.sleep(0.4)

vis = scan(c)
y40, y47 = vis.get(40), vis.get(47)
print("y40:", y40, "y47:", y47, flush=True)
if y40 and y47:
    click(c, 18, y40)
    time.sleep(0.5)
    shift_click(c, 18, y47)
    right_click(c, 18, y47)
    d = c.eval(DUMP)
    print(json.dumps(d, ensure_ascii=False, indent=1)[:4000], flush=True)
    key(c, "Escape", "Escape", 27)
c.close()
