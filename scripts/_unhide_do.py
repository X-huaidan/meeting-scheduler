# -*- coding: utf-8 -*-
"""One-shot: select whole rows, right-click, then click "取消隐藏行".

Everything happens inside one CDP session so the context menu stays open
between the right-click and the item click.

Usage:
    python _unhide_do.py <first_y> <last_y> <menu_x> <menu_y> <tag>

Coordinates are CSS px (viewport 1536x737; device screenshot is 1920x922).
"""
import os
import sys
import time

sys.path.insert(0, os.path.dirname(__file__))
from cdp import get_page_ws, CDP  # noqa: E402
from sheet_ui import SHIFT, click, key, key_up, snap, mouse_move, mouse_down, mouse_up  # noqa: E402

ROW_HEADER_X = 18


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
    time.sleep(1.1)


def main():
    first_y = int(sys.argv[1]) if len(sys.argv) > 1 else 218
    last_y = int(sys.argv[2]) if len(sys.argv) > 2 else 287
    menu_x = int(sys.argv[3]) if len(sys.argv) > 3 else 90
    menu_y = int(sys.argv[4]) if len(sys.argv) > 4 else 286
    tag = sys.argv[5] if len(sys.argv) > 5 else "r22_25"

    ws, tab = get_page_ws()
    if not ws:
        print("NO_TAB")
        return 1
    print("Driving:", tab["title"])
    c = CDP(ws)
    out = os.path.dirname(__file__)

    click(c, ROW_HEADER_X, first_y)
    time.sleep(0.45)
    shift_click(c, ROW_HEADER_X, last_y)
    snap(c, os.path.join(out, f"d_{tag}_1_range.png"))

    right_click(c, ROW_HEADER_X, last_y)
    snap(c, os.path.join(out, f"d_{tag}_2_menu.png"))

    click(c, menu_x, menu_y)
    time.sleep(1.4)
    snap(c, os.path.join(out, f"d_{tag}_3_after.png"))
    print(f"saved d_{tag}_1_range.png / _2_menu.png / _3_after.png")

    c.close()
    return 0


if __name__ == "__main__":
    sys.exit(main())
