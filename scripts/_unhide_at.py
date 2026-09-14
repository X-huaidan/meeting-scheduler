# -*- coding: utf-8 -*-
"""Unhide one hidden band by clicking its two neighbouring row headers.

  python _unhide_at.py <anchorCell> <yAbove> <yBelow> <tag> [--menu-only]

Tries the Alt+Shift+9 shortcut first, verifies by re-reading the row number at
yBelow, and falls back to the row-header context menu (the only DOM-visible path).
"""
import base64
import sys
import time

sys.path.insert(0, ".")
from cdp import get_page_ws, CDP
from sheet_ui import (click, key, key_up, mouse_move, mouse_down, mouse_up,
                      chord, SHIFT, ALT, CTRL)
from _goto import goto_addr
from _grid_calib import nb, parse

ROWX = int(__import__("os").environ.get("ROWX", "26"))

FIND_UNHIDE = """
(() => {
  const root = document.querySelector('.context-menu_contextmenu__2Aa6v')
            || document.querySelector('[class*="contextmenu"]');
  if (!root) return {err: 'no context menu'};
  const rr = root.getBoundingClientRect();
  const items = [];
  const hits = [];
  for (const e of root.querySelectorAll('*')) {
    const t = (e.textContent || '').trim();
    const r = e.getBoundingClientRect();
    if (r.width <= 0 || r.height <= 0) continue;
    if (t === 'Alt+Shift+9') {
      hits.push({x: Math.round(rr.x + rr.width / 2),
                 y: Math.round(r.y + r.height / 2),
                 txt: t, w: Math.round(r.width), h: Math.round(r.height)});
    }
    if (t && t.length < 20 && /隐藏|取消/.test(t)) {
      items.push({t: t, x: Math.round(r.x + r.width/2), y: Math.round(r.y + r.height/2),
                  w: Math.round(r.width), h: Math.round(r.height)});
    }
  }
  return {hits: hits, items: items,
          menu: [Math.round(rr.x), Math.round(rr.y), Math.round(rr.width), Math.round(rr.height)]};
})()
"""


def shift_click(c, x, y):
    key(c, "Shift", "ShiftLeft", 16, SHIFT)
    time.sleep(0.05)
    mouse_move(c, x, y)
    time.sleep(0.04)
    mouse_down(c, x, y, "left", 1, SHIFT)
    time.sleep(0.04)
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


def crop(c, path, x, y, w, h, scale=2):
    r = c.send("Page.captureScreenshot", {
        "format": "png", "clip": {"x": x, "y": y, "width": w, "height": h, "scale": scale}})
    d = (r or {}).get("result", {}).get("data")
    if d:
        open(path, "wb").write(base64.b64decode(d))
    return path


def main():
    anchor, y1, y2, tag = sys.argv[1], int(sys.argv[2]), int(sys.argv[3]), sys.argv[4]
    menu_only = "--menu-only" in sys.argv
    ws, tab = get_page_ws()
    c = CDP(ws)
    c.ws.settimeout(20)
    nb(c)  # warm up

    print("goto", anchor, "->", repr(goto_addr(c, anchor)), flush=True)
    print("row above:", nb(c) if click(c, ROWX, y1) or True else "?", flush=True)
    click(c, ROWX, y1)
    time.sleep(0.4)
    print("  before: y=%d -> %r" % (y1, nb(c)), flush=True)

    shift_click(c, ROWX, y2)
    sel = nb(c)
    print("  after shift-click y=%d: sel=%r" % (y2, sel), flush=True)
    crop(c, f"{tag}_sel.png", 0, 120, 320, 620, 2)

    if not menu_only:
        print("  trying Alt+Shift+9 (raw) ...", flush=True)
        chord(c, "9", "Digit9", 57, ALT | SHIFT, raw=True)
        time.sleep(1.4)
        click(c, ROWX, y2)
        time.sleep(0.4)
        after_key = nb(c)
        print("  after shortcut: y=%d -> %r" % (y2, after_key), flush=True)
        if after_key and after_key != sel:
            print("  ==> SHORTCUT WORKED", flush=True)
            crop(c, f"{tag}_done.png", 0, 120, 320, 620, 2)
            c.close()
            return

    print("  falling back to context menu", flush=True)
    click(c, ROWX, y1)
    time.sleep(0.35)
    shift_click(c, ROWX, y2)
    print("  sel again:", repr(nb(c)), flush=True)
    right_click(c, ROWX, y2)
    info = c.eval(FIND_UNHIDE)
    print("  menu probe:", info, flush=True)
    hits = (info or {}).get("hits") or []
    if not hits:
        key(c, "Escape", "Escape", 27)
        time.sleep(0.3)
        print("  !! 取消隐藏行 not offered", flush=True)
        c.close()
        return
    h = hits[0]
    click(c, h["x"], h["y"])
    time.sleep(1.6)
    click(c, ROWX, y2)
    time.sleep(0.4)
    print("  after menu click: y=%d -> %r" % (y2, nb(c)), flush=True)
    crop(c, f"{tag}_done.png", 0, 120, 320, 620, 2)
    c.close()


if __name__ == "__main__":
    main()
