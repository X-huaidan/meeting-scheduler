# -*- coding: utf-8 -*-
"""Unhide remaining hidden rows by selecting WHOLE ROWS (not a cell range).

Why the previous attempt missed some rows
-----------------------------------------
Selecting `A3:A60` via the Name Box selects a *cell range*, which is NOT the
same as selecting whole rows. Tencent Docs' "取消隐藏行" acts on whole-row
selections; a plain cell range did not trigger it for every hidden block
(only some got expanded). The working recipe from the earlier session was a
whole-row selection (row header click + Shift+click another header).

Robust approach here
--------------------
1. Go to A3 via the Name Box.
2. Press Shift+Space  -> selects the whole row (R3).
3. Press Ctrl+Shift+Down -> extends the whole-row selection downward.
4. Press Alt+Shift+9 (取消隐藏行) twice for safety.
No y-coordinate guessing for row headers is needed.

Then screenshot the whole range and also dump the set of visible row numbers
by reading the row-header pixel column is overkill; we just screenshot.
"""
import os
import sys
import time

sys.path.insert(0, os.path.dirname(__file__))
from cdp import get_page_ws, CDP  # noqa: E402
from sheet_ui import (  # noqa: E402
    CTRL, SHIFT, ALT, click, key, key_up, snap, chord,
)

NAME_BOX_X = 30
NAME_BOX_Y = 111


def goto(c, addr: str):
    """Type an address into the Name Box and press Enter."""
    click(c, NAME_BOX_X, NAME_BOX_Y)
    time.sleep(0.3)
    chord(c, "a", "KeyA", 65, CTRL)          # select existing text
    time.sleep(0.1)
    key(c, "Delete", "Delete", 46, 0)
    key_up(c, "Delete", "Delete", 46, 0)
    time.sleep(0.15)
    c.send("Input.insertText", {"text": addr})
    time.sleep(0.2)
    key(c, "Enter", "Enter", 13, 0)
    key_up(c, "Enter", "Enter", 13, 0)
    time.sleep(0.4)


def shift_space(c):
    """Shift+Space -> select the whole current row."""
    key(c, "Shift", "ShiftLeft", 16, SHIFT)
    time.sleep(0.03)
    key(c, " ", "Space", 32, SHIFT)
    key_up(c, " ", "Space", 32, SHIFT)
    time.sleep(0.03)
    key_up(c, "Shift", "ShiftLeft", 16, 0)
    time.sleep(0.35)


def ctrl_shift_down(c):
    """Ctrl+Shift+Down -> extend selection down to the last row with data."""
    key(c, "Control", "ControlLeft", 17, CTRL)
    key(c, "Shift", "ShiftLeft", 16, CTRL | SHIFT)
    time.sleep(0.03)
    key(c, "ArrowDown", "ArrowDown", 40, CTRL | SHIFT)
    key_up(c, "ArrowDown", "ArrowDown", 40, CTRL | SHIFT)
    time.sleep(0.03)
    key_up(c, "Shift", "ShiftLeft", 16, CTRL)
    key_up(c, "Control", "ControlLeft", 17, 0)
    time.sleep(0.4)


def unhide(c):
    """Alt+Shift+9 -> 取消隐藏行."""
    chord(c, "9", "Digit9", 57, ALT | SHIFT)


def main():
    ws, tab = get_page_ws()
    if not ws:
        print("NO_TAB")
        return 1
    print("Driving:", tab["title"], "|", tab["url"][:80])
    c = CDP(ws)
    out = os.path.dirname(__file__)

    # Step 1-3: select whole rows R3..end
    goto(c, "A3")
    snap(c, os.path.join(out, "ur_0_at_a3.png"))
    shift_space(c)
    snap(c, os.path.join(out, "ur_1_row3_selected.png"))
    ctrl_shift_down(c)
    snap(c, os.path.join(out, "ur_2_extended.png"))

    # Step 4: unhide (twice for safety)
    unhide(c)
    time.sleep(1.2)
    snap(c, os.path.join(out, "ur_3_after_unhide.png"))
    unhide(c)
    time.sleep(0.8)
    snap(c, os.path.join(out, "ur_4_after_unhide2.png"))

    c.close()
    return 0


if __name__ == "__main__":
    sys.exit(main())
