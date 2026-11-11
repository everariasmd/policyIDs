#!/usr/bin/env python3
"""Render the 1080x1920 background track (everything BEHIND the presenter) from a segment plan.

    build_bg.py PLAN.tsv --broll broll/ --assets ev/ --out bg.mp4 [--work segs/]

PLAN.tsv: one segment per line, whitespace separated, '#' comments, '-' for an unused column:

    start  end    kind   media          offset  asset        asset2
    0      2.42   full   gym2.mp4       0       f_h74.png    -
    10.80  13.30  ev2    xray.mp4       3       c_wrob.png   b_study.png
    25.4   32.2   strip  ecgstrip.png   0       b_k.png      -

Segments must be contiguous (each start = previous end) and the last end should be >= the
presenter export's length. Times are seconds on the EXPORTED video's timeline.

kinds (what goes on screen; the presenter is composited on top later):
  ban    B-roll video lightly dimmed + headline banner (asset) at the top.
  ev     B-roll dimmed+blurred + evidence card (asset) popping in near the top (y=60).
  ev2    ev, plus a banner (asset2) directly under the card.
  stack  two cards: asset at the top (e.g. news headline), asset2 under it (e.g. photo/finding).
  banev  banner (asset2) on top, card (asset) below it (good for a tall image like a specimen).
  img    still image (media = PNG/JPG) full-bleed with a slow push-in + optional banner (asset).
         Use for a real photo: the person in the story, a race photo.
  full   B-roll very dark + blurred + full-frame overlay PNG (asset, from fullframe.py).
  strip  very wide PNG (media) scrolling right-to-left (e.g. ecg_strip.py) + optional banner.

Every video kind gets a slow 8% push-in so stills of B-roll never feel static.
"""
import argparse
import os
import subprocess
import sys

from PIL import Image

W, H = 1080, 1920
DIM = "colorchannelmixer=rr=0.45:gg=0.45:bb=0.45,boxblur=6"
POP = "scale=w='trunc(iw*min(1,0.9+0.1*t/0.25)/2)*2':h=-2:eval=frame"  # 90%->100% in 0.25 s
ENC = ["-an", "-c:v", "libx264", "-preset", "veryfast", "-crf", "20", "-pix_fmt", "yuv420p", "-r", "30"]


def pushin(d):
    return ("scale=1080:1920:force_original_aspect_ratio=increase,crop=1080:1920,fps=30,"
            f"scale=w='trunc(1080*(1+0.08*t/{d})/2)*2':h=-2:eval=frame,crop=1080:1920,setsar=1")


def resolve(p, *dirs):
    if p in ("-", "", None):
        return None
    if os.path.isabs(p) or os.path.exists(p):
        return p
    for d in dirs:
        q = os.path.join(d, p)
        if os.path.exists(q):
            return q
    sys.exit(f"missing file: {p} (looked in {dirs})")


def height(p):
    return Image.open(p).height


