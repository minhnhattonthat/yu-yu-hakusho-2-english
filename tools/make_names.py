"""One-off art generator: English intro fighter names -> art/intro_names.png (128x64, 2bpp indices, like the ROM block).

    python -X utf8 tools/make_names.py [--font C:/Windows/Fonts/impact.ttf]

Layout = block $8A:EAC9 (16 tiles wide): each name owns 8x4 tiles (64x32 px): Yusuke (top left), Kurama (top right),
Kuwabara (bottom left), Hiei (bottom right). Index 1 = white (BG3 palette 0). graphics.py only reads the PNG.
"""
import sys
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "art" / "intro_names.png"
NAMES = [("Yusuke", 0, 0), ("Kurama", 64, 0), ("Kuwabara", 0, 32), ("Hiei", 64, 32)]
SIZE, SCALE = 20, 4


def draw_name(font_path, name):
    f = ImageFont.truetype(font_path, SIZE * SCALE)
    box = f.getbbox(name)
    big = Image.new("L", (box[2] + 16, box[3] + 16), 0)
    ImageDraw.Draw(big).text((8, 8), name, font=f, fill=255)
    big = big.crop(big.getbbox())
    w = min(64, max(1, big.width // SCALE))
    h = max(1, round(big.height / SCALE))
    return big.resize((w, h), Image.LANCZOS).point(lambda v: 1 if v > 120 else 0)


def main():
    font_path = sys.argv[sys.argv.index("--font") + 1] if "--font" in sys.argv else "C:/Windows/Fonts/impact.ttf"
    im = Image.new("P", (128, 64), 0)
    im.putpalette([0, 0, 0, 248, 248, 248, 216, 216, 216, 176, 176, 176] + [0] * 756)
    for name, x0, y0 in NAMES:
        m = draw_name(font_path, name)
        ox, oy = x0 + (64 - m.width) // 2, y0 + (32 - m.height) // 2
        for y in range(m.height):
            for x in range(m.width):
                if m.getpixel((x, y)):
                    im.putpixel((ox + x, oy + y), 1)
    OUT.parent.mkdir(exist_ok=True)
    im.save(OUT)
    prev = Image.new("RGB", (128, 64), (48, 0, 96))
    prev.paste(im.convert("RGB"), mask=im.convert("L").point(lambda v: 255 if v else 0))
    prev.resize((512, 256), Image.NEAREST).save(ROOT / "work" / "g" / "intro_names.png")
    print("wrote", OUT)


if __name__ == "__main__":
    main()
