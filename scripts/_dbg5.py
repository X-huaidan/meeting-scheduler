# -*- coding: utf-8 -*-
"""选中 A3:A60 后用 Alt+Shift+9 取消隐藏行"""
import os
import sys
import time

sys.path.insert(0, r"C:\Users\changan\.workbuddy\skills\meeting-scheduler\scripts")
from cdp import CDP, get_page_ws  # noqa
import sheet_ui as ui  # noqa

OUT = r"D:\WorkBuddy\2026-09-11-08-46-35\outputs"


def log(m):
    print(m, flush=True)


def namebox(c, text):
    ui.click(c, 35, 104)
    time.sleep(0.4)
    ui.chord(c, "a", "KeyA", 65, ui.CTRL)
    time.sleep(0.3)
    c.send("Input.insertText", {"text": text})
    time.sleep(0.3)
    ui.key(c, "Enter", "Enter", 13)
    ui.key_up(c, "Enter", "Enter", 13)
    time.sleep(0.9)


def main():
    ws, tab = get_page_ws("docs.qq.com")
    c = CDP(ws)
    c.ws.settimeout(20)
    log("connected")

    # 关菜单
    ui.key(c, "Escape", "Escape", 27)
    ui.key_up(c, "Escape", "Escape", 27)
    time.sleep(0.4)
    ui.click(c, 700, 400)
    time.sleep(0.4)
    ui.go_home(c)
    time.sleep(0.8)

    # 选中 A3:A60
    namebox(c, "A3:A60")
    ui.snap(c, os.path.join(OUT, "e1_sel.png"))
    log("selected A3:A60")

    # Alt+Shift+9
    ui.chord(c, "9", "Digit9", 57, ui.ALT | ui.SHIFT)
    time.sleep(1.5)
    ui.snap(c, os.path.join(OUT, "e2_after.png"))
    log("pressed Alt+Shift+9")

    c.close()
    os._exit(0)


if __name__ == "__main__":
    main()