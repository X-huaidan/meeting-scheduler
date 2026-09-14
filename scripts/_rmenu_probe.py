# -*- coding: utf-8 -*-
"""Try right-clicking at several spots and report every menu-ish container."""
import base64
import sys
import time

sys.path.insert(0, ".")
from cdp import get_page_ws, CDP
from sheet_ui import mouse_move, mouse_down, mouse_up, key
from _goto import goto_addr
from _grid_calib import nb

PROBE = """
(() => {
  const out = [];
  for (const e of document.querySelectorAll('body *')) {
    const cl = String(e.className || '');
    if (!cl) continue;
    if (!/menu|popup|dropdown|dui-|context/i.test(cl)) continue;
    const r = e.getBoundingClientRect();
    if (r.width > 60 && r.height > 30 && r.width < 700 && r.height < 900)
      out.push([cl.slice(0, 80), Math.round(r.x), Math.round(r.y),
                Math.round(r.width), Math.round(r.height)]);
    if (out.length >= 15) break;
  }
  return JSON.stringify(out);
})()
"""


def main():
    spots = [(26, 205), (26, 400), (28, 300), (60, 205), (300, 205),
             (26, 190), (18, 205)]
    ws, tab = get_page_ws()
    c = CDP(ws)
    c.ws.settimeout(20)
    nb(c)
    print("goto A45 ->", repr(goto_addr(c, "A45")), flush=True)

    for (x, y) in spots:
        mouse_move(c, x, y)
        time.sleep(0.25)
        mouse_down(c, x, y, "right", 1)
        time.sleep(0.15)
        mouse_up(c, x, y, "right", 1)
        time.sleep(1.1)
        info = c.eval(PROBE)
        has = bool(info) and info != "[]"
        print(f"  rclick ({x},{y}) -> {info if has else 'NO MENU'}", flush=True)
        if has:
            r = c.send("Page.captureScreenshot", {"format": "png"})
            d = (r or {}).get("result", {}).get("data")
            if d:
                open(f"m_{x}_{y}.png", "wb").write(base64.b64decode(d))
            print(f"     saved m_{x}_{y}.png", flush=True)
            break
        key(c, "Escape", "Escape", 27)
        time.sleep(0.3)
    c.close()


if __name__ == "__main__":
    main()
