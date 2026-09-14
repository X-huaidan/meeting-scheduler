# -*- coding: utf-8 -*-
"""Select a cell range by dragging, then click the context-menu 取消隐藏行 item.

  python _drag_unhide.py <anchorCell> <x1> <y1> <x2> <y2> <tag> [--dry]
"""
import base64
import sys
import time

sys.path.insert(0, ".")
from cdp import get_page_ws, CDP
from sheet_ui import (click, key, key_up, mouse_move, mouse_down, mouse_up)
from _goto import goto_addr
from _grid_calib import nb

FIND = """
(() => {
  const out = [];
  for (const e of document.querySelectorAll('[class*="dui-menu-item"]')) {
    const r = e.getBoundingClientRect();
    if (r.width < 60 || r.height < 20 || r.x < 0 || r.y < 0) continue;
    const t = (e.textContent || '').replace(/\\s+/g, ' ').trim();
    out.push({t: t.slice(0, 40), x: Math.round(r.x), y: Math.round(r.y),
              w: Math.round(r.width), h: Math.round(r.height),
              cx: Math.round(r.x + r.width / 2), cy: Math.round(r.y + r.height / 2),
              cls: String(e.className).slice(0, 70)});
  }
  return JSON.stringify(out);
})()
"""


def drag(c, x1, y1, x2, y2, steps=14):
    mouse_move(c, x1, y1)
    time.sleep(0.12)
    mouse_down(c, x1, y1, "left", 1)
    time.sleep(0.18)
    for i in range(1, steps + 1):
        xi = int(x1 + (x2 - x1) * i / steps)
        yi = int(y1 + (y2 - y1) * i / steps)
        c.send("Input.dispatchMouseEvent",
               {"type": "mouseMoved", "x": xi, "y": yi, "button": "left"})
        time.sleep(0.05)
    time.sleep(0.2)
    mouse_up(c, x2, y2, "left", 1)
    time.sleep(0.6)


def right_click(c, x, y):
    mouse_move(c, x, y)
    time.sleep(0.25)
    mouse_down(c, x, y, "right", 1)
    time.sleep(0.15)
    mouse_up(c, x, y, "right", 1)
    time.sleep(1.3)


def shot(c, path):
    r = c.send("Page.captureScreenshot", {"format": "png"})
    d = (r or {}).get("result", {}).get("data")
    if d:
        open(path, "wb").write(base64.b64decode(d))
    return path


def main():
    anchor = sys.argv[1]
    x1, y1, x2, y2 = (int(v) for v in sys.argv[2:6])
    tag = sys.argv[6] if len(sys.argv) > 6 else "du"
    dry = "--dry" in sys.argv

    ws, tab = get_page_ws()
    c = CDP(ws)
    c.ws.settimeout(20)
    nb(c)
    print("goto", anchor, "->", repr(goto_addr(c, anchor)), flush=True)

    drag(c, x1, y1, x2, y2)
    print("after drag, namebox =", repr(nb(c)), flush=True)
    shot(c, f"{tag}_sel.png")

    mx, my = (x1 + x2) // 2, (y1 + y2) // 2
    right_click(c, mx, my)
    items = c.eval(FIND)
    print("menu items:", items, flush=True)
    shot(c, f"{tag}_menu.png")

    if dry:
        key(c, "Escape", "Escape", 27)
        c.close()
        return

    import json
    try:
        arr = json.loads(items or "[]")
    except Exception:
        arr = []
    tgt = [it for it in arr if "取消隐藏" in it["t"]]
    if not tgt:
        print("!! no 取消隐藏 item in menu", flush=True)
        key(c, "Escape", "Escape", 27)
        c.close()
        return
    it = tgt[0]
    print(f"clicking {it['t']!r} at ({it['cx']},{it['cy']}) disabled={'disabled' in it['cls']}",
          flush=True)
    click(c, it["cx"], it["cy"])
    time.sleep(1.8)
    shot(c, f"{tag}_done.png")
    print("done ->", f"{tag}_done.png", flush=True)
    c.close()


if __name__ == "__main__":
    main()
