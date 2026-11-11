#!/bin/bash
# Lift the action of a B-roll clip into the visible zone ABOVE the presenter's head.
#
#   reframe_broll.sh SRC.mp4 OUT.mp4 Y0 H [TOP=250] [ZOOM=0.8]
#
# Most vertical stock clips frame the subject in the middle or lower half (a person planking
# on the floor, a leg exercise), which is exactly where the presenter cut-out sits, so the
# viewer never sees it. This crops the band Y0..Y0+H (in the clip's 1080x1920-scaled
# frame), scales it by ZOOM, and places it at y=TOP over a dark blurred copy of the same
# clip. Use the result like any other B-roll in plan.tsv.
# Find Y0/H by looking at a frame first, e.g. ffmpeg -ss 3 -i SRC -frames:v 1 -vf scale=270:-2 f.png
set -euo pipefail
SRC=$1; OUT=$2; Y0=$3; H=$4; TOP=${5:-250}; ZOOM=${6:-0.8}
ffmpeg -nostdin -v error -y -i "$SRC" -filter_complex "\
[0:v]scale=1080:1920:force_original_aspect_ratio=increase,crop=1080:1920,fps=30,split[a][b];\
[a]boxblur=20,colorchannelmixer=rr=0.5:gg=0.5:bb=0.5[bg];\
[b]crop=1080:$H:0:$Y0,scale=trunc(iw*$ZOOM/2)*2:-2[band];\
[bg][band]overlay=(W-w)/2:$TOP,setsar=1" -an -c:v libx264 -preset veryfast -crf 19 "$OUT"
echo "$OUT"
