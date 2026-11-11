#!/usr/bin/env python3
"""Full-frame overlay (1080x1920 RGBA) for hook / comparison moments: headline lines on top,
then one big image, or two images side by side with coloured labels underneath.
Used with the `full` segment kind in build_bg.py (shown over a very dark blurred background).

One image (e.g. the first MRI in a "this is the thigh of..." hook):
    fullframe.py OUT.png --line "AGE 74:white" --line "DOESN'T TRAIN:red" --img mri74.png

Two images side by side (before/after, sedentary vs trained):
    fullframe.py OUT.png --line "SAME AGE.:white" --line "DIFFERENT FUTURE.:yellow" \
        --img mri74.png --label "AGE 74 · SEDENTARY:red" --img mri70.png --label "AGE 70 · TRAINS:green"

Optional --crop x0,y0,x1,y1 (one per --img, in order; use 'none' to skip) trims junk such as a
white margin on a screenshot.
Everything sits in the top ~45% of the frame because the presenter occupies the bottom.
"""
import argparse
import os
import sys

from PIL import Image, ImageDraw, ImageFont

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from _common import H, W, box, color, ensure_dir, font_path  # noqa: E402


def _rounded(img, width, radius=20):
    h = int(img.height * width / img.width)
    img = img.resize((width, h), Image.LANCZOS)
    m = Image.new("L", (width, h), 0)
    ImageDraw.Draw(m).rounded_rectangle([0, 0, width - 1, h - 1], radius=radius, fill=255)
    return img, m


def _text(d, xy, s, c, size, fp, max_w=None):
    while max_w and d.textlength(s, font=ImageFont.truetype(fp, size)) > max_w and size > 24:
        size -= 2
    d.text(xy, s, font=ImageFont.truetype(fp, size), fill=color(c),
           stroke_width=7, stroke_fill=(0, 0, 0), anchor="mt")


def fullframe(out, lines, imgs, labels=(), crops=()):
    fp = font_path()
    o = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(o)
    y = 60
    for ln in lines:
        txt, _, c = ln.rpartition(":") if ":" in ln else (ln, "", "white")
        _text(d, (W // 2, y), txt, c, 88, fp, max_w=1000)
        y += 100
    srcs = []
    for i, p in enumerate(imgs):
        im = Image.open(p).convert("RGB")
        cr = crops[i] if i < len(crops) else None
        if cr and cr != "none":
            im = im.crop(box(cr))
        srcs.append(im)
    top = y + 30
    if len(srcs) == 1:
        im, m = _rounded(srcs[0], 1020)
        o.paste(im, (30, top), m)
    elif len(srcs) == 2:
        bottoms = []
        for i, src in enumerate(srcs):
            im, m = _rounded(src, 520)
            x = 14 + i * 532
            o.paste(im, (x, top), m)
            bottoms.append(top + im.height)
        ly = max(bottoms) + 16
        for i, lab in enumerate(labels[:2]):
            txt, _, c = lab.rpartition(":") if ":" in lab else (lab, "", "white")
            _text(d, (14 + i * 532 + 260, ly), txt, c, 40, fp, max_w=510)
    else:
        raise SystemExit("give 1 or 2 --img")
    ensure_dir(out)
    o.save(out)
    print(out)


if __name__ == "__main__":
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("out")
    ap.add_argument("--line", action="append", default=[], help="TEXT:color")
    ap.add_argument("--img", action="append", required=True)
    ap.add_argument("--label", action="append", default=[], help="TEXT:color (two-image mode)")
    ap.add_argument("--crop", action="append", default=[])
    a = ap.parse_args()
    fullframe(a.out, a.line, a.img, a.label, a.crop)
