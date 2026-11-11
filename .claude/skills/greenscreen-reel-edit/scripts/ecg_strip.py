#!/usr/bin/env python3
"""Heart-monitor strip (green trace on a dark grid) for the `strip` segment kind, which scrolls it
right-to-left like a live monitor. A worked example of a *generated* visual: when no real image
shows a mechanism (rising potassium -> arrhythmia -> arrest), draw one.

    ecg_strip.py OUT.png [--mode hyperkalemia|normal|flatline]

hyperkalemia: T waves grow taller beat by beat, degrade into a sine wave, then flatline.
"""
import argparse
import math
import os
import sys

from PIL import Image, ImageChops, ImageDraw, ImageFilter

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from _common import ensure_dir  # noqa: E402


def strip(out, mode="hyperkalemia", width=7560, height=700, base=380):
    st = Image.new("RGB", (width, height), (4, 14, 8))
    d = ImageDraw.Draw(st)
    for x in range(0, width, 40):
        d.line([(x, 0), (x, height)], fill=(18, 70, 38) if x % 200 == 0 else (10, 40, 22))
    for y in range(0, height, 40):
        d.line([(0, y), (width, y)], fill=(18, 70, 38) if y % 200 == 0 else (10, 40, 22))

    def beat(x0, t_amp):
        pts = []
        for i in range(300):
            u = i / 300
            y = (-18 * math.exp(-((u - .12) / .03) ** 2) + 12 * math.exp(-((u - .25) / .008) ** 2)
                 - 210 * math.exp(-((u - .28) / .012) ** 2) + 40 * math.exp(-((u - .31) / .01) ** 2)
                 - t_amp * math.exp(-((u - .55) / (.05 if t_amp > 60 else .07)) ** 2))
            pts.append((x0 + i, base + y))
        return pts

    pts, x, n = [], 0, 0
    stop = width if mode == "normal" else width - (700 if mode == "flatline" else 1500)
    while x < stop - 300:
        amp = 30 if mode != "hyperkalemia" else 30 + min(150, n * 14)
        pts += beat(x, amp)
        x += 300
        n += 1
    if mode == "hyperkalemia":
        while x < width - 700:
            pts.append((x, base - 120 * math.sin(x / 35)))
            x += 1
    while x < width:
        pts.append((x, base))
        x += 1
    d.line(pts, fill=(60, 255, 120), width=6, joint="curve")
    st = ImageChops.add(st, st.filter(ImageFilter.GaussianBlur(6)))  # phosphor glow
    ensure_dir(out)
    st.save(out)
    print(out, st.size)


if __name__ == "__main__":
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("out")
    ap.add_argument("--mode", default="hyperkalemia", choices=["hyperkalemia", "normal", "flatline"])
    a = ap.parse_args()
    strip(a.out, a.mode)
