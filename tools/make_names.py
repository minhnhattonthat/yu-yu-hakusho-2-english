"""Art generator: English intro fighter names -> art/intro_names.png (128x64, 2bpp indices, like the ROM block).

    python -X utf8 tools/make_names.py

Layout = block $8A:EAC9 (16 tiles wide): each name owns 8x4 tiles (64x32 px): Yusuke (top left), Kurama (top right),
Kuwabara (bottom left), Hiei (bottom right). Index 1 = white, 3 = grey shadow (BG3 palette 0). The text is the game's
VWF font (font/en_glyphs.txt). graphics.py only reads the PNG.
"""
import sys
from pathlib import Path

from PIL import Image

sys.path.insert(0, str(Path(__file__).parent))
import gfxtext  # noqa: E402

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "art" / "intro_names.png"
NAMES = [("Yusuke", 0, 0), ("Kurama", 64, 0), ("Kuwabara", 0, 32), ("Hiei", 64, 32)]


def main():
    im = Image.new("P", (128, 64), 0)
    im.putpalette([0, 0, 0, 248, 248, 248, 216, 216, 216, 176, 176, 176] + [0] * 756)
    for name, x0, y0 in NAMES:
        g = gfxtext.render(name, stroke=1, shadow=3)
        ox, oy = x0 + (64 - gfxtext.width(name)) // 2, y0 + 8
        for y in range(16):
            for x in range(min(len(g[0]), 64)):
                if g[y][x]:
                    im.putpixel((ox + x, oy + y), g[y][x])
    OUT.parent.mkdir(exist_ok=True)
    im.save(OUT)
    prev = Image.new("RGB", (128, 64), (48, 0, 96))
    prev.paste(im.convert("RGB"), mask=im.convert("L").point(lambda v: 255 if v else 0))
    prev.resize((512, 256), Image.NEAREST).save(ROOT / "work" / "g" / "intro_names.png")
    print("wrote", OUT)


if __name__ == "__main__":
    main()
