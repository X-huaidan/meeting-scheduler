# -*- coding: utf-8 -*-
"""Row navigation/selection driven by keystrokes, using the visible-row list.

`_kb.active()` returns the name box contents = the active cell. Walking down from
A2 enumerates the *visible* rows (arrows skip hidden ones), which both tells us
the current hidden ranges and lets us compute exactly how many presses are
needed to reach a target row -- no guesswork, no overshoot.
"""
import re

from _kb import (CTRL, SHIFT, ALT, active, combo, down, hide_rows,  # noqa: F401
                 select_row, to_top, unhide_rows, extend_down)


def row_of(bar):
    if not bar:
        return None
    m = re.search(r"(\d+)$", str(bar))
    return int(m.group(1)) if m else None


def visible_rows(c, upto=70, limit=160):
    """Visible row numbers from A2 downwards, stopping once >= upto."""
    to_top(c)
    rows = [row_of(active(c))]
    for _ in range(limit):
        down(c, 1)
        r = row_of(active(c))
        if r is None or r == rows[-1]:
            break
        rows.append(r)
        if r >= upto:
            break
    return rows


def hidden_in(vis, lo=2, hi=70):
    have = set(vis)
    return [r for r in range(lo, hi + 1) if r not in have]


def goto_row(c, row, vis=None):
    """Move the active cell to `row`. Raises if it cannot land exactly there."""
    if vis is None:
        vis = visible_rows(c, row + 6)
    before = [r for r in vis if r < row]
    to_top(c)
    if before:
        down(c, len(before))
    got = row_of(active(c))
    guard = 0
    while got != row and guard < 12:
        if got is None:
            raise RuntimeError("lost active cell")
        if got < row:
            down(c, 1)
        else:
            combo(c, "ArrowUp", "ArrowUp", 38, 0, pause=0.05)
        got = row_of(active(c))
        guard += 1
    if got != row:
        raise RuntimeError("goto_row(%d) stuck at %s" % (row, got))
    return got


def select_from(c, a):
    """Move to row a and select the whole row."""
    goto_row(c, a)
    select_row(c)
    return row_of(active(c))
