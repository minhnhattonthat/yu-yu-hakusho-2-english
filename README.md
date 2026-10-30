# Yu Yu Hakusho 2: Kakutou no Shou English translation

Unofficial English fan translation of **Yu Yu Hakusho 2: Kakutou no Shou** (Super Famicom, Namco, 1994): the source
text and tools that build the patch.

**No game data is included.** Download the BPS patch from the [latest release](../../releases/latest) and apply it to
your own unheadered dump, `Yu Yu Hakusho 2 - Kakutou no Shou (Japan).sfc` (CRC32 EEF45A93). The release README lists
the hashes, patching steps and known issues.

**Found a bug?** [Report it](../../issues/new/choose): untranslated text, typos, overflow, crashes. Attaching a savestate
helps most.

## Translation status
| Part | Status |
|---|---|
| Story mode, win/lose quotes, announcer, endings | Translated |
| Menus, options, move lists, battle labels, hint screen, fight HUD names | Translated ("Experience" on the story tally reads "EXP": room for 3 letters) |
| Training text and the punching mini-game | Translated |
| Title screen and attract-mode names | Translated (logo, subtitle and copyright lines redrawn in English) |
| Brush-calligraphy series logo behind mode select and story pages | Left in Japanese (artwork) |
| Staff credits and voice cast | Translated |

Names follow the official English (Funimation) dub, in Western order, without honorifics. English uses a
variable-width font.

Known issues: the calligraphy backdrop and "EXP" above; the staff roll reuses the Japanese letter cells, so
"E ri ri n" and "Ma Ma" are unevenly spaced and the programmer 仁田 石 reads "Nitta".

## Building from source
You need your own ROM under `rom/` (gitignored) and asar. See `CLAUDE.md` for the commands
(`python -X utf8 tools/build.py`, `tools/check.py`, `tools/release.py`) and `docs/re/` for the text engine, VWF, menu
and graphics research.

- `script/`: messages, substrings, battle labels and other text (Japanese + English)
- `asm/`: VWF and relocation patches
- `font/`, `art/`: English font and graphics art
- `tools/`: build, text batches, fit, graphics and release tools
- `tbl/`: text tables
- `glossary.md`: naming rulings

## Support

If you enjoy this translation, you can support my work on Ko-fi:

[![Support me on Ko-fi](https://ko-fi.com/img/githubbutton_sm.svg)](https://ko-fi.com/minhnhattonthat)

Translation, tools and patch were produced with AI assistance (Claude, Anthropic) under the direction of the project
owner. Yu Yu Hakusho is (c) Yoshihiro Togashi / Shueisha; the game is (c) Namco. This project is not affiliated with
them. Do not share patched ROMs.
