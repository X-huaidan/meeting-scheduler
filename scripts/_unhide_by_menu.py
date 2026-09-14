# -*- coding: utf-8 -*-
"""Unhide hidden rows via the row-header right-click menu.

Recipe (verified in the earlier session for R14/R15):
  1. Click the row header of the first visible anchor row  -> selects that row.
  2. Shift+click the row header of the last visible anchor row -> extends to a
     whole-row range that *contains* the hidden rows in between.
  3. Right-click inside the selected row headers -> context menu appears with
     the item "取消隐藏行 <range>" (unhide rows) enabled.
  4. Click that menu item.

This script only performs steps 1-3 and then takes a screenshot so the menu
layout can be inspected/calibrated before clicking. The menu item's position
is reported as an offset guess.

Usage:
    python _unhide_by_menu.py <first_row_y> <last_row_y> <tag>
"""
import os
import sys
import time

sys.path.insert(0, os.path.dirname(__file__))
from cdp import get_page_ws, CDP  # noqa: E402
from sheet_ui import SHIFT, click, key, key_up, snap, mouse_move, mouse_down, mouse_up  # noqa: E402

ROW_HEADER_X = 18


def shift_click(c, x, y):
    key(c, "Shift", "ShiftLeft", 16, SHIFT)
    time.sleep(0.05)
    mouse_move(c, x, y)
    time.sleep(0.05)
    mouse_down(c, x, y, "left", 1, SHIFT)
    time.sleep(0.05)
    mouse_up(c, x, y, "left", 1, SHIFT)
    time.sleep(0.05)
    key_up(c, "Shift", "ShiftLeft", 16, 0)
    time.sleep(0.3)


def right_click(c, x, y):
    mouse_move(c, x, y)
    time.sleep(0.15)
    mouse_down(c, x, y, "right", 1)
    time.sleep(0.12)
    mouse_up(c, x, y, "right", 1)
    time.sleep(1.0)


def main():
    first_y = int(sys.argv[1]) if len(sys.argv) > 1 else 169
    last_y = int(sys.argv[2]) if len(sys.argv) > 2 else 245
    tag = sys.argv[3] if len(sys.argv) > 3 else "r22_25"

    ws, tab = get_page_ws()
    if not ws:
        print("NO_TAB")
        return 1
    print("Driving:", tab["title"])
    c = CDP(ws)
    out = os.path.dirname(__file__)

    # 1. select first row
    click(c, ROW_HEADER_X, first_y)
    time.sleep(0.4)
    snap(c, os.path.join(out, f"m_{tag}_1_first.png"))
    # 2. extend to last row
    shift_click(c, ROW_HEADER_X, last_y)
    snap(c, os.path.join(out, f"m_{tag}_2_range.png"))
    # 3. right click
    right_click(c, ROW_HEADER_X, last_y)
    snap(c, os.path.join(out, f"m_{tag}_3_menu.png"))
    print(f"saved m_{tag}_1_first.png / _2_range.png / _3_menu.png")

    c.close()
    return 0


if __name__ == "__main__":
    sys.exit(main())
