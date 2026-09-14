# -*- coding: utf-8 -*-
"""Map row number -> CSS y in the current viewport (click the row header)."""
import sys
import time

sys.path.insert(0, ".")
from cdp import get_page_ws, CDP
from sheet_ui import click
from _grid_calib import nb, parse
from _goto import goto_addr

ROWX = 26


def main():
    addr = sys.argv[1] if len(sys.argv) > 1 else None
    lo = int(sys.argv[2]) if len(sys.argv) > 2 else 145
    hi = int(sys.argv[3]) if len(sys.argv) > 3 else 740
    step = int(sys.argv[4]) if len(sys.argv) > 4 else 6

    ws, tab = get_page_ws()
    c = CDP(ws)
    if addr:
        print("goto", addr, "->", repr(goto_addr(c, addr)), flush=True)

    found = {}
    for y in range(lo, hi, step):
        click(c, ROWX, y)
        p = parse(nb(c))
        if p:
            found.setdefault(p[1], []).append(y)

    print(f"\nrow -> y (clicked at x={ROWX})", flush=True)
    for r in sorted(found):
        ys = found[r]
        print(f"  {r:3d} : y {ys[0]:3d}..{ys[-1]:3d}  (n={len(ys)})", flush=True)
    c.close()


if __name__ == "__main__":
    main()
