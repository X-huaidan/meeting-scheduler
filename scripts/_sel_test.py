# -*- coding: utf-8 -*-
"""Which method actually extends a whole-row selection? Test 4 variants."""
import sys
import time

sys.path.insert(0, ".")
from cdp import get_page_ws, CDP
from sheet_ui import (click, key, key_up, mouse_move, mouse_down, mouse_up,
                      chord, CTRL, SHIFT)
from _grid_calib import nb

ROWX = 30


def reset(c):
    click(c, 300, 400)
    time.sleep(0.2)
    chord(c, "Home", "Home", 36, CTRL)
    time.sleep(0.8)


def v1(c, y1, y2):
    """Shift keyDown (keyDown) + mouse with modifiers."""
    click(c, ROWX, y1)
    time.sleep(0.3)
    a = nb(c)
    key(c, "Shift", "ShiftLeft", 16, SHIFT)
    mouse_move(c, ROWX, y2)
    time.sleep(0.05)
    mouse_down(c, ROWX, y2, "left", 1, SHIFT)
    mouse_up(c, ROWX, y2, "left", 1, SHIFT)
    key_up(c, "Shift", "ShiftLeft", 16, 0)
    time.sleep(0.45)
    return a, nb(c)


def v2(c, y1, y2):
    """Mouse-only modifiers (no Shift key event)."""
    click(c, ROWX, y1)
    time.sleep(0.3)
    a = nb(c)
    mouse_move(c, ROWX, y2)
    time.sleep(0.05)
    mouse_down(c, ROWX, y2, "left", 1, SHIFT)
    mouse_up(c, ROWX, y2, "left", 1, SHIFT)
    time.sleep(0.45)
    return a, nb(c)


def v3(c, y1, y2):
    """rawKeyDown Shift + mouse with modifiers."""
    click(c, ROWX, y1)
    time.sleep(0.3)
    a = nb(c)
    key(c, "Shift", "ShiftLeft", 16, SHIFT, raw=True)
    mouse_move(c, ROWX, y2)
    time.sleep(0.05)
    mouse_down(c, ROWX, y2, "left", 1, SHIFT)
    mouse_up(c, ROWX, y2, "left", 1, SHIFT)
    key_up(c, "Shift", "ShiftLeft", 16, 0)
    time.sleep(0.45)
    return a, nb(c)


def v4(c, y1, y2):
    """row click then Shift+Down keyboard extension."""
    click(c, ROWX, y1)
    time.sleep(0.3)
    a = nb(c)
    for _ in range(3):
        key(c, "Shift", "ShiftLeft", 16, SHIFT)
        key(c, "ArrowDown", "ArrowDown", 40, SHIFT)
        key_up(c, "ArrowDown", "ArrowDown", 40, SHIFT)
        key_up(c, "Shift", "ShiftLeft", 16, 0)
        time.sleep(0.25)
    return a, nb(c)


def main():
    variants = [("V1 shift-key", v1), ("V2 mouse-only", v2),
                ("V3 raw-shift", v3), ("V4 shift-down", v4)]
    ws, tab = get_page_ws()
    c = CDP(ws)
    c.ws.settimeout(20)
    nb(c)

    y1, y2 = 220, 280      # rows 3 and 4 under Ctrl+Home
    for name, fn in variants:
        reset(c)
        before = nb(c)
        a, b = fn(c, y1, y2)
        print(f"{name:14s} reset={before!r:8s} start={a!r:10s} after={b!r}", flush=True)
        key(c, "Escape", "Escape", 27)
        time.sleep(0.3)
    c.close()


if __name__ == "__main__":
    main()
