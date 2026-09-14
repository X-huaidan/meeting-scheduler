# -*- coding: utf-8 -*-
"""纯标准库 PNG 解码 / 裁切 / 自动切片 —— 会议截图识别的主力工具。

为什么坚持零依赖：Pillow 装得上但很慢（2026-09-14 首次装 4m54s @ 25kB/s），
而技能原有的 `_pix.py` 依赖 PIL —— 一旦 Pillow 缺失，整条像素校验链路就废
（家里机器就真实发生过）。本模块只用 zlib + struct，换任何机器都能跑；
解码一张 1728x6328 的长图约 2.4s，完全够用。

三个用法：
    # 1. 一键把长图切成若干"可直接 Read"的片段（日常主力）
    python _png.py auto  <src.png> [outdir] [--cols N] [--maxh 420]

    # 2. 手动精确裁切 + 放大（慎用/confirm 单个字时用）
    python _png.py crop  <src.png> <dst.png> <x> <y> <w> <h> <scale>

    # 3. 只看 나는 구조 감지结果（调试用，不产出文件）
    python _png.py bands <src.png>

`auto` 做了什么：
  1. 自动识别背景色（出现最多的颜色），按"偏离背景"判定文字像素
  2. 逐行扫描密度 → 合并成文字带；**过滤掉表格横线**（整行暗像素占比过高）
  3. 按 maxh 把文字带归组成片段，且不切断任何一条文字带
  4. 内容列范围收紧（左右留白砍掉）；宽度过大时在中段最空白处自动竖切成 N 栏
  5. 每片放大到目标宽度后写出，编号 `<prefix>_NN[_cN].png`，并打印坐标清单

参数说明：
  --cols N    横向切成 N 栏（默认：宽度 >1200 时自动 2 栏，否则 1）
  --maxh N    单片段最大原始高度（默认 420，越小字越大越清楚）
  --targetw N 输出目标宽度（默认 1500，控制放大倍数）
  --prefix S  输出文件名前缀（默认取源文件名）

产物目录：默认写到环境变量 SNAP_DIR（与 `_boot.snap()` 一致），没设就落当前目录。
**不要把产物落在技能目录里**——见 SKILL.md「临时文件纪律」。
"""
import os
import struct
import sys
import zlib


# ---------------------------------------------------------------- PNG 解码

def read_png(path):
    """返回 (w, h, px)；px[y][x] = (r, g, b, a)。支持 8bit / 非隔行 / 灰/RGB/RGBA/调色板。"""
    with open(path, "rb") as f:
        data = f.read()
    if data[:8] != b"\x89PNG\r\n\x1a\n":
        raise ValueError("not a png: %s" % path)

    pos, idat = 8, bytearray()
    w = h = depth = ctype = interlace = None
    palette = None
    while pos < len(data):
        (ln,) = struct.unpack(">I", data[pos:pos + 4])
        typ = data[pos + 4:pos + 8]
        body = data[pos + 8:pos + 8 + ln]
        pos += 12 + ln
        if typ == b"IHDR":
            w, h, depth, ctype, _c, _f, interlace = struct.unpack(">IIBBBBB", body)
        elif typ == b"PLTE":
            palette = [tuple(body[i:i + 3]) for i in range(0, len(body), 3)]
        elif typ == b"IDAT":
            idat += body
        elif typ == b"IEND":
            break
    if depth != 8:
        raise ValueError("only 8-bit supported, got %s" % depth)
    if interlace:
        raise ValueError("interlaced png not supported")

    nch = {0: 1, 2: 3, 3: 1, 4: 2, 6: 4}[ctype]
    raw = zlib.decompress(bytes(idat))
    stride = w * nch
    rows, prev, p = [], bytearray(stride), 0
    for _ in range(h):
        ft = raw[p]
        p += 1
        line = bytearray(raw[p:p + stride])
        p += stride
        if ft == 1:
            for i in range(nch, stride):
                line[i] = (line[i] + line[i - nch]) & 0xFF
        elif ft == 2:
            for i in range(stride):
                line[i] = (line[i] + prev[i]) & 0xFF
        elif ft == 3:
            for i in range(stride):
                a = line[i - nch] if i >= nch else 0
                line[i] = (line[i] + ((a + prev[i]) >> 1)) & 0xFF
        elif ft == 4:
            for i in range(stride):
                a = line[i - nch] if i >= nch else 0
                b = prev[i]
                c = prev[i - nch] if i >= nch else 0
                pa, pb, pc = abs(b - c), abs(a - c), abs(a + b - 2 * c)
                pr = a if (pa <= pb and pa <= pc) else (b if pb <= pc else c)
                line[i] = (line[i] + pr) & 0xFF
        rows.append(bytes(line))
        prev = line

    out = []
    for line in rows:
        px = []
        for i in range(w):
            v = line[i * nch:(i + 1) * nch]
            if ctype == 6:
                px.append(tuple(v))
            elif ctype == 2:
                px.append((v[0], v[1], v[2], 255))
            elif ctype == 0:
                px.append((v[0],) * 3 + (255,))
            elif ctype == 4:
                px.append((v[0],) * 3 + (v[1],))
            else:
                px.append(tuple(palette[v[0]]) + (255,))
        out.append(px)
    return w, h, out


