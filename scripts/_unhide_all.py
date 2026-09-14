# -*- coding: utf-8 -*-
"""Unhide ALL hidden rows by selecting the entire sheet, then Alt+Shift+9.

Findings so far
---------------
- Selecting a plain cell range (A3:A60) only expanded ONE hidden block per
  press (R26..R29 got unhidden, R23/24 etc. stayed hidden). The selection is
  reset after the command, so a single press is not enough for multiple blocks.
- Shift+Space is NOT the "select whole row" shortcut in Tencent Docs.
- Therefore: select the entire sheet (Ctrl+A, possibly twice) so that EVERY
  hidden block is inside the selection, then fire Alt+Shift+9 a few times.

Also prints the CSS viewport size so future row-header clicks can be
calibrated against the screenshot's pixel size.
"""
import os
import sys
import time

sys.path.insert(0, os.path.dirname(__file__))
from cdp import get_page_ws, CDP  # noqa: E402
from sheet_ui import CTRL, SHIFT, ALT, click, key, key_up, snap, chord  # noqa: E402


def select_all(c, times=2):
    """Ctrl+A. First press selects the used range, second selects everything."""
    for _ in range(times):
        chord(c, "a", "KeyA", 65, CTRL)
        time.sleep(0.35)


def unhide(c):
    chord(c, "9", "Digit9", 57, ALT | SHIFT)


def main():
    ws, tab = get_page_ws()
    if not ws:
        print("NO_TAB")
        return 1
    print("Driving:", tab["title"], "|", tab["url"][:80])
    c = CDP(ws)

    # Report viewport size (for future coordinate calibration).
    layout = c.send("Page.getLayoutMetrics", {})
    try:
        vp = layout["result"]["cssLayoutViewport"]
        print(f"viewport: {vp['clientWidth']}x{vp['clientHeight']} (css px)")
    except Exception as e:
        print("layout metrics unavailable:", e)

    out = os.path.dirname(__file__)

    click(c, 200, 200)          # focus the grid
    time.sleep(0.3)
    chord(c, "Home", "Home", 36, CTRL)
    time.sleep(0.4)
    select_all(c, times=2)
    snap(c, os.path.join(out, "sel_all.png"))
    print("saved sel_all.png")

    for i in range(4):
        unhide(c)
        time.sleep(1.0)
        snap(c, os.path.join(out, f"sel_all_unhide_{i}.png"))
        print(f"saved sel_all_unhide_{i}.png")

    c.close()
    return 0


if __name__ == "__main__":
    sys.exit(main())
