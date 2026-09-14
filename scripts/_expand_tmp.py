# -*- coding: utf-8 -*-
"""选中 R3 起整行范围并展开隐藏行"""
import os
import sys
import time

sys.path.insert(0, r"C:\Users\changan\.workbuddy\skills\meeting-scheduler\scripts")
from cdp import CDP, get_page_ws  # noqa
import sheet_ui as ui  # noqa

OUT = r"D:\WorkBuddy\2026-09-11-08-46-35\outputs"


def main():
    ws, tab = get_page_ws("docs.qq.com")
    c = CDP(ws)

    # 关掉可能存在的菜单
    ui.key(c, "Escape", "Escape", 27)
    ui.key_up(c, "Escape", "Escape", 27)
    time.sleep(0.5)
    ui.click(c, 700, 400)
    time.sleep(0.3)

    ui.go_home(c)
    time.sleep(0.8)

    # 点击 R3 行号
    ui.click(c, 28, 228)
    time.sleep(0.8)
    ui.snap(c, os.path.join(OUT, "step_r3.png"))

    # Shift+PageDown x N 扩展选区
    for i in range(3):
        ui.chord(c, "PageDown", "PageDown", 34, ui.SHIFT)
        time.sleep(0.9)
    ui.snap(c, os.path.join(OUT, "step_shiftpd.png"))

    c.close()
    os._exit(0)


if __name__ == "__main__":
    main()