def write_png(path, pixels):
    h = len(pixels)
    w = len(pixels[0]) if h else 0

    def chunk(typ, body):
        return (struct.pack(">I", len(body)) + typ + body
                + struct.pack(">I", zlib.crc32(typ + body) & 0xFFFFFFFF))

    raw = bytearray()
    for row in pixels:
        raw.append(0)
        for p in row:
            raw += bytes(p[:4])
    png = b"\x89PNG\r\n\x1a\n"
    png += chunk(b"IHDR", struct.pack(">IIBBBBB", w, h, 8, 6, 0, 0, 0))
    png += chunk(b"IDAT", zlib.compress(bytes(raw), 6))
    png += chunk(b"IEND", b"")
    with open(path, "wb") as f:
        f.write(png)


def scale_up(px, sc):
    """最近邻放大 —— 小字识别时比插值更保真（插值会把笔画糊成一团）。"""
    out = []
    for row in px:
        line = []
        for p in row:
            line.extend([p] * sc)
        for _ in range(sc):
            out.append(line)
    return out


# ---------------------------------------------------------------- 内容分析

def _dominant_color(px, w, h, step=7):
    """背景色 = 出现最多的颜色。"""
    from collections import Counter
    c = Counter()
    for y in range(0, h, step):
        row = px[y]
        for x in range(0, w, step):
            c[row[x][:3]] += 1
    return c.most_common(1)[0][0]


def build_profile(w, h, px, bg, thresh=110, step_x=3):
    """一次算完全图的逐行统计，后续所有分析复用它 —— 避免重复 O(w*h) 扫描。

    每行 -> (hit, n, lo, hi)，hit 是与背景色距离超阈值的采样点数。
    """
    prof = []
    for y in range(h):
        row = px[y]
        n = hit = 0
        lo = hi = None
        for x in range(0, w, step_x):
            p = row[x][:3]
            n += 1
            if abs(p[0] - bg[0]) + abs(p[1] - bg[1]) + abs(p[2] - bg[2]) > thresh:
                hit += 1
                if lo is None:
                    lo = x
                hi = x
        prof.append((hit, n, lo, hi))
    return prof


def find_bands_from_profile(prof, min_text=3, line_ratio=0.55, gap=14):
    """把连续的文字行合并成带；丢掉表格横线。

    line_ratio：整行暗像素占比超过它 -> 判定为横线/边框，不当文字带。
    gap：两条带之间空白小于它 -> 合并（同一个会议块内的换行）。

    注意：内容排版很密的长图（企微会议列表）几乎行行有字，gap 会把整张图
    合并成一个巨大的 band。这没关系 —— 后面 `_group_chunks` 会按 maxh
    在密度最低处二次切分，不会真的产出巨无霸片段。
    """
    raw = []
    cur = None
    for y, (hit, n, lo, hi) in enumerate(prof):
        if hit >= min_text and (n == 0 or hit / n < line_ratio):
            if cur is None:
                cur = [y, y, lo, hi]
            else:
                cur[1] = y
                cur[2] = lo if lo is not None else cur[2]
                cur[3] = hi if hi is not None else cur[3]
        else:
            if cur is not None:
                raw.append(tuple(cur))
                cur = None
    if cur:
        raw.append(tuple(cur))

    bands = []
    for b in raw:
        if bands and b[0] - bands[-1][1] <= gap:
            p = bands[-1]
            bands[-1] = (p[0], b[1],
                         min(p[2] or 0, b[2] if b[2] is not None else p[2] or 0),
                         max(p[3] or 0, b[3] if b[3] is not None else p[3] or 0))
        else:
            bands.append(b)
    return bands


