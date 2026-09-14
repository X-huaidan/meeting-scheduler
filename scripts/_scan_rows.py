# -*- coding: utf-8 -*-
"""Scan the row-header column and report which row each y coordinate selects.

Reads the Name Box DOM value (class `.bar-label`, e.g. "A47") after each click,
so the mapping is exact rather than pixel-estimated.

Usage: python _scan_rows.py <anchor_cell>
"""
import os
import re
import sys
import time

sys.path.insert(0, os.path.dirname(__file__))
from cdp import get_page_ws, CDP  # noqa: E402
from sheet_ui import CTRL, click, key, key_up, chord  # noqa: E402

NAME_BOX_X = 30
NAME_BOX_Y = 111
ROW_HEADER_X = 18
PROBE = "document.querySelector('.bar-label').value"
ROW_RE = re.compile(r"A?(\d+)")

# work in *device* pixels: CDP input uses CSS px, but the screenshot is
# 1.25x. We only need relative ordering, so scan the CSS viewport height.
SCAN_TOP = 130
SCAN_BOTTOM = 730
STEP = 6


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


def probe_row(c) -> int:
    v = c.eval(PROBE)
    if not isinstance(v, str):
        return -1
    m = ROW_RE.search(v)
    return int(m.group(1)) if m else -1


def main():
    anchor = sys.argv[1] if len(sys.argv) > 1 else "A47"
    ws, tab = get_page_ws()
    if not ws:
        print("NO_TAB")
        return 1
    print("Driving:", tab["title"], "anchor:", anchor)
    c = CDP(ws)

    goto(c, anchor)
    print("scanning y from", SCAN_TOP, "to", SCAN_BOTTOM, "step", STEP)
    found = {}
    for y in range(SCAN_TOP, SCAN_BOTTOM + 1, STEP):
        click(c, ROW_HEADER_X, y)
        time.sleep(0.16)
        r = probe_row(c)
        found.setdefault(r, y)     # first y hitting a given row
        print(f"y={y:4d} -> row {r}")

    print("\n--- summary (row -> first y) ---")
    for r in sorted(found):
        if r > 0:
            print(f"row {r}: y={found[r]}")

    c.close()
    return 0


if __name__ == "__main__":
    sys.exit(main())
