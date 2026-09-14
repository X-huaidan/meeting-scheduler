# -*- coding: utf-8 -*-
"""Hover the 行高列宽 submenu inside the open context menu and capture it."""
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


ws, tab = get_page_ws()
c = CDP(ws)
print("tab:", tab.get("title"), flush=True)

# hover the 行高列宽 row of the still-open menu
for x in (120, 200, 245, 260):
    mouse_move(c, x, 328)
    time.sleep(0.7)
crop(c, OUT + r"\e_submenu.png", 0, 92, 620, 645, 1.5)
print("e_submenu.png", flush=True)

c.close()
