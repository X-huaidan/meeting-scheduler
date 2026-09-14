# -*- coding: utf-8 -*-
"""Safely jump to a cell via the Name Box (with focus verification).

Never sends Ctrl+A unless the Name Box input actually has focus -- the
19:35 incident (whole-sheet wipe) came from Ctrl+A landing on the grid.
"""
import base64
import sys
import time

sys.path.insert(0, ".")
from cdp import get_page_ws, CDP
from sheet_ui import click, chord, key, key_up, CTRL
from _grid_calib import nb

NAMEBOX_X, NAMEBOX_Y = 30, 111

ACTIVE = r"""
(() => {
  const a = document.activeElement;
  if (!a) return 'none';
  const r = a.getBoundingClientRect ? a.getBoundingClientRect() : {x:-1,y:-1,width:-1,height:-1};
  return [a.tagName, a.className || '', a.id || '',
          Math.round(r.x), Math.round(r.y), Math.round(r.width)].join('|');
})()
"""

KEYMAP = {}
for i, ch in enumerate("ABCDEFGHIJKLMNOPQRSTUVWXYZ"):
    KEYMAP[ch] = (ch, f"Key{ch}", 65 + i)
for i in range(10):
    KEYMAP[str(i)] = (str(i), f"Digit{i}", 48 + i)


def focus_ok(info):
    low = info.lower()
    return ("input" in low) and ("bar" in low or "name" in low or "grid-input" in low)


def goto_addr(c, addr, tries=4):
    """Return the name-box text after committing, or None if focus never took."""
    for _ in range(tries):
        click(c, NAMEBOX_X, NAMEBOX_Y)
        time.sleep(0.35)
        info = c.eval(ACTIVE)
        if focus_ok(info):
            break
    else:
        print("  !! name box never took focus; active =", info, flush=True)
        return None

    # focus confirmed -> Ctrl+A now only selects the input's own text
    chord(c, "a", "KeyA", 65, CTRL)
    time.sleep(0.12)
    for ch in addr.upper():
        k = KEYMAP.get(ch)
        if not k:
            continue
        key(c, k[0], k[1], k[2], 0, text=ch)
        time.sleep(0.03)
    key(c, "Enter", "Enter", 13)
    key_up(c, "Enter", "Enter", 13)
    time.sleep(0.9)
    return nb(c)


def crop(c, path, x, y, w, h, scale=2):
    r = c.send("Page.captureScreenshot", {
        "format": "png",
        "clip": {"x": x, "y": y, "width": w, "height": h, "scale": scale},
    })
    data = (r or {}).get("result", {}).get("data")
    if not data:
        raise RuntimeError(f"crop failed: {r}")
    open(path, "wb").write(base64.b64decode(data))
    return path


def main():
    addr = sys.argv[1] if len(sys.argv) > 1 else "A45"
    tag = sys.argv[2] if len(sys.argv) > 2 else "gt"
    ws, tab = get_page_ws()
    c = CDP(ws)
    got = goto_addr(c, addr)
    print(f"goto {addr} -> {got!r}", flush=True)
    crop(c, f"{tag}_hdr.png", 0, 140, 46, 600, scale=2)
    c.close()


if __name__ == "__main__":
    main()
