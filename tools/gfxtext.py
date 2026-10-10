"""Render English with the VWF font (font/en_glyphs.txt) into pixel grids for graphics blocks.

    grid = render("RAGE", stroke=15, shadow=14)       # 16 rows x width pixels (ints); 0 = transparent
    cells = slice_tiles(grid, cols, rows)             # [row][col] 8x8 grids, 16 px lines use rows=2
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
import font  # noqa: E402

GLYPHS = font.parse(font.ART.read_text(encoding="utf-8"))


def render(text, stroke=1, shadow=3, tight=0, pad=0):
    """16-row grid; glyph advance = font width - tight (like the in-game VWF). `shadow` None = no drop shadow."""
    x, grid = pad, [[0] * (pad + sum(font.width(GLYPHS[c]) for c in text) + 2) for _ in range(16)]
    for ch in text:
        rows = GLYPHS[ch]
        px = font.pixels(rows)
        for y in range(16):
            for gx in range(8):
                v = px[y][gx]
                if v == 0 or x + gx >= len(grid[0]):
                    continue
                v = stroke if v == font.STROKE else shadow
                if v is not None and grid[y][x + gx] == 0:
                    grid[y][x + gx] = v
        x += font.width(rows) - tight
    return grid


def width(text, tight=0):
    return sum(font.width(GLYPHS[c]) - tight for c in text) + 1


def slice_tiles(grid, cols, rows):
    """Cut a 16*rows/8 grid into 8x8 tiles; pads with 0 on the right/bottom."""
    h = len(grid)
    out = []
    for ty in range(rows):
        line = []
        for tx in range(cols):
            line.append([[grid[ty * 8 + r][tx * 8 + c] if ty * 8 + r < h and tx * 8 + c < len(grid[0]) else 0
                          for c in range(8)] for r in range(8)])
        out.append(line)
    return out
