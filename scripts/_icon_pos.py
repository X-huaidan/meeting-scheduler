# -*- coding: utf-8 -*-
"""Locate the collapse/expand (▲/▼) glyphs in the row-header gutter.

The glyphs live in the leftmost ~14 CSS px of the row header. We crop that
strip at high zoom and look for dark pixel runs -- one run per glyph.
"""
import base64
import sys
import time

sys.path.insert(0, ".")
from cdp import get_page_ws, CDP
from PIL import Image

from _goto import goto_addr

STRIP_X, STRIP_Y, STRIP_W, STRIP_H = 0, 140, 14, 600
SCALE = 4
THRESH = 170
MIN_W, MIN_H = 2, 3


def crop_raw(c, x, y, w, h, scale):
    r = c.send("Page.captureScreenshot", {
        "format": "png",
        "clip": {"x": x, "y": y, "width": w, "height": h, "scale": scale},
    })
    data = (r or {}).get("result", {}).get("data")
    if not data:
        raise RuntimeError(f"crop failed: {r}")
    return base64.b64decode(data)


def runs_of(img):
    """Dark-pixel runs (top->bottom) as (y0, y1, x0, x1) in image coords."""
    w, h = img.size
    px = img.convert("RGB").load()
    rows = []
    for y in range(h):
        xs = [x for x in range(w)
              if all(v < THRESH for v in px[x, y])]
        rows.append(xs)

    out, cur = [], None
    for y, xs in enumerate(rows):
        if len(xs) >= MIN_W:
            if cur is None:
                cur = [y, y, min(xs), max(xs)]
            else:
                cur[1] = y
                cur[2] = min(cur[2], min(xs))
                cur[3] = max(cur[3], max(xs))
        else:
            if cur and cur[1] - cur[0] >= MIN_H:
                out.append(tuple(cur))
            cur = None
    if cur and cur[1] - cur[0] >= MIN_H:
        out.append(tuple(cur))
    return out


def main():
    addr = sys.argv[1] if len(sys.argv) > 1 else None
    tag = sys.argv[2] if len(sys.argv) > 2 else "ic"
    ws, tab = get_page_ws()
    c = CDP(ws)
    if addr:
        print("goto", addr, "->", repr(goto_addr(c, addr)), flush=True)

    raw = crop_raw(c, STRIP_X, STRIP_Y, STRIP_W, STRIP_H, SCALE)
    open(f"{tag}_strip.png", "wb").write(raw)
    img = Image.open(f"{tag}_strip.png")
    rx = img.size[0] / STRIP_W          # actual px per CSS px (scale * dpr)
    ry = img.size[1] / STRIP_H
    print(f"strip image: {img.size}  ratio x={rx:.2f} y={ry:.2f}", flush=True)

    print("\n-- glyph runs (CSS coords) --", flush=True)
    for a, b, xa, xb in runs_of(img):
        cy = STRIP_Y + ((a + b) / 2) / ry
        cx = ((xa + xb) / 2) / rx
        print(f"  imgY {a:4d}..{b:4d}  CSS y {STRIP_Y + a/ry:7.1f}..{STRIP_Y + b/ry:7.1f}"
              f"  center=({cx:5.1f},{cy:6.1f})  h={(b-a)/ry:4.1f} w={(xb-xa)/rx:4.1f}",
              flush=True)
    c.close()



if __name__ == "__main__":
    main()
