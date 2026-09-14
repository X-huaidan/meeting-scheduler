# -*- coding: utf-8 -*-
"""Probe several right-click positions to find one that actually opens the
row context menu for the R40:R46 selection.

After each right-click we screenshot; Escape closes any menu before the next try.
"""
import os
import sys
import time

sys.path.insert(0, os.path.dirname(__file__))
from cdp import get_page_ws, CDP  # noqa: E402
from sheet_ui import CTRL, SHIFT, click, key, key_up, snap, chord, mouse_move, mouse_down, mouse_up  # noqa: E402

NAME_BOX_X = 30
NAME_BOX_Y = 111
ROW_HEADER_X = 18

CANDIDATES = [
    (18, 318, "hdr_r40"),
    (18, 340, "hdr_r46"),
    (400, 300, "cell_in_sel"),
    (200, 330, "cell2"),
]


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


def shift_click(c, x, y):
    key(c, "Shift", "ShiftLeft", 16, SHIFT, raw=True)
    time.sleep(0.05)
    mouse_move(c, x, y)
    time.sleep(0.05)
    mouse_down(c, x, y, "left", 1, SHIFT)
    time.sleep(0.05)
    mouse_up(c, x, y, "left", 1, SHIFT)
    time.sleep(0.05)
    key_up(c, "Shift", "ShiftLeft", 16, 0)
    time.sleep(0.35)


def esc(c):
    key(c, "Escape", "Escape", 27, 0)
    key_up(c, "Escape", "Escape", 27, 0)
    time.sleep(0.4)


def main():
    ws, tab = get_page_ws()
    if not ws:
        print("NO_TAB")
        return 1
    print("Driving:", tab["title"], flush=True)
    c = CDP(ws)
    out = os.path.dirname(__file__)

    goto(c, "A47")

    for x, y, tag in CANDIDATES:
        # re-establish the row range selection each time
        click(c, ROW_HEADER_X, 316)
        time.sleep(0.4)
        shift_click(c, ROW_HEADER_X, 334)
        time.sleep(0.3)

        mouse_move(c, x, y)
        time.sleep(0.15)
        mouse_down(c, x, y, "right", 1)
        time.sleep(0.12)
        mouse_up(c, x, y, "right", 1)
        time.sleep(1.1)
        snap(c, os.path.join(out, f"rc_{tag}.png"))
        print(f"right-clicked ({x},{y}) -> rc_{tag}.png", flush=True)
        esc(c)

    c.close()
    return 0


if __name__ == "__main__":
    sys.exit(main())
