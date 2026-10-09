"""Options screen in English (docs/re/options.md).

The screen's BG3 font ($B2:DC0D, LZ, 0xED0 bytes -> VRAM $6000) and BG3 map ($B2:E732, LZ, 0x800 bytes ->
$7E2800 -> VRAM $6C00) are replaced by raw data: the original plus English 16x16 cells (4 tiles TL,TR,BL,BR, like
text cells). Dynamic values come from the label writer $81:E0FE: label index -> pointer table $81:E12E -> list of
cell words ($2000 | first tile), $FFFF-terminated.
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
import font  # noqa: E402
import lz  # noqa: E402
import text  # noqa: E402

CHR_SRC, MAP_SRC = (0xB2, 0xDC0D), (0xB2, 0xE732)
PTRS, NPTRS = 0x0E12E, 14                 # $81:E12E label pointer table
LIST_ADDR = 0xFF30                         # $81:FF30: new label lists (bank $81 tail after the HUD tables)
CELLS = 0x60                               # VRAM $6000-$6BFF: 96 cells (the map sits at $6C00)
FREE_CELLS = list(range(0x3B, CELLS)) + list(range(0x01, 0x22))   # after "N", then the old kana/kanji cells
ATTR = 0x2000

# static labels: (row, col, cells, text); old tiles in [col, col + clear) of rows row/row+1 are blanked first
STATIC = [
    (4, 3, 7, "Game Level"),
    (18, 10, 6, ""), (18, 12, 4, "Auto Mode"),
    (20, 13, 3, ""), (20, 12, 3, "Defense"),
] + [(r, 12, 4, t) for r, t in ((10, "Light Punch"), (12, "Strong Punch"), (14, "Light Kick"), (16, "Strong Kick"))]
TIGHT = {"Light Punch", "Strong Punch", "Light Kick", "Strong Kick", "Button"}   # 1 px less per letter
BUTTON_ROWS, BUTTON_COLS = (10, 12, 14, 16), (5, 25)   # "ボタン" after each button icon (1P, 2P): 4 columns, the
                                                         # 1-player blanking ($81:DD61) clears 2P cols 23-28 only
# dynamic lists: label index -> (text, cells written, padded with blank cells)
LISTS = {0: ("Easy", 5), 1: ("Normal", 5), 2: ("Hard", 5), 3: ("Very Hard", 5),
         10: ("Low", 3), 11: ("Normal", 3), 12: ("High", 3)}


def advance(c, widths, tight):
    return widths[ord(c) - 0x20] - (1 if tight and c != " " else 0)


def strip(s, ncells, glyphs, widths):
    """16 x 16*ncells pixels of s in the VWF font."""
    px = [[0] * (16 * ncells + 8) for _ in range(16)]
    x = 0
    for c in s:
        g = glyphs[ord(c) - 0x20]
        for y in range(16):
            for xx in range(8):
                if g[y][xx] and not px[y][x + xx]:          # tight text: keep the stroke over a neighbour's shadow
                    px[y][x + xx] = g[y][xx]
                elif g[y][xx] == font.STROKE:
                    px[y][x + xx] = g[y][xx]
        x += advance(c, widths, s in TIGHT)
    if x - 1 > 16 * ncells:
        raise SystemExit(f"options: {s!r} is {x}px > {ncells} cells")
    return px


def cell_bytes(px, c):
    out = bytearray(64)
    for t, (tx, ty) in enumerate([(0, 0), (1, 0), (0, 1), (1, 1)]):
        for r in range(8):
            for b in range(8):
                v = px[ty * 8 + r][c * 16 + tx * 8 + b]
                out[t * 16 + r * 2] |= (v & 1) << (7 - b)
                out[t * 16 + r * 2 + 1] |= (v >> 1 & 1) << (7 - b)
    return bytes(out)


def build(rom):
    _, widths, glyphs = font.build()
    chr_ = bytearray(lz.interleave(lz.decompress(rom, lz.snes_off(*CHR_SRC))))
    chr_ += bytes(CELLS * 64 - len(chr_))
    tmap = bytearray(lz.decompress(rom, lz.snes_off(*MAP_SRC)))
    free = iter(FREE_CELLS)
    made = {}

    def cells(s, n):
        if (s, n) not in made:
            used = -(-(sum(advance(c, widths, s in TIGHT) for c in s) - 1) // 16) if s else 0
            px = strip(s, n, glyphs, widths)
            ids = []
            for c in range(used):
                k = next(free)
                chr_[k * 64:(k + 1) * 64] = cell_bytes(px, c)
                ids.append(k)
            made[s, n] = ids
        return made[s, n]

    def put(row, col, tile):
        o = (row * 32 + col) * 2
        tmap[o:o + 2] = (ATTR | tile).to_bytes(2, "little")

    for row, col, n, s in STATIC:
        for r in (row, row + 1):
            for c in range(col, col + 2 * n):
                put(r, c, 0)
        for i, k in enumerate(cells(s, n)):
            put(row, col + 2 * i, 4 * k)
            put(row, col + 2 * i + 1, 4 * k + 1)
            put(row + 1, col + 2 * i, 4 * k + 2)
            put(row + 1, col + 2 * i + 1, 4 * k + 3)
    button = cells("Button", 2)
    for row in BUTTON_ROWS:
        for col0 in BUTTON_COLS:
            for r in (row, row + 1):
                for c in range(col0, col0 + 4):
                    put(r, c, 0)
            for i, k in enumerate(button):
                put(row, col0 + 2 * i, 4 * k)
                put(row, col0 + 2 * i + 1, 4 * k + 1)
                put(row + 1, col0 + 2 * i, 4 * k + 2)
                put(row + 1, col0 + 2 * i + 1, 4 * k + 3)
    ptrs = bytearray(rom[PTRS:PTRS + 2 * NPTRS])
    lists = bytearray()
    for idx, (s, n) in LISTS.items():
        ids = cells(s, n)
        words = [ATTR | 4 * k for k in ids] + [ATTR] * (n - len(ids)) + [0xFFFF]
        ptrs[2 * idx:2 * idx + 2] = (LIST_ADDR + len(lists)).to_bytes(2, "little")
        lists += b"".join(w.to_bytes(2, "little") for w in words)
    if LIST_ADDR + len(lists) > 0x10000:
        raise SystemExit("options: label lists overflow bank $81")
    return bytes(chr_), bytes(tmap), bytes(ptrs), bytes(lists)


if __name__ == "__main__":
    out = build(text.ROM.read_bytes())
    for name, data in zip(("opt_chr", "opt_map", "opt_ptrs", "opt_lists"), out):
        (text.ROOT / "build" / f"{name}.bin").write_bytes(data)
    print("options:", [len(d) for d in out])
