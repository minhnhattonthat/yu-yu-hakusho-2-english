# Text engine (story / menus / win quotes)

ROM: LoROM FastROM ($30), 2 MB, header "YUUYUU HAKUSYO 2", checksum $51AC. Base: No-Intro "Yu Yu Hakusho 2 - Kakutou no Shou (Japan)", CRC32 EEF45A93, SHA-1 54198529c9d989b7dbaf767d5185e9557f178292.

## Encoding
- 16-bit little-endian words. Glyph codes `$0100-$02FF` (512 glyphs). `tbl/jp.tbl` (byte-order keys, e.g. `0101=あ`).
- Kana in gojuon order from $0101 (あ). Many unused kana slots hold kanji (ぢ→粉, ハ→★, ホ→鬪 ...).
- Controls, **no argument words**:
  - `0000` end; `000A` newline (past line limit `$0B03` → auto wait + clear page)
  - `0001-007F` draw as space ($0100)
  - `0080-00DF` call substring `code-$80` from table `$88:E4ED` (64 entries: names, special moves)
  - `00E0-00F5` no-op
  - `00F6-00F9` print WRAM variable strings `$0B39/$0B49/$0B59/$0B69`
  - `00FA-00FD` call substring `$0B29/$0B2B/... + $30` (fighter names via the substring table)
  - `00FE` clear box, `00FF` wait for A + clear.

## Tables
- Message table `$88:A927` (file 0x42927), 296 × 16-bit pointers into bank $88. Many duplicates.
- Substring table `$88:E4ED` (file 0x464ED), 64 entries.
- Text data 0x42B77-0x475BB, fully covered by both tables (test_text.py).

## Code
- Per-frame printer `$80:D7FB` (state bits in `$0B12`), main stream `$80:D963`: `Y = [$A927 + 2*$0B07] + $0B09`, `DB=$88`, read loop `$80:D979`.
- Substring stream `$80:D8B7`: `Y = [$E4ED + 2*$0B0E] + $0B10`.
- Glyph draw `$80:DA94` → `$80:DB3A`: copies glyph `(code-$100)*64` bytes from WRAM font `$7F0000` (4 2bpp tiles TL,TR,BL,BR) to staging `$7E8000`, DMA to VRAM `$B5 = $6000 + (row*$2C + col*4)*8` (words). Box is 11 cells × N lines; `$0B00` col, `$0B01` row, `$0B03` max row.
- Immediate string draw `$80:D7CE` (A = pointer in current DB): draws until `0000` or the column wraps to 0. Menus call it with offsets into the concatenated label strings M000-M005 (fixed-width cells, no terminators). ~45 call sites (JSL $80D7CE / $80D75A / $80D7FB).
- Font: decompressed at boot by `$87:8000` from `$AC:8000` and `$AC:B076` (decompressor `$81:8CF3`) to `$7F0000` (0x8000 bytes).

## Open
- M11D-M127 (voice cast list) decode as nonsense: different font loaded for that screen.
- Glyph `$93A5` inside substring S2E (踏?みつけ) is out of range: original data bug, keep.
