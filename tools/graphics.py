"""English versions of the graphics that are not text-engine strings (docs/re/graphics.md): mini-game rage gauge, title
screen, intro names. Each function edits blocks through gfx.Gfx; build.py calls apply().
"""
import struct
import sys
from pathlib import Path

from PIL import Image

sys.path.insert(0, str(Path(__file__).parent))
import gfx  # noqa: E402
import gfxtext  # noqa: E402

# Free file-offset ranges for re-compressed blocks that cannot overwrite their original (see gfx.Gfx.apply): bank tails
# of $B4, $B5 (after the options map), $B1 (after the options font), $B2, $8A.
FREE = [(0x1A6EE9, 0x1A8000), (0x1AF680, 0x1B0000), (0x18F900, 0x190000), (0x197A23, 0x198000), (0x057B00, 0x058000)]


def gauge(g):
    """Mini-game rage gauge: 怒 = 3x4 cells at BG1 tiles $18-$1F,$28-$2B (block $B2:EB9E loads at tile $10, 4bpp, pal 1:
    15 = white, 14 = black). English "RAGE" fills the two cell rows beside the bar."""
    data = bytearray(g.raw(0xB2, 0xEB9E))
    top, bot, blank = (0x19, 0x1A, 0x1B, 0x2A), (0x1C, 0x1D, 0x1E, 0x2B), (0x18, 0x1F, 0x28, 0x29)
    zero = bytes(32)
    for t in blank:
        data[(t - 0x10) * 32:(t - 0x10) * 32 + 32] = zero
    tiles = gfxtext.slice_tiles(gfxtext.render("RAGE", stroke=15, shadow=14, pad=2), 4, 2)
    for row, cells in enumerate((top, bot)):
        for col, t in enumerate(cells):
            data[(t - 0x10) * 32:(t - 0x10) * 32 + 32] = gfx.tile_bytes(tiles[row][col], 4)
    g.replace(0xB2, 0xEB9E, data)


LOGO = Path(__file__).resolve().parent.parent / "art" / "title_logo.png"   # tools/make_logo.py
NAMES = LOGO.with_name("intro_names.png")                                    # tools/make_names.py
TITLE_ONLY = lambda b_at, a_at: min(b_at, a_at) > 0x17C700   # not the namco splash ($AF:C60B), which shares the text tiles


def _tile_allocator(tiles, first, bpp):
    """Returns tile(px8x8) -> tile number: blank cells -> `blank`, equal cells share a number from `pool`."""
    cache, pool = {}, iter(first)

    def tile(px, blank):
        if not any(any(r) for r in px):
            return blank
        key = tuple(map(tuple, px))
        if key not in cache:
            n = next(pool, None)
            if n is None:
                raise ValueError("title graphics need more tiles than the block has")
            tiles[n * 8 * bpp:(n + 1) * 8 * bpp] = gfx.tile_bytes(px, bpp)
            cache[key] = n
        return cache[key]
    return tile


def _cut(grid, r, c):
    return [[grid[r * 8 + y][c * 8 + x] for x in range(8)] for y in range(8)]


def title_bg1(g):
    """BG1 (4bpp, $B4:8000 tiles, $B4:99A8 map: screen 1 rows 0-10 = logo, screen 2 rows 11-13 = subtitle): the logo comes
    from art/title_logo.png (32x11 cells), the subtitle is rendered with the VWF font; every tile is re-deduplicated."""
    tiles = bytearray(g.raw(0xB4, 0x8000))
    ents = list(struct.unpack("<1024H", g.raw(0xB4, 0x99A8, il=False)))
    n = len(tiles) // 32
    tiles[64:] = bytes(len(tiles) - 64)           # tiles 0/1 stay blank
    tile = _tile_allocator(tiles, range(2, n), 4)
    png = Image.open(LOGO)
    logo = [[png.getpixel((x, y)) for x in range(256)] for y in range(88)]
    for r in range(11):
        for c in range(32):
            e = ents[r * 32 + c]
            ents[r * 32 + c] = (e & 0xFC00) | tile(_cut(logo, r, c), 1)
    sub = gfxtext.render("Fighting Chapter", stroke=1, shadow=9)
    x0 = (256 - gfxtext.width("Fighting Chapter")) // 2
    line = [[0] * 256 for _ in range(16)]
    for y in range(16):
        for x, v in enumerate(sub[y]):
            if x0 + x < 256:
                line[y][x0 + x] = v
    for r in range(3):                           # screen 2 rows 11-13 start at entry 352
        for c in range(32):
            k = 352 + r * 32 + c
            ents[k] = (ents[k] & 0xFC00) | (tile(_cut(line, r, c), 1) if r < 2 else 1)
    g.replace(0xB4, 0x8000, tiles)
    g.replace(0xB4, 0x99A8, struct.pack("<1024H", *ents), il=False)


