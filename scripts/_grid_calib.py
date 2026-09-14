# -*- coding: utf-8 -*-
"""Calibrate grid geometry: find CSS coords of a given cell address."""
import re
import sys
import time

sys.path.insert(0, ".")
from cdp import get_page_ws, CDP
from sheet_ui import snap, click, chord, CTRL, SHIFT, key, key_up

BAR = r"""
(() => {
  const sels = ['#all-grid-input', 'input.bar-label', '.bar-label input',
                '.bar-label', '[class*="nameBox"] input', '[class*="name-box"] input'];
  for (const s of sels) {
    const e = document.querySelector(s);
    if (!e) continue;
    const v = (e.value !== undefined && e.value !== null) ? e.value : (e.textContent || '');
    if (v && String(v).trim()) return String(v).trim();
  }
  // fallback: scan a bounded set of inputs
  const ins = document.querySelectorAll('input');
  for (const e of ins) {
    const r = e.getBoundingClientRect();
    if (r.width > 20 && r.width < 200 && r.height > 10 && r.height < 40 && r.y < 200) {
      if (e.value && /^[A-Z]+\d+/i.test(e.value)) return e.value;
    }
  }
  return '';
})()
"""

CELL_RE = re.compile(r"([A-Z]+)(\d+)")


def nb(c):
    for _ in range(6):
        v = c.eval(BAR)
        if v:
            return v
        time.sleep(0.1)
    return ""


def parse(v):
    m = CELL_RE.search(v.replace(" ", ""))
    if not m:
        return None
    col = 0
    for ch in m.group(1):
        col = col * 26 + (ord(ch) - 64)
    return (col, int(m.group(2)))


def go_home(c):
    click(c, 300, 400)
    time.sleep(0.2)
    chord(c, "Home", "Home", 36, CTRL)
    time.sleep(0.8)


def main():
    ws, tab = get_page_ws()
    c = CDP(ws)
    print("tab:", tab["title"], flush=True)

    go_home(c)
    print("after home, namebox =", nb(c), flush=True)
    snap(c, "g_home.png")

    # --- scan columns along the top data row area ---
    # find a y that is inside the grid: probe a few y values at x=300
    print("\n-- probe y at x=300 --", flush=True)
    for y in (150, 170, 190, 210, 230):
        click(c, 300, y)
        print(f"  (300,{y}) -> {nb(c)}", flush=True)

    print("\n-- probe x along a fixed y --", flush=True)
    y0 = 200
    for x in range(40, 900, 40):
        click(c, x, y0)
        print(f"  ({x},{y0}) -> {nb(c)}", flush=True)

    c.close()


if __name__ == "__main__":
    main()
