# -*- coding: utf-8 -*-
"""Scroll through the sheet and map visible row numbers to y coords."""
import sys
import time

sys.path.insert(0, ".")
from cdp import get_page_ws, CDP
from sheet_ui import snap, click, chord, CTRL
from _grid_calib import nb, parse, go_home

ROWX = 18


def wheel(c, dy, x=700, y=400):
    c.send("Input.dispatchMouseEvent",
           {"type": "mouseWheel", "x": x, "y": y, "deltaX": 0, "deltaY": dy})
    time.sleep(0.35)


def scan(c):
    """Return {row: y} for the current viewport."""
    out = {}
    for y in range(190, 700, 14):
        click(c, ROWX, y)
        p = parse(nb(c))
        if p and p[1] not in out:
            out[p[1]] = y
    return out


def main():
    ws, tab = get_page_ws()
    c = CDP(ws)
    go_home(c)

    seen = {}
    for i in range(10):
        vis = scan(c)
        for r, y in vis.items():
            seen.setdefault(r, y)
        rows = sorted(vis)
        print(f"[{i}] scroll={i} rows {rows[0] if rows else '-'}..{rows[-1] if rows else '-'} "
              f"n={len(rows)}", flush=True)
        if rows and rows[-1] >= 70:
            break
        # scroll by ~the height of the visible block we just scanned
        step = 480
        wheel(c, step)

    print("\n=== all visible row numbers ===", flush=True)
    allr = sorted(seen)
    print(allr, flush=True)

    miss = [r for r in range(1, max(allr) + 1) if r not in seen]
    print("missing (hidden or never probed):", miss, flush=True)
    c.close()


if __name__ == "__main__":
    main()