def content_xrange(prof, w, pad=12):
    """内容整体的左右边界（用于砍掉大片留白）。直接用 profile 的 lo/hi。"""
    lo, hi = None, 0
    for (_hit, _n, rlo, rhi) in prof:
        if rlo is not None:
            lo = rlo if lo is None else min(lo, rlo)
            hi = max(hi, rhi)
    if lo is None:
        return 0, w
    return max(0, lo - pad), min(w, hi + pad)


def best_vsplit(prof, xlo, xhi, ncols):
    """在中段密度最低的竖列处切分 —— 避免在文字中间竖切。

    ncols=2 -> 返回 1 个切点；ncols=3 -> 返回 2 个。太窄时不切（会切断列）。
    """
    if ncols <= 1:
        return None, None, None
    span = xhi - xlo
    if span < 700:
        return None, None, None

    cuts = []
    for k in range(1, ncols):
        center = xlo + span * k / float(ncols)
        lo = int(max(xlo + span * 0.18, center - span * 0.22))
        hi = int(min(xhi - span * 0.18, center + span * 0.22))
        if hi <= lo:
            continue
        best, bx = None, None
        for x in range(lo, hi, 2):
            d = 0
            for (_hit, _n, rlo, rhi) in prof:
                if rlo is not None and rlo <= x <= rhi:
                    d += 1
            if best is None or d < best:
                best, bx = d, x
        if bx is not None:
            cuts.append(bx)
    return (cuts or None), xlo, xhi


# ---------------------------------------------------------------- CLI

def cmd_bands(args):
    src = args[0]
    w, h, px = read_png(src)
    bg = _dominant_color(px, w, h)
    prof = build_profile(w, h, px, bg)
    bands = find_bands_from_profile(prof)
    xlo, xhi = content_xrange(prof, w)
    print("src %s  %dx%d  bg=%s  content_x=[%d,%d]"
          % (os.path.basename(src), w, h, bg, xlo, xhi))
    for i, b in enumerate(bands):
        print("  band %2d  y %5d-%-5d h=%-4d x[%d..%d]"
              % (i, b[0], b[1], b[1] - b[0] + 1,
                 b[2] if b[2] is not None else -1,
                 b[3] if b[3] is not None else -1))


def _group_chunks(bands, maxh, overlap=24):
    """把 band 归组成片段 (y0, y1)；超过 maxh 时另起一片。

    排版很密的长图会合成单个巨 band，这里不会把它切开 —— 交给 `_split_tall`
    按"密度最低的行"二次切分，避免把一条会议记录拦腰斩断。
    """
    if not bands:
        return []
    chunks = []
    cur = [bands[0][0], bands[0][1]]
    for (y0, y1, _a, _b) in bands[1:]:
        if y1 - cur[0] + 1 <= maxh:
            cur[1] = y1
        else:
            chunks.append(tuple(cur))
            cur = [y0, y1]
    chunks.append(tuple(cur))

    out, i = [], 0
    while i < len(chunks):
        if i + 1 < len(chunks) and chunks[i + 1][0] - chunks[i][1] < overlap:
            out.append((chunks[i][0], chunks[i + 1][1]))
            i += 2
        else:
            out.append(chunks[i])
            i += 1
    return out


def _split_tall(chunk, prof, maxh):
    """把过高的片段纵向切开，切点选附近文字最少的那一行。"""
    y0, y1 = chunk
    if y1 - y0 + 1 <= maxh:
        return [chunk]
    out, s = [], y0
    while y1 - s + 1 > maxh:
        target = s + maxh
        lo = s + int(maxh * 0.55)
        hi = min(y1, target + int(maxh * 0.30))
        if hi < lo:
            hi = min(y1, s + maxh)
        best_y, best_d = None, None
        for y in range(lo, hi + 1):
            d = prof[y][0]
            if best_d is None or d < best_d:
                best_d, best_y = d, y
        if best_y is None or best_y <= s:
            best_y = hi
        out.append((s, best_y))
        s = best_y + 1
    if s <= y1:
        out.append((s, y1))
    return out


