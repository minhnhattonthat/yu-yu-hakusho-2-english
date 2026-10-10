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


def compressed_len(rom, off):
    """Bytes the block at `off` occupies (header + flag bytes + literals/words)."""
    size = rom[off] | rom[off + 1] << 8
    pos, n, bits, flags = off + 2, 0, 0, 0
    while n < size:
        if bits == 0:
            flags, bits = rom[pos], 8
            pos += 1
        bits -= 1
        lit, flags = flags & 1, flags >> 1
        if lit:
            pos += 1
            n += 1
        else:
            n += (rom[pos] & 15) + 3
            pos += 2
    return pos - off


def interleave(data):
    """$81:8CFE: each 16-byte tile stored as plane 0 rows then plane 1 rows -> SNES 2bpp (row-interleaved)."""
    out = bytearray(len(data))
    for t in range(0, len(data) - 15, 16):
        for r in range(8):
            out[t + 2 * r] = data[t + r]
            out[t + 2 * r + 1] = data[t + 8 + r]
    return bytes(out)


def deinterleave(data):
    """Inverse of interleave(): SNES 2bpp row-interleaved -> the planar-per-16-bytes layout the LZ block stores."""
    out = bytearray(len(data))
    for t in range(0, len(data) - 15, 16):
        for r in range(8):
            out[t + r] = data[t + 2 * r]
            out[t + 8 + r] = data[t + 2 * r + 1]
    return bytes(out)


def compress(data):
    """Greedy LZ for the game's decoder (longest match, window 4095, 3-18 bytes); decompress(compress(x)) == x."""
    out = bytearray([len(data) & 255, len(data) >> 8])
    pos, n = 0, len(data)
    chains = {}
    group, flags, nbits = bytearray(), 0, 0
    while pos < n:
        best, dist = 0, 0
        key = bytes(data[pos:pos + 3])
        if len(key) == 3:
            for cand in reversed(chains.get(key, [])[-64:]):
                if pos - cand > 4095:
                    break
                ln = 3
                while ln < 18 and pos + ln < n and data[cand + ln] == data[pos + ln]:
                    ln += 1
                if ln > best:
                    best, dist = ln, pos - cand
        step = best if best >= 3 else 1
        if best >= 3:
            group += ((dist << 4) | (best - 3)).to_bytes(2, "little")
        else:
            flags |= 1 << nbits
            group.append(data[pos])
        nbits += 1
        for p in range(pos, pos + step):
            k = bytes(data[p:p + 3])
            if len(k) == 3:
                chains.setdefault(k, []).append(p)
        pos += step
        if nbits == 8:
            out.append(flags)
            out += group
            group, flags, nbits = bytearray(), 0, 0
    if nbits:
        out.append(flags)
        out += group
    return bytes(out)


def snes_off(bank, addr):
    return ((bank & 0x7F) << 15) | (addr & 0x7FFF)
