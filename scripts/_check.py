# -*- coding: utf-8 -*-
"""Layout sanity check: list hidden rows and verify must-stay-visible rows.

The lunch-break separator rows must NEVER be hidden (rule A.8.9 / B.8.7), so
this script takes their row numbers and proves they are still visible -- using
the visible-row enumeration (ArrowDown skips hidden rows), not a screenshot.

Usage:
    python _check.py 6 18 32 46 57        # row numbers that must be visible
    python _check.py                      # just print the hidden set

Scan window defaults to rows 2..90; override with env vars SHEET_LO / SHEET_HI.
"""
import os
import sys

sys.path.insert(0, __file__.rsplit("\\", 1)[0])
from _boot import connect, snap                       # noqa: E402
from _rowsx import hidden_in, visible_rows             # noqa: E402

LO = int(os.environ.get("SHEET_LO", "2"))
HI = int(os.environ.get("SHEET_HI", "90"))


def main():
    must = []
    for a in sys.argv[1:]:
        a = a.strip().strip(',')
        if a:
            must.append(int(a))

    c, tab = connect()
    vis = visible_rows(c, HI)
    hidden = hidden_in(vis, LO, HI)

    print("visible rows:", len(vis))
    print("hidden      :", hidden)

    bad = []
    for r in must:
        ok = r not in hidden
        if not ok:
            bad.append(r)
        print("  must-visible R%-3d -> %s" % (r, "ok" if ok else "HIDDEN!"))

    if must:
        print("RESULT:", ("PROBLEM, hidden but must be visible: %s" % bad) if bad else "OK")
    snap(c, "check.png")
    c.close()
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main())
