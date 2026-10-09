"""Relative search for a kana string in the ROM under common kana orderings.

    python -X utf8 tools/relsearch.py ROM いのちをおとした [--width 1|2]
"""
import sys

JIS = "ぁあぃいぅうぇえぉおかがきぎくぐけげこごさざしじすずせぜそぞただちぢっつづてでとどなにぬねのはばぱひびぴふぶぷへべぺほぼぽまみむめもゃやゅゆょよらりるれろゎわゐゑをん"
GOJUON = "あいうえおかきくけこさしすせそたちつてとなにぬねのはひふへほまみむめもやゆよらりるれろわをん"
GOJUON_SMALL = "あいうえおかきくけこさしすせそたちつてとなにぬねのはひふへほまみむめもやゆよらりるれろわをんぁぃぅぇぉっゃゅょ"
ORDERS = {"jis": JIS, "gojuon": GOJUON, "gojuon_small": GOJUON_SMALL}


def search(rom, word, width):
    for name, order in ORDERS.items():
        if any(c not in order for c in word):
            continue
        idx = [order.index(c) for c in word]
        deltas = [b - a for a, b in zip(idx, idx[1:])]
        n = len(word)
        for be in (False, True) if width == 2 else (False,):
            for off in range(len(rom) - n * width):
                vals = [int.from_bytes(rom[off + i * width: off + (i + 1) * width], "big" if be else "little")
                        for i in range(n)]
                if all(vals[i + 1] - vals[i] == deltas[i] for i in range(n - 1)):
                    base = vals[0] - idx[0]
                    print(f"{name} w{width}{'be' if be else ''} @ {off:06X} base={base:X} {rom[off:off + n * width].hex(' ')}")


if __name__ == "__main__":
    rom = open(sys.argv[1], "rb").read()
    width = int(sys.argv[3]) if len(sys.argv) > 3 else 1
    search(rom, sys.argv[2], width)
