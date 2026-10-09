# Graphics text

LZ format (decoder `$81:8C35`, Python `tools/lz.py`): 16-bit output size, flag bytes LSB first, 1 = literal,
0 = word W -> copy (W & 15) + 3 bytes from distance W >> 4 (before the start reads 0). `$81:8CF3` = decode +
`$81:8CFE` re-interleave of each 16-byte tile into SNES 2bpp. `$81:96B2` = ROM -> VRAM DMA (A addr, X bank,
Y VRAM, $00 size); `$81:968B` = $7E8000 -> VRAM DMA.

## Fight HUD names (tools/hud.py)
- Block `$88:98CF` (0x960 bytes, uncompressed) -> VRAM `$7000` = BG3 tiles $200-$295; kanji names in $240-$295.
- Tables `$81:CF93` (P1) / `$81:D03B` (P2): 14 fighters x 12 tile bytes (6 wide x 2 rows); fighter id = `$0C04` /
  `$1104`. Ids: 0 Yusuke, 1 Kuwabara, 2 Hiei, 3 Kurama, 4 Genkai, 5 Suzaku, 6 Chu, 7 Jin, 8 Shishiwakamaru,
  9/10/13 Toguro, 11 Masked Fighter, 12 Young Genkai.
- English: block moved to `$B5:DE80` and grown to 0x1000 (tiles up to $2FF; VRAM $74B0-$77FF is unused in fights),
  rows widened to 10 tiles (P1 cols 4-13, P2 cols 18-27), tables at `$81:FD00` / `$81:FE18` (stride 20).

## Options screen (tools/options.py)
- Loader `$81:DCB6`: BG3 font `$B2:DC0D` (0xED0 -> VRAM $6000), BG3 map `$B2:E732` -> $7E8000 -> $7E2800 ->
  VRAM $6C00. Both replaced by raw copies (`load_opt_chr`/`load_opt_map`, data at `$B1:E100` / `$B5:EE80`).
- Cells are 16x16 = 4 tiles (TL,TR,BL,BR) like text cells. Static labels live in the map; dynamic values come from
  `$81:E0FE` (label index -> `$81:E12E` pointers -> cell words `$2000|tile`, `$FFFF` end): 0-3 difficulty,
  4-7 button icons, 8/9 OFF/ON, 10-12 defence level. New lists at `$81:FF30`.
- 1-player mode blanks the 2P panel (`$81:DD61`, cols 23-28 only), so 2P labels must stay within those columns.

## Not done
- Attract-mode name kanji: LZ block `$8A:EAC9` (2bpp, names 4 tiles wide x 2, two styles); the intro tilemaps
  (`$8A:F4CC`, `$8A:F2D1`) would need widening for English.
- Title logo, copyright lines, mini-game "怒" gauge.
