# -*- coding: utf-8 -*-
"""Pixel measurements on a sheet screenshot -- the reliable way to verify that a
formatting restore actually matched the original (2026-09-14).

Why pixels: `get_cell_style` is not exposed through the host's MCP tool set, the
sandbox's `getBackground()` returns a bogus '#000000', and eyeballing a
screenshot is unreliable for cut-off columns (column I sits half off-screen).

How to use it after a restore:
    python _pix.py colors  old.png            # row background colours
    python _pix.py colors  new.png
    python _pix.py align   old.png 186:214 384:456       # per-column text bbox
    python _pix.py align   new.png 186:214 384:456
    python _pix.py row     old.png 350        # colour across x at one y

Verification rule: for the SAME row+column, the text pixel interval `text[x0-x1]`
must be identical before and after.  Equal interval => alignment/font restored.

Traps this tool exists to avoid:
  * crop/window must be >=100px wider than the target, otherwise the window edge
    clips the real glyphs and the border line gets mistaken for text;
  * row 1 is FROZEN, so it renders at the same screen y at any scroll position --
    measuring it is always safe, but measuring body rows requires knowing the
    scroll position.
"""
import sys
from collections import Counter

from PIL import Image

GRID = [62, 77, 152, 294, 577, 1059, 1199, 1322]
NAMES = ["A", "B 日期", "C 时间", "D 会议名称", "E 会议议程",
         "F 地点", "G 参会领导", "H 参会人员"]


def _load(path):
    im = Image.open(path).convert("RGB")
    print("image", path, im.size)
    return im, im.load()


def _modal(px, x0, x1, y0, y1):
    c = Counter()
    for y in range(y0, y1):
        for x in range(x0, x1, 2):
            c[px[x, y]] += 1
    return c.most_common(1)[0][0]


def cmd_colors(path):
    """Collapse consecutive scanlines with the same modal background colour."""
    im, px = _load(path)
    W, H = im.size
    prev, start = None, 0
    for y in range(0, H):
        c = Counter()
        for x in range(90, min(1060, W), 2):
            c[px[x, y]] += 1
        mode = c.most_common(1)[0][0]
        if prev is None:
            prev, start = mode, y
            continue
        if mode != prev:
            if y - start >= 3:
                print("  y %4d-%4d h=%3d  #%02X%02X%02X"
                      % (start, y - 1, y - start, prev[0], prev[1], prev[2]))
            prev, start = mode, y
    if H - start >= 3:
        print("  y %4d-%4d h=%3d  #%02X%02X%02X"
              % (start, H - 1, H - start, prev[0], prev[1], prev[2]))


def _dist(a, b):
    return abs(a[0] - b[0]) + abs(a[1] - b[1]) + abs(a[2] - b[2])


def cmd_align(path, bands):
    """Per-column text bbox + left/right padding -> after the dominant bg."""
    im, px = _load(path)
    for arg in bands:
        y0, y1 = [int(v) for v in arg.split(":")]
        bg = _modal(px, 200, 1000, y0, y1)
        print("\n=== band y %d..%d  bg=(%d,%d,%d) ===" % (y0, y1, *bg))
        for i in range(len(GRID) - 1):
            xa, xb = GRID[i] + 3, GRID[i + 1] - 3
            cols = [x for x in range(xa, xb)
                    if any(_dist(px[x, y], bg) > 110 for y in range(y0, y1))]
            if not cols:
                print("  %-11s x[%4d-%4d]  no text" % (NAMES[i], xa, xb))
                continue
            lo, hi = cols[0], cols[-1]
            w = xb - xa
            left, right = lo - xa, xb - hi
            tag = "CENTER" if (left < 0.22 * w and right < 0.22 * w) else (
                "LEFT" if left <= right else "RIGHT")
            print("  %-11s x[%4d-%4d] text[%4d-%4d] Lpad=%3d Rpad=%3d -> %s"
                  % (NAMES[i], xa, xb, lo, hi, left, right, tag))


def cmd_row(path, y):
    """Colour runs across one scanline -- finds the horizontal extent of a fill."""
    im, px = _load(path)
    W = im.size[0]
    y = int(y)
    prev, start = None, 0
    for x in range(0, W):
        c = px[x, y]
        if prev is None:
            prev, start = c, x
            continue
        if max(abs(c[i] - prev[i]) for i in range(3)) > 18:
            if x - start >= 4:
                print("  x %4d-%4d (%3d)  #%02X%02X%02X"
                      % (start, x - 1, x - start, prev[0], prev[1], prev[2]))
            prev, start = c, x
    if W - start >= 4:
        print("  x %4d-%4d (%3d)  #%02X%02X%02X"
              % (start, W - 1, W - start, prev[0], prev[1], prev[2]))


if __name__ == "__main__":
    cmd = sys.argv[1]
    if cmd == "colors":
        cmd_colors(sys.argv[2])
    elif cmd == "align":
        cmd_align(sys.argv[2], sys.argv[3:])
    elif cmd == "row":
        cmd_row(sys.argv[2], sys.argv[3])
    else:
        print(__doc__)
