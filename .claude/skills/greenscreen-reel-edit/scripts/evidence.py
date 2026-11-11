#!/usr/bin/env python3
"""Evidence cards from page screenshots (news headline, study abstract, medical image).

The look: only the part that proves the point, key words marker-highlighted in yellow,
rounded corners, soft drop shadow, transparent PNG ready to float over B-roll.

Subcommands
-----------
card    Crop one box out of a screenshot.
    evidence.py card SRC.png OUT.png --box 550,280,1370,360 [--hl 550,282,1310,352 ...] [--width 1040]

stitch  Pull several rows (e.g. title + journal line + 2 abstract lines) into one compact card.
        Use it to split a long abstract line into shorter rows so the text gets BIG on a phone.
    evidence.py stitch SRC.png OUT.png --row x0,y0,x1,y1 --row ... [--hl ...] [--width 960]

gaps    Find the white gaps between words on one text line, so rows split cleanly
        (never mid-word). --debug writes a 2x zoom of the line with every gap labelled.
    evidence.py gaps SRC.png --y 1044,1068 [--x 545,1380] [--debug gaps.png]

All coordinates are pixels of SRC (screenshots from Tella get_source_thumbnail at width 1920).
Highlight boxes are in SRC coordinates too and are applied before cropping.
"""
import argparse
import os
import sys

from PIL import Image, ImageChops, ImageDraw, ImageFilter, ImageFont

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from _common import HIGHLIGHT, box, ensure_dir, font_path  # noqa: E402


def _highlight(im, hls):
    if not hls:
        return im
    layer = Image.new("RGB", im.size, (255, 255, 255))
    d = ImageDraw.Draw(layer)
    for r in hls:
        d.rectangle(r, fill=HIGHLIGHT)
    return ImageChops.multiply(im, layer)  # multiply keeps the text dark, like a real marker


def _frame(crop, out, width, radius=22, pad=30):
    h = int(crop.height * width / crop.width)
    crop = crop.resize((width, h), Image.LANCZOS)
    mask = Image.new("L", (width, h), 0)
    ImageDraw.Draw(mask).rounded_rectangle([0, 0, width - 1, h - 1], radius=radius, fill=255)
    canvas = Image.new("RGBA", (width + 2 * pad, h + 2 * pad), (0, 0, 0, 0))
    shadow = Image.new("L", canvas.size, 0)
    ImageDraw.Draw(shadow).rounded_rectangle([pad, pad + 8, pad + width, pad + h + 8], radius=radius, fill=170)
    canvas.paste((0, 0, 0, 255), (0, 0), shadow.filter(ImageFilter.GaussianBlur(14)))
    canvas.paste(crop, (pad, pad), mask)
    ensure_dir(out)
    canvas.save(out)
    print(out, canvas.size)
    return canvas.size


def card(src, out, crop_box, hls=(), width=1040):
    im = _highlight(Image.open(src).convert("RGB"), hls)
    return _frame(im.crop(crop_box), out, width)


def stitch(src, out, rows, hls=(), width=960, gap=14, margin=20):
    im = _highlight(Image.open(src).convert("RGB"), hls)
    parts = [im.crop(r) for r in rows]
    w = max(p.width for p in parts) + 2 * margin
    h = sum(p.height for p in parts) + gap * (len(parts) - 1) + 2 * margin
    sheet = Image.new("RGB", (w, h), (255, 255, 255))
    y = margin
    for p in parts:
        sheet.paste(p, (margin, y))
        y += p.height + gap
    return _frame(sheet, out, width)


def gaps(src, y0, y1, x0=0, x1=None, min_w=5, thresh=200, debug=None):
    im = Image.open(src).convert("L")
    x1 = x1 or im.width
    blank = [all(im.getpixel((x, y)) > thresh for y in range(y0, y1)) for x in range(x0, x1)]
    found, run = [], 0
    for i, b in enumerate(blank + [False]):
        if b:
            run += 1
        else:
            if run >= min_w:
                found.append(x0 + i - run // 2 - 1)
            run = 0
    if debug:
        c = Image.open(src).convert("RGB").crop((x0, y0 - 6, x1, y1 + 6))
        c = c.resize((c.width * 2, c.height * 2))
        d = ImageDraw.Draw(c)
        f = ImageFont.truetype(font_path(), 11)
        for g in found:
            X = (g - x0) * 2
            d.line([(X, 0), (X, c.height)], fill="red")
            d.text((X + 2, 0), str(g), fill="red", font=f)
        ensure_dir(debug)
        c.save(debug)
    return found


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)
    a = sub.add_parser("card")
    a.add_argument("src"); a.add_argument("out")
    a.add_argument("--box", required=True, type=box)
    a.add_argument("--hl", action="append", type=box, default=[])
    a.add_argument("--width", type=int, default=1040)
    b = sub.add_parser("stitch")
    b.add_argument("src"); b.add_argument("out")
    b.add_argument("--row", action="append", type=box, required=True)
    b.add_argument("--hl", action="append", type=box, default=[])
    b.add_argument("--width", type=int, default=960)
    g = sub.add_parser("gaps")
    g.add_argument("src")
    g.add_argument("--y", required=True)
    g.add_argument("--x", default=None)
    g.add_argument("--debug", default=None)
    args = ap.parse_args()
    if args.cmd == "card":
        card(args.src, args.out, args.box, args.hl, args.width)
    elif args.cmd == "stitch":
        stitch(args.src, args.out, args.row, args.hl, args.width)
    else:
        y0, y1 = (int(v) for v in args.y.split(","))
        x0, x1 = (int(v) for v in args.x.split(",")) if args.x else (0, None)
        print(gaps(args.src, y0, y1, x0, x1, debug=args.debug))


if __name__ == "__main__":
    main()