def seg_cmd(kind, d, media, off, a, b, out):
    vin = ["-stream_loop", "-1", "-ss", str(off), "-i", media] if media else []
    still = lambda p: ["-loop", "1", "-framerate", "30", "-i", p]  # noqa: E731
    base = pushin(d)
    if kind == "ban":
        inp = vin + still(a)
        fc = f"[0:v]{base},colorchannelmixer=rr=0.7:gg=0.7:bb=0.7[bg];[bg][1:v]overlay=0:0[v]"
    elif kind == "ev":
        inp = vin + still(a)
        fc = (f"[0:v]{base},{DIM}[bg];[1:v]{POP}[im];"
              "[bg][im]overlay=x='(W-w)/2':y='60+(1-min(1,t/0.25))*30'[v]")
    elif kind == "ev2":
        inp = vin + still(a) + still(b)
        by = height(a) - 40
        fc = (f"[0:v]{base},{DIM}[bg];[1:v]{POP}[im];"
              f"[bg][im]overlay=x='(W-w)/2':y='20+(1-min(1,t/0.25))*30'[t1];[t1][2:v]overlay=0:{by}[v]")
    elif kind == "stack":
        inp = vin + still(a) + still(b)
        y2 = height(a) - 7
        fc = (f"[0:v]{base},{DIM}[bg];[1:v]{POP}[im];[2:v]{POP}[im2];"
              f"[bg][im2]overlay=x='(W-w)/2':y='{y2}+(1-min(1,t/0.25))*30'[t1];"
              "[t1][im]overlay=x='(W-w)/2':y=10[v]")
    elif kind == "banev":
        inp = vin + still(a) + still(b)
        fc = (f"[0:v]{base},{DIM}[bg];[1:v]{POP}[im];"
              "[bg][im]overlay=x='(W-w)/2':y='230+(1-min(1,t/0.25))*30'[t1];[t1][2:v]overlay=0:-40[v]")
    elif kind == "img":
        inp = still(media) + (still(a) if a else [])
        fc = f"[0:v]scale=2160:-2,{base},colorchannelmixer=rr=0.8:gg=0.8:bb=0.8"
        fc += "[bg];[bg][1:v]overlay=0:0[v]" if a else "[v]"
    elif kind == "full":
        inp = vin + still(a)
        fc = (f"[0:v]{base},colorchannelmixer=rr=0.3:gg=0.3:bb=0.3,boxblur=10[bg];[1:v]format=rgba[o];"
              "[bg][o]overlay=0:'(1-min(1,t/0.2))*25'[v]")
    elif kind == "strip":
        sw, sh = Image.open(media).size
        travel = max(0, sw - W)
        inp = still(media) + (still(a) if a else [])
        fc = (f"[0:v]crop={W}:{sh}:x='min({travel},t*{travel}/{d})':y=0,"
              f"pad={W}:{H}:0:300:color=0x040e08,setsar=1")
        fc += "[bg];[bg][1:v]overlay=0:-50[v]" if a else "[v]"
    else:
        sys.exit(f"unknown kind {kind}")
    return ["ffmpeg", "-nostdin", "-v", "error", "-y"] + inp + ["-t", str(d), "-filter_complex", fc,
                                                                "-map", "[v]"] + ENC + [out]


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("plan")
    ap.add_argument("--broll", default="broll")
    ap.add_argument("--assets", default="ev")
    ap.add_argument("--out", default="bg.mp4")
    ap.add_argument("--work", default="segs")
    ap.add_argument("--only", type=int, nargs="*", help="re-render only these segment indexes")
    a = ap.parse_args()
    os.makedirs(a.work, exist_ok=True)
    segs, prev_end = [], None
    for ln in open(a.plan):
        ln = ln.split("#", 1)[0].strip()
        if not ln or ln.lower().startswith("start"):
            continue
        cols = ln.split() + ["-"] * 7
        s, e, kind, media, off, asset, asset2 = cols[:7]
        s, e = float(s), float(e)
        if prev_end is not None and abs(s - prev_end) > 0.001:
            print(f"warning: gap/overlap at {prev_end} -> {s}", file=sys.stderr)
        prev_end = e
        segs.append((s, e, kind, media, 0 if off == "-" else float(off), asset, asset2))
    listfile = os.path.join(a.work, "list.txt")
    with open(listfile, "w") as lf:
        for i, (s, e, kind, media, off, asset, asset2) in enumerate(segs):
            out = os.path.join(a.work, f"s{i:02d}.mp4")
            lf.write(f"file '{os.path.abspath(out)}'\n")
            if a.only is not None and i not in a.only and os.path.exists(out):
                continue
            d = round(e - s, 3)
            m = resolve(media, a.broll, a.assets)
            cmd = seg_cmd(kind, d, m, off, resolve(asset, a.assets), resolve(asset2, a.assets), out)
            print(f"[{i:02d}] {s:7.2f}-{e:7.2f} {kind:5s} {media} {asset} {asset2}", flush=True)
            subprocess.run(cmd, check=True)
    subprocess.run(["ffmpeg", "-nostdin", "-v", "error", "-y", "-f", "concat", "-safe", "0",
                    "-i", listfile, "-c", "copy", a.out], check=True)
    dur = subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", a.out],
                         capture_output=True, text=True).stdout.strip()
    print(f"{a.out}: {dur}s")


if __name__ == "__main__":
    main()
