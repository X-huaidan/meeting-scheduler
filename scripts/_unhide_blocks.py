# -*- coding: utf-8 -*-
"""Batch unhide hidden rows via row-header right-click menu.

Each block is (first_y, last_y) — coordinates from the DOM-based row scanner.
The menu item "取消隐藏行" sits ~5px above the right-click y on this UI; we
reuse the (90, click_y-5) recipe that worked for R22..R30.

Usage:  python _unhide_blocks.py
"""
import os
import sys
import time

sys.path.insert(0, os.path.dirname(__file__))
from cdp import get_page_ws, CDP  # noqa: E402
from sheet_ui import SHIFT, click, key, key_up, snap, mouse_move, mouse_down, mouse_up  # noqa: E402

ROW_HEADER_X = 18
MENU_X = 90       # menu items sit around css x=84..170; x=90 is safe


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


def process_one(c, first_y, last_y, tag, out_dir):
    click(c, ROW_HEADER_X, first_y)
    time.sleep(0.45)
    shift_click(c, ROW_HEADER_X, last_y)
    snap(c, os.path.join(out_dir, f"b_{tag}_1_range.png"))

    right_click(c, ROW_HEADER_X, last_y)
    snap(c, os.path.join(out_dir, f"b_{tag}_2_menu.png"))

    click(c, MENU_X, last_y - 5)   # menu item just above the click point
    time.sleep(1.4)
    snap(c, os.path.join(out_dir, f"b_{tag}_3_after.png"))
    print(f"done block {tag}: first_y={first_y} last_y={last_y}")


def main():
    # Visible-block coordinates from the _scan_rows.py A47 result.
    # Process BOTTOM-UP: expanding a block shifts everything *below* it, so
    # handling lower blocks first keeps the coordinates of upper blocks valid.
    blocks = [
        # (first_y of visible row above, last_y of visible row below, tag)
        (526, 586, "r51_55"),    # R51..R55, contains hidden R52-R54
        (466, 526, "r49_51"),    # R49..R51, contains hidden R50
        (316, 334, "r40_46"),    # R40..R46, contains hidden R41-R45
    ]

    ws, tab = get_page_ws()
    if not ws:
        print("NO_TAB")
        return 1
    print("Driving:", tab["title"])
    c = CDP(ws)
    out = os.path.dirname(__file__)
    for fy, ly, tag in blocks:
        process_one(c, fy, ly, tag, out)
    c.close()
    return 0


if __name__ == "__main__":
    sys.exit(main())
