# Yu Yu Hakusho 2: Kakutou no Shou English translation

Unofficial English fan translation of **Yu Yu Hakusho 2: Kakutou no Shou** (Super Famicom, Namco, 1994): the source
text and tools that build the patch.

**No game data is included.** Download the BPS patch from the [latest release](../../releases/latest) and apply it to
your own unheadered dump, `Yu Yu Hakusho 2 - Kakutou no Shou (Japan).sfc` (CRC32 EEF45A93). The release README lists
the hashes, patching steps and known issues.

## What is translated
All story text, menus, move lists, battle labels, the hint screen, the options screen, the training and mini-game text,
the HUD names, the title logo and copyright lines, attract-mode names and the staff credits. Names follow the official
English (Funimation) dub, in Western order, without honorifics. English uses a variable-width font.

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
