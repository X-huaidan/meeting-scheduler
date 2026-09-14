# -*- coding: utf-8 -*-
"""With the whole sheet selected, right-click a row header and capture the menu."""
import base64
import sys
import time

sys.path.insert(0, r"C:\Users\changan\.workbuddy\skills\meeting-scheduler\scripts")
from cdp import get_page_ws, CDP                    # noqa: E402
from sheet_ui import click, key, mouse_move, mouse_down, mouse_up   # noqa: E402

OUT = r"C:\Users\changan\.workbuddy\skills\meeting-scheduler\scripts"


def crop(c, path, x, y, w, h, scale=3):
    r = c.send("Page.captureScreenshot", {
        "format": "png",
        "clip": {"x": x, "y": y, "width": w, "height": h, "scale": scale}})
    d = (r or {}).get("result", {}).get("data")
    if not d:
        return None
    open(path, "wb").write(base64.b64decode(d))
    return path


def rclick(c, x, y):
    mouse_move(c, x, y)
    time.sleep(0.2)
    mouse_down(c, x, y, "right", 1)
    time.sleep(0.12)
    mouse_up(c, x, y, "right", 1)
    time.sleep(1.1)


ws, tab = get_page_ws()
c = CDP(ws)
print("tab:", tab.get("title"), flush=True)
key(c, "Escape", "Escape", 27)
time.sleep(0.4)

# re-select all (previous run left everything selected, but be safe)
click(c, 18, 145)
time.sleep(0.6)

rclick(c, 18, 300)
crop(c, OUT + r"\d_hdr_menu.png", 0, 92, 520, 645, 1.6)
print("d_hdr_menu.png", flush=True)

c.close()
