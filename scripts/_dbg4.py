# -*- coding: utf-8 -*-
"""点 R3 行号 -> 滚轮滚到下方 -> 截图"""
import os
import sys
import time

sys.path.insert(0, r"C:\Users\changan\.workbuddy\skills\meeting-scheduler\scripts")
from cdp import CDP, get_page_ws  # noqa
import sheet_ui as ui  # noqa

OUT = r"D:\WorkBuddy\2026-09-11-08-46-35\outputs"


def log(m):
    print(m, flush=True)


def wheel(c, x, y, dy):
    c.send("Input.dispatchMouseEvent", {
        "type": "mouseWheel", "x": x, "y": y, "deltaX": 0, "deltaY": dy})


def main():
    ws, tab = get_page_ws("docs.qq.com")
    c = CDP(ws)
    c.ws.settimeout(20)
    log("connected")

    # 点击 R3 行号
    ui.click(c, 28, 228)
    time.sleep(0.8)
    log("clicked R3 header")
    ui.snap(c, os.path.join(OUT, "s1_r3.png"))
    log("snap1 ok")

    # 滚轮向下
    for i in range(5):
        wheel(c, 400, 400, 600)
        time.sleep(0.4)
    time.sleep(0.8)
    log("scrolled")
    ui.snap(c, os.path.join(OUT, "s2_scrolled.png"))
    log("snap2 ok")

    c.close()
    os._exit(0)


if __name__ == "__main__":
    main()