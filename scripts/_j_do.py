# -*- coding: utf-8 -*-
"""Job: run a sequence of row visibility operations, verifying after each one.

Ops are given as tokens:
    U13-68   unhide rows 13..68   (select the band, Alt+Shift+9)
    H18-24   hide   rows 18..24   (select the band, Ctrl+Alt+9)

Every op is followed by a full re-probe of the visible row list, so the script
reports exactly which rows ended up hidden -- and because each op re-reads the
sheet, a dropped keystroke is visible immediately instead of silently
corrupting the layout.

Usage: python _j_do.py "U13-68" "H16-16" ...

The scan window defaults to rows 2..90 and can be overridden with the env vars
SHEET_LO / SHEET_HI -- the sheet now runs past row 83, so a hard-coded 70 would
silently ignore the weekend rows.
"""
import os
import sys

sys.path.insert(0, __file__.rsplit("\\", 1)[0])
from _boot import connect, snap                     # noqa: E402
from _kb import extend_down, hide_rows, select_row, unhide_rows  # noqa: E402
from _rowsx import goto_row, hidden_in, visible_rows  # noqa: E402

LO = int(os.environ.get("SHEET_LO", "2"))
HI = int(os.environ.get("SHEET_HI", "90"))


def parse(tok):
    kind = tok[0].upper()
    a, b = tok[1:].split("-")
    return kind, int(a), int(b)


def main():
    ops = sys.argv[1:]
    c, tab = connect()

    for i, tok in enumerate(ops):
        kind, a, b = parse(tok)
        vis = visible_rows(c, HI)
        if kind == "U":
            # start at a and sweep far enough to surely cover b
            goto_row(c, a, vis)
            select_row(c)
            extent = (b - a) + 30
            extend_down(c, extent)
            print(f"[{i}] unhide {a}..{b}: anchored at {a}, swept +{extent}", flush=True)
            unhide_rows(c)
        else:
            goto_row(c, a, vis)
            select_row(c)
            extend_down(c, b - a)
            print(f"[{i}] hide {a}..{b}: anchored at {a}, swept +{b - a}", flush=True)
            hide_rows(c)
        snap(c, f"do_{i}_{kind}{a}_{b}.png")
        vis2 = visible_rows(c, HI)
        print("     hidden now:", hidden_in(vis2, LO, HI), flush=True)

    snap(c, "do_final.png")
    print("FINAL hidden:", hidden_in(visible_rows(c, HI), LO, HI), flush=True)
    c.close()


if __name__ == "__main__":
    main()
