# -*- coding: utf-8 -*-
"""Select a range via the Name Box, right-click, and dump the visible menu."""
import base64
import sys
import time

sys.path.insert(0, ".")
from cdp import get_page_ws, CDP
from sheet_ui import click, key, key_up, mouse_move, mouse_down, mouse_up
from _goto import goto_addr, KEYMAP
from _grid_calib import nb

DUMP = """
(() => {
  const vis = [];
  for (const e of document.querySelectorAll('body *')) {
    const cl = String(e.className || '');
    if (!cl || !/dui-menu/i.test(cl)) continue;
    const r = e.getBoundingClientRect();
    if (r.width < 60 || r.height < 25 || r.x < 0 || r.y < 0) continue;
    if (/hidden/i.test(cl)) continue;
    vis.push({cls: cl.slice(0, 60), x: Math.round(r.x), y: Math.round(r.y),
              w: Math.round(r.width), h: Math.round(r.height),
              txt: (e.textContent || '').replace(/\\s+/g, ' ').trim().slice(0, 260)});
  }
  return JSON.stringify(vis.slice(0, 10));
})()
"""


def type_text(c, s):
    for ch in s:
        k = KEYMAP.get(ch.upper())
        if k:
            key(c, k[0], k[1], k[2], 0, text=ch)
            time.sleep(0.03)


def namebox(c, text):
    """Commit `text` into the Name Box, verifying focus first."""
    from _goto import ACTIVE, focus_ok
    for _ in range(4):
        click(c, 30, 111)
        time.sleep(0.35)
        if focus_ok(c.eval(ACTIVE)):
            break
    else:
        return None
    from sheet_ui import chord, CTRL
    chord(c, "a", "KeyA", 65, CTRL)
    time.sleep(0.12)
    type_text(c, text)
    key(c, "Enter", "Enter", 13)
    key_up(c, "Enter", "Enter", 13)
    time.sleep(1.0)
    return nb(c)


def main():
    rng = sys.argv[1] if len(sys.argv) > 1 else "A40:I46"
    ws, tab = get_page_ws()
    c = CDP(ws)
    c.ws.settimeout(20)
    nb(c)
    print("goto A45 ->", repr(goto_addr(c, "A45")), flush=True)

    got = namebox(c, rng)
    print(f"namebox {rng!r} -> {got!r}", flush=True)

    # right click inside the selection (row 40 band is visible around y=190)
    for y in (190, 200, 205):
        mouse_move(c, 300, y)
        time.sleep(0.25)
        mouse_down(c, 300, y, "right", 1)
        time.sleep(0.15)
        mouse_up(c, 300, y, "right", 1)
        time.sleep(1.2)
        info = c.eval(DUMP)
        print(f"\n  rclick (300,{y}) ->", info, flush=True)
        if info and info != "[]":
            r = c.send("Page.captureScreenshot", {"format": "png"})
            d = (r or {}).get("result", {}).get("data")
            if d:
                open(f"r_{y}.png", "wb").write(base64.b64decode(d))
            print(f"  saved r_{y}.png", flush=True)
            break
        key(c, "Escape", "Escape", 27)
        time.sleep(0.4)
    c.close()


if __name__ == "__main__":
    main()
