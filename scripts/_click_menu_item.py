# -*- coding: utf-8 -*-
"""Click the "取消隐藏行" item in the row-header context menu.

Menu geometry (CSS px, viewport 1536x737):
  The menu opens near the click point. In the captured menu screenshot the
  item "取消隐藏行" sits at display (x~60, y~203) on a 1092-wide render of a
  1920-wide device screenshot, so css = display * 1.4066 -> (~84, ~286).

This script just clicks a given css point and screenshots the result.

Usage: python _click_menu_item.py <x> <y> <tag>
"""
import os
import sys
import time

sys.path.insert(0, os.path.dirname(__file__))
from cdp import get_page_ws, CDP  # noqa: E402
from sheet_ui import click, snap  # noqa: E402


def main():
    x = int(sys.argv[1]) if len(sys.argv) > 1 else 90
    y = int(sys.argv[2]) if len(sys.argv) > 2 else 286
    tag = sys.argv[3] if len(sys.argv) > 3 else "post"

    ws, tab = get_page_ws()
    if not ws:
        print("NO_TAB")
        return 1
    print("Driving:", tab["title"])
    c = CDP(ws)
    out = os.path.dirname(__file__)

    click(c, x, y)
    time.sleep(1.3)
    snap(c, os.path.join(out, f"ci_{tag}.png"))
    print("saved", f"ci_{tag}.png")

    c.close()
    return 0


if __name__ == "__main__":
    sys.exit(main())
