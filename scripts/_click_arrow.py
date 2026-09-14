# -*- coding: utf-8 -*-
"""Click one point (intended: the ▼ row-group toggle) and screenshot the result.

Usage: python _click_arrow.py <x> <y> <tag> [anchor]
"""
import os
import sys
import time

sys.path.insert(0, os.path.dirname(__file__))
from cdp import get_page_ws, CDP  # noqa: E402
from sheet_ui import CTRL, click, key, key_up, snap, chord  # noqa: E402

NAME_BOX_X = 30
NAME_BOX_Y = 111


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


def main():
    x = int(sys.argv[1]) if len(sys.argv) > 1 else 10
    y = int(sys.argv[2]) if len(sys.argv) > 2 else 315
    tag = sys.argv[3] if len(sys.argv) > 3 else "t1"
    anchor = sys.argv[4] if len(sys.argv) > 4 else "A3"

    ws, tab = get_page_ws()
    if not ws:
        print("NO_TAB")
        return 1
    print("Driving:", tab["title"], flush=True)
    c = CDP(ws)
    out = os.path.dirname(__file__)

    goto(c, anchor)
    snap(c, os.path.join(out, f"ar_{tag}_before.png"))
    click(c, x, y)
    time.sleep(1.2)
    snap(c, os.path.join(out, f"ar_{tag}_after.png"))
    print(f"clicked ({x},{y}) -> ar_{tag}_after.png", flush=True)

    c.close()
    return 0


if __name__ == "__main__":
    sys.exit(main())
