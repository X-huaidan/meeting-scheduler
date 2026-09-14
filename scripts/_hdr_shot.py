# -*- coding: utf-8 -*-
"""Crop + zoom the row-header strip so row numbers are readable."""
import base64
import sys
import time

sys.path.insert(0, ".")
from cdp import get_page_ws, CDP
from sheet_ui import chord, click, CTRL
from _grid_calib import nb, go_home
from _rowmap import wheel

SHOT = sys.argv[1] if len(sys.argv) > 1 else "h_00.png"


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
    ws, tab = get_page_ws()
    c = CDP(ws)
    go_home(c)
    print("home ->", nb(c), flush=True)
    crop(c, SHOT, 0, 140, 46, 600, scale=2)
    print("wrote", SHOT, flush=True)
    c.close()


if __name__ == "__main__":
    main()
