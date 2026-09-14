# -*- coding: utf-8 -*-
"""Try two things at once:

1. Select whole rows by typing a ROW address ("22:25") into the Name Box —
   the standard spreadsheet way to select whole rows without row-header clicks.
2. Fire Alt+Shift+9 using rawKeyDown (which Tencent Docs' canvas actually
   listens to), instead of the plain keyDown that was silently ignored.

Also probes the DOM for the Name Box value so we can confirm the selection
without guessing from pixels.
"""
import os
import sys
import time

sys.path.insert(0, os.path.dirname(__file__))
from cdp import get_page_ws, CDP  # noqa: E402
from sheet_ui import CTRL, ALT, SHIFT, click, key, key_up, snap, chord  # noqa: E402

NAME_BOX_X = 30
NAME_BOX_Y = 111
PROBE_JS = (
    "[...document.querySelectorAll('input')].map(e=>({"
    "cls:(e.className||'').slice(0,40),val:e.value,ph:e.placeholder||''}))"
)


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

    print("inputs:", c.eval(PROBE_JS))

    # 1. select whole rows 22..25 via the name box
    goto(c, "22:25")
    print("after select:", c.eval(PROBE_JS))
    snap(c, os.path.join(out, "nt_1_sel_rows.png"))

    # 2. Alt+Shift+9 with rawKeyDown
    chord(c, "9", "Digit9", 57, ALT | SHIFT, raw=True)
    time.sleep(1.2)
    snap(c, os.path.join(out, "nt_2_after_unhide_raw.png"))

    # 3. again for safety
    chord(c, "9", "Digit9", 57, ALT | SHIFT, raw=True)
    time.sleep(0.8)
    snap(c, os.path.join(out, "nt_3_after_unhide_raw2.png"))
    print("done")

    c.close()
    return 0


if __name__ == "__main__":
    sys.exit(main())
