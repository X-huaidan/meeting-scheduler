# -*- coding: utf-8 -*-
"""Keep the dedicated Chrome on port 9223 alive for the whole session.

Run this as a *background* task:
    python _hold.py
It launches Chrome (own profile, port 9223) if it is not already up, then
stays alive and re-launches it whenever the port dies. Ctrl-C stops both.

The point: the sandbox tears down child processes when a normal shell command
returns, so the browser must be owned by a long-lived holder process.
"""
import subprocess
import sys
import time

sys.path.insert(0, __file__.rsplit("\\", 1)[0])
import _boot  # noqa: E402


def launch():
    b = _boot._find_browser()
    if not b:
        print("NO BROWSER", flush=True)
        return False
    cmd = [b, f"--remote-debugging-port={_boot.PORT}",
           f"--user-data-dir={_boot.PROFILE}",
           "--no-first-run", "--no-default-browser-check", _boot.URL]
    print("launching:", " ".join(cmd), flush=True)
    subprocess.Popen(cmd, close_fds=True, creationflags=0x00000008 | 0x00000200)
    for _ in range(30):
        time.sleep(1.0)
        if _boot._version():
            print("up:", _boot._version(), flush=True)
            return True
    return False


def main():
    print("holder started, port", _boot.PORT, flush=True)
    while True:
        if not _boot._version():
            print("port dead -> relaunch", flush=True)
            launch()
        time.sleep(5)


if __name__ == "__main__":
    main()
