# Yu Yu Hakusho 2: Kakutou no Shou (SNES) English translation

Skill: translate-retro-game (H:/translation/.claude/skills/translate-retro-game/SKILL.md). Read it before ROM, text or QA work.

## Commands (run from repo root; always `python -X utf8`)
- Dump:     `python -X utf8 tools/text.py dump [--force]` -> script/messages.json, script/substrings.json (never clobbers without --force)
- Check:    `python -X utf8 tools/check.py` (pytest tests/; the pre-commit hook runs this)
- Smoke:    `python -X utf8 H:/translation/.claude/skills/translate-retro-game/scripts/emu.py ROM --out work/qa/smoke --frames 1800 --smoke`
- Story route: `--route-str "1450 -;6 start;300 -;6 start;120 -;6 start;300 -" --mash 90 --mash-key a` (title -> story mode -> dialogue)
- Disasm:   `python -X utf8 tools/dis65816.py ROM 80D950 [n] [--m8] [--x8]`; font sheet: `tools/fontview.py`

## Paths
- ROM: `rom/Yu Yu Hakusho 2 - Kakutou no Shou (Japan).sfc` (gitignored). Mesen2: tools/mesen2/Mesen.exe, asar: tools/asar/asar.exe.
- Text: script/*.json (id, off, jp, en, same_as). Table: tbl/jp.tbl. Glossary + rulings: glossary.md. Lua hooks: tools/lua/.
- RE notes: docs/re/text-engine.md (encoding, tables, renderer, menus).

## Rulings
- Official EN names (Viz/Funimation), Western order, no honorifics. Credits in English. No abbreviations. Specs/plans pre-approved.
- Review agents may use the multi-openai agent (gpt-6-astra).

## Status
- Done: setup, recon (text bank $88, 296 msgs + 64 substrings, roundtrip test).
- Next: identity build, expanded-ROM relocation + VWF spike, marker build.
