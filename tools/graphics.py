"""English versions of the graphics that are not text-engine strings (docs/re/graphics.md): mini-game rage gauge, title
screen, intro names. Each function edits blocks through gfx.Gfx; build.py calls apply().
"""
import json
import struct
import sys
from pathlib import Path

from PIL import Image

sys.path.insert(0, str(Path(__file__).parent))
import fit  # noqa: E402
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
    """Attract-mode fighter names (BG3, 2bpp, $8A:EAC9 tiles, $8A:F2D1 map): art/intro_names.png (tools/make_names.py,
    4 strips of 32 px) is cut into deduplicated tiles and each name's 4 map rows are rewritten, centred where the kanji
    were. Map rows per name (4 rows x 32 entries, copied to VRAM as one 0x100 byte chunk): Yusuke 12, Kurama 4,
    Kuwabara 8, Hiei 0; kanji centre x in pixels from the old map columns."""
    d = bytearray(len(g.raw(0x8A, 0xEAC9)))
    ents = list(struct.unpack("<1024H", g.raw(0x8A, 0xF2D1, il=False)))
    png = Image.open(NAMES)
    tile = _tile_allocator(d, range(1, len(d) // 16), 2)
    for i, (row, centre) in enumerate(((12, 128), (4, 200), (8, 56), (0, 56))):
        cols = [x for x in range(png.width) if any(png.getpixel((x, i * 32 + y)) for y in range(32))]
        w = max(cols) + 1
        n = (w + 7) // 8
        x0 = max(0, min(256 - n * 8, centre - w // 2)) // 8     # first map column; text starts at its left edge
        for r in range(4):
            for c in range(32):
                ents[(row + r) * 32 + c] = 0x2000
            for c in range(n):
                px = [[png.getpixel((c * 8 + x, i * 32 + r * 8 + y)) if c * 8 + x < png.width else 0
                       for x in range(8)] for y in range(8)]
                ents[(row + r) * 32 + x0 + c] = 0x2000 | tile(px, 0)
    g.replace(0x8A, 0xEAC9, d)
    g.replace(0x8A, 0xF2D1, struct.pack("<1024H", *ents), il=False)


def mode_headers(rom):
    """Centre the mode-select banner titles. The banner is a 16-line HDMA strip (channel 1 -> BG3HOFS/VOFS, table at
    $7E:0220) that scrolls one label row of the BG3 map into view; its horizontal scroll comes from $80:F735 (word per
    mode 0-3: Story, Tournament, Battle, Training), the Sound template $80:F8F7 (+6) and, for "Mode Select" itself, the
    main template $80:F8BC (+1). Label ink starts at map column 9 (47 for Mode Select), so screen x = 8 * col - scroll;
    the banner centre is x = 128. Map columns that scroll in from the left are blank."""
    msgs = json.loads((Path(__file__).resolve().parent.parent / "script" / "messages.json").read_text(encoding="utf-8"))
    runs = [r.strip() for r in next(e for e in msgs if e["id"] == "M004")["en"].split("|")]

    def scroll(label, col):
        ink = sum(fit.WIDTHS[ord(c) - 0x20] for c in label) - 1   # last column is the gap
        return round(8 * col + ink / 2 - 128) & 0xFFFF

    for i, label in enumerate((runs[0], runs[2], runs[3], runs[4])):
        rom[0x7735 + 2 * i:0x7737 + 2 * i] = scroll(label, 9).to_bytes(2, "little")
    rom[0x78FD:0x78FF] = scroll(runs[5], 9).to_bytes(2, "little")
    rom[0x78BD:0x78BF] = scroll(runs[15], 47).to_bytes(2, "little")


def apply(rom, orig):
    mode_headers(rom)
    g = gfx.Gfx(orig)
    intro_names(g)
    gauge(g)
    title_bg1(g)
    title_bg3(g)
    return g.apply(rom, FREE)
