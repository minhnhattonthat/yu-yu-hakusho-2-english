import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "tools"))
import build  # noqa: E402
import text  # noqa: E402

ROOT = text.ROOT
ORIG = text.ROM.read_bytes()
ROMDIFF = "H:/translation/.claude/skills/translate-retro-game/scripts/romdiff.py"
# Code hooks in bank $80 + VWF code in $A0 + text tables/free space (asm/main.asm, build.FREE)
ALLOWED = ["5966-5969", "58BA-58BD", "5AAE-5AB3", "588A-588F", "106100-107FFF",
           f"{build.MSG_TABLE:X}-{build.FREE[0][0] - 1:X}"] + [f"{a:X}-{b - 1:X}" for a, b in build.FREE]


def read_ptr(rom, off):
    p = int.from_bytes(rom[off:off + 3], "little")
    return ((p & 0x7F0000) >> 1) | (p & 0x7FFF)


def test_relocated_japanese_decodes_like_original(tmp_path):
    out = tmp_path / "jp.sfc"
    build.build(out, "jp")
    rom = out.read_bytes()
    for table, count, new in ((text.MSG_TABLE, text.MSG_COUNT, build.MSG_TABLE),
                              (text.SUB_TABLE, text.SUB_COUNT, build.SUB_TABLE)):
        for i, _, jp, _ in text.read_table(ORIG, table, count):
            assert text.JP.decode(rom, read_ptr(rom, new + 3 * i))[0] == jp, (hex(table), i)
    r = subprocess.run([sys.executable, ROMDIFF, str(text.ROM), str(out)] + ALLOWED, capture_output=True, text=True)
    assert r.returncode == 0, r.stdout + r.stderr


def test_marker_build_assembles(tmp_path):
    build.build(tmp_path / "marker.sfc", "marker")


def test_encode_en_packs_pairs():
    assert build.encode_en("Hi!{n}") == bytes([ord("H"), ord("i"), ord("!"), 0x03, 0x0A, 0, 0, 0])
