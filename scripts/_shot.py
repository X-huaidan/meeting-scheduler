# -*- coding: utf-8 -*-
"""Screenshot helper that works around two CDP traps (2026-09-14).

  1. Input events are *dropped* when the tab is not the foreground tab, so a
     click looks like it "did nothing".  Always `Page.bringToFront` first.
  2. Right after `Page.reload` the sheet has **no active cell**
     (`document.querySelector('.bar-label').value` is ''), so every
     keyboard-driven helper (visible_rows / goto_row / to_top) reads garbage.
     Click the grid once to re-activate a cell before using the keyboard.

Usage:
    from _shot import connect_ready, shot
    c, tab = connect_ready()          # connects + activates a cell
    shot(c, r"D:\\out\\top.png")
    shot(c, r"D:\\out\\zoom.png", clip=(0, 80, 1536, 430), scale=1.6)
"""
import base64
import os
import sys
import time

_HERE = os.path.dirname(os.path.abspath(__file__))
if _HERE not in sys.path:
    sys.path.insert(0, _HERE)

import _boot  # noqa: E402
import _kb    # noqa: E402


def click_grid(c, x=300, y=300):
    """Click a cell in the grid. bringToFront is mandatory (see trap 1)."""
    try:
        c.send("Page.bringToFront")
    except Exception:
        pass
    time.sleep(0.4)
    for t in ("mouseMoved", "mousePressed", "mouseReleased"):
        c.send("Input.dispatchMouseEvent", {
            "type": t, "x": x, "y": y, "button": "left", "clickCount": 1,
            "buttons": 0 if t == "mouseMoved" else 1, "pointerType": "mouse"})
        time.sleep(0.06)
    time.sleep(1.5)


def activate(c, tries=4):
    """Make sure an active cell exists (trap 2)."""
    if _kb.active(c):
        return True
    for _ in range(tries):
        click_grid(c)
        if _kb.active(c):
            return True
    return False


def connect_ready(wait_page=25, settle=2.5, top=True):
    """Connect, guarantee an active cell, and optionally jump to A2."""
    c, tab = _boot.connect(wait_page=wait_page, settle=settle)
    activate(c)
    if top:
        _kb.to_top(c)
        time.sleep(0.8)
    return c, tab


def shot(c, path, clip=None, scale=1, tries=6):
    """Screenshot with retries (capture intermittently times out)."""
    params = {"format": "png"}
    if clip:
        params["clip"] = {"x": clip[0], "y": clip[1], "width": clip[2],
                          "height": clip[3], "scale": scale}
    r = None
    for _ in range(tries):
        r = c.send("Page.captureScreenshot", params)
        d = (r or {}).get("result", {}).get("data")
        if d:
            os.makedirs(os.path.dirname(path), exist_ok=True)
            open(path, "wb").write(base64.b64decode(d))
            print("saved", path, os.path.getsize(path), flush=True)
            return path
        time.sleep(1.5)
    raise RuntimeError("screenshot failed: %s" % (r,))


if __name__ == "__main__":
    c, tab = connect_ready()
    out = sys.argv[1] if len(sys.argv) > 1 else "shot.png"
    shot(c, out)
