"""English VWF font: font/en_glyphs.txt art -> 8x16 2bpp glyphs (top tile, bottom tile) + width table.

Art: 'char X' (or 'char space') then 13 rows of 6 chars ('#' stroke, '.' empty), baseline after row 9.
Glyph g = ascii - 0x20, 32 bytes each, bit 7 = leftmost pixel. Width = last inked column + 2 (1 px gap).

    python -X utf8 tools/font.py OUT_FONT.bin OUT_WIDTHS.bin [--preview out.png]
"""
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
ART = ROOT / "font" / "en_glyphs.txt"
W, H, TOP = 6, 13, 2        # art size; art row 0 lands on glyph row TOP
STROKE, SHADOW = 1, 3       # palette indices: text colour, drop shadow (right/down)
SPACE_W = 4


def parse(text):
    glyphs, cur, rows = {}, None, []
    for line in text.splitlines():
        if not line.strip() or line.startswith("# ") or line == "#":
            continue
        if line.startswith("char "):
            if cur is not None:
                glyphs[cur] = rows
            name = line[5:]
            cur, rows = (" " if name == "space" else name), []
            if len(cur) != 1:
                raise ValueError(f"bad char line {line!r}")
            continue
        if len(line) != W:
            raise ValueError(f"char {cur!r}: row {line!r} is not {W} wide")
        rows.append(line)
    if cur is not None:
        glyphs[cur] = rows
    for ch, r in glyphs.items():
        if len(r) != H:
            raise ValueError(f"char {ch!r}: {len(r)} rows, expected {H}")
    return glyphs


def pixels(rows):
    """16x8 grid of palette indices with shadow."""
    px = [[0] * 8 for _ in range(16)]
    for y, row in enumerate(rows):
        for x, c in enumerate(row):
            if c == "#":
                px[TOP + y][x] = STROKE
    if SHADOW:
        for y in range(15, -1, -1):
            for x in range(7, -1, -1):
                if px[y][x] == 0 and ((x and px[y][x - 1] == STROKE) or (y and px[y - 1][x] == STROKE)):
                    px[y][x] = SHADOW
    return px


def encode(px):
    out = bytearray(32)
    for y in range(16):
        base = (y // 8) * 16 + (y % 8) * 2
        for x in range(8):
            v = px[y][x]
            out[base] |= (v & 1) << (7 - x)
            out[base + 1] |= (v >> 1 & 1) << (7 - x)
    return bytes(out)


def width(rows):
    cols = [x for row in rows for x, c in enumerate(row) if c == "#"]
    return max(cols) + 2 if cols else SPACE_W


def build():
    glyphs = parse(ART.read_text(encoding="utf-8"))
    font, widths, grids = bytearray(), bytearray(), []
    for code in range(0x20, 0x80):
        rows = glyphs.get(chr(code), ["." * W] * H)
        px = pixels(rows)
        font += encode(px)
        widths.append(min(width(rows) + (1 if SHADOW else 0) - 1, 8) if chr(code) != " " else SPACE_W)
        grids.append(px)
    return bytes(font), bytes(widths), grids


def text_width(widths, s):
    return sum(widths[ord(c) - 0x20] for c in s)


if __name__ == "__main__":
    font, widths, grids = build()
    Path(sys.argv[1]).write_bytes(font)
    Path(sys.argv[2]).write_bytes(widths)
    if "--preview" in sys.argv:
        from PIL import Image
        sample = "The quick brown fox jumps over the lazy dog. Yusuke Urameshi! 0123456789?"
        img = Image.new("RGB", (8 + text_width(widths, sample), 20), (40, 40, 90))
        pal = [None, (255, 255, 255), (150, 150, 150), (20, 20, 40)]
        x = 4
        for ch in sample:
            g = ord(ch) - 0x20
            for y in range(16):
                for xx in range(8):
                    v = grids[g][y][xx]
                    if v:
                        img.putpixel((x + xx, 2 + y), pal[v])
            x += widths[g]
        img.resize((img.width * 3, img.height * 3), Image.NEAREST).save(sys.argv[sys.argv.index("--preview") + 1])
