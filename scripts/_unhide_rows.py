# -*- coding: utf-8 -*-
"""One-shot: unhide all hidden rows in R3:R60 using the Name Box.

Why name box instead of clicking row headers
-------------------------------------------
- Row-header y coordinates depend on row height/zoom; estimating them is
  fragile (e.g. R60 ≈ 1706px is far below the viewport).
- Name box always works: click (30, 111), type "A3:A60", press Enter.
  This selects every cell from A3 to A60 inclusive, which **includes**
  any hidden rows in between, satisfying Tencent Docs' "select a range
  containing hidden rows" prerequisite for "取消隐藏行 Alt+Shift+9".

Strategy
--------
1. Connect via CDP to the 孟总会议行程表 tab (NOT 空白表格).
2. Click the Name Box, type `A3:A60`, press Enter.
3. Press Alt+Shift+9 → expands every hidden row in the selected range.
4. Press it a second time for safety (no-op if nothing left to unhide).
5. Screenshot before/after, then read the final sheet state via MCP to
   confirm R3..R60 row numbers are contiguous (no gaps).
"""
import os
import sys
import time

sys.path.insert(0, os.path.dirname(__file__))
from cdp import get_page_ws, CDP  # noqa: E402
from sheet_ui import (  # noqa: E402
    CTRL, ALT, SHIFT, click, key, key_up, snap, chord,
    mouse_move, mouse_down, mouse_up,
)

NAME_BOX_X = 30
NAME_BOX_Y = 111


def select_via_name_box(c, addr: str):
    """Click the name box, type a cell range, press Enter."""
    click(c, NAME_BOX_X, NAME_BOX_Y)
    time.sleep(0.3)
    # Clear the current name-box text with Ctrl+A, Delete.
    chord(c, "a", "KeyA", 65, CTRL)
    time.sleep(0.1)
    key(c, "Delete", "Delete", 46, 0)
    key_up(c, "Delete", "Delete", 46, 0)
    time.sleep(0.15)
    # Type the new address.
    c.send("Input.insertText", {"text": addr})
    time.sleep(0.2)
    key(c, "Enter", "Enter", 13, 0)
    key_up(c, "Enter", "Enter", 13, 0)
    time.sleep(0.5)


def unhide_via_shortcut(c):
    """Alt+Shift+9 — Tencent Docs '取消隐藏行' shortcut."""
    chord(c, "9", "Digit9", 57, ALT | SHIFT)


def main():
    ws, tab = get_page_ws()
    if not ws:
        print("NO_TAB")
        return 1
    print("Driving:", tab["title"], "|", tab["url"][:80])
    c = CDP(ws)

    out_dir = os.path.dirname(__file__)
    snap(c, os.path.join(out_dir, "before_unhide.png"))
    print("saved before_unhide.png")

    select_via_name_box(c, "A3:A60")
    snap(c, os.path.join(out_dir, "after_select_r3_r60.png"))
    print("saved after_select_r3_r60.png")

    unhide_via_shortcut(c)
    time.sleep(1.2)
    snap(c, os.path.join(out_dir, "after_unhide1.png"))
    print("saved after_unhide1.png")

    # Second press for safety — no-op if nothing is hidden.
    unhide_via_shortcut(c)
    time.sleep(0.8)
    snap(c, os.path.join(out_dir, "after_unhide2.png"))
    print("saved after_unhide2.png")

    c.close()
    return 0


if __name__ == "__main__":
    sys.exit(main())
