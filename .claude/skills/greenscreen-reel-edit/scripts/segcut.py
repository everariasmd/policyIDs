"""Memory-safe frame-exact cutting: each kept segment is encoded on its own (input seek +
frame count), then the pieces are joined with the concat demuxer. One big trim/concat graph
buffered the whole take in RAM (14 GB) on a 134 s source."""
import os, subprocess


def cut_segments(src, segs, out, vf_for=lambda i: None, crf=14, preset="fast"):
    tmp = out + ".parts"
    os.makedirs(tmp, exist_ok=True)
    names = []
    for i, (a, b) in enumerate(segs):
        k0, k1 = round(a * 30), round(b * 30)
        n = k1 - k0
        if n <= 0:
            continue
        name = os.path.join(tmp, f"p{i:03d}.mp4")
        cmd = ["ffmpeg", "-nostdin", "-v", "error", "-y", "-ss", f"{(k0 - 0.5) / 30:.4f}", "-i", src, "-an",
               "-frames:v", str(n)]
        vf = vf_for(i)
        cmd += ["-vf", (vf + "," if vf else "") + "setsar=1,format=yuv420p"]
        cmd += ["-r", "30", "-c:v", "libx264", "-preset", preset, "-crf", str(crf), name]
        subprocess.run(cmd, check=True)
        names.append(name)
    lst = os.path.join(tmp, "list.txt")
    open(lst, "w").write("".join(f"file '{os.path.abspath(nm)}'\n" for nm in names))
    subprocess.run(["ffmpeg", "-nostdin", "-v", "error", "-y", "-f", "concat", "-safe", "0", "-i", lst, "-c", "copy", out], check=True)
    for nm in names:
        os.remove(nm)
    os.remove(lst)
    os.rmdir(tmp)
