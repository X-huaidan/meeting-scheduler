# -*- coding: utf-8 -*-
"""Keyboard drivers for the Tencent Docs sheet canvas.

Why keyboard: measured on this machine, one mouse event costs ~1.7s round trip
(the browser acks the input event only after a repaint), while a key event is
~30ms. Everything that can be done with keys should be.

Verified behaviour of the sheet:
  * Ctrl+Home        -> active cell becomes A2 (row 1 is the frozen header)
  * ArrowDown        -> next *visible* row (hidden rows are skipped)
  * Shift+Space      -> select the whole row of the active cell
  * Shift+ArrowDown  -> extend the row selection downwards
  * Ctrl+Alt+9       -> hide the selected row(s)
  * Alt+Shift+9      -> unhide the selected row(s)
"""
import time

CTRL, SHIFT, ALT = 2, 8, 1

VK = {
    "Home": 36, "ArrowDown": 40, "ArrowUp": 38, "ArrowLeft": 37, "ArrowRight": 39,
    "Space": 32, "PageDown": 34, "PageUp": 33, "End": 35, "Tab": 9, "Enter": 13,
}


def kd(c, name, code, vk, mods=0):
    c.send("Input.dispatchKeyEvent", {
        "type": "rawKeyDown", "key": name, "code": code,
        "windowsVirtualKeyCode": vk, "nativeVirtualKeyCode": vk, "modifiers": mods})


def ku(c, name, code, vk, mods=0):
    c.send("Input.dispatchKeyEvent", {
        "type": "keyUp", "key": name, "code": code,
        "windowsVirtualKeyCode": vk, "nativeVirtualKeyCode": vk, "modifiers": mods})


def tap(c, name, code, vk, mods=0):
    kd(c, name, code, vk, mods)
    ku(c, name, code, vk, mods)


def _mods_down(c, mods):
    if mods & CTRL:
        kd(c, "Control", "ControlLeft", 17, CTRL)
    if mods & ALT:
        kd(c, "Alt", "AltLeft", 18, mods)
    if mods & SHIFT:
        kd(c, "Shift", "ShiftLeft", 16, mods)


def _mods_up(c, mods):
    if mods & SHIFT:
        ku(c, "Shift", "ShiftLeft", 16, mods & ~SHIFT)
    if mods & ALT:
        ku(c, "Alt", "AltLeft", 18, mods & ~ALT)
    if mods & CTRL:
        ku(c, "Control", "ControlLeft", 17, 0)


def combo(c, name, code, vk, mods, pause=0.15):
    """One full chord: modifiers down, key down+up, modifiers up."""
    _mods_down(c, mods)
    kd(c, name, code, vk, mods)
    ku(c, name, code, vk, mods)
    _mods_up(c, mods)
    time.sleep(pause)


def to_top(c):
    combo(c, "Home", "Home", 36, CTRL, pause=0.7)


def down(c, n, pause=0.012):
    """Press ArrowDown n times (plain move of the active cell)."""
    for i in range(n):
        kd(c, "ArrowDown", "ArrowDown", 40, 0)
        ku(c, "ArrowDown", "ArrowDown", 40, 0)
        if pause:
            time.sleep(pause)
    time.sleep(0.25)


def select_row(c):
    """Shift+Space -- select the whole row of the active cell."""
    combo(c, " ", "Space", 32, SHIFT, pause=0.4)


def extend_down(c, n, pause=0.012):
    """Hold Shift and press ArrowDown n times, extending the selection."""
    kd(c, "Shift", "ShiftLeft", 16, SHIFT)
    for _ in range(n):
        kd(c, "ArrowDown", "ArrowDown", 40, SHIFT)
        ku(c, "ArrowDown", "ArrowDown", 40, SHIFT)
        if pause:
            time.sleep(pause)
    ku(c, "Shift", "ShiftLeft", 16, 0)
    time.sleep(0.4)


def hide_rows(c):
    combo(c, "9", "Digit9", 57, CTRL | ALT, pause=1.2)


def unhide_rows(c):
    combo(c, "9", "Digit9", 57, ALT | SHIFT, pause=1.2)


def active(c):
    return c.eval("document.querySelector('.bar-label').value")
