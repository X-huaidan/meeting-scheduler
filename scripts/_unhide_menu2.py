# -*- coding: utf-8 -*-
"""Select whole rows via row-header clicks (CSS px coordinates) and open the
right-click menu, then screenshot so we can locate the "取消隐藏行" item.

CSS px reference for this viewport (1536x737):
  screenshot is 1920x922 device px  ->  css = device / 1.25
  row-header column x = 18
  R22 header centre ~ y=218, R25 ~ y=287, R30 ~ y=352 (approx)

Usage: python _unhide_menu2.py <first_y> <last_y> <tag>
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
    tag = sys.argv[3] if len(sys.argv) > 3 else "r22_25"

    ws, tab = get_page_ws()
    if not ws:
        print("NO_TAB")
        return 1
    print("Driving:", tab["title"])
    c = CDP(ws)
    out = os.path.dirname(__file__)

    click(c, ROW_HEADER_X, first_y)
    time.sleep(0.45)
    snap(c, os.path.join(out, f"mm_{tag}_1_first.png"))
    print("saved", f"mm_{tag}_1_first.png")

    shift_click(c, ROW_HEADER_X, last_y)
    snap(c, os.path.join(out, f"mm_{tag}_2_range.png"))
    print("saved", f"mm_{tag}_2_range.png")

    right_click(c, ROW_HEADER_X, last_y)
    snap(c, os.path.join(out, f"mm_{tag}_3_menu.png"))
    print("saved", f"mm_{tag}_3_menu.png")

    c.close()
    return 0


if __name__ == "__main__":
    sys.exit(main())
