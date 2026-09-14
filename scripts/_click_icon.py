# -*- coding: utf-8 -*-
"""Click one ▲/▼ glyph and report what changed."""
import base64
import sys
import time

sys.path.insert(0, ".")
from cdp import get_page_ws, CDP
from sheet_ui import click
from _goto import goto_addr
from _icon_pos import crop_raw, runs_of, STRIP_X, STRIP_Y, STRIP_W, STRIP_H, SCALE
from PIL import Image


def report(c, tag):
    raw = crop_raw(c, STRIP_X, STRIP_Y, STRIP_W, STRIP_H, SCALE)
    p = f"{tag}_strip.png"
    open(p, "wb").write(raw)
    img = Image.open(p)
    rx = img.size[0] / STRIP_W
    ry = img.size[1] / STRIP_H
    res = []
    for a, b, xa, xb in runs_of(img):
        res.append((((xa + xb) / 2) / rx, STRIP_Y + ((a + b) / 2) / ry))
    return res


def main():
    addr = sys.argv[1]
    x = float(sys.argv[2])
    y = float(sys.argv[3])
    tag = sys.argv[4] if len(sys.argv) > 4 else "ci"

    ws, tab = get_page_ws()
    c = CDP(ws)
    print("goto", addr, "->", repr(goto_addr(c, addr)), flush=True)

    before = report(c, f"{tag}_before")
    print(f"glyphs before ({len(before)}):", flush=True)
    for gx, gy in before:
        print(f"   ({gx:5.1f},{gy:6.1f})", flush=True)

    print(f"\nclicking ({x},{y}) ...", flush=True)
    click(c, x, y)
    time.sleep(1.3)

    after = report(c, f"{tag}_after")
    print(f"glyphs after ({len(after)}):", flush=True)
    for gx, gy in after:
        print(f"   ({gx:5.1f},{gy:6.1f})", flush=True)

    crop_raw(c, 0, 140, 60, 600, 2)
    raw = crop_raw(c, 0, 140, 60, 600, 2)
    open(f"{tag}_after_hdr.png", "wb").write(raw)
    print(f"\nwrote {tag}_after_hdr.png", flush=True)
    c.close()


if __name__ == "__main__":
    main()
