#!/bin/bash
# Key the presenter (exported from Tella on solid #FF00FF magenta) over the background track.
#
#   composite.sh BG.mp4 FG.mp4 OUT.mp4 [extra ffmpeg input args, e.g. -t 6 for a quick test]
#
# - colorkey removes the magenta; the geq "despill" pulls magenta fringe out of hair/edges;
#   eroding + blurring the alpha softens the cut-out edge.
# - Audio: 80 Hz high-pass (rumble) + loudnorm to -14 LUFS (Instagram/TikTok loudness).
#   No music is added, on purpose.
# - A full 2-minute render takes ~10-15 min: run it in the background with a long timeout.
set -euo pipefail
BG=$1; FG=$2; OUT=$3; shift 3
ffmpeg -nostdin -v error -y "$@" -i "$BG" "$@" -i "$FG" -filter_complex "\
[1:v]format=rgba,colorkey=0xFF00FF:0.30:0.06,\
geq=r='r(X,Y)-max(0,min(r(X,Y),b(X,Y))-g(X,Y))':g='g(X,Y)':b='b(X,Y)-max(0,min(r(X,Y),b(X,Y))-g(X,Y))':a='alpha(X,Y)',\
split[c][a];[a]alphaextract,erosion,erosion,gblur=sigma=1.2[m];[c][m]alphamerge[fgk];\
[0:v][fgk]overlay=0:0:shortest=1,format=yuv420p[v];\
[1:a]highpass=f=80,loudnorm=I=-14:TP=-1.5:LRA=11[a]" \
  -map "[v]" -map "[a]" -c:v libx264 -preset medium -crf 19 -c:a aac -b:a 192k -movflags +faststart "$OUT"
ffprobe -v error -show_entries format=duration -of csv=p=0 "$OUT"
echo "DONE $OUT"
