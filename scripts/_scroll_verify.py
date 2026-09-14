# -*- coding: utf-8 -*-
"""Scroll from the top of the sheet and capture a screenshot per screen,
so we can visually verify that R3..R60 has no skipped row numbers
(i.e. no hidden rows remain).

Saves scroll_00.png, scroll_01.png, ... into the scripts dir.
"""
import os
import sys
import time

sys.path.insert(0, os.path.dirname(__file__))
from cdp import get_page_ws, CDP  # noqa: E402
from sheet_ui import CTRL, click, chord, page_down, snap  # noqa: E402


def main():
    ws, tab = get_page_ws()
    if not ws:
        print("NO_TAB")
        return 1
    print("Driving:", tab["title"], "|", tab["url"][:80])
    c = CDP(ws)

    out = os.path.dirname(__file__)
    # Focus grid, then jump to A1.
    click(c, 200, 200)
    time.sleep(0.2)
    chord(c, "Home", "Home", 36, CTRL)
    time.sleep(0.5)

    for i in range(6):
        p = os.path.join(out, f"scroll_{i:02d}.png")
        snap(c, p)
        print("saved", os.path.basename(p))
        if i < 5:
            page_down(c, 1, pause=0.8)

    c.close()
    return 0


if __name__ == "__main__":
    sys.exit(main())
