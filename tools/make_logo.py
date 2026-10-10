"""One-off art generator: English title logo "YU YU / HAKUSHO" + the original gold "2" -> art/title_logo.png.

    python -X utf8 tools/make_logo.py [--font C:/Windows/Fonts/ariblk.ttf]

The PNG is indexed (palette 2 of the title screen, index 0 = transparent) and 256x88 = the 32x11 cells of BG1 rows 0-10,
so it can be touched up by hand; build.py (graphics.py) only reads the PNG. Needs Pillow and a heavy sans font.
"""
import struct
import sys
from pathlib import Path

from PIL import Image, ImageDraw, ImageFilter, ImageFont

sys.path.insert(0, str(Path(__file__).parent))
import gfx  # noqa: E402
import text  # noqa: E402

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "art" / "title_logo.png"
W, H = 256, 88
# title screen BG1 palette 2 (CGRAM $20-$2F): index -> RGB
PAL = [(40, 0, 112), (248, 248, 248), (176, 16, 24), (208, 176, 32), (72, 128, 176), (144, 144, 144), (216, 120, 128),
       (0, 0, 0), (200, 184, 184), (56, 56, 56), (192, 64, 72), (136, 176, 232), (144, 104, 8), (120, 0, 0),
       (224, 208, 208), (0, 0, 0)]
WHITE, RED, GOLD, BLUE, DARK = 1, 2, 3, 4, 13


def original_canvas(rom):
    g = gfx.Gfx(rom)
    tiles = g.raw(0xB4, 0x8000)
    ents = struct.unpack("<1024H", g.raw(0xB4, 0x99A8, il=False))
    canvas = [[0] * W for _ in range(H)]
    for r in range(11):
        for c in range(32):
            px = gfx.tile_px(tiles, ents[r * 32 + c] & 0x3FF, 4)
            for y in range(8):
                for x in range(8):
                    canvas[r * 8 + y][c * 8 + x] = px[y][x]
    return canvas


def keep_two(canvas):
    """Flood fill (8-neighbour, colours gold/outline) from the middle of the "2" -> its pixels only."""
    ok = {GOLD, 9, 12}
    seen = set()
    stack = [next((y, x) for x in range(215, W) for y in range(H) if canvas[y][x] == GOLD)]
    while stack:
        y, x = stack.pop()
        if (y, x) in seen or not (0 <= y < H and 0 <= x < W) or canvas[y][x] not in ok:
            continue
        seen.add((y, x))
        stack += [(y + dy, x + dx) for dy in (-1, 0, 1) for dx in (-1, 0, 1)]
    return seen


def word(text_, font_path, cap, width, scale=4):
    """Binary mask of `text_` with cap height `cap` px, squeezed/stretched to `width` px (supersampled)."""
    f = ImageFont.truetype(font_path, cap * scale * 4 // 3)
    box = f.getbbox(text_)
    big = Image.new("L", (box[2] + 8, box[3] + 8), 0)
    ImageDraw.Draw(big).text((4, 4), text_, font=f, fill=255)
    big = big.crop(big.getbbox())
    return big.resize((width, cap), Image.LANCZOS).point(lambda v: 255 if v > 110 else 0)


def paint(canvas, mask, x0, y0, fill, rim, outer, outer_w):
    """Layered outline: letter fill, 1 px rim, `outer_w` px outer colour, 1 px dark edge."""
    pad = outer_w + 4
    m = Image.new("L", (mask.width + 2 * pad, mask.height + 2 * pad), 0)
    m.paste(mask, (pad, pad))
    d1 = m.filter(ImageFilter.MaxFilter(3))
    d = [m, d1]
    for _ in range(outer_w + 1):
        d.append(d[-1].filter(ImageFilter.MaxFilter(3)))
    layers = [(d[-1], DARK), (d[-2], outer), (d[1], rim), (m, fill)]
    for lay, col in layers:
        for y in range(lay.height):
            for x in range(lay.width):
                if lay.getpixel((x, y)):
                    X, Y = x0 - pad + x, y0 - pad + y
                    if 0 <= X < W and 0 <= Y < H:
                        canvas[Y][X] = col


def main():
    font_path = sys.argv[sys.argv.index("--font") + 1] if "--font" in sys.argv else "C:/Windows/Fonts/ariblk.ttf"
    rom = text.ROM.read_bytes()
    canvas = original_canvas(rom)
    two = keep_two(canvas)
    new = [[0] * W for _ in range(H)]
    for y, x in two:
        new[y][x] = canvas[y][x]
    for y, x in sorted(two):   # the old 書 overlapped the 2's left edge: close any gap in its dark outline
        if canvas[y][x] == GOLD:
            for dy, dx in ((0, -1), (0, 1), (-1, 0), (1, 0)):
                if 0 <= y + dy < H and 0 <= x + dx < W and not new[y + dy][x + dx]:
                    new[y + dy][x + dx] = 9
    top = word("YU YU", font_path, 26, 118)
    bot = word("HAKUSHO", font_path, 26, 184)
    paint(new, bot, 8, 54, WHITE, BLUE, RED, 2)
    paint(new, top, 8 + (184 - 118) // 2, 16, BLUE, WHITE, RED, 2)
    im = Image.new("P", (W, H), 0)
    im.putpalette([c for rgb in PAL for c in rgb] + [0] * (768 - 48))
    im.putdata([v for row in new for v in row])
    OUT.parent.mkdir(exist_ok=True)
    im.save(OUT)
    im.convert("RGB").resize((W * 4, H * 4), Image.NEAREST).save(ROOT / "work" / "g" / "logo_new.png")
    print("wrote", OUT)


if __name__ == "__main__":
    main()
