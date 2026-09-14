# -*- coding: utf-8 -*-
"""Jump to the bottom of the sheet and crop the row-header strip."""
import base64
import sys
import time

sys.path.insert(0, ".")
from cdp import get_page_ws, CDP
from sheet_ui import chord, click, CTRL
from _grid_calib import nb, go_home

TAG = sys.argv[1] if len(sys.argv) > 1 else "b"
DELTA = int(sys.argv[2]) if len(sys.argv) > 2 else 0   # wheel delta after Ctrl+End


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


def wheel(c, dy, x=700, y=400):
    c.send("Input.dispatchMouseEvent",
           {"type": "mouseWheel", "x": x, "y": y, "deltaX": 0, "deltaY": dy})
    time.sleep(0.4)


def main():
    ws, tab = get_page_ws()
    c = CDP(ws)
    click(c, 300, 400)
    time.sleep(0.2)
    chord(c, "End", "End", 35, CTRL)
    time.sleep(0.9)
    print("after Ctrl+End, namebox =", nb(c), flush=True)
    if DELTA:
        wheel(c, DELTA)
        print("after wheel, namebox =", nb(c), flush=True)
    crop(c, f"{TAG}_hdr.png", 0, 140, 46, 600, scale=2)
    crop(c, f"{TAG}_full.png", 0, 100, 1536, 640, scale=1)
    print(f"wrote {TAG}_hdr.png / {TAG}_full.png", flush=True)
    c.close()


if __name__ == "__main__":
    main()
