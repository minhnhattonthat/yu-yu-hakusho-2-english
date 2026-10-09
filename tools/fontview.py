"""Render a 16x16 2bpp glyph font (64 bytes/glyph) to PNG, each glyph labelled with its code.

    python -X utf8 tools/fontview.py FONT.bin OUT.png [--first 100] [--cols 8] [--scale 3]
"""
import sys
from PIL import Image, ImageDraw


def tile2bpp(b):
    return [[((b[r * 2] >> (7 - c)) & 1) | (((b[r * 2 + 1] >> (7 - c)) & 1) << 1) for c in range(8)] for r in range(8)]


def glyph(data):
    """64 bytes -> 16x16 pixel values; tiles stored TL, TR, BL, BR."""
    px = [[0] * 16 for _ in range(16)]
    for i, (tx, ty) in enumerate([(0, 0), (1, 0), (0, 1), (1, 1)]):
        t = tile2bpp(data[i * 16:(i + 1) * 16])
        for r in range(8):
            for c in range(8):
                px[ty * 8 + r][tx * 8 + c] = t[r][c]
    return px


def arg(name, default):
    return sys.argv[sys.argv.index(name) + 1] if name in sys.argv else default


if __name__ == "__main__":
    data = open(sys.argv[1], "rb").read()
    first, cols, S = int(arg("--first", "100"), 16), int(arg("--cols", "8")), int(arg("--scale", "3"))
    n = len(data) // 64
    cw, ch = 16 * S + 8, 16 * S + 14
    img = Image.new("RGB", (cols * cw, ((n + cols - 1) // cols) * ch), "white")
    d = ImageDraw.Draw(img)
    for g in range(n):
        px = glyph(data[g * 64:(g + 1) * 64])
        x0, y0 = (g % cols) * cw, (g // cols) * ch
        d.text((x0 + 2, y0), f"{first + g:03X}", fill=(0, 0, 255))
        d.rectangle([x0, y0 + 12, x0 + 16 * S - 1, y0 + 12 + 16 * S - 1], fill=(225, 235, 255))
        for y in range(16):
            for x in range(16):
                if px[y][x]:
                    d.rectangle([x0 + x * S, y0 + 12 + y * S, x0 + x * S + S - 1, y0 + 12 + y * S + S - 1], fill=(0, 0, 0))
    img.save(sys.argv[2])
