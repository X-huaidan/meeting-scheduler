# -*- coding: utf-8 -*-
"""Unhide every hidden row in the meeting sheet.

Recipe (the only reliable one found):
  * grid + row headers are <canvas> -> keyboard shortcuts (Alt+Shift+9) never land
  * the row-header right-click menu IS DOM
    (`div.dui-menu.context-menu_contextmenu__*`) -> locate 取消隐藏行 exactly
  * "取消隐藏行" only appears when the selected whole-row range *spans* the hidden
    rows, so select (first_visible_above .. first_visible_below) with
    click + shift-click **inside one viewport** (scrolling in between breaks the
    shift-extend anchor).

Loop: scan the visible rows (click each row-header y, read the name box), find a
hidden band whose two neighbours are both on screen, unhide it, re-scan.

Usage: python weekly_unhide.py [--report]
"""
import json
import os
import sys
import time

sys.path.insert(0, os.path.dirname(__file__))
from cdp import get_page_ws, CDP                                     # noqa: E402
from sheet_ui import click, key, key_up, mouse_move, mouse_down, mouse_up, SHIFT   # noqa: E402

ROW_HEADER_X = 18
BAR = "document.querySelector('.bar-label') ? document.querySelector('.bar-label').value : ''"

FIND_UNHIDE = """
(() => {
  const root = document.querySelector('.context-menu_contextmenu__2Aa6v')
            || document.querySelector('[class*="contextmenu"]');
  if (!root) return {err: 'no context menu'};
  const rr = root.getBoundingClientRect();
  const hits = [];
  // The visible label of each row-menu entry is not exposed as text, but the
  // shortcut hint is: Ctrl+Alt+9 = 隐藏行, Alt+Shift+9 = 取消隐藏行 (one row below).
  for (const e of root.querySelectorAll('*')) {
    const t = (e.textContent || '').trim();
    if (t !== 'Alt+Shift+9') continue;
    const r = e.getBoundingClientRect();
    if (r.width <= 0 || r.height <= 0) continue;
    let li = e, chain = [];
    for (let i = 0; i < 5 && li.parentElement; i++) {
      li = li.parentElement;
      if (li.getBoundingClientRect().width >= rr.width * 0.8) break;
    }
    const lr = li.getBoundingClientRect();
    hits.push({x: Math.round(rr.x + rr.width / 2),
               y: Math.round(r.y + r.height / 2),
               liY: Math.round(lr.y), liH: Math.round(lr.height),
               cls: String(li.className).slice(0, 90),
               disabled: /disabled/i.test(String(li.className))});
  }
  return {hits: hits, menu: [Math.round(rr.x), Math.round(rr.y), Math.round(rr.width), Math.round(rr.height)]};
})()
"""


def parse_row(v):
    if not isinstance(v, str) or not v:
        return -1
    v = v.replace("$", "")
    if ":" in v:
        v = v.split(":")[0]
    d = "".join(ch for ch in v if ch.isdigit())
    return int(d) if d else -1


def wheel(c, dy, x=500, y=400):
    c.send("Input.dispatchMouseEvent", {"type": "mouseWheel", "x": x, "y": y,
                                        "deltaX": 0, "deltaY": dy, "button": "none"})
    time.sleep(0.3)


def fast_click(c, x, y):
    """Lean click for scanning (no sleeps between events, just round trips)."""
    c.send("Input.dispatchMouseEvent", {"type": "mouseMoved", "x": x, "y": y, "button": "none"})
    c.send("Input.dispatchMouseEvent", {"type": "mousePressed", "x": x, "y": y,
                                        "button": "left", "clickCount": 1})
    c.send("Input.dispatchMouseEvent", {"type": "mouseReleased", "x": x, "y": y,
                                        "button": "left", "clickCount": 1})
    time.sleep(0.03)


def row_at(c, y):
    fast_click(c, ROW_HEADER_X, y)
    return parse_row(c.eval(BAR))


def scan(c, lo=185, hi=645, step=6):
    """Map {row: y} for the current view. Retries if the view scrolled mid-scan."""
    vis = {}
    for attempt in range(3):
        start = row_at(c, 200)
        vis = {}
        for y in range(lo, hi, step):
            r = row_at(c, y)
            if r > 0 and r not in vis:
                vis[r] = y
        end = row_at(c, 200)
        if start == end and start > 0:
            return vis
        print(f"     (unstable scan {start}->{end}, retry)", flush=True)
    return vis


