"""Build the English ROM.

    python -X utf8 tools/build.py [--marker] [--out build/yyh2_en.sfc]

--marker: every message becomes "[id]" + filler of the Japanese run's pixel width, controls kept (marker build).
Untranslated entries (empty "en") are inserted as their Japanese text.
"""
import json
import re
import shutil
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
import font  # noqa: E402
import text  # noqa: E402

ROOT = text.ROOT
ASAR = ROOT / "tools" / "asar" / "asar.exe"
MSG_TABLE = 0x42B77                       # $88:AB77, must match asm/main.asm
SUB_TABLE = MSG_TABLE + text.MSG_COUNT * 3
# Free space in banks $80-$BF (text banks must mirror low WRAM): (start, end) file offsets.
FREE = [
    (SUB_TABLE + text.SUB_COUNT * 3, text.TEXT_END),   # old JP text in $88
    (0x17DB30, 0x180000),                              # $AF tail
    (0x1ADE80, 0x1B0000),                              # $B5 tail
    (0x18E100, 0x190000),                              # $B1 tail
]
TOKEN = re.compile(r"(\{[^}]*\})")
CTRL = {"end": 0x0000, "n": 0x000A, "clr": 0x00FE, "wait": 0x00FF, "tab": 0x0300,
        "var0": 0xF6, "var1": 0xF7, "var2": 0xF8, "var3": 0xF9,
        "name0": 0xFA, "name1": 0xFB, "name2": 0xFC, "name3": 0xFD}


def encode_en(s):
    """English text -> 16-bit words: ASCII packed two per word, one leftover as $03xx, controls as words."""
    words = []
    for part in TOKEN.split(s):
        if not part:
            continue
        if part.startswith("{"):
            name = part[1:-1]
            if name in CTRL:
                words.append(CTRL[name])
            elif re.fullmatch(r"sub[89A-D][0-9A-F]", name):
                words.append(int(name[3:], 16))
            else:
                raise ValueError(f"unknown control {part} in {s!r}")
            continue
        run = []
        for ch in part:
            if 0x20 <= ord(ch) < 0x7F:
                run.append(ord(ch))
                continue
            flush(run, words)
            code = text.JP.enc.get(ch)            # Japanese glyph (arrows, symbols) kept as-is
            if code is None or len(code) != 2:
                raise ValueError(f"unencodable {ch!r} in {s!r}")
            words.append(code[0] | code[1] << 8)
        flush(run, words)
    if not words or words[-1] != 0:
        words.append(0)
    return b"".join(w.to_bytes(2, "little") for w in words)


def flush(run, words):
    for i in range(0, len(run) - 1, 2):
        words.append(run[i] | run[i + 1] << 8)
    if len(run) % 2:
        words.append(0x0300 | run[-1])
    run.clear()


FILLER = "The quick brown fox jumps over the lazy dog and keeps running far away "


def marker(entry, widths):
    """Same controls as the JP text; each text run replaced by filler of the same pixel width, id first."""
    out, first = [], True
    for part in TOKEN.split(entry["jp"]):
        if not part:
            continue
        if part.startswith("{"):
            out.append(part)
            continue
        budget = 16 * len(part)
        s = f"[{entry['id']}]" if first else ""
        first = False
        for ch in FILLER * 4:
            if font.text_width(widths, s + ch) > budget:
                break
            s += ch
        out.append(s)
    return "".join(out)


class Allocator:
    def __init__(self, regions):
        self.regions = [list(r) for r in regions]

    def put(self, rom, data):
        for r in self.regions:
            start, end = r
            if end - start >= len(data) and start // 0x8000 == (start + len(data) - 1) // 0x8000:
                rom[start:start + len(data)] = data
                r[0] += len(data)
                return start
        raise ValueError(f"out of text space for {len(data)} bytes")


def snes(off):
    return 0x800000 | (off // 0x8000) << 16 | 0x8000 | (off & 0x7FFF)


def insert(rom, entries, table_off, alloc, mode, widths):
    placed = {}
    for i, e in enumerate(entries):
        src = entries_by_id[e["same_as"]] if "same_as" in e else e
        if src["id"] not in placed:
            if mode == "marker":
                data = encode_en(marker(src, widths))
            elif src.get("en"):
                data = encode_en(src["en"])
            else:
                data = text.JP.encode(src["jp"])
            placed[src["id"]] = snes(alloc.put(rom, data))
        rom[table_off + 3 * i:table_off + 3 * i + 3] = placed[src["id"]].to_bytes(3, "little")


entries_by_id = {}


def build(out, mode):
    out.parent.mkdir(parents=True, exist_ok=True)
    fbin, wbin, _ = font.build()
    (ROOT / "build" / "font_en.bin").write_bytes(fbin)
    (ROOT / "build" / "font_w.bin").write_bytes(wbin)
    shutil.copyfile(text.ROM, out)
    r = subprocess.run([str(ASAR), "--no-title-check", "--fix-checksum=off", str(ROOT / "asm" / "main.asm"), str(out)],
                       capture_output=True, text=True)
    if r.returncode:
        sys.exit("asar failed:\n" + r.stdout + r.stderr)
    rom = bytearray(out.read_bytes())
    msgs = json.loads((ROOT / "script" / "messages.json").read_text(encoding="utf-8"))
    subs = json.loads((ROOT / "script" / "substrings.json").read_text(encoding="utf-8"))
    entries_by_id.clear()
    entries_by_id.update({e["id"]: e for e in msgs + subs})
    for a, b in FREE:
        rom[a:b] = b"\xff" * (b - a)
    alloc = Allocator(FREE)
    insert(rom, msgs, MSG_TABLE, alloc, mode, wbin)
    insert(rom, subs, SUB_TABLE, alloc, mode, wbin)
    out.write_bytes(rom)
    used = sum(r[0] - a for r, (a, _) in zip(alloc.regions, FREE))
    print(f"built {out} ({mode}), text {used} bytes")


if __name__ == "__main__":
    mode = "marker" if "--marker" in sys.argv else "en"
    out = Path(sys.argv[sys.argv.index("--out") + 1]) if "--out" in sys.argv else ROOT / "build" / "yyh2_en.sfc"
    build(out, mode)
