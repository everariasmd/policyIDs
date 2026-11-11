"""Shared helpers for the green-screen reel scripts (fonts, colors, canvas size)."""
import glob
import os

W, H = 1080, 1920  # vertical 9:16 canvas

YELLOW = (250, 204, 21)
WHITE = (255, 255, 255)
RED = (239, 68, 68)
GREEN = (74, 222, 128)
HIGHLIGHT = (255, 226, 40)  # multiplied over page screenshots -> marker-pen look

COLORS = {"white": WHITE, "yellow": YELLOW, "red": RED, "green": GREEN}


def font_path():
    """Heaviest available sans font. Inter Black is the house style; DejaVu Bold is the fallback."""
    for pat in ("/usr/share/fonts/**/Inter-Black.otf", "/usr/share/fonts/**/Inter-ExtraBold.otf",
                "/usr/share/fonts/**/DejaVuSans-Bold.ttf"):
        hits = glob.glob(pat, recursive=True)
        if hits:
            return hits[0]
    raise SystemExit("No bold font found; install fonts-inter or fonts-dejavu")


def color(name_or_rgb):
    if isinstance(name_or_rgb, tuple):
        return name_or_rgb
    s = name_or_rgb.strip().lower()
    if s in COLORS:
        return COLORS[s]
    s = s.lstrip("#")
    return tuple(int(s[i:i + 2], 16) for i in (0, 2, 4))


def box(s):
    """'x0,y0,x1,y1' -> tuple of ints."""
    v = tuple(int(float(p)) for p in s.split(","))
    if len(v) != 4:
        raise ValueError(f"box needs 4 numbers: {s}")
    return v


def ensure_dir(path):
    d = os.path.dirname(os.path.abspath(path))
    os.makedirs(d, exist_ok=True)
