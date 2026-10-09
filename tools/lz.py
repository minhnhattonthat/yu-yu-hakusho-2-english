"""The game's LZSS decompressor ($81:8C35) and tile re-interleave ($81:8CF3 = decompress + $81:8CFE).

Format: 16-bit output size, then flag bytes read LSB first: 1 = literal byte, 0 = 16-bit word W, copy
(W & 15) + 3 bytes from distance W >> 4 back; positions before the start of the output read as 0.
"""


def decompress(rom, off):
    size = rom[off] | rom[off + 1] << 8
    pos, out = off + 2, bytearray()
    flags = bits = 0
    while len(out) < size:
        if bits == 0:
            flags, bits = rom[pos], 8
            pos += 1
        bits -= 1
        lit = flags & 1
        flags >>= 1
        if lit:
            out.append(rom[pos])
            pos += 1
            continue
        w = rom[pos] | rom[pos + 1] << 8
        pos += 2
        n, src = (w & 15) + 3, len(out) - (w >> 4)
        for _ in range(n):
            out.append(out[src] if src >= 0 else 0)
            src += 1
    return bytes(out[:size])


def interleave(data):
    """$81:8CFE: each 16-byte tile stored as plane 0 rows then plane 1 rows -> SNES 2bpp (row-interleaved)."""
    out = bytearray(len(data))
    for t in range(0, len(data) - 15, 16):
        for r in range(8):
            out[t + 2 * r] = data[t + r]
            out[t + 2 * r + 1] = data[t + 8 + r]
    return bytes(out)


def snes_off(bank, addr):
    return ((bank & 0x7F) << 15) | (addr & 0x7FFF)
