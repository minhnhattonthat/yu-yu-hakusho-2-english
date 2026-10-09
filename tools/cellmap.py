"""Show which text cells (VRAM $6000, 4 tiles each) the BG3 tilemap places where, from a vramdump.lua dump.

    python -X utf8 tools/cellmap.py work/qa/X/vram.bin [--map 4800] [--wide] [--rows]
Prints the 32x28 screen as 8-px tile columns: the TL quadrant of cell c shows as c (3 chars), other text tiles as
'...', other tiles blank. --rows prints each screen row's runs instead: "row y: x=.. cells a-b (n)".
"""
import sys


def cells(vram, base, screens):
    grid = []
    for y in range(28):
        row = []
        for x in range(32 * screens):
            scr, xx = divmod(x, 32)
            a = (base + scr * 0x400 + y * 32 + xx) * 2
            e = vram[a] | vram[a + 1] << 8
            t = e & 0x3FF
            row.append(divmod(t, 4) if e and t < 1024 else None)
        grid.append(row)
    return grid


def main():
    vram = open(sys.argv[1], "rb").read()
    base = int(sys.argv[sys.argv.index("--map") + 1], 16) if "--map" in sys.argv else 0x4800
    grid = cells(vram, base, 2 if "--wide" in sys.argv else 1)
    if "--rows" in sys.argv:
        for y, row in enumerate(grid):
            tl = [(x, c) for x, v in enumerate(row) if v and v[1] == 0 for c in [v[0]]]
            if tl:
                print(f"row {y:2d}: x={tl[0][0]:2d} cells {tl[0][1]}-{tl[-1][1]} ({len(tl)})")
        return
    for y, row in enumerate(grid):
        print(f"{y:2d} " + "".join("   " if v is None else (f"{v[0]:3d}" if v[1] == 0 else "...") for v in row))


if __name__ == "__main__":
    main()
