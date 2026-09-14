# -*- coding: utf-8 -*-
"""Minimal CDP client to run JS / dispatch input in the user's already-open Chrome tab.

Usage:
    python cdp.py "<js expression>"

Requires Chrome started with --remote-debugging-port=9222 and websocket-client installed.
Key trick: suppress_origin=True avoids the 403 Origin check.
"""
import json
import sys
import urllib.request

import websocket


def get_page_ws(target_url_substr="docs.qq.com", exclude_substr=None):
    """Find the target page and return its websocket URL.

    Prefers an exact URL-substring match. When several pages match (e.g. the
    user also has a blank template sheet open), skips blank/template pages and
    blank-titled tabs so we never drive the wrong document.
    """
    if exclude_substr is None:
        exclude_substr = "is_blank_or_template=blank"
    data = json.loads(urllib.request.urlopen("http://127.0.0.1:9222/json", timeout=5).read())
    pages = [t for t in data if t.get("type") == "page" and t.get("webSocketDebuggerUrl")]
    matches = [t for t in pages if target_url_substr in t.get("url", "")]
    if not matches:
        return None, None
    # Prefer non-blank documents
    good = [t for t in matches
            if exclude_substr not in t.get("url", "")
            and "空白" not in t.get("title", "")
            and t.get("title", "").strip() not in ("", "新标签页", "New Tab")]
    chosen = (good or matches)[0]
    return chosen["webSocketDebuggerUrl"], chosen


class CDP:
    def __init__(self, ws_url):
        self.ws = websocket.create_connection(
            ws_url, timeout=120, suppress_origin=True, origin=None
        )
        self._id = 0

    def send(self, method, params=None):
        self._id += 1
        mid = self._id
        self.ws.send(json.dumps({"id": mid, "method": method, "params": params or {}}))
        while True:
            try:
                msg = json.loads(self.ws.recv())
            except Exception as e:
                return {"error": str(e), "id": mid}
            if msg.get("id") == mid:
                return msg

    def eval(self, expr, await_promise=False):
        r = self.send("Runtime.evaluate", {
            "expression": expr,
            "returnByValue": True,
            "awaitPromise": await_promise,
        })
        res = r.get("result", {})
        if "exceptionDetails" in res:
            return {"error": res["exceptionDetails"].get("text")}
        return res.get("result", {}).get("value")

    def close(self):
        try:
            self.ws.close()
        except Exception:
            pass


def main():
    ws_url, tab = get_page_ws()
    if not ws_url:
        print("NO_TAB")
        return
    c = CDP(ws_url)
    expr = sys.argv[1] if len(sys.argv) > 1 else "1+1"
    print(json.dumps(c.eval(expr), ensure_ascii=False, default=str))
    c.close()


if __name__ == "__main__":
    main()
