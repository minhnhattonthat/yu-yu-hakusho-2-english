"""Art generator: English intro fighter names -> art/intro_names.png (112x128, index 1 = white, 0 = clear).

    python -X utf8 tools/make_names.py

Four 32 px strips, in this order: Yusuke, Kurama, Kuwabara, Hiei, text left aligned. The text is the game's VWF font
(font/en_glyphs.txt) doubled in size, no shadow, matching the 32 px kanji it replaces. graphics.py cuts the strips into
tiles and centres each name where the kanji were.
"""
import sys
from pathlib import Path

from PIL import Image

sys.path.insert(0, str(Path(__file__).parent))
import gfxtext  # noqa: E402

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "art" / "intro_names.png"
NAMES = ["Yusuke", "Kurama", "Kuwabara", "Hiei"]
W = 112


def main():
    im = Image.new("P", (W, 32 * len(NAMES)), 0)
    im.putpalette([0, 0, 0, 248, 248, 248] + [0] * 762)
    for i, name in enumerate(NAMES):
        g = gfxtext.render(name, stroke=1, shadow=None)
        for y in range(16):
            for x in range(len(g[0])):
                if g[y][x] and 2 * x + 1 < W:
                    for dy in (0, 1):
                        for dx in (0, 1):
                            im.putpixel((2 * x + dx, i * 32 + 2 * y + dy), 1)
    OUT.parent.mkdir(exist_ok=True)
    im.save(OUT)
    prev = Image.new("RGB", im.size, (48, 0, 96))
    prev.paste(im.convert("RGB"), mask=im.convert("L").point(lambda v: 255 if v else 0))
    prev.resize((im.width * 3, im.height * 3), Image.NEAREST).save(ROOT / "work" / "g" / "intro_names.png")
    print("wrote", OUT)


if __name__ == "__main__":
    main()