def cmd_auto(args):
    src = args[0]
    outdir = args[1] if len(args) > 1 and not args[1].startswith("--") else None

    def _opt(name, default):
        flag = "--" + name
        if flag in args:
            return args[args.index(flag) + 1]
        return default

    maxh = int(_opt("maxh", 420))
    targetw = int(_opt("targetw", 1400))
    prefix = _opt("prefix", os.path.splitext(os.path.basename(src))[0])
    cols_opt = _opt("cols", None)

    if outdir is None:
        outdir = os.environ.get("SNAP_DIR") or os.getcwd()
    outdir = os.path.expanduser(outdir)
    os.makedirs(outdir, exist_ok=True)

    w, h, px = read_png(src)
    bg = _dominant_color(px, w, h)
    prof = build_profile(w, h, px, bg)
    bands = find_bands_from_profile(prof)
    if not bands:
        print("no text bands found in %s" % src)
        return 1
    xlo, xhi = content_xrange(prof, w)
    cspan = xhi - xlo

    # 竖切只在"不切就会因为 Read 缩放而看不清"时才做，默认不切（会切断表格列）
    ncols = int(cols_opt) if cols_opt else (2 if cspan > targetw * 1.3 else 1)
    cuts, _, _ = best_vsplit(prof, xlo, xhi, ncols)
    if cuts and cuts[0] is not None:
        col_ranges, prev = [], xlo
        for c in list(cuts) + [xhi]:
            col_ranges.append((prev, c))
            prev = c
    else:
        col_ranges = [(xlo, xhi)]

    chunks = []
    for c in _group_chunks(bands, maxh):
        chunks.extend(_split_tall(c, prof, maxh))

    made = []
    for ci, (cy0, cy1) in enumerate(chunks):
        for ri, (xa, xb) in enumerate(col_ranges):
            crop = [row[xa:xb] for row in px[cy0:cy1 + 1]]
            cw = xb - xa
            # 窄内容放大回 targetw；已经够宽的就不放（避免文件过大）
            sc = max(1, min(3, int(round(targetw / float(cw))))) if cw < targetw * 0.85 else 1
            big = scale_up(crop, sc) if sc > 1 else crop
            name = "%s_%02d.png" % (prefix, ci) if len(col_ranges) == 1 \
                else "%s_%02d_c%d.png" % (prefix, ci, ri + 1)
            dst = os.path.join(outdir, name)
            write_png(dst, big)
            made.append((name, cy0, cy1, xa, xb, sc, len(big[0]), len(big)))

    print("src %s  %dx%d  bg=%s" % (os.path.basename(src), w, h, bg))
    print("bands=%d -> chunks=%d cols=%d -> %s"
          % (len(bands), len(chunks), len(col_ranges), outdir))
    for m in made:
        print("  %-36s y[%4d-%4d] x[%4d-%4d] x%d -> %dx%d"
              % (m[0], m[1], m[2], m[3], m[4], m[5], m[6], m[7]))
    return 0


def cmd_crop(args):
    src, dst = args[0], args[1]
    x, y, cw, ch, sc = (int(v) for v in args[2:7])
    w, h, px = read_png(src)
    x2, y2 = min(x + cw, w), min(y + ch, h)
    crop = [row[x:x2] for row in px[y:y2]]
    big = scale_up(crop, sc) if sc > 1 else crop
    write_png(dst, big)
    print("OK src=%dx%d crop=(%d,%d,%d,%d) scale=%d -> %dx%d  %s"
          % (w, h, x, y, x2 - x, y2 - y, sc, len(big[0]), len(big), dst))
    return 0


if __name__ == "__main__":
    if len(sys.argv) < 3:
        print(__doc__)
        sys.exit(1)
    cmd, rest = sys.argv[1], sys.argv[2:]
    if cmd == "auto":
        sys.exit(cmd_auto(rest))
    elif cmd == "crop":
        sys.exit(cmd_crop(rest))
    elif cmd == "bands":
        cmd_bands(rest)
    else:
        print(__doc__)
        sys.exit(1)
