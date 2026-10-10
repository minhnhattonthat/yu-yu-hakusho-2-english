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

## Block replacement (tools/gfx.py, tools/graphics.py)
`gfx.Gfx` decodes an LZ block, takes edited data, re-compresses it (`lz.compress`, within ~2% of the game's size) and
overwrites the original when it fits and nothing else loads it; otherwise it goes to `graphics.FREE` and the loaders
(`LDX #bank / LDA #addr / JSL $81:8CF3|8C35`, either order) are repointed. `only=` limits which loaders move (the namco
splash `$AF:C60B` shares `$B4:9354` with the title and keeps the original). Every touched range is in `allowed_ranges.txt`.
- Title (`$AF:C73C`, return path `$AF:CD0B`): BG1 tiles `$B4:8000` (4bpp, 252 tiles, pal 2) + map `$B4:99A8` (screen 1 rows
  0-10 = logo, screen 2 rows 11-13 = subtitle); BG3 tiles `$B4:9354` (2bpp; text index 2, shadow 3) + map `$B4:9CB1`
  (screen rows 14-26: PUSH START 14, namcot 16-17, copyright 19-20 / 22-23, 1994 line 25-26). The logo is
  `art/title_logo.png` (256x88 indices; `tools/make_logo.py` draws "YU YU / HAKUSHO" and keeps the gold 2; edit the PNG by
  hand if wanted), cut into deduplicated tiles. Subtitle "Fighting Chapter" and the two copyright lines use the VWF font.
- Mini-game gauge: `$B2:EB9E` (4bpp, loads at BG1 tile $10, pal 1: 15 white / 14 black); 怒 was cells $18-$1F,$28-$2B, now
  "RAGE" in the two cell rows beside the bar.
- Intro names: `$8A:EAC9` (2bpp, 16 tiles wide; each name 8x4 tiles = 64x32 px: Yusuke, Kurama top, Kuwabara, Hiei bottom),
  `art/intro_names.png` from `tools/make_names.py`. The maps that place them are unchanged (width limit 64 px).

## Debug views
`tools/bgview.py` (BG layer from a dump), `tools/oamview.py` (sprites), `tools/gfxview.py` (block tiles),
`tools/lua/vramseq.lua` / `titletrace.lua` (timed dumps, decompress + DMA log). Run timing varies between runs (autoplay),
so dump a frame window or trigger on a VRAM value instead of an absolute frame.

## Not done
- Brush-calligraphy "幽遊白書" backdrop of the mode select and story cards (tiles `$B2:C6A3`, 4bpp 192 tiles).
