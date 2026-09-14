# -*- coding: utf-8 -*-
"""Anchor at the rows around each remaining hidden block and screenshot, so
row-header y coordinates can be measured for the next unhide pass.

Anchors chosen so the hidden block lands mid-viewport:
  A38 -> shows R40..R47 area (block R41-R45)
  A47 -> shows R48..R56 area (blocks R50, R52-R54)
  A56 -> shows R57..R66 area (block R59-R64)
"""
import os
import sys
import time

sys.path.insert(0, os.path.dirname(__file__))
from cdp import get_page_ws, CDP  # noqa: E402
from sheet_ui import CTRL, click, key, key_up, snap, chord  # noqa: E402

NAME_BOX_X = 30
NAME_BOX_Y = 111
ANCHORS = [38, 47, 56]


def goto(c, addr: str):
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
    ws, tab = get_page_ws()
    if not ws:
        print("NO_TAB")
        return 1
    print("Driving:", tab["title"])
    c = CDP(ws)
    out = os.path.dirname(__file__)
    for a in ANCHORS:
        goto(c, f"A{a}")
        p = os.path.join(out, f"an_{a}.png")
        snap(c, p)
        print("saved", os.path.basename(p))
    c.close()
    return 0


if __name__ == "__main__":
    sys.exit(main())
