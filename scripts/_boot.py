# -*- coding: utf-8 -*-
"""Ensure a dedicated Chrome is up on PORT and return a live CDP connection.

The sandbox tears down child processes when a shell command returns, so the
browser has to be (re)launched *inside* the same python process that drives it.
Call connect() at the start of every job script.
"""
import json
import os
import subprocess
import time
import urllib.request

# never let the corporate proxy swallow 127.0.0.1
os.environ.setdefault("no_proxy", "127.0.0.1,localhost")
os.environ.setdefault("NO_PROXY", "127.0.0.1,localhost")
for k in ("http_proxy", "HTTP_PROXY", "https_proxy", "HTTPS_PROXY", "all_proxy", "ALL_PROXY"):
    v = os.environ.get(k, "")
    if v and "127.0.0.1" not in v:
        os.environ["no_proxy"] = "127.0.0.1,localhost," + os.environ.get("no_proxy", "")

PORT = int(os.environ.get("CDP_PORT", "9223"))
# cdp.py reads CDP_PORT at *import* time, so pin it before importing.
os.environ["CDP_PORT"] = str(PORT)
PROFILE = r"C:\Users\changan\.workbuddy\chrome-debug"
URL = "https://docs.qq.com/sheet/DT3Z4cGNQZmVpU2xV?tab=000001"

CANDIDATES = [
    r"C:\Program Files\Google\Chrome\Application\chrome.exe",
    r"C:\Program Files (x86)\Google\Chrome\Application\chrome.exe",
    os.path.expandvars(r"%LOCALAPPDATA%\Google\Chrome\Application\chrome.exe"),
    os.path.expandvars(r"%ProgramFiles%\Microsoft\Edge\Application\msedge.exe"),
]

_HERE = os.path.dirname(os.path.abspath(__file__))
# Screenshots go here. Defaults to the scripts/ dir for backwards compatibility,
# but jobs should set SNAP_DIR to a workspace folder -- otherwise every run
# leaves PNGs inside the skill (they then get committed / bloat the skill).
SNAP_DIR = os.environ.get("SNAP_DIR") or _HERE
import sys  # noqa: E402
sys.path.insert(0, _HERE)
from cdp import get_page_ws, CDP  # noqa: E402


def _get(path, timeout=4):
    return json.loads(urllib.request.urlopen(
        f"http://127.0.0.1:{PORT}{path}", timeout=timeout).read())


def _version():
    try:
        return _get("/json/version").get("Browser")
    except Exception:
        return None


def _find_browser():
    for p in CANDIDATES:
        if p and os.path.exists(p):
            return p
    return None


def connect(wait_page=25, settle=2.5):
    """Return (cdp, tab). Launches Chrome in this process if the port is dead."""
    if not _version():
        b = _find_browser()
        if not b:
            raise RuntimeError("no chrome found")
        os.makedirs(PROFILE, exist_ok=True)
        cmd = [b, f"--remote-debugging-port={PORT}", f"--user-data-dir={PROFILE}",
               "--no-first-run", "--no-default-browser-check", URL]
        print("launching chrome ...", flush=True)
        subprocess.Popen(cmd, close_fds=True,
                         creationflags=0x00000008 | 0x00000200)
        for _ in range(30):
            time.sleep(1.0)
            if _version():
                break
        else:
            raise RuntimeError("debug port never came up")
    print("browser:", _version(), flush=True)
    time.sleep(settle)          # let the sheet finish loading
    for i in range(wait_page):
        ws, tab = get_page_ws()
        if i == 0:
            try:
                raw = _get("/json")
                print("  raw pages:", len(raw), flush=True)
                for t in raw:
                    print("   -", t.get("type"), t.get("url")[:60],
                          "ws=", bool(t.get("webSocketDebuggerUrl")), flush=True)
            except Exception as e:
                print("  raw list failed:", e, flush=True)
        if ws:
            print("tab:", tab.get("title"), "|", tab.get("url")[:70], flush=True)
            c = CDP(ws)
            c.ws.settimeout(40)
            return c, tab
        time.sleep(1.0)
    try:
        for t in _get("/json"):
            print("  TAB:", t.get("type"), "|", repr(t.get("title"))[:60],
                  "|", t.get("url")[:110], flush=True)
    except Exception as e:
        print("  (cannot list tabs:", e, ")", flush=True)
    raise RuntimeError("no docs.qq.com tab")


def reload_page(c, settle=5.0):
    """Hard-reset the page UI (clears stuck context menus / odd edit states)."""
    c.send("Page.reload", {"ignoreCache": False})
    time.sleep(settle)
    return c.eval("document.title")


def snap(c, name, tries=5, clip=None, scale=None):
    """Screenshot with retries -- capture intermittently times out right after a
    scroll (the renderer is busy), and a single lost frame is not an error."""
    import base64
    r = None
    for i in range(tries):
        params = {"format": "png"}
        if clip:
            params["clip"] = {"x": clip[0], "y": clip[1],
                              "width": clip[2], "height": clip[3], "scale": scale or 1}
        r = c.send("Page.captureScreenshot", params)
        d = (r or {}).get("result", {}).get("data")
        if d:
            os.makedirs(SNAP_DIR, exist_ok=True)
            p = os.path.join(SNAP_DIR, name)
            open(p, "wb").write(base64.b64decode(d))
            print("saved", p, os.path.getsize(p), "bytes", flush=True)
            return p
        time.sleep(1.2)
    print("FAILED", name, r, flush=True)
    raise RuntimeError("screenshot failed: %s" % (r,))
