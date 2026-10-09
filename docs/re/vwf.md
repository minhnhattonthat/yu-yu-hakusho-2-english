# English rendering (asm/main.asm)

## Relocation
- New 24-bit tables at `$88:AB77` (296 messages) and `$88:AB77+888` (64 substrings), written by tools/build.py.
- Hooks `$80:D966` (main) and `$80:D8BA` (substring) JML to `main_ptr`/`sub_ptr` in `$A0:E100`, which set DB to the
  string's bank and Y to ptr + offset, then JML back to the read loop `$80:D979`.
- **Text banks must be `$80-$BF`**: the read loop touches `$0Bxx` with absolute addressing while DB = text bank, so the
  bank must mirror low WRAM. Free space used (build.FREE): old JP area in $88, tails of $AF, $B5, $B1.

## Encoding (English)
- `>= $2020`: two ASCII chars, low byte first. `$0320-$037E`: one ASCII char. `$0300` = `{tab}` (pen to next cell
  boundary; for menus whose tilemap places 16-px cells). Japanese glyph codes still work (cell aligned).
- Controls unchanged (`{n}` `{clr}` `{wait}` `{end}` `{nameX}` `{subXX}`).

## VWF
- `$80:DAAE` (glyph draw) → `vwf_glyph`. Pen = cell (`$0B01*11 + $0B00`) + pixel offset `$0AF0`.
  `$0AF1/$0AF2` hold the `$0B00/$0B01` seen after the last glyph; any other value means the pen was moved (newline,
  menu label at a new position) and resets the pixel offset. Box clear (`$80:D88A` hook) also resets it.
- WRAM `$7E8000-$7E8FFF` is a mirror of the 64 text cells at VRAM `$6000` (64 bytes per cell, tiles TL,TR,BL,BR).
  Glyphs (8x16, 2 tiles, 32 bytes, from font/en_glyphs.txt) are OR-ed in at 8-px tile columns, shifted with the
  hardware multiplier. A cell is zeroed when the pen first enters it.
- Upload: the original NMI routine `$80:8C17` copies `$7E8000+$B9 .. +$B7` to VRAM `$B5 + $B9/2`; vwf sets
  `$B5=$6000`, `$B9/$B7` = touched range (merged with a pending upload), sets `$B3` bit 0.
- WRAM used: `$0AF0-$0AF2`, scratch `$09B0-$09BF` (never written by the original in a story+battle run;
  re-check with tools/lua/wramuse.lua after touring other modes).
- Line width: 11 cells = 176 px.
