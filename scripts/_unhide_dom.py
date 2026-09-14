# -*- coding: utf-8 -*-
"""Unhide remaining hidden blocks using DOM-located context-menu items.

Why: guessing the menu item's y (last_y - 5) hit the wrong item and triggered
"拖拽，无法移动只包含合并单元格一部分的行". The context menu is DOM-rendered,
so we can locate the exact "取消隐藏行" element and click its centre.

Flow per block (bottom-up so upper coordinates stay valid):
  1. click first row header, Shift+click last row header
  2. right-click on the selected header
  3. JS: find the leaf element whose text is "取消隐藏行", get its rect
  4. click that point
  5. screenshot

Coordinates come from a fresh DOM scan (the page scrolled since the last one).
"""
import os
import sys
import time

sys.path.insert(0, os.path.dirname(__file__))
from cdp import get_page_ws, CDP  # noqa: E402
from sheet_ui import (  # noqa: E402
    CTRL, SHIFT, click, key, key_up, snap, chord, mouse_move, mouse_down, mouse_up,
)

NAME_BOX_X = 30
NAME_BOX_Y = 111
ROW_HEADER_X = 18

PROBE_ROW = "document.querySelector('.bar-label').value"
FIND_MENU_ITEM = """
(() => {
  const want = '取消隐藏行';
  const all = [...document.querySelectorAll('*')];
  const hits = [];
  for (const e of all) {
    if (e.children.length) continue;              // leaf only
    const t = (e.textContent || '').trim();
    if (!t.includes(want)) continue;
    const r = e.getBoundingClientRect();
    if (r.width > 0 && r.height > 0)
      hits.push({x: Math.round(r.x + r.width/2), y: Math.round(r.y + r.height/2),
                 t, w: Math.round(r.width), h: Math.round(r.height),
                 tag: e.tagName, cls: String(e.className||'').slice(0,50)});
  }
  return hits;
})()
"""


def goto(c, addr):
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


def probe_row(c):
    v = c.eval(PROBE_ROW)
    if not isinstance(v, str):
        return -1
    digits = "".join(ch for ch in v if ch.isdigit())
    return int(digits) if digits else -1


def scan(c, rows_needed, lo=140, hi=730, step=4):
    """Return {row: y} for the requested rows within the current scroll view."""
    found = {}
    for y in range(lo, hi + 1, step):
        click(c, ROW_HEADER_X, y)
        time.sleep(0.14)
        r = probe_row(c)
        if r in rows_needed and r not in found:
            found[r] = y
    return found


def shift_click(c, x, y):
    key(c, "Shift", "ShiftLeft", 16, SHIFT, raw=True)
    time.sleep(0.05)
    mouse_move(c, x, y)
    time.sleep(0.05)
    mouse_down(c, x, y, "left", 1, SHIFT)
    time.sleep(0.05)
    mouse_up(c, x, y, "left", 1, SHIFT)
    time.sleep(0.05)
    key_up(c, "Shift", "ShiftLeft", 16, 0)
    time.sleep(0.35)


def right_click(c, x, y):
    mouse_move(c, x, y)
    time.sleep(0.15)
    mouse_down(c, x, y, "right", 1)
    time.sleep(0.12)
    mouse_up(c, x, y, "right", 1)
    time.sleep(1.1)


def unhide_block(c, first_y, last_y, tag, out):
    click(c, ROW_HEADER_X, first_y)
    time.sleep(0.45)
    shift_click(c, ROW_HEADER_X, last_y)
    snap(c, os.path.join(out, f"x_{tag}_1_range.png"))

    right_click(c, ROW_HEADER_X, last_y)
    snap(c, os.path.join(out, f"x_{tag}_2_menu.png"))

    hits = c.eval(FIND_MENU_ITEM)
    print(f"[{tag}] menu item candidates:", hits)
    if not hits:
        print(f"[{tag}] !! could not locate 取消隐藏行 in DOM")
        return False
    t = hits[0]
    click(c, t["x"], t["y"])
    time.sleep(1.4)
    snap(c, os.path.join(out, f"x_{tag}_3_after.png"))
    print(f"[{tag}] clicked ({t['x']},{t['y']})")
    return True


def main():
    ws, tab = get_page_ws()
    if not ws:
        print("NO_TAB")
        return 1
    print("Driving:", tab["title"])
    c = CDP(ws)
    out = os.path.dirname(__file__)

    goto(c, "A47")
    needed = {40, 46, 49, 51, 55}
    coords = scan(c, needed)
    print("scan result:", coords)

    if not all(r in coords for r in needed):
        print("!! incomplete scan:", {r: coords.get(r) for r in needed})

    # bottom-up
    plan = []
    if 51 in coords and 55 in coords:
        plan.append((coords[51], coords[55], "r51_55"))
    if 49 in coords and 51 in coords:
        plan.append((coords[49], coords[51], "r49_51"))
    if 40 in coords and 46 in coords:
        plan.append((coords[40], coords[46], "r40_46"))

    for fy, ly, tag in plan:
        ok = unhide_block(c, fy, ly, tag, out)
        print(f"[{tag}] {'OK' if ok else 'FAILED'}")

    c.close()
    return 0


if __name__ == "__main__":
    sys.exit(main())
