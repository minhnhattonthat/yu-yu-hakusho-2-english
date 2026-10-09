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
import fit  # noqa: E402
import font  # noqa: E402
import hud  # noqa: E402
import options  # noqa: E402
import text  # noqa: E402

ROOT = text.ROOT
ASAR = ROOT / "tools" / "asar" / "asar.exe"
MSG_TABLE = 0x42B77                       # $88:AB77, must match asm/main.asm
SUB_TABLE = MSG_TABLE + text.MSG_COUNT * 3
# Free space in banks $80-$BF (text banks must mirror low WRAM): (start, end) file offsets.
FREE = [
    (SUB_TABLE + text.SUB_COUNT * 3, text.TEXT_END),   # old JP text in $88
    (0x17DB30, text.AUX_MOVED_FREE[0]),                # $AF tail (its last 256 bytes hold text.AUX_MOVED)
]   # $B1 / $B5 tails hold the options screen and HUD graphics (asm/main.asm)
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


# Cell-grid screens: the tilemap shows fixed runs of 16-px cells, filled in stream order. English for these ids is
# "row | row | ...", one entry per run; ">" right-aligns a row. (docs/re/menus.md)
MOVE_GRID = [11, 9, 8, 9, 11, 10, 12, 12, 12, 13, 13, 12]
GRIDS = {mid: MOVE_GRID for mid in ["M01E", "M01F"] + [f"M{i:03X}" for i in range(0x64, 0x70)]}
# Story|Mode|Tournament|Battle|Training|Sound|Start Game|Options|Stereo|Music|Effects|0|0|Press B|to exit|Select|
# 1|P|VS|2|COM: the menu tilemaps reuse runs ("2P" = cell 74 + the "P" of "1P", every item + the shared "Mode").
GRIDS["M004"] = [5, 3, 4, 3, 6, 4, 7, 5, 4, 6, 5, 2, 2, 5, 4, 4, 1, 1, 2, 1, 3]
GRIDS["M005"] = GRIDS["M004"][8:]
GRIDS.update({f"T{i:02X}": [8, 1] for i in range(1, 5)})   # tally label | digit cell the game overwrites
CREDITS = ["M0FA", "M0FB"] + [f"M{i:03X}" for i in range(0x11C, 0x128)]
# Staff roll: role and name runs; the roll's tilemap reuses cells (くん = 20+49, ちゃん = 47-49, ママ = 39 twice).
GRIDS["M0FA"] = [4, 5, 2, 1, 4, 3, 1, 6, 4, 4, 4, 1, 3, 1, 3, 2, 1, 5, 2, 4, 5, 6, 2, 2, 2, 1, 4, 6, 8, 4, 5, 4, 6,
                 1, 1, 1, 1, 3]
GRIDS["M0FB"] = [4, 4, 4, 5, 6, 6, 8, 5, 2, 4]
GRIDS["M11C"] = [4]
GRIDS["M0F8"] = GRIDS["M0F9"] = [10, 12, 13, 13, 12]               # secret-code hint ($8A:F721 tilemap)
GRIDS.update({f"M{i:03X}": [7, 5] for i in range(0x11D, 0x128)})   # cast: 7-cell row over a 5-cell row