def title_bg3(g):
    """BG3 (2bpp, $B4:9354 tiles, $B4:9CB1 map = screen rows 14-26): the two copyright lines (rows 19-20, 22-23) become
    English; the (c) cells, PUSH START, namcot and the 1994 line keep their tiles; new cells reuse the freed ones."""
    t = bytearray(g.raw(0xB4, 0x9354))
    m = list(struct.unpack("<416H", g.raw(0xB4, 0x9CB1, il=False)))
    rows = {19: "Yoshihiro Togashi / Shueisha", 22: "Fuji Television / Studio Pierrot"}
    at = lambda y: (y - 14) * 32
    keep = {0} | {e & 0x3FF for y in range(14, 27) if y not in (19, 20, 22, 23) for e in m[at(y):at(y) + 32]}
    copy = [[gfx.tile_px(t, n, 2) for n in row] for row in ((0x20, 0x21), (0x30, 0x31))]   # the (c) sign, 2x2 cells
    copy_px = [[copy[y // 8][x // 8][y % 8][x % 8] for x in range(16)] for y in range(16)]
    free = [n for n in range(1, len(t) // 16) if n not in keep]
    for n in free:
        t[n * 16:(n + 1) * 16] = bytes(16)
    tile = _tile_allocator(t, free, 2)
    for y, s in rows.items():
        attr = next(e & 0xFC00 for e in m[at(y):at(y) + 32] if e)
        for yy in (y, y + 1):
            m[at(yy):at(yy) + 32] = [0] * 32
        text = gfxtext.render(s, stroke=2, shadow=3)
        x0 = (256 - (17 + gfxtext.width(s))) // 2
        line = [[0] * 256 for _ in range(16)]
        for yy in range(16):
            line[yy][x0:x0 + 16] = copy_px[yy]
            for x, v in enumerate(text[yy]):
                if x0 + 17 + x < 256 and v:
                    line[yy][x0 + 17 + x] = v
        for r in range(2):
            for c in range(32):
                n = tile(_cut(line, r, c), 0)
                m[at(y + r) + c] = (attr | n) if n else 0
    g.replace(0xB4, 0x9354, t, only=TITLE_ONLY)
    g.replace(0xB4, 0x9CB1, struct.pack("<416H", *m), il=False, only=TITLE_ONLY)


def intro_names(g):
    """Attract-mode fighter names (BG3, 2bpp, $8A:EAC9): 4 names of 8x4 tiles in a 16-tile-wide layout, replaced by
    art/intro_names.png (tools/make_names.py). The tilemaps that place them stay as they are."""
    d = bytearray(g.raw(0x8A, 0xEAC9))
    png = Image.open(NAMES)
    for ty in range(8):
        for tx in range(16):
            px = [[png.getpixel((tx * 8 + x, ty * 8 + y)) for x in range(8)] for y in range(8)]
            d[(ty * 16 + tx) * 16:(ty * 16 + tx + 1) * 16] = gfx.tile_bytes(px, 2)
    d[0x80 * 16:0x81 * 16] = bytes(16)           # stray sparkle tile the old Yusuke map still points at
    g.replace(0x8A, 0xEAC9, d)


def apply(rom, orig):
    g = gfx.Gfx(orig)
    intro_names(g)
    gauge(g)
    title_bg1(g)
    title_bg3(g)
    return g.apply(rom, FREE)
