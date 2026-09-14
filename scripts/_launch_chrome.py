# -*- coding: utf-8 -*-
"""Launch a dedicated Chrome instance (own profile + debug port) on the sheet."""
import json
import os
import subprocess
import time
import urllib.request

# 跨设备：不要写死用户名，用当前用户的 USERPROFILE 展开
PROFILE = os.path.expandvars(r"%USERPROFILE%\.workbuddy\chrome-debug")
PORT = 9223
URL = "https://docs.qq.com/sheet/DT3Z4cGNQZmVpU2xV?tab=000001"

CANDIDATES = [
    r"C:\Program Files\Google\Chrome\Application\chrome.exe",
    r"C:\Program Files (x86)\Google\Chrome\Application\chrome.exe",
    os.path.expandvars(r"%LOCALAPPDATA%\Google\Chrome\Application\chrome.exe"),
    os.path.expandvars(r"%ProgramFiles%\Microsoft\Edge\Application\msedge.exe"),
]


def find_browser():
    for p in CANDIDATES:
        if p and os.path.exists(p):
            return p
    return None


def alive():
    try:
        d = json.loads(urllib.request.urlopen(
            f"http://127.0.0.1:{PORT}/json/version", timeout=3).read())
        return d.get("Browser")
    except Exception:
        return None


def main():
    b = find_browser()
    print("browser:", b, flush=True)
    if not b:
        print("NO BROWSER FOUND")
        return

    already = alive()
    if already:
        print("port already alive:", already, flush=True)
    else:
        os.makedirs(PROFILE, exist_ok=True)
        cmd = [b, f"--remote-debugging-port={PORT}", f"--user-data-dir={PROFILE}",
               "--no-first-run", "--no-default-browser-check", URL]
        print("launching:", " ".join(cmd), flush=True)
        # DETACHED_PROCESS | CREATE_NEW_PROCESS_GROUP: keep the browser alive
        # after this launcher exits (and out of any job object the harness uses).
        flags = 0x00000008 | 0x00000200  # DETACHED_PROCESS | CREATE_NEW_PROCESS_GROUP
        subprocess.Popen(cmd, close_fds=True, creationflags=flags)

    for i in range(20):
        time.sleep(1.5)
        v = alive()
        if v:
            print(f"debug port {PORT} alive after {(i + 1) * 1.5:.0f}s ->", v, flush=True)
            break
    else:
        print("port never came up", flush=True)
        return

    time.sleep(4)
    tabs = json.loads(urllib.request.urlopen(f"http://127.0.0.1:{PORT}/json", timeout=5).read())
    for t in tabs:
        if t.get("type") == "page":
            print("  tab:", t.get("title", "")[:40], "|", t.get("url", "")[:80], flush=True)


if __name__ == "__main__":
    main()
