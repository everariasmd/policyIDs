#!/bin/bash
# Turn a still (AI-generated B-roll, a photo) into a 10 s B-roll clip framed for this format:
# the image sits in the visible zone above the presenter (y=250, 980 px wide) with a slow 5%
# push-in, over a dark blurred copy of itself. Use the mp4 as `media` in plan.tsv.
#
#   still_to_clip.sh IMG.png OUT.mp4 [SECONDS=10]
#
# For a Higgsfield image: the sandbox can't reach its CDN, so Tella import_from_url the image
# URL (video:false), get_source_thumbnail width 1920, and crop the letterboxed 4:3 image out
# of the 1920x1080 capture first: PIL crop (378,102,1542,978).
set -euo pipefail
IMG=$1; OUT=$2; D=${3:-10}
ffmpeg -nostdin -v error -y -loop 1 -framerate 30 -i "$IMG" -t "$D" -filter_complex "\
[0:v]split[a][b];\
[a]scale=1080:1920:force_original_aspect_ratio=increase,crop=1080:1920,boxblur=24,colorchannelmixer=rr=0.45:gg=0.45:bb=0.45[bg];\
[b]scale=w='trunc(980*(1+0.05*t/$D)/2)*2':h=-2:eval=frame,crop=980:min(ih\,736):(iw-980)/2:(ih-min(ih\,736))/2[band];\
[bg][band]overlay=(W-w)/2:250,setsar=1,format=yuv420p" -an -c:v libx264 -preset veryfast -crf 19 "$OUT"
echo "$OUT"