def layout_width(s):
    """Pen pixels used by s: ASCII by VWF width, Japanese glyphs cell aligned (16 px)."""
    px = 0
    for ch in s:
        if 0x20 <= ord(ch) < 0x7F:
            px += fit.WIDTHS[ord(ch) - 0x20]
        else:
            px = -(-px // 16) * 16 + 16
    return px


def grid_text(mid, en):
    """'row | row' -> stream text: each row padded to its run of cells ({tab} + full-width spaces).
    One space after '|' is the separator; further leading spaces indent (4 px each)."""
    rows = [(r[1:] if r.startswith(" ") else r).rstrip() for r in en.split("|")]
    spans = GRIDS[mid]
    if len(rows) > len(spans):
        raise SystemExit(f"{mid}: {len(rows)} rows > {len(spans)} runs")
    out = []
    for row, span in zip(rows, spans):
        align = row[:1] if row[:1] in (">", "^") else ""
        row = row[1:].strip() if align else row
        w = layout_width(row)
        if w - 1 > span * 16:              # width ends in a shadow/gap column that may fall off the edge
            raise SystemExit(f"{mid}: row {row!r} is {w}px > {span * 16}px")
        if align:
            pad = max(0, span * 16 - w) // (1 if align == ">" else 2)
            row = " " * (pad // fit.WIDTHS[0]) + row
            w = layout_width(row)
        used = -(-w // 16)
        out.append(row + ("{tab}" if w % 16 else "") + "　" * (span - used))
    return "".join(out)


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
            if mode == "cells" and (src["id"] in GRIDS or src["id"] in CREDITS):   # cells show stream index % 100
                n = sum(GRIDS[src["id"]]) if src["id"] in GRIDS else len(TOKEN.sub("", src["jp"]))
                data = encode_en("".join(f"{k % 100}{{tab}}" for k in range(1, n + 1)))
            elif mode in ("marker", "cells"):
                data = encode_en(marker(src, widths))
            elif mode != "jp" and src.get("en"):
                data = encode_entry(src)
            else:
                data = text.JP.encode(src["jp"])
            placed[src["id"]] = snes(alloc.put(rom, data))
        rom[table_off + 3 * i:table_off + 3 * i + 3] = placed[src["id"]].to_bytes(3, "little")


entries_by_id = {}


def encode_entry(e):
    if e["id"] in GRIDS:
        return encode_en(grid_text(e["id"], e["en"]))
    wrapped, errs = fit.wrap(e["en"], e["id"])
    if errs:
        raise SystemExit("\n".join(errs))
    return encode_en(wrapped)


def insert_other(rom, entries, mode):
    """Strings outside the story bank (text.AUX_TABLES / AUX_FIXED): translated ones move to their bank's tail."""
    allocs = {pre: Allocator([free]) for pre, (_, _, _, free) in text.AUX_TABLES.items()}
    for pre, (_, _, _, (a, b)) in text.AUX_TABLES.items():
        rom[a:b] = b"\xff" * (b - a)
    placed = {}
    moved = Allocator([text.AUX_MOVED_FREE])
    a, b = text.AUX_MOVED_FREE
    rom[a:b] = b"\xff" * (b - a)
    for e in entries:
        if e["id"] in text.AUX_MOVED:
            if mode == "jp" or not e.get("en"):
                continue
            _, ptr_op, x_op, ndig = text.AUX_MOVED[e["id"]]
            head, _, tail = e["en"].partition("{num}")
            head_b = encode_en(head)[:-2]                 # drop the terminator
            data = head_b + text.JP.encode("　" * ndig) + encode_en(tail)
            off = moved.put(rom, data)
            rom[ptr_op:ptr_op + 2] = (0x8000 | off & 0x7FFF).to_bytes(2, "little")
            rom[x_op:x_op + 2] = len(head_b).to_bytes(2, "little")   # byte offset of the first digit word
            continue
        if mode == "cells" and e["id"][0] in "BT":     # one letter per cell shows how many cells are on screen
            e = dict(e, en="".join(f"{c}{{tab}}" for c in "ABCDEFGHIJ"))
            data = encode_en(e["en"])
        elif mode == "jp" or not e.get("en"):
            continue
        else:
            data = encode_entry(e)
        if e["id"] in text.AUX_FIXED:
            off, size = text.AUX_FIXED[e["id"]]
            if len(data) > size:
                raise SystemExit(f"{e['id']}: {len(data)} bytes > {size}")
            rom[off:off + size] = data.ljust(size, b"\0")
            continue
        pre, i = e["id"][0], int(e["id"][1:], 16)
        table, _, bank, _ = text.AUX_TABLES[pre]
        if (pre, data) not in placed:
            placed[pre, data] = allocs[pre].put(rom, data)
        rom[table + 2 * i:table + 2 * i + 2] = (placed[pre, data] - bank + 0x8000).to_bytes(2, "little")
        if pre == "B" and mode != "cells":   # keep the label centred: shift its scroll offset by half the change
            o = text.B_OFFSETS + 2 * i
            old = int.from_bytes(rom[o:o + 2], "little", signed=True)
            jp_w = layout_width(e["jp"].replace("{end}", ""))
            new = old - (jp_w - layout_width(e["en"])) // 2
            rom[o:o + 2] = new.to_bytes(2, "little", signed=True)


def build(out, mode):
    out.parent.mkdir(parents=True, exist_ok=True)
    fbin, wbin, _ = font.build()
    (ROOT / "build" / "font_en.bin").write_bytes(fbin)
    (ROOT / "build" / "font_w.bin").write_bytes(wbin)
    for name, data in zip(("hud_block", "hud_p1", "hud_p2"), hud.build(text.ROM.read_bytes())):
        (ROOT / "build" / f"{name}.bin").write_bytes(data)
    for name, data in zip(("opt_chr", "opt_map", "opt_ptrs", "opt_lists"), options.build(text.ROM.read_bytes())):
        (ROOT / "build" / f"{name}.bin").write_bytes(data)
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
    insert_other(rom, json.loads((ROOT / "script" / "other.json").read_text(encoding="utf-8")), mode)
    out.write_bytes(rom)
    used = sum(r[0] - a for r, (a, _) in zip(alloc.regions, FREE))
    print(f"built {out} ({mode}), text {used} bytes")


if __name__ == "__main__":
    mode = "marker" if "--marker" in sys.argv else "cells" if "--cells" in sys.argv else "en"
    out = Path(sys.argv[sys.argv.index("--out") + 1]) if "--out" in sys.argv else ROOT / "build" / "yyh2_en.sfc"
    build(out, mode)
