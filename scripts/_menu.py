# -*- coding: utf-8 -*-
"""Read / click the Tencent Docs context menu.

Why the weird approach: the menu is DOM (good), but the cell-menu variant puts
its <li> boxes at x=0.8 because a CSS transform moves the visual copy -- so
getBoundingClientRect() lies. We therefore *hit-test*: walk a grid of points
with document.elementFromPoint() and record which menu text sits at which point.
That is transform-proof and needs a single round trip.

read_menu(c)  -> {"items": [[text, [x, y]], ...], "range": ..., "hide": ..., "unhide": ...}
click_item(c, substring)
"""
import time

# grid of sample points over the region where a context menu can appear
SCAN_JS = r"""
(function () {
  const MENU_RE = /dui-menu|menu-item|contextmenu|context-menu/i;
  const seen = new Map();
  // The <li> and the wrapping <ul> sit in the SAME stack, and the <ul>'s text is
  // the whole menu, so prefer the innermost actual <li class="dui-menu-item">.
  const grab = function (stack) {
    for (let i = 0; i < stack.length; i++) {
      const el = stack[i];
      if (!el.tagName || el.tagName !== 'LI') continue;
      const cls = (el.className || '').toString();
      if (!MENU_RE.test(cls)) continue;
      if (/menu-item-description/.test(cls)) continue;   // shortcut hint, not an item
      return el;
    }
    return null;
  };
  for (let y = 2; y <= 730; y += 8) {
    for (let x = 6; x <= 1530; x += 16) {
      const stack = document.elementsFromPoint(x, y);
      if (!stack || !stack.length) continue;
      const cand = grab(stack);
      if (!cand) continue;
      const t = (cand.textContent || '').replace(/\s+/g, '');
      if (!t || t.length > 40) continue;
      // key by class -- more stable than the label text
      const key = (cand.className || '').toString().replace('dui-menu-item', '').trim();
      if (!seen.has(key)) seen.set(key, [t, 0, 0, 0, 1e9, 1e9, -1, -1]);
      const s = seen.get(key);
      s[1] += x; s[2] += y; s[3] += 1;
      s[4] = Math.min(s[4], x); s[5] = Math.min(s[5], y);
      s[6] = Math.max(s[6], x); s[7] = Math.max(s[7], y);
    }
  }
  const items = [];
  seen.forEach(function (s, key) {
    items.push([s[0], [+(s[1] / s[3]).toFixed(1), +(s[2] / s[3]).toFixed(1),
                   s[4], s[5], s[6], s[7], s[3]], key]);
  });
  let range = null, hide = null, unhide = null;
  items.forEach(function (it) {
    const t = it[0], r = it[1], key = it[2];
    if (/行分为一组|行分组/.test(t)) range = t;
    // NOTE: 'contextmenu-item-cancel-hide-row' CONTAINS 'hide-row', so match the
    // exact class -- a substring test would aim at 取消隐藏行 while thinking it
    // was aiming at 隐藏行 (they are adjacent items, 32px apart).
    if (key === 'contextmenu-item-hide-row') hide = [r[0], r[1]];
    else if (key === 'contextmenu-item-cancel-hide-row') unhide = [r[0], r[1]];
    else if (t.indexOf('隐藏行') === 0) hide = hide || [r[0], r[1]];
    else if (t.indexOf('取消隐藏行') === 0) unhide = unhide || [r[0], r[1]];
  });
  return {items: items, range: range, hide: hide, unhide: unhide};
})()
"""


EMPTY = {"items": [], "range": None, "hide": None, "unhide": None}

# Cheap variant for the row probe. The sheet pre-renders several copies of every
# menu, and the copies' getBoundingClientRect() is unreliable (transformed
# containers report layout coords). So: take the candidate <li>s, and keep only
# the ones that are actually *hit-testable* at their own centre. Few candidates,
# a handful of elementFromPoint calls -- far cheaper than a grid scan.
RANGE_JS = r"""
(function () {
  const SEL = 'li[class*="contextmenu-item-set-row-combination"],'
            + 'li[class*="contextmenu-item-cancel-row-combination"]';
  const live = [];
  const cands = document.querySelectorAll(SEL);
  for (let i = 0; i < cands.length; i++) {
    const li = cands[i];
    const b = li.getBoundingClientRect();
    if (b.width < 60 || b.height < 8) continue;
    const cx = b.x + b.width / 2, cy = b.y + b.height / 2;
    if (cx < 1 || cy < 1 || cx > innerWidth - 1 || cy > innerHeight - 1) continue;
    const st = document.elementsFromPoint(cx, cy);
    let ok = false;
    for (let k = 0; k < st.length; k++) {
      if (st[k] === li || (st[k].closest && st[k].closest('li') === li)) { ok = true; break; }
    }
    if (ok) live.push([(li.textContent || '').replace(/\s+/g, ''), b.x, b.y, b.width]);
  }
  return {n: cands.length, live: live};
})()
"""


def read_range(c):
    """Return the context menu's self-reported selection, e.g. '将[16-25]行分为一组'."""
    r = c.eval("(function(){try{return " + RANGE_JS.strip() +
               "}catch(e){return {n:-1,live:[],err:String(e&&e.message)}}})()")
    if not isinstance(r, dict):
        return None, r
    live = r.get("live") or []
    for t, x, y, w in live:
        if "[" in t:
            return t, r
    return (live[0][0] if live else None), r


def read_menu(c):
    """Scan the page for an open context menu. Never raises."""
    r = c.eval("(function(){try{return " + SCAN_JS.strip() +
               "}catch(e){return {items:[],range:null,hide:null,unhide:null,"
               "err:String(e&&e.message)}}})()")
    if isinstance(r, dict) and "items" in r:
        if r.get("err"):
            print("   [menu scan err]", r["err"], flush=True)
        return r
    print("   [menu scan] unexpected:", r, flush=True)
    return dict(EMPTY)


def labels(menu):
    """Item labels in visual (top-to-bottom) order."""
    items = list(menu.get("items") or [])
    items.sort(key=lambda it: it[1][1])
    return [it[0] for it in items]


def click_item(c, substr, menu=None, pause=1.3):
    from sheet_ui import click
    m = menu or read_menu(c)
    for it in m.get("items") or []:
        if substr in it[0]:
            click(c, it[1][0], it[1][1])
            time.sleep(pause)
            return it[0]
    return None


def press_esc(c):
    for t in ("rawKeyDown", "keyDown", "keyUp"):
        c.send("Input.dispatchKeyEvent", {"type": t, "key": "Escape", "code": "Escape",
                                          "windowsVirtualKeyCode": 27,
                                          "nativeVirtualKeyCode": 27})
    time.sleep(0.5)


def rclick(c, x, y, pause=1.0):
    from sheet_ui import mouse_down, mouse_move, mouse_up
    mouse_move(c, x, y)
    time.sleep(0.15)
    mouse_down(c, x, y, "right", 1)
    time.sleep(0.12)
    mouse_up(c, x, y, "right", 1)
    time.sleep(pause)
