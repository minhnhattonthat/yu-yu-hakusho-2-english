"""Render one BG layer of a vramdump.lua dump (palette indices as grey), to find which tiles draw a screen.

    python -X utf8 tools/bgview.py vram.bin OUT.png --chr 2000 --map 5800 [--bpp 4] [--w 32] [--h 32] [--scale 2]
chr/map are the word addresses printed in ppu.txt (layers[n].chrAddress / tilemapAddress, hex here). --w/--h = tiles.
Tile numbers are drawn into the PNG only with --ids (small, for locating tiles).
"""
import sys
from PIL import Image


def arg(name, default):
    return sys.argv[sys.argv.index(name) + 1] if name in sys.argv else default


def tile(vram, base, n, bpp):
    sz = 8 * bpp
    a = base + n * sz
    px = [[0] * 8 for _ in range(8)]
    for r in range(8):
        for p in range(bpp // 2):
            lo, hi = vram[a + p * 16 + r * 2], vram[a + p * 16 + r * 2 + 1]
            for c in range(8):
                px[r][c] |= (((lo >> (7 - c)) & 1) | (((hi >> (7 - c)) & 1) << 1)) << (p * 2)
    return px


def main():
    vram = open(sys.argv[1], "rb").read()
    chr_b = int(arg("--chr", "0"), 16) * 2
    map_b = int(arg("--map", "0"), 16) * 2
    bpp = int(arg("--bpp", "4"))
    w, h, sc = int(arg("--w", "32")), int(arg("--h", "32")), int(arg("--scale", "2"))
    top = (1 << bpp) - 1
    img = Image.new("L", (w * 8, h * 8))
    cache = {}
    for y in range(h):
        for x in range(w):
            scr = (x // 32) + (y // 32) * (2 if w > 32 else 1)
            a = map_b + scr * 0x800 + ((y % 32) * 32 + x % 32) * 2
            e = vram[a] | vram[a + 1] << 8
            n = e & 0x3FF
            if (n, e >> 14) not in cache:
                cache[(n, e >> 14)] = tile(vram, chr_b, n, bpp)
            t = cache[(n, e >> 14)]
            for r in range(8):
                for c in range(8):
                    xx = 7 - c if e & 0x4000 else c
                    yy = 7 - r if e & 0x8000 else r
                    img.putpixel((x * 8 + xx, y * 8 + yy), t[r][c] * 255 // top)
    img.resize((w * 8 * sc, h * 8 * sc), Image.NEAREST).save(sys.argv[2])


if __name__ == "__main__":
    main()
