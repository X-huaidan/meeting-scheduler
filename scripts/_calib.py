# -*- coding: utf-8 -*-
"""Calibrate the CDP coordinate space against the screenshot pixel space.

Prints window.innerWidth/Height, devicePixelRatio, and the visual viewport so
we know whether screenshot pixels == CDP input pixels.
Then clicks a candidate row-header y and screenshots to confirm which row got
selected (the Name Box will show e.g. "A22" / "22:22" when a whole row is selected).
"""
import os
import sys
import time

sys.path.insert(0, os.path.dirname(__file__))
from cdp import get_page_ws, CDP  # noqa: E402
from sheet_ui import CTRL, click, key, key_up, snap, chord  # noqa: E402

NAME_BOX_X = 30
NAME_BOX_Y = 111


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
    c = CDP(ws)
    print("tab:", tab["title"])

    print("innerWidth/Height:", c.eval("window.innerWidth + 'x' + window.innerHeight"))
    print("devicePixelRatio:", c.eval("window.devicePixelRatio"))
    m = c.send("Page.getLayoutMetrics")
    try:
        r = m["result"]
        print("cssLayoutViewport:", r["cssLayoutViewport"])
        print("visualViewport:", {k: r["visualViewport"][k] for k in
                                  ("clientWidth", "clientHeight", "scale") if k in r["visualViewport"]})
    except Exception as e:
        print("metrics err", e, m)

    out = os.path.dirname(__file__)
    # Anchor at A22, then click row header at candidate y to see which row selects.
    goto(c, "A22")
    snap(c, os.path.join(out, "cal_anchor_a22.png"))
    print("saved cal_anchor_a22.png")

    for y in (204, 215, 230, 245, 258):
        click(c, 18, y)
        time.sleep(0.4)
        p = os.path.join(out, f"cal_click_y{y}.png")
        snap(c, p)
        print("saved", os.path.basename(p))

    c.close()
    return 0


if __name__ == "__main__":
    sys.exit(main())
