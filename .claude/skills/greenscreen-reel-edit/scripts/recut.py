#!/usr/bin/env python3
"""Compute Tella cuts from the AUDIO, not from transcript word times.

Why: Tella's word timestamps are often 60-160 ms off. Cutting exactly at a word boundary
(cut_clip_by_transcript, or update_clip with word times) clips the tail of the kept word or
leaves a fragment of the removed one ("...ause fat loss", "If- If you wanna"). The creator
heard that as being "cut off". And remove_silences leaves 300-600 ms pauses that they heard
as "the edit pauses". This script fixes both:

  1. every removed span (retake / false start) starts and ends at the quietest 10 ms frame
     near the transcript boundary, and
  2. every pause longer than --max-pause is shortened to --keep-after ms after the speech
     plus --keep-before ms before the next speech (a natural breath, no dead air),
  3. any seam that still touches loud audio is reported.

Input: the UNCUT audio. Get it by saving the clip's cuts, update_clip {cuts: []}, export
without subtitles, and downloading it (rehost through vidiq_video_upload if needed). Then:

    recut.py uncut.mp4 --remove 13370-13760 --remove 64046-68034 ... --out cuts.json
    # (removed spans = transcript source times of the words to drop, from get_transcript
    #  with includeCut: true; refine by hand with --show T to print levels around time T)

Apply with update_clip {cuts: <cuts.json>} and re-export. Afterwards hide (hidden: true) any
transcript word whose start falls just before a removed span. Tella treats it as kept and it
would flash in the captions.
"""
import argparse
import json
import math
import os
import struct
import subprocess
import sys
import tempfile


def levels(path):
    raw = os.path.join(tempfile.mkdtemp(), "a.raw")
    subprocess.run(["ffmpeg", "-nostdin", "-v", "error", "-y", "-i", path, "-ac", "1", "-ar", "16000",
                    "-f", "s16le", raw], check=True)
    d = open(raw, "rb").read()
    n = len(d) // 2
    s = struct.unpack("<%dh" % n, d)
    F = 160  # 10 ms
    out = []
    for i in range(0, n - F, F):
        seg = s[i:i + F]
        r = math.sqrt(sum(x * x for x in seg) / F)
        out.append(20 * math.log10(max(r, 1) / 32768))
    return out


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("audio")
    ap.add_argument("--remove", action="append", default=[], help="START-END ms of words to drop")
    ap.add_argument("--snap", type=int, default=120, help="search +-ms around each removed boundary")
    ap.add_argument("--thr", type=float, default=-38, help="speech threshold dBFS (10 ms RMS)")
    ap.add_argument("--max-pause", type=int, default=280, help="shorten pauses longer than this (ms)")
    ap.add_argument("--keep-after", type=int, default=130, help="silence kept after speech (ms)")
    ap.add_argument("--keep-before", type=int, default=100, help="silence kept before speech (ms)")
    ap.add_argument("--tail", type=int, default=300, help="silence kept after the last word (ms)")
    ap.add_argument("--show", type=int, action="append", default=[], help="print levels around T ms")
    ap.add_argument("--out", default="cuts.json")
    a = ap.parse_args()

    db = levels(a.audio)
    N = len(db)
    for t in a.show:
        k = t // 10
        print(t, " ".join(f"{(k + j) * 10}:{int(db[k + j])}" for j in range(-25, 26) if 0 <= k + j < N))
    if a.show and not a.remove:
        return

    def quietest(t):
        lo, hi = max(0, (t - a.snap) // 10), min(N - 1, (t + a.snap) // 10)
        return min(range(lo, hi + 1), key=lambda k: db[k])

    rm = [False] * N
    for span in a.remove:
        s, e = (int(x) for x in span.split("-"))
        s0, e0 = quietest(s), quietest(e)
        for k in range(s0, e0 + 1):
            rm[k] = True
        print(f"remove {s}-{e} -> {s0 * 10}-{e0 * 10}  (levels {db[s0]:.0f} / {db[e0]:.0f} dB)", file=sys.stderr)

    loud = lambda k: db[k] > a.thr  # noqa: E731
    kept = [k for k in range(N) if not rm[k]]
    cut = {k for k in range(N) if rm[k]}
    voiced = [k for k in kept if loud(k)]
    cut |= set(range(0, max(0, voiced[0] - 8)))
    cut |= set(range(min(N, voiced[-1] + a.tail // 10), N))
    ka, kb, mp = a.keep_after // 10, a.keep_before // 10, a.max_pause // 10
    i = 0
    while i < len(kept):
        if loud(kept[i]):
            i += 1
            continue
        j = i
        while j < len(kept) and not loud(kept[j]):
            j += 1
        run = kept[i:j]
        if i > 0 and j < len(kept) and len(run) > mp:
            cut |= set(run[ka:len(run) - kb])
        i = j
    ranges = []
    for k in sorted(cut):
        if ranges and k == ranges[-1][1]:
            ranges[-1][1] = k + 1
        else:
            ranges.append([k, k + 1])
    ranges = [[s * 10, e * 10] for s, e in ranges if (e - s) >= 8 or any(rm[t] for t in range(s, e))]
    total_ms = N * 10
    if ranges and ranges[-1][1] >= total_ms:  # Tella rejects a cut past the clip end
        ranges[-1][1] = total_ms - 10
    removed = sum(e - s for s, e in ranges)
    print(f"{len(ranges)} cuts, {removed / 1000:.2f}s removed, final {(total_ms - removed) / 1000:.2f}s", file=sys.stderr)
    bad = [(s, e) for s, e in ranges if s > 0 and e < total_ms - 20 and
           (db[s // 10 - 1] > a.thr + 3 or db[min(N - 1, e // 10)] > a.thr + 3)]
    if bad:
        print("LOUD SEAMS (check with --show and adjust --remove):", bad, file=sys.stderr)
    json.dump([{"startTimeMs": s, "durationMs": e - s} for s, e in ranges], open(a.out, "w"))
    print(a.out)


if __name__ == "__main__":
    main()
