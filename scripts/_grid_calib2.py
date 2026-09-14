# -*- coding: utf-8 -*-
"""Scan columns F..J and rows 3.. down to build a complete coord map."""
import sys
import time

sys.path.insert(0, ".")
from cdp import get_page_ws, CDP
from sheet_ui import snap, click, chord, CTRL
from _grid_calib import nb, parse, go_home


def main():
    ws, tab = get_page_ws()
    c = CDP(ws)
    go_home(c)
    print("home ->", nb(c), flush=True)

    print("\n-- columns: probe x at y=200 --", flush=True)
    prev = None
    for x in range(860, 1540, 20):
        click(c, x, 200)
        v = nb(c)
        p = parse(v)
        col = p[0] if p else "?"
        if col != prev:
            print(f"  x={x:4d} -> {v}  (col {col})", flush=True)
            prev = col

    print("\n-- rows: probe y at x=180 (col C) --", flush=True)
    prev = None
    for y in range(185, 700, 8):
        click(c, 180, y)
        v = nb(c)
        p = parse(v)
        row = p[1] if p else "?"
        if row != prev:
            print(f"  y={y:4d} -> {v}  (row {row})", flush=True)
            prev = row

    snap(c, "g_calib2.png")
    c.close()


if __name__ == "__main__":
    main()
