# -*- coding: utf-8 -*-
"""调试：定位卡在哪一步"""
import os
import sys
import time

sys.path.insert(0, r"C:\Users\changan\.workbuddy\skills\meeting-scheduler\scripts")
from cdp import CDP, get_page_ws  # noqa
import sheet_ui as ui  # noqa


def log(msg):
    print(msg, flush=True)


def main():
    log("1. getting ws")
    ws, tab = get_page_ws("docs.qq.com")
    log(f"2. tab={tab['title']}")
    c = CDP(ws)
    log("3. connected")
    ui.click(c, 700, 400)
    log("4. clicked")
    c.close()
    log("5. closed")
    os._exit(0)


if __name__ == "__main__":
    main()