def bands_of(vis):
    rows = sorted(vis)
    return [(a + 1, b - 1) for a, b in zip(rows, rows[1:]) if b - a > 1]


def shift_click(c, x, y):
    key(c, "Shift", "ShiftLeft", 16, SHIFT)
    time.sleep(0.05)
    mouse_move(c, x, y)
    time.sleep(0.05)
    mouse_down(c, x, y, "left", 1, SHIFT)
    time.sleep(0.05)
    mouse_up(c, x, y, "left", 1, SHIFT)
    time.sleep(0.05)
    key_up(c, "Shift", "ShiftLeft", 16, 0)
    time.sleep(0.4)


def right_click(c, x, y):
    mouse_move(c, x, y)
    time.sleep(0.15)
    mouse_down(c, x, y, "right", 1)
    time.sleep(0.12)
    mouse_up(c, x, y, "right", 1)
    time.sleep(1.1)


def to_top(c):
    for _ in range(25):
        wheel(c, -900)
    time.sleep(0.4)


def unhide(c, y_first, y_last):
    """Select rows spanning the band and click 取消隐藏行. Returns True on success."""
    click(c, ROW_HEADER_X, y_first)
    time.sleep(0.45)
    shift_click(c, ROW_HEADER_X, y_last)
    sel = c.eval(BAR)
    right_click(c, ROW_HEADER_X, y_last)
    info = c.eval(FIND_UNHIDE)
    hits = (info or {}).get("hits") if isinstance(info, dict) else None
    if not hits:
        print(f"     ! no 取消隐藏行 (sel={sel!r} menu={(info or {}).get('menu')})", flush=True)
        key(c, "Escape", "Escape", 27)
        time.sleep(0.3)
        return False
    t = hits[0]
    click(c, t["x"], t["y"])
    time.sleep(1.6)
    print(f"     ok sel={sel!r} clicked ({t['x']},{t['y']}) disabled={t['disabled']} "
          f"li=[{t['liY']},{t['liH']}] cls={t['cls']}", flush=True)
    return True


def main():
    report_only = "--report" in sys.argv
    ws, tab = get_page_ws()
    if not ws:
        print("NO_TAB")
        return 1
    print("tab:", tab.get("title"), flush=True)
    c = CDP(ws)
    key(c, "Escape", "Escape", 27)
    time.sleep(0.4)

    seen_bands = set()
    failed = set()
    to_top(c)

    for rnd in range(20):
        vis = scan(c)
        bs = [b for b in bands_of(vis) if b[0] > 2]
        for b in bs:
            seen_bands.add(b)
        print(f"[{rnd:02d}] rows {min(vis) if vis else '-'}..{max(vis) if vis else '-'} "
              f"bands={bs}", flush=True)
        if report_only:
            wheel(c, 420)
            continue
        act = [b for b in bs if (b[0] - 1) in vis and (b[1] + 1) in vis and b not in failed]
        if act:
            b = act[0]
            print(f"     unhiding {b[0]}..{b[1]}", flush=True)
            ok = unhide(c, vis[b[0] - 1], vis[b[1] + 1])
            if not ok:
                failed.add(b)
            continue
        if [b for b in bs if b not in failed]:
            wheel(c, 150)
            continue
        if vis and max(vis) >= 60:
            print("reached the end of the week table", flush=True)
            break
        wheel(c, 420)

    if report_only:
        print("bands seen:", sorted(seen_bands), flush=True)
        c.close()
        return 0

    # ---------- verification sweep ----------
    key(c, "Escape", "Escape", 27)
    time.sleep(0.3)
    to_top(c)
    allvis = {}
    for _ in range(10):
        allvis.update(scan(c))
        wheel(c, 420)
    print("all rows seen:", sorted(allvis), flush=True)
    print("REMAINING HIDDEN BANDS:", bands_of(allvis), flush=True)
    c.close()
    return 0


if __name__ == "__main__":
    sys.exit(main())
