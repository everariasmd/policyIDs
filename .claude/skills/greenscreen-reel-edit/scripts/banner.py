#!/usr/bin/env python3
"""Headline banner: big heavy text, black stroke, no box. Transparent 1080x480 PNG laid at the top.

    banner.py OUT.png "POTASSIUM SPIKES" "= HEART STOPS"            # line 2 yellow (default)
    banner.py OUT.png "AGE 74" "DOESN'T TRAIN" --colors white,red
    banner.py OUT.png "ONE LINE ONLY" --colors yellow

Each line auto-shrinks to fit 990 px. Keep it to 2 lines of <= ~22 characters: it is a
headline for the point being made, not a sentence. The default palette (white, then yellow)
puts the punchline in yellow.
"""
import argparse
import os
import sys

from PIL import Image, ImageDraw, ImageFont

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from _common import W, color, ensure_dir, font_path  # noqa: E402


def banner(out, lines, colors=None, size=84, top=70, line_h=100, max_w=990, stroke=8):
    colors = colors or (["white", "yellow"] if len(lines) > 1 else ["yellow"])
    fp = font_path()
    im = Image.new("RGBA", (W, 480), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    y = top
    for i, text in enumerate(lines):
        sz = size
        while d.textlength(text, font=ImageFont.truetype(fp, sz)) > max_w and sz > 30:
            sz -= 2
        f = ImageFont.truetype(fp, sz)
        x = (W - d.textlength(text, font=f)) / 2
        d.text((x, y), text, font=f, fill=color(colors[min(i, len(colors) - 1)]),
               stroke_width=stroke, stroke_fill=(0, 0, 0))
        y += line_h
    ensure_dir(out)
    im.save(out)
    print(out)


if __name__ == "__main__":
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("out")
    ap.add_argument("lines", nargs="+")
    ap.add_argument("--colors", default=None, help="comma list per line: white,yellow,red,green or hex")
    a = ap.parse_args()
    banner(a.out, a.lines, a.colors.split(",") if a.colors else None)
