# -*- coding: utf-8 -*-
"""Right-click the row header at a FIXED point so the context menu always lands
in the same place, then capture zoomed shots of the row header + the menu."""
import base64
import sys
import time

sys.path.insert(0, r"C:\Users\changan\.workbuddy\skills\meeting-scheduler\scripts")
from cdp import get_page_ws, CDP                                   # noqa: E402
from sheet_ui import click, key, key_up, chord, mouse_move, mouse_down, mouse_up, CTRL   # noqa: E402

OUT = r"C:\Users\changan\.workbuddy\skills\meeting-scheduler\scripts"


def crop(c, path, x, y, w, h, scale=3):
    r = c.send("Page.captureScreenshot", {
        "format": "png",
        "clip": {"x": x, "y": y, "width": w, "height": h, "scale": scale},
    })
    d = (r or {}).get("result", {}).get("data")
    if not d:
        print("crop failed", r)
        return None
    open(path, "wb").write(base64.b64decode(d))
    return path


ws, tab = get_page_ws()
c = CDP(ws)
print("tab:", tab.get("title"), flush=True)

# deterministic scroll
click(c, 30, 111)
time.sleep(0.2)
chord(c, "a", "KeyA", 65, CTRL)
key(c, "3", "Digit3", 51, 0, text="3")
key(c, "Return", "Enter", 13)
time.sleep(0.9)
print("at A3", flush=True)

# make sure no menu is open
key(c, "Escape", "Escape", 27)
time.sleep(0.4)

crop(c, OUT + r"\z_before_head.png", 0, 92, 46, 645, 3)
print("z_before_head.png", flush=True)

# fixed right-click on row header
X, Y = 18, 300
mouse_move(c, X, Y)
time.sleep(0.2)
mouse_down(c, X, Y, "right", 1)
time.sleep(0.15)
mouse_up(c, X, Y, "right", 1)
time.sleep(1.0)

crop(c, OUT + r"\z_menu_full.png", 0, 92, 500, 645, 1.6)
print("z_menu_full.png", flush=True)

c.close()
