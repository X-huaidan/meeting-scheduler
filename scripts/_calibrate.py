# -*- coding: utf-8 -*-
"""Calibrate: click down the grid column and read the name box to map y -> row.

Also reports the hidden rows (they occupy 0px, so consecutive clicks land on
the same row number).
"""
import sys
import time

sys.path.insert(0, r"C:\Users\changan\.workbuddy\skills\meeting-scheduler\scripts")
from cdp import get_page_ws, CDP                   # noqa: E402
from sheet_ui import click, key               # noqa: E402

READ = ("(function(){var e=document.querySelector('.bar-label');"
        "return e? (e.value!==undefined? e.value : e.textContent) : 'NO_BARLABEL';})()")


def wheel(c, dy, x=600, y=400):
    c.send("Input.dispatchMouseEvent", {
        "type": "mouseWheel", "x": x, "y": y,
        "deltaX": 0, "deltaY": dy, "button": "none"})
    time.sleep(0.35)


ws, tab = get_page_ws()
c = CDP(ws)
print("tab:", tab.get("title"), flush=True)

key(c, "Escape", "Escape", 27)
time.sleep(0.3)
click(c, 600, 400)
time.sleep(0.3)

for _ in range(20):
    wheel(c, -900)
print("=== TOP ===", flush=True)
prev = None
for y in range(100, 735, 12):
    click(c, 600, y)
    v = c.eval(READ)
    if v != prev:
        print(f"  y={y:4d}  {v}", flush=True)
        prev = v

for _ in range(25):
    wheel(c, 900)
print("=== BOTTOM ===", flush=True)
prev = None
for y in range(100, 735, 12):
    click(c, 600, y)
    v = c.eval(READ)
    if v != prev:
        print(f"  y={y:4d}  {v}", flush=True)
        prev = v

c.close()
