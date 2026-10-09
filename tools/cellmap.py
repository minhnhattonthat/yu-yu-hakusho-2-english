"""Show which text cells (VRAM $6000, 4 tiles each) the BG3 tilemap places where, from a vramdump.lua dump.

    python -X utf8 tools/cellmap.py work/qa/X/vram.bin [--map 4800] [--wide]
Prints the 32x28 visible screen (first 32-wide screen) as 8-px tile columns: TL quadrant of cell c shows as c
(decimal, 2 chars), other quadrants as '..', non-text tiles as '  '.
"""
import sys


def main():
    vram = open(sys.argv[1], "rb").read()
    base = int(sys.argv[sys.argv.index("--map") + 1], 16) if "--map" in sys.argv else 0x4800
    screens = 2 if "--wide" in sys.argv else 1
    for y in range(28):
        row = []
        for x in range(32 * screens):
            scr, xx = divmod(x, 32)
            a = (base + scr * 0x400 + y * 32 + xx) * 2
            e = vram[a] | vram[a + 1] << 8
            t = e & 0x3FF
            if t < 256 and e != 0:
                c, q = divmod(t, 4)
                row.append(f"{c:2d}" if q == 0 else "..")
            else:
                row.append("  ")
        print(f"{y:2d} " + "".join(row))


if __name__ == "__main__":
    main()
