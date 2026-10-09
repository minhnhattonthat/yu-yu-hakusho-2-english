"""Fight HUD fighter names: 32x16 2bpp graphics, 128 bytes each (4 top tiles, then 4 bottom tiles), uncompressed
at file 0x41CCF + 128*i (bank $88). Render: python -X utf8 tools/hudnames.py ROM OUT.png [first] [count]
"""
import sys
from PIL import Image

sys.path.insert(0, __file__.rsplit("\\", 1)[0].rsplit("/", 1)[0])
from fontview import tile2bpp  # noqa: E402

BASE = 0x41CCF
SIZE = 128


def decode(data):
    px = [[0] * 32 for _ in range(16)]
    for t in range(8):
        tile = tile2bpp(data[t * 16:(t + 1) * 16])
        tx, ty = t % 4, t // 4
        for r in range(8):
            for c in range(8):
                px[ty * 8 + r][tx * 8 + c] = tile[r][c]
    return px


def encode(px):
    out = bytearray(SIZE)
    for t in range(8):
        tx, ty = t % 4, t // 4
        for r in range(8):
            for c in range(8):
                v = px[ty * 8 + r][tx * 8 + c]
                out[t * 16 + r * 2] |= (v & 1) << (7 - c)
                out[t * 16 + r * 2 + 1] |= (v >> 1 & 1) << (7 - c)
    return bytes(out)


if __name__ == "__main__":
    rom = open(sys.argv[1], "rb").read()
    first = int(sys.argv[3]) if len(sys.argv) > 3 else -4
    count = int(sys.argv[4]) if len(sys.argv) > 4 else 20
    pal = [(40, 40, 90), (255, 255, 255), (150, 150, 150), (0, 0, 0)]
    img = Image.new("RGB", (40 * 4, 20 * ((count + 3) // 4)), (0, 0, 0))
    for k in range(count):
        off = BASE + SIZE * (first + k)
        px = decode(rom[off:off + SIZE])
        for y in range(16):
            for x in range(32):
                img.putpixel(((k % 4) * 40 + x, (k // 4) * 20 + y), pal[px[y][x]])
    img.resize((img.width * 3, img.height * 3), Image.NEAREST).save(sys.argv[2])
