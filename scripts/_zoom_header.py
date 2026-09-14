# -*- coding: utf-8 -*-
"""Capture a magnified crop of the row-header column to locate the ▼ icons.

Page.captureScreenshot supports clip {x,y,width,height,scale}, so we can zoom
into the header column without any image library.

Usage: python _zoom_header.py <anchor_cell> <tag>
"""
import base64
import os
import sys
import time

sys.path.insert(0, os.path.dirname(__file__))
from cdp import get_page_ws, CDP  # noqa: E402
from sheet_ui import CTRL, click, key, key_up, chord  # noqa: E402

NAME_BOX_X = 30
NAME_BOX_Y = 111


def goto(c, addr):
    click(c, NAME_BOX_X, NAME_BOX_Y)
    time.sleep(0.3)
    chord(c, "a", "KeyA", 65, CTRL)
    time.sleep(0.1)
    key(c, "Delete", "Delete", 46, 0)
    key_up(c, "Delete", "Delete", 46, 0)
    time.sleep(0.15)
    c.send("Input.insertText", {"text": addr})
    time.sleep(0.25)
    key(c, "Enter", "Enter", 13, 0)
    key_up(c, "Enter", "Enter", 13, 0)
    time.sleep(0.7)


def crop(c, path, x, y, w, h, scale=3):
    r = c.send("Page.captureScreenshot", {
        "format": "png",
        "clip": {"x": x, "y": y, "width": w, "height": h, "scale": scale},
    })
    data = (r or {}).get("result", {}).get("data")
    if not data:
        print("crop failed:", r)
        return None
    open(path, "wb").write(base64.b64decode(data))
    return path


def main():
    anchor = sys.argv[1] if len(sys.argv) > 1 else "A3"
    tag = sys.argv[2] if len(sys.argv) > 2 else "a3"

    ws, tab = get_page_ws()
    if not ws:
        print("NO_TAB")
        return 1
    print("Driving:", tab["title"], flush=True)
    c = CDP(ws)
    out = os.path.dirname(__file__)

    goto(c, anchor)
    p = os.path.join(out, f"zoom_{tag}.png")
    crop(c, p, 0, 100, 70, 640, scale=3)
    print("saved", os.path.basename(p), flush=True)

    c.close()
    return 0


if __name__ == "__main__":
    sys.exit(main())
