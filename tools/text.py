"""Story text bank ($88:A927 message table, $88:E4ED substring table) <-> script/*.json.

    python -X utf8 tools/text.py dump [--force]   # writes script/messages.json, script/substrings.json
"""
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from tbl import Table  # noqa: E402

ROOT = Path(__file__).resolve().parent.parent
ROM = ROOT / "rom" / "Yu Yu Hakusho 2 - Kakutou no Shou (Japan).sfc"
JP = Table.load(ROOT / "tbl" / "jp.tbl")

BANK = 0x40000           # file offset of $88:8000
MSG_TABLE, MSG_COUNT = 0x42927, 296
SUB_TABLE, SUB_COUNT = 0x464ED, 64
TEXT_START, TEXT_END = 0x42B77, 0x475BB   # message + substring data, substring table sits inside at 0x464ED


def word(rom, off):
    return rom[off] | rom[off + 1] << 8


def to_off(ptr):
    return BANK + ptr - 0x8000


def read_table(rom, table, count):
    """[(index, file offset, jp text, byte length)] for every slot, duplicates included."""
    out = []
    for i in range(count):
        off = to_off(word(rom, table + 2 * i))
        text, used = JP.decode(rom, off)
        out.append((i, off, text, used))
    return out


# Strings outside the story bank, copied to $0400 and drawn by $80:D7CE. Same encoding.
#   prefix: (16-bit pointer table offset, count, file offset of the table's bank, free tail (start, end))
AUX_TABLES = {
    "B": (0x2B408, 23, 0x28000, (0x2E9F1, 0x30000)),   # $85 battle labels + winner names; offsets at $85:B3DA
    "T": (0xF9E3, 6, 0x8000, (0xFA85, 0x10000)),        # $81 story result tally (体力, 霊力, ...)
}
B_OFFSETS = 0x2B3DA                                     # $85: BG3 scroll offset per label (centres it)
AUX_FIXED = {"P00": (0x2EF, 12), "P01": (0x2FB, 12)}    # $80 PAUSE / blank: fixed 12-byte MVN copies


def aux_entries(rom):
    out = []
    for pre, (table, count, bank, _) in AUX_TABLES.items():
        for i in range(count):
            off = bank + word(rom, table + 2 * i) - 0x8000
            out.append({"id": f"{pre}{i:02X}", "off": f"{off:06X}", "jp": JP.decode(rom, off)[0], "en": ""})
    for mid, (off, size) in AUX_FIXED.items():
        out.append({"id": mid, "off": f"{off:06X}", "jp": JP.decode(rom, off)[0], "en": ""})
    return out


def dump(force=False):
    rom = ROM.read_bytes()
    script = ROOT / "script"
    script.mkdir(exist_ok=True)
    other = script / "other.json"           # not "aux.json": AUX is a reserved device name on Windows
    if not other.exists() or force:
        other.write_text(json.dumps(aux_entries(rom), ensure_ascii=False, indent=1) + "\n", encoding="utf-8",
                         newline="\n")
        print(f"wrote {other}")
    for name, table, count in (("messages", MSG_TABLE, MSG_COUNT), ("substrings", SUB_TABLE, SUB_COUNT)):
        path = script / f"{name}.json"
        if path.exists() and not force:
            print(f"{path} exists, not overwriting (use --force)")
            continue
        first = {}
        entries = []
        for i, off, text, _ in read_table(rom, table, count):
            e = {"id": f"{name[0].upper()}{i:03X}", "off": f"{off:06X}", "jp": text, "en": ""}
            if off in first:
                e["same_as"] = first[off]
                del e["en"]
            else:
                first[off] = e["id"]
            entries.append(e)
        path.write_text(json.dumps(entries, ensure_ascii=False, indent=1) + "\n", encoding="utf-8", newline="\n")
        print(f"wrote {path} ({len(entries)} entries)")


if __name__ == "__main__":
    if sys.argv[1:2] == ["dump"]:
        dump("--force" in sys.argv)
    else:
        sys.exit(__doc__)
