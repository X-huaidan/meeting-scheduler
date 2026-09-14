# -*- coding: utf-8 -*-
"""Step 1 for block R40:R46 — select the whole rows, right-click, screenshot.

Also times each CDP primitive so we can see what is slow (screenshot? eval?).

Run with -u for unbuffered output.
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


def t(label, fn):
    t0 = time.time()
    r = fn()
    print(f"  {label}: {time.time()-t0:.2f}s", flush=True)
    return r


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


def right_click(c, x, y):
    mouse_move(c, x, y)
    time.sleep(0.15)
    mouse_down(c, x, y, "right", 1)
    time.sleep(0.12)
    mouse_up(c, x, y, "right", 1)
    time.sleep(1.0)


def main():
    ws, tab = get_page_ws()
    if not ws:
        print("NO_TAB")
        return 1
    print("Driving:", tab["title"], flush=True)
    c = CDP(ws)
    out = os.path.dirname(__file__)

    t("goto A47", lambda: goto(c, "A47"))
    t("probe row", lambda: c.eval("document.querySelector('.bar-label').value"))
    t("click R40", lambda: click(c, ROW_HEADER_X, 316))
    t("probe after click", lambda: c.eval("document.querySelector('.bar-label').value"))
    t("shift-click R46", lambda: shift_click(c, ROW_HEADER_X, 334))
    t("snap range", lambda: snap(c, os.path.join(out, "s1_range.png")))
    t("right-click", lambda: right_click(c, ROW_HEADER_X, 334))
    t("snap menu", lambda: snap(c, os.path.join(out, "s1_menu.png")))

    print("done", flush=True)
    c.close()
    return 0


if __name__ == "__main__":
    sys.exit(main())
