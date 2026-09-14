# -*- coding: utf-8 -*-
import base64
import os
import sys
import time

sys.path.insert(0, r"C:\Users\changan\.workbuddy\skills\meeting-scheduler\scripts")
from cdp import CDP, get_page_ws  # noqa


def log(m):
    print(m, flush=True)


def main():
    ws, tab = get_page_ws("docs.qq.com")
    c = CDP(ws)
    log("connected")
    c.ws.settimeout(15)
    t0 = time.time()
    try:
        r = c.send("Page.captureScreenshot", {"format": "png"})
        log(f"snap returned in {time.time()-t0:.1f}s, keys={list(r.keys())}")
        if "result" in r and "data" in r["result"]:
            open(r"D:\WorkBuddy\2026-09-11-08-46-35\outputs\dbg_snap.png", "wb").write(
                base64.b64decode(r["result"]["data"]))
            log("file written")
    except Exception as e:
        log(f"EXC: {type(e).__name__}: {e}")
    c.close()
    os._exit(0)


if __name__ == "__main__":
    main()