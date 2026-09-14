# -*- coding: utf-8 -*-
"""Diagnose: does shift-click extend the row selection, and does the menu open?"""
import base64
import sys
import time

sys.path.insert(0, ".")
from cdp import get_page_ws, CDP
from sheet_ui import click, key, key_up, mouse_move, mouse_down, mouse_up, SHIFT
from _goto import goto_addr
from _grid_calib import nb

SEL_PROBE = """
(() => {
  const out = [];
  for (const sel of ['#all-grid-input', 'input.bar-label', '.bar-label',
                     '[class*="nameBox"]', '[class*="name-box"]']) {
    const e = document.querySelector(sel);
    if (e) out.push(sel + ' => ' + JSON.stringify(e.value !== undefined ? e.value : e.textContent));
  }
  return out.join(' | ');
})()
"""

MENU_PROBE = """
(() => {
  const ns = [];
  for (const e of document.querySelectorAll('div')) {
    const cl = String(e.className || '');
    if (/menu|popup|dropdown|dui-/i.test(cl)) {
      const r = e.getBoundingClientRect();
      if (r.width > 80 && r.height > 40 && r.x < 900)
        ns.push([cl.slice(0, 70), Math.round(r.x), Math.round(r.y),
                 Math.round(r.width), Math.round(r.height)]);
    }
  }
  return JSON.stringify(ns.slice(0, 12));
})()
"""


def shot(c, path):
    r = c.send("Page.captureScreenshot", {"format": "png"})
    d = (r or {}).get("result", {}).get("data")
    if d:
        open(path, "wb").write(base64.b64decode(d))
    return path


def main():
    y1, y2 = int(sys.argv[1]), int(sys.argv[2])
    ws, tab = get_page_ws()
    c = CDP(ws)
    c.ws.settimeout(20)
    nb(c)
    print("goto A45 ->", repr(goto_addr(c, "A45")), flush=True)

    click(c, 26, y1)
    time.sleep(0.4)
    print("click y=%d -> %r" % (y1, nb(c)), flush=True)
    shot(c, "d1_click.png")

    key(c, "Shift", "ShiftLeft", 16, SHIFT)
    time.sleep(0.06)
    mouse_move(c, 26, y2)
    time.sleep(0.06)
    mouse_down(c, 26, y2, "left", 1, SHIFT)
    time.sleep(0.06)
    mouse_up(c, 26, y2, "left", 1, SHIFT)
    time.sleep(0.1)
    key_up(c, "Shift", "ShiftLeft", 16, 0)
    time.sleep(0.5)
    print("shiftclick y=%d -> %r" % (y2, nb(c)), flush=True)
    print("selection dom:", c.eval(SEL_PROBE), flush=True)
    shot(c, "d2_shift.png")

    mouse_move(c, 26, y2)
    time.sleep(0.15)
    mouse_down(c, 26, y2, "right", 1)
    time.sleep(0.12)
    mouse_up(c, 26, y2, "right", 1)
    time.sleep(1.2)
    shot(c, "d3_menu.png")
    print("menu containers:", c.eval(MENU_PROBE), flush=True)
    c.close()


if __name__ == "__main__":
    main()
