# -*- coding: utf-8 -*-
"""Sheet UI helper: input events for Tencent Docs sheet via CDP.

Provides:
  snap(c, path)                      screenshot
  click(c, x, y)                     left click
  key(c, name, code, vk, mods, text) keyDown
  key_up(c, name, code, vk, mods)    keyUp
  goto_row(c, y)                     click a row header to select the whole row
  hide_row(c, y)                     select row then hide via context menu (== Ctrl+Alt+9)
  page_down(c, n)                    scroll down n screens

Coord notes for the meeting sheet (1092x711 viewport, 100% zoom):
  name box        (30, 111)
  row header x    ~28      (x=40 lands in the cell area, NOT the row header)
  row y           visual center; ~47px step when row height is 60pt
"""
import base64
import sys
import time

sys.path.insert(0, ".")
from cdp import get_page_ws, CDP  # noqa: E402

CTRL, SHIFT, ALT = 2, 8, 1


def snap(c, path, retries=3):
    """Screenshot the page. Retries on CDP errors (capture can transiently fail)."""
    last = None
    for _ in range(retries):
        r = c.send("Page.captureScreenshot", {"format": "png"})
        data = (r or {}).get("result", {}).get("data")
        if data:
            open(path, "wb").write(base64.b64decode(data))
            return path
        last = r
        time.sleep(0.6)
    raise RuntimeError(f"screenshot failed after {retries} tries: {last}")


def mouse_move(c, x, y):
    c.send("Input.dispatchMouseEvent", {"type": "mouseMoved", "x": x, "y": y, "button": "none"})


def mouse_down(c, x, y, button="left", count=1, modifiers=0):
    c.send("Input.dispatchMouseEvent", {
        "type": "mousePressed", "x": x, "y": y, "button": button,
        "clickCount": count, "modifiers": modifiers})


def mouse_up(c, x, y, button="left", count=1, modifiers=0):
    c.send("Input.dispatchMouseEvent", {
        "type": "mouseReleased", "x": x, "y": y, "button": button,
        "clickCount": count, "modifiers": modifiers})


def click(c, x, y, button="left", count=1, modifiers=0):
    mouse_move(c, x, y)
    time.sleep(0.05)
    mouse_down(c, x, y, button, count, modifiers)
    time.sleep(0.05)
    mouse_up(c, x, y, button, count, modifiers)
    time.sleep(0.15)


def key(c, name, code, vk, modifiers=0, text=None, raw=False):
    """Dispatch a key event.

    Tencent Docs' canvas listens on the raw keydown path: sending type
    "keyDown" is often ignored for shortcut chords (e.g. Alt+Shift+9), while
    "rawKeyDown" works. Pass raw=True for shortcuts.
    """
    p = {"type": "rawKeyDown" if raw else "keyDown", "key": name, "code": code,
         "windowsVirtualKeyCode": vk, "nativeVirtualKeyCode": vk, "modifiers": modifiers}
    if text and not raw:
        p["text"] = text
    c.send("Input.dispatchKeyEvent", p)


def key_up(c, name, code, vk, modifiers=0):
    c.send("Input.dispatchKeyEvent", {
        "type": "keyUp", "key": name, "code": code,
        "windowsVirtualKeyCode": vk, "nativeVirtualKeyCode": vk, "modifiers": modifiers})


def chord(c, main_key, main_code, main_vk, mods, raw=False):
    """Press a modifier chord, e.g. chord(c, '9', 'Digit9', 57, CTRL|ALT).

    raw=True dispatches rawKeyDown (needed for Tencent Docs canvas shortcuts).
    """
    if mods & CTRL:
        key(c, "Control", "ControlLeft", 17, CTRL, raw=raw)
    if mods & ALT:
        key(c, "Alt", "AltLeft", 18, mods, raw=raw)
    if mods & SHIFT:
        key(c, "Shift", "ShiftLeft", 16, mods, raw=raw)
    key(c, main_key, main_code, main_vk, mods, raw=raw)
    key_up(c, main_key, main_code, main_vk, mods)
    if mods & SHIFT:
        key_up(c, "Shift", "ShiftLeft", 16, mods & ~SHIFT)
    if mods & ALT:
        key_up(c, "Alt", "AltLeft", 18, mods & ~ALT)
    if mods & CTRL:
        key_up(c, "Control", "ControlLeft", 17, 0)
    time.sleep(0.15)


def select_grid(c, x=200, y=300):
    """Give the grid focus by clicking an empty cell."""
    click(c, x, y)


def go_home(c):
    """Ctrl+Home: scroll back to the top."""
    select_grid(c)
    chord(c, "Home", "Home", 36, CTRL)


def page_down(c, n=1, pause=0.7):
    for _ in range(n):
        key(c, "PageDown", "PageDown", 34)
        key_up(c, "PageDown", "PageDown", 34)
        time.sleep(pause)


def select_row(c, y, x=28):
    """Click the row header to select the whole row."""
    click(c, x, y)
    time.sleep(0.45)


def hide_row_via_menu(c, y, x=28, menu_dx=72, menu_dy=-55):
    """Select the row, right-click its header, then click '隐藏行' in the context menu.

    menu_dx/menu_dy are offsets from the click point to the menu item.
    Defaults assume the menu opens with the clicked point at its left/bottom area
    around x=0..185, y=0..700 and '隐藏行' sits ~72px right, ~55px above the click row.
    Calibrate after the first menu screenshot.
    """
    select_row(c, y, x)
    mouse_move(c, x, y)
    time.sleep(0.15)
    mouse_down(c, x, y, "right", 1)
    time.sleep(0.15)
    mouse_up(c, x, y, "right", 1)
    time.sleep(0.9)
    snap(c, "ctx_menu_check.png")   # inspect this to calibrate the offsets
    click(c, x + menu_dx, y + menu_dy)
    time.sleep(1.0)


if __name__ == "__main__":
    ws, tab = get_page_ws()
    c = CDP(ws)
    print("tab:", tab["title"], "|", tab["url"][:70])
    c.close()
