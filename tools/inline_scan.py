"""Find strings that code copies into the $0400 draw buffer: `LDA src,x|y` (abs or long) followed within a few
bytes by `STA $0400,x|y`. Prints the source and its decoded text; tables of pointers show up as several hits.

    python -X utf8 tools/inline_scan.py ROM
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from text import JP  # noqa: E402


def scan(rom):
    hits = []
    for o in range(len(rom) - 8):
        op = rom[o]
        if op in (0xB9, 0xBD):                       # LDA abs,y / abs,x
            src = (o // 0x8000) * 0x8000 + (rom[o + 1] | rom[o + 2] << 8) - 0x8000
            nxt = o + 3
        elif op == 0xBF:                             # LDA long,x
            addr = rom[o + 1] | rom[o + 2] << 8 | rom[o + 3] << 16
            if not addr & 0x8000:
                continue
            src = ((addr & 0x7F0000) >> 1) | (addr & 0x7FFF)
            nxt = o + 4
        else:
            continue
        window = rom[nxt:nxt + 6]
        if any(window[i] in (0x99, 0x9D) and window[i + 1:i + 3] == b"\x00\x04" for i in range(4)):
            hits.append((o, src))
    return hits


if __name__ == "__main__":
    rom = open(sys.argv[1], "rb").read()
    for o, src in scan(rom):
        if 0 <= src < len(rom):
            try:
                s = JP.decode(rom, src, maxlen=80)[0]
            except ValueError:
                s = "(no end)"
            print(f"code {0x80 + o // 0x8000:02X}:{0x8000 | o & 0x7FFF:04X}  src {src:06X}  {s[:60]}")
