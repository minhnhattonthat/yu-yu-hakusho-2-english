"""Replace LZ-compressed graphics blocks (docs/re/graphics.md): edit the decompressed block, re-compress it into free
space and repoint every loader (`LDX #bank / LDA #addr / JSL $81:8CF3 or $81:8C35`) at the new copy.

    g = Gfx(rom_bytes)                       # the original ROM
    raw = g.raw(0xB2, 0xEB9E)                # SNES-format tiles (4bpp/2bpp, row-interleaved) for $8CF3 blocks
    g.replace(0xB2, 0xEB9E, new_raw)         # schedule; il=False for $8C35 blocks (tilemaps, loaded as is)
    g.apply(rom, FREE)                       # rom: bytearray to patch; FREE: [(start, end)] file-offset regions
Original blocks stay in place (unused). Prints nothing; returns [(start, end)] of every byte range it wrote.
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
import lz  # noqa: E402

DECOMP_IL, DECOMP_PLAIN = 0x8CF3, 0x8C35      # $81:xxxx entry points (interleaving / plain)


def tile_bytes(px, bpp):
    """8x8 grid of palette indices -> SNES tile bytes (bit planes in pairs, rows interleaved)."""
    out = bytearray(8 * bpp)
    for pl in range(bpp):
        for r in range(8):
            v = 0
            for c in range(8):
                v |= ((px[r][c] >> pl) & 1) << (7 - c)
            out[(pl // 2) * 16 + r * 2 + (pl & 1)] = v
    return bytes(out)


def tile_px(data, n, bpp):
    """Inverse of tile_bytes for tile n of an SNES-format buffer."""
    a = n * 8 * bpp
    return [[sum(((data[a + (pl // 2) * 16 + r * 2 + (pl & 1)] >> (7 - c)) & 1) << pl for pl in range(bpp))
             for c in range(8)] for r in range(8)]


def loader_sites(rom, bank, addr):
    """[(bank byte offset, address word offset)] of every `LDX #bank / LDA #addr / JSL $81:8CF3|8C35` (either order)."""
    lo, hi = addr & 255, addr >> 8
    out = []
    for pat, b_at, a_at in ((bytes([0xA2, bank, 0x00, 0xA9, lo, hi, 0x22]), 1, 4),
                            (bytes([0xA9, lo, hi, 0xA2, bank, 0x00, 0x22]), 4, 1)):
        i = rom.find(pat)
        while i >= 0:
            if rom[i + 8:i + 10] == b"\x8c\x81" and rom[i + 7] in (0xF3, 0x35):
                out.append((i + b_at, i + a_at))
            i = rom.find(pat, i + 1)
    return out


class Gfx:
    def __init__(self, rom):
        self.rom = bytes(rom)
        self.jobs = []

    def raw(self, bank, addr, il=True):
        d = lz.decompress(self.rom, lz.snes_off(bank, addr))
        return lz.interleave(d) if il else d

    def replace(self, bank, addr, data, il=True, only=None):
        """only(b_at, a_at) -> bool picks which loaders get repointed (others keep loading the original block)."""
        self.jobs.append((bank, addr, bytes(data), il, only))

    def apply(self, rom, free):
        regions = [list(r) for r in free]
        written = []
        for bank, addr, data, il, only in self.jobs:
            every = loader_sites(self.rom, bank, addr)
            sites = [s for s in every if only is None or only(*s)]
            if not sites:
                raise ValueError(f"no loader for {bank:02X}:{addr:04X}")
            blob = lz.compress(lz.deinterleave(data) if il else data)
            old = lz.snes_off(bank, addr)
            if len(sites) == len(every) and len(blob) <= lz.compressed_len(self.rom, old):
                rom[old:old + len(blob)] = blob      # nothing else loads the old block: overwrite it, loaders unchanged
                written.append((old, old + len(blob) - 1))
                continue
            for r in regions:
                if r[1] - r[0] >= len(blob):
                    start = r[0]
                    r[0] += len(blob)
                    break
            else:
                raise ValueError(f"out of graphics space for {len(blob)} bytes ({bank:02X}:{addr:04X})")
            rom[start:start + len(blob)] = blob
            written.append((start, start + len(blob) - 1))
            nb, na = 0x80 | start >> 15, 0x8000 | start & 0x7FFF
            for b_at, a_at in sites:
                rom[b_at], rom[a_at], rom[a_at + 1] = nb, na & 255, na >> 8
                written += [(b_at, b_at), (a_at, a_at + 1)]
        return written
