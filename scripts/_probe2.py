# -*- coding: utf-8 -*-
"""Probe row numbers at the glyph y-positions (short timeouts, live output)."""
import sys
import time

sys.path.insert(0, ".")
from cdp import get_page_ws, CDP
from sheet_ui import click
from _grid_calib import nb, parse
from _goto import goto_addr

ROWX = 26


def main():
    ys = []
    for a in sys.argv[1:]:
        if "-" in a:
            lo, hi, st = (int(v) for v in a.replace(":", "-").split("-"))
            ys += list(range(lo, hi + 1, st))
        else:
            ys.append(int(a))

    ws, tab = get_page_ws()
    c = CDP(ws)
    c.ws.settimeout(15)
    print("goto A45 ->", repr(goto_addr(c, "A45")), flush=True)

    for y in ys:
        t0 = time.time()
        click(c, ROWX, y)
        v = nb(c)
        p = parse(v)
        print(f"  y={y:4d} -> {v!r:12s} row={p[1] if p else '?':>4}  "
              f"({time.time()-t0:.2f}s)", flush=True)
    c.close()


if __name__ == "__main__":
    main()
