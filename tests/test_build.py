import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "tools"))
import build  # noqa: E402
import text  # noqa: E402

ROOT = text.ROOT
ORIG = text.ROM.read_bytes()
ROMDIFF = "H:/translation/.claude/skills/translate-retro-game/scripts/romdiff.py"
ALLOWED = [line.split()[0] for line in (ROOT / "tools" / "allowed_ranges.txt").read_text().splitlines()
           if line.strip() and not line.startswith("#")]


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


def test_english_build_writes_only_allowed_ranges(tmp_path):
    out = tmp_path / "en.sfc"
    build.build(out, "en")
    r = subprocess.run([sys.executable, ROMDIFF, str(text.ROM), str(out)] + ALLOWED, capture_output=True, text=True)
    assert r.returncode == 0, r.stdout + r.stderr


def test_encode_en_packs_pairs():
    assert build.encode_en("Hi!{n}") == bytes([ord("H"), ord("i"), ord("!"), 0x03, 0x0A, 0, 0, 0])
