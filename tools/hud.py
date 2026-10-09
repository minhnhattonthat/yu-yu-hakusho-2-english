"""Fight HUD fighter names in English (see docs/re/hud.md).

The original HUD graphics block ($88:98CF, 0x960 bytes -> VRAM $7000 = BG3 tiles $200-$295) holds kanji names in
tiles $240-$295; per-fighter tables ($81:CF93 P1, $81:D03B P2) list 6x2 tile bytes. This writes:
  build/hud_block.bin  original block + English name tiles, extended to 0x1000 bytes (tiles $200-$2FF, VRAM
                       $7000-$77FF, unused above $74B0 in fights)
  build/hud_p1.bin / hud_p2.bin  14 fighters x 2 rows x WIDE tile bytes (P1 left-aligned, P2 right-aligned)
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
import font  # noqa: E402
import text  # noqa: E402

ROOT = text.ROOT
BLOCK, BLOCK_SIZE, NEW_SIZE = 0x418CF, 0x960, 0x1000
WIDE = 10                      # tiles per name row (cols 4-13 for P1, 18-27 for P2)
# fighter id -> name (ids from the original tables: 2 = Hiei, 3 = Kurama, 11 = masked fighter, 12 = young Genkai)
NAMES = ["Yusuke", "Kuwabara", "Hiei", "Kurama", "Genkai", "Suzaku", "Chu", "Jin", "Shishiwakamaru", "Toguro",
         "Toguro", "Masked Fighter", "Genkai", "Toguro"]
FREE_TILES = list(range(0x40, 0x96)) + list(range(0x96, 0x100))   # old name tiles + the new tail


def render(name, glyphs, widths):
    """16-row pixel strip of the name in the VWF font."""
    w = sum(widths[ord(c) - 0x20] for c in name)
    px = [[0] * (w + 8) for _ in range(16)]
    x = 0
    for c in name:
        g = glyphs[ord(c) - 0x20]
        for y in range(16):
            for xx in range(8):
                if g[y][xx]:
                    px[y][x + xx] = g[y][xx]
        x += widths[ord(c) - 0x20]
    return px, w


def tile(px, tx, ty):
    out = bytearray(16)
    for r in range(8):
        for c in range(8):
            x = tx * 8 + c
            v = px[ty * 8 + r][x] if x < len(px[0]) else 0
            out[r * 2] |= (v & 1) << (7 - c)
            out[r * 2 + 1] |= (v >> 1 & 1) << (7 - c)
    return bytes(out)


def build(rom):
    _, widths, glyphs = font.build()
    block = bytearray(rom[BLOCK:BLOCK + BLOCK_SIZE]) + bytes(NEW_SIZE - BLOCK_SIZE)
    for t in FREE_TILES:
        block[t * 16:(t + 1) * 16] = bytes(16)
    free = iter(FREE_TILES)
    placed = {}
    p1, p2 = bytearray(), bytearray()
    for name in NAMES:
        if name not in placed:
            px, w = render(name, glyphs, widths)
            n = -(-(w - 1) // 8)              # the last column is the shadow/gap
            if n > WIDE:
                raise SystemExit(f"HUD name {name!r} needs {n} tiles > {WIDE}")
            rows = []
            for ty in range(2):
                ids = []
                for tx in range(n):
                    t = next(free)
                    block[t * 16:(t + 1) * 16] = tile(px, tx, ty)
                    ids.append(t)
                rows.append(ids)
            placed[name] = rows
        for ty in range(2):
            ids = placed[name][ty]
            p1 += bytes(ids + [0] * (WIDE - len(ids)))
        for ty in range(2):
            ids = placed[name][ty]
            p2 += bytes([0] * (WIDE - len(ids)) + ids)
    return bytes(block), bytes(p1), bytes(p2)


if __name__ == "__main__":
    block, p1, p2 = build(text.ROM.read_bytes())
    (ROOT / "build" / "hud_block.bin").write_bytes(block)
    (ROOT / "build" / "hud_p1.bin").write_bytes(p1)
    (ROOT / "build" / "hud_p2.bin").write_bytes(p2)
    print(f"hud: block {len(block):#x}, tables {len(p1)}+{len(p2)} bytes")
