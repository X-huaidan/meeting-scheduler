# -*- coding: utf-8 -*-
"""Locate the select-all corner button, select everything, then open the row menu."""
import base64
import json
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


def probe(c, pts):
    js = ("(function(pts){return pts.map(function(p){var e=document.elementsFromPoint(p[0],p[1]);"
          "return p+':'+(e||[]).slice(0,3).map(function(x){try{return x.tagName+'|'+"
          "(x.className&&x.className.toString?x.className.toString().slice(0,60):'');}catch(E){return '?';}}).join(' >> ');});})"
          "(%s)" % json.dumps(pts))
    return c.eval(js)


def rclick(c, x, y):
    mouse_move(c, x, y)
    time.sleep(0.2)
    mouse_down(c, x, y, "right", 1)
    time.sleep(0.12)
    mouse_up(c, x, y, "right", 1)
    time.sleep(1.0)


ws, tab = get_page_ws()
c = CDP(ws)
print("tab:", tab.get("title"), flush=True)
key(c, "Escape", "Escape", 27)
time.sleep(0.4)

print(json.dumps(probe(c, [[18, 145], [18, 135], [30, 150], [12, 145], [18, 155]]),
                 ensure_ascii=False, indent=1), flush=True)
crop(c, OUT + r"\c_corner.png", 0, 120, 60, 60, 6)

# select all via the corner button
click(c, 18, 145)
time.sleep(0.6)
crop(c, OUT + r"\c_sel_all.png", 0, 92, 46, 645, 2)

# open the menu from a cell inside the selection (does it offer 取消隐藏行?)
rclick(c, 620, 380)
crop(c, OUT + r"\c_menu_cell.png", 0, 92, 520, 645, 1.6)
print("shot c_menu_cell.png", flush=True)

c.close()
