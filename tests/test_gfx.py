import struct
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "tools"))
import gfx  # noqa: E402
import graphics  # noqa: E402
import lz  # noqa: E402
import text  # noqa: E402

ORIG = text.ROM.read_bytes()
BLOCKS = [(0xB2, 0xEB9E), (0xB4, 0x8000), (0xB4, 0x9354), (0xB4, 0x99A8), (0xB4, 0x9CB1), (0x8A, 0xEAC9)]


def test_lz_compress_roundtrips_game_blocks():
    for bank, addr in BLOCKS:
        raw = lz.decompress(ORIG, lz.snes_off(bank, addr))
        blob = lz.compress(raw)
        assert lz.decompress(blob + bytes(4), 0) == raw
        assert lz.compressed_len(blob, 0) == len(blob)


def test_graphics_patches_load_what_was_built():
    rom = bytearray(ORIG)
    graphics.apply(rom, ORIG)
    new = gfx.Gfx(bytes(rom))
    # title copyright map: the two English lines sit in rows 19-20 / 22-23 of the $B4:9CB1 map, row 14-26 block
    sites = gfx.loader_sites(bytes(rom), 0x80 | 0x1A6EE9 >> 15, 0x8000 | 0x1A6EE9 & 0x7FFF)
    assert len(sites) == 2                         # both title paths load the relocated tile block
    ents = struct.unpack("<416H", lz.decompress(bytes(rom), 0x1A74AD))
    assert any(ents[(19 - 14) * 32:(20 - 14) * 32]) and any(ents[(22 - 14) * 32:(23 - 14) * 32])
    assert new.raw(0xB2, 0xEB9E) != gfx.Gfx(ORIG).raw(0xB2, 0xEB9E)      # RAGE replaced the kanji tiles
