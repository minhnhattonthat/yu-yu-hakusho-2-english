"""Find 16-bit pointer tables (same LoROM bank) whose targets decode as 0000-terminated glyph strings.

    python -X utf8 tools/findtext.py ROM [--min 3]
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from tbl import Table  # noqa: E402

JP = Table.load(Path(__file__).resolve().parent.parent / "tbl" / "jp.tbl")


def is_string(rom, off):
    """True if off starts a 0000-terminated run of 1..80 words that are glyphs/known controls, with a real glyph."""
    glyphs = 0
    for i in range(80):
        if off + 2 * i + 1 >= len(rom):
            return False
        w = rom[off + 2 * i] | rom[off + 2 * i + 1] << 8
        if w == 0:
            return glyphs > 0
        if 0x101 <= w <= 0x2FF:
            glyphs += 1
        elif not (w == 0x100 or w == 0x0A or 0x80 <= w <= 0xDF or 0xF6 <= w <= 0xFF):
            return False
    return False


def scan(rom, minrun):
    found = []
    for bank in range(len(rom) // 0x8000):
        base = bank * 0x8000
        for par in (0, 1):
            run = []
            for o in range(base + par, base + 0x8000 - 1, 2):
                p = rom[o] | rom[o + 1] << 8
                if p >= 0x8000 and is_string(rom, base + p - 0x8000):
                    run.append(o)
                    continue
                if len(run) >= minrun:
                    found.append((run[0], len(run)))
                run = []
    return found


if __name__ == "__main__":
    rom = open(sys.argv[1], "rb").read()
    minrun = int(sys.argv[sys.argv.index("--min") + 1]) if "--min" in sys.argv else 3
    for start, n in scan(rom, minrun):
        bank = start // 0x8000
        p = rom[start] | rom[start + 1] << 8
        first = JP.decode(rom, bank * 0x8000 + p - 0x8000)[0]
        print(f"{start:06X} (${0x80 + bank:02X}:{0x8000 + start % 0x8000:04X}) x{n}: {first[:40]}")
