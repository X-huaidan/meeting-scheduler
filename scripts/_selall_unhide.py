# -*- coding: utf-8 -*-
"""Select a range spanning the whole table, then try Alt+Shift+9 (unhide).

Hypothesis: the earlier Alt+Shift+9 failures were because nothing was selected
that spanned hidden rows.
"""
import base64
import sys
import time

sys.path.insert(0, r"C:\Users\changan\.workbuddy\skills\meeting-scheduler\scripts")
from cdp import get_page_ws, CDP                                   # noqa: E402
from sheet_ui import (click, key, key_up, chord, snap, CTRL, ALT, SHIFT)  # noqa: E402

OUT = r"C:\Users\changan\.workbuddy\skills\meeting-scheduler\scripts"


def crop(c, path, x, y, w, h, scale=3):
    r = c.send("Page.captureScreenshot", {
        "format": "png",
        "clip": {"x": x, "y": y, "width": w, "height": h, "scale": scale},
    })
    d = (r or {}).get("result", {}).get("data")
    if not d:
        print("crop failed", r, flush=True)
        return None
    open(path, "wb").write(base64.b64decode(d))
    return path


def namebox(c, text):
    """Type text into the name box and press Enter (insertText avoids keymap issues)."""
    click(c, 30, 111)
    time.sleep(0.25)
    chord(c, "a", "KeyA", 65, CTRL)
    time.sleep(0.1)
    c.send("Input.insertText", {"text": text})
    time.sleep(0.25)
    key(c, "Return", "Enter", 13)
    time.sleep(0.9)


ws, tab = get_page_ws()
c = CDP(ws)
print("tab:", tab.get("title"), flush=True)

key(c, "Escape", "Escape", 27)
time.sleep(0.4)

namebox(c, "A3:I70")
crop(c, OUT + r"\u1_sel_head.png", 0, 92, 46, 645, 3)
snap(c, OUT + r"\u1_sel_full.png")
print("selected A3:I70", flush=True)

# try the shortcut
chord(c, "9", "Digit9", 57, ALT | SHIFT, raw=True)
time.sleep(1.2)
crop(c, OUT + r"\u2_after_key_head.png", 0, 92, 46, 645, 3)
snap(c, OUT + r"\u2_after_key_full.png")
print("sent Alt+Shift+9", flush=True)

# jump down to look for gaps near row 38..70
namebox(c, "A38")
crop(c, OUT + r"\u3_r38_head.png", 0, 92, 46, 645, 3)
print("u3_r38_head.png", flush=True)

c.close()
