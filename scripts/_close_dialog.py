# -*- coding: utf-8 -*-
"""Close any modal dialog (e.g. the '拖拽，无法移动…' alert) and report state.

Tries, in order: click a visible 确定/OK button, then Escape.
"""
import os
import sys
import time

sys.path.insert(0, os.path.dirname(__file__))
from cdp import get_page_ws, CDP  # noqa: E402
from sheet_ui import key, key_up, snap  # noqa: E402

FIND_BTN = """
(() => {
  const cands = [...document.querySelectorAll('button, [class*=btn], [role=button], div')]
    .filter(e => {
      const t = (e.textContent || '').trim();
      if (t !== '确定' && t !== '确 定' && t !== 'OK') return false;
      const r = e.getBoundingClientRect();
      return r.width > 0 && r.height > 0 && r.width < 200 && r.height < 80;
    });
  if (!cands.length) return null;
  const r = cands[cands.length - 1].getBoundingClientRect();
  return {x: r.x + r.width / 2, y: r.y + r.height / 2};
})()
"""


def main():
    ws, tab = get_page_ws()
    if not ws:
        print("NO_TAB")
        return 1
    print("Driving:", tab["title"])
    c = CDP(ws)
    out = os.path.dirname(__file__)

    pos = c.eval(FIND_BTN)
    print("confirm button:", pos)
    if pos:
        from sheet_ui import click
        click(c, pos["x"], pos["y"])
        time.sleep(0.8)
    else:
        key(c, "Escape", "Escape", 27, 0)
        key_up(c, "Escape", "Escape", 27, 0)
        time.sleep(0.6)

    time.sleep(0.5)
    snap(c, os.path.join(out, "closed_dialog.png"))
    print("saved closed_dialog.png")
    c.close()
    return 0


if __name__ == "__main__":
    sys.exit(main())
