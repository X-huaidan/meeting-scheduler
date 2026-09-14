# -*- coding: utf-8 -*-
"""Scroll through the sheet with the mouse wheel and capture the row-header strip
at each step, so we can see exactly where hidden rows still are."""
import base64
import sys
import time

sys.path.insert(0, r"C:\Users\changan\.workbuddy\skills\meeting-scheduler\scripts")
from cdp import get_page_ws, CDP                    # noqa: E402
from sheet_ui import click, key, key_up            # noqa: E402

OUT = r"C:\Users\changan\.workbuddy\skills\meeting-scheduler\scripts"


def crop(c, path, x, y, w, h, scale=2):
    r = c.send("Page.captureScreenshot", {
        "format": "png",
        "clip": {"x": x, "y": y, "width": w, "height": h, "scale": scale},
    })
    d = (r or {}).get("result", {}).get("data")
    if not d:
        return None
    open(path, "wb").write(base64.b64decode(d))
    return path


def wheel(c, dy, x=500, y=400):
    c.send("Input.dispatchMouseEvent", {
        "type": "mouseWheel", "x": x, "y": y,
        "deltaX": 0, "deltaY": dy, "button": "none"})
    time.sleep(0.55)


ws, tab = get_page_ws()
c = CDP(ws)
print("tab:", tab.get("title"), flush=True)

key(c, "Escape", "Escape", 27)
time.sleep(0.3)
click(c, 500, 400)            # focus the grid
time.sleep(0.3)

# scroll to the very top
for _ in range(15):
    wheel(c, -900)
print("at top", flush=True)

for i in range(9):
    p = crop(c, OUT + rf"\sm_{i:02d}.png", 0, 92, 46, 645, 2)
    print(f"sm_{i:02d}.png", flush=True)
    wheel(c, 320)

c.close()
