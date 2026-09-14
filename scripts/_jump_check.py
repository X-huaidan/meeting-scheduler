# -*- coding: utf-8 -*-
"""Jump to specific rows via the Name Box and screenshot each, to verify
whether the hidden rows have been unhidden.

Targets (1-based): 20, 40, 49, 58  — chosen so each screenshot shows the
hidden block that was supposed to be expanded right below the anchor row.
"""
import os
import sys
import time

sys.path.insert(0, os.path.dirname(__file__))
from cdp import get_page_ws, CDP  # noqa: E402
from sheet_ui import CTRL, click, key, key_up, snap, chord  # noqa: E402

NAME_BOX_X = 30
NAME_BOX_Y = 111
ANCHORS = [20, 22, 40, 49, 58, 65]


def goto(c, addr: str):
    click(c, NAME_BOX_X, NAME_BOX_Y)
    time.sleep(0.3)
    chord(c, "a", "KeyA", 65, CTRL)
    time.sleep(0.1)
    key(c, "Delete", "Delete", 46, 0)
    key_up(c, "Delete", "Delete", 46, 0)
    time.sleep(0.15)
    c.send("Input.insertText", {"text": addr})
    time.sleep(0.2)
    key(c, "Enter", "Enter", 13, 0)
    key_up(c, "Enter", "Enter", 13, 0)
    time.sleep(0.6)


def main():
    ws, tab = get_page_ws()
    if not ws:
        print("NO_TAB")
        return 1
    print("Driving:", tab["title"], "|", tab["url"][:80])
    c = CDP(ws)
    out = os.path.dirname(__file__)

    for a in ANCHORS:
        goto(c, f"A{a}")
        p = os.path.join(out, f"jump_{a}.png")
        snap(c, p)
        print("saved", os.path.basename(p))

    c.close()
    return 0


if __name__ == "__main__":
    sys.exit(main())
