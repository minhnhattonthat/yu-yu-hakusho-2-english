"""Decompress an LZ block from the ROM and render its tiles as a grey sheet (palette indices), tile numbers on the left.

    python -X utf8 tools/gfxview.py ROM BANK:ADDR OUT.png [--bpp 2|4] [--cols 16] [--scale 2] [--plain]
--plain = block was loaded with $81:8C35 (no tile re-interleave); default is $81:8CF3 (interleave, SNES 2bpp/4bpp tiles).
"""
import sys
from PIL import Image
import lz


def arg(name, default):
    return sys.argv[sys.argv.index(name) + 1] if name in sys.argv else default


def tile_px(data, a, bpp):
    px = [[0] * 8 for _ in range(8)]
    for r in range(8):
        for p in range(bpp // 2):
            lo, hi = data[a + p * 16 + r * 2], data[a + p * 16 + r * 2 + 1]
            for c in range(8):
                px[r][c] |= (((lo >> (7 - c)) & 1) | (((hi >> (7 - c)) & 1) << 1)) << (p * 2)
    return px


def sheet(data, bpp, cols, scale):
    n = len(data) // (8 * bpp)
    rows = (n + cols - 1) // cols
    img = Image.new("L", (cols * 8, rows * 8))
    for t in range(n):
        px = tile_px(data, t * 8 * bpp, bpp)
        for r in range(8):
            for c in range(8):
                img.putpixel(((t % cols) * 8 + c, (t // cols) * 8 + r), px[r][c] * 255 // ((1 << bpp) - 1))
    return img.resize((img.width * scale, img.height * scale), Image.NEAREST)


def main():
    rom = open(sys.argv[1], "rb").read()
    bank, addr = (int(x, 16) for x in sys.argv[2].split(":"))
    data = lz.decompress(rom, lz.snes_off(bank, addr))
    if "--plain" not in sys.argv:
        data = lz.interleave(data)
    sheet(data, int(arg("--bpp", "4")), int(arg("--cols", "16")), int(arg("--scale", "2"))).save(sys.argv[3])
    print(len(data), "bytes")


if __name__ == "__main__":
    main()
