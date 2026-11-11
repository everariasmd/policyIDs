#!/usr/bin/env python3
"""Contact sheet for QA, so you can look before (and after) the long render.

Before rendering: quick key of FG over BG at chosen times
    preview.py --bg bg.mp4 --fg fg.mp4 --times 1,5,12,30 --out sheet.png
After rendering: frames of the finished video
    preview.py --video final.mp4 --times 1,5,12,30 --out sheet.png

Tiles are 270 px wide, 6 per row; read the PNG with the Read tool to inspect it.
"""
import argparse
import os
import subprocess
import tempfile

from PIL import Image


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--bg"); ap.add_argument("--fg"); ap.add_argument("--video")
    ap.add_argument("--times", required=True)
    ap.add_argument("--out", default="sheet.png")
    ap.add_argument("--tile", type=int, default=270)
    ap.add_argument("--cols", type=int, default=6)
    a = ap.parse_args()
    times = [float(t) for t in a.times.split(",")]
    tmp = tempfile.mkdtemp()
    tiles = []
    for i, t in enumerate(times):
        p = os.path.join(tmp, f"{i}.png")
        if a.video:
            cmd = ["ffmpeg", "-nostdin", "-v", "error", "-y", "-ss", str(t), "-i", a.video,
                   "-frames:v", "1", "-vf", f"scale={a.tile}:-2", p]
        else:
            cmd = ["ffmpeg", "-nostdin", "-v", "error", "-y", "-ss", str(t), "-i", a.bg, "-ss", str(t), "-i", a.fg,
                   "-frames:v", "1", "-filter_complex",
                   f"[1:v]format=rgba,colorkey=0xFF00FF:0.30:0.06[f];[0:v][f]overlay=0:0,scale={a.tile}:-2", p]
        subprocess.run(cmd, check=True)
        tiles.append(Image.open(p))
    th = tiles[0].height
    rows = (len(tiles) + a.cols - 1) // a.cols
    sheet = Image.new("RGB", (a.tile * min(a.cols, len(tiles)), th * rows))
    for i, im in enumerate(tiles):
        sheet.paste(im, ((i % a.cols) * a.tile, (i // a.cols) * th))
    sheet.save(a.out)
    print(a.out, sheet.size)


if __name__ == "__main__":
    main()
