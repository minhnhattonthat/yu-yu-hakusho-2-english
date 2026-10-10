"""Render the on-screen sprites of a vramseq/ring dump (vram + oam + ppu) with palette indices as grey, to see which sprites
draw what. Prints nothing but writes OUT.png (256x224).

    python -X utf8 tools/oamview.py PREFIX OUT.png [--scale 2] [--sizes 8,16]   (PREFIX = path without .vram.bin etc.)
OBSEL is read from PREFIX.ppu.txt (oamBaseAddress, oamAddressOffset = word gap between name tables); --sizes = small,large.
"""
import sys
from PIL import Image


def arg(name, default):
    return sys.argv[sys.argv.index(name) + 1] if name in sys.argv else default


def main():
    p = sys.argv[1]
    vram = open(p + ".vram.bin", "rb").read()
    oam = open(p + ".oam.bin", "rb").read()
    ppu = dict(l.split("=", 1) for l in open(p + ".ppu.txt").read().split("\n") if "=" in l)
    base = int(ppu["ppu.oamBaseAddress"]) * 0x2000 // 1 if int(ppu["ppu.oamBaseAddress"]) < 8 else int(ppu["ppu.oamBaseAddress"])
    gap = int(ppu["ppu.oamAddressOffset"])
    small, large = (int(x) for x in arg("--sizes", "8,16").split(","))
    sc = int(arg("--scale", "2"))
    img = Image.new("L", (512, 224), 0)
    hi = oam[512:544]
    for i in range(127, -1, -1):
        x, y, t, a = oam[i * 4:i * 4 + 4]
        h = (hi[i // 4] >> ((i % 4) * 2)) & 3
        x |= (h & 1) << 8
        if x >= 256:
            x -= 512
        size = large if h >> 1 else small
        for ty in range(size // 8):
            for tx in range(size // 8):
                n = (t & 0xF0) + (((t & 0x0F) + tx) & 0x0F) + ty * 16 if True else t
                n = (t + tx + ty * 16) & 0xFF
                addr = (base + (gap if a & 1 else 0) + n * 16) * 2 & 0xFFFF
                for r in range(8):
                    for c in range(8):
                        v = 0
                        for pl in range(4):
                            b = vram[(addr + (pl // 2) * 32 + r * 2 + (pl & 1)) & 0xFFFF]
                            v |= ((b >> (7 - c)) & 1) << pl
                        if not v:
                            continue
                        px = (7 - c if a & 0x40 else c) + (size // 8 - 1 - tx if a & 0x40 else tx) * 8
                        py = (7 - r if a & 0x80 else r) + (size // 8 - 1 - ty if a & 0x80 else ty) * 8
                        X, Y = x + px, y + py
                        if 0 <= X < 256 and 0 <= Y < 224:
                            img.putpixel((X, Y), 40 + v * 14)
    img.crop((0, 0, 256, 224)).resize((256 * sc, 224 * sc), Image.NEAREST).save(sys.argv[2])


if __name__ == "__main__":
    main()
