# Yu Yu Hakusho 2: Kakutou no Shou (SNES) English translation

Skill: translate-retro-game (H:/translation/.claude/skills/translate-retro-game/SKILL.md). Read it before ROM, text or QA work.

## Commands (run from repo root; always `python -X utf8`)
- Build:  `python -X utf8 tools/build.py [--marker|--cells] [--out build/yyh2_en.sfc]` (font -> asar asm/main.asm -> text insert; fails on overflow). `--cells` prints each grid cell's stream index (menu/credits layout debugging).
- Check:  `python -X utf8 tools/check.py` (pytest tests/ + `batches.py lint`; the pre-commit hook runs this)
- Text:   `tools/batches.py split|check|merge|pairs <batch>` (batches b01-b03, special, other, subs, credits), `apply FILE` (id<TAB>EN fixes). Fit one line: `tools/fit.py M070 "text"`.
- Smoke:  `python -X utf8 H:/translation/.claude/skills/translate-retro-game/scripts/emu.py build/yyh2_en.sfc --out work/qa/smoke --frames 1800 --smoke`
- Story autoplay (whole story + credits, ~65k frames): `emu.py ROM --out DIR --route-str "1450 -;6 start;300 -;6 start;120 -;6 start;100 -" --frames 40000 --script tools/lua/autoplay.lua` (keeps P1 HP $0C0A at 50, opponent $110A at 1; logs message ids). States: work/states/mode_select.mss, pre_credits.mss (EN build), train_select.mss.
- Debug Lua: tools/lua/ vwflog (VWF calls), vramdump (+tools/cellmap.py), vramaddr (who uploads a tilemap), wramuse (free WRAM), ramsnap, fontdump. Disasm: tools/dis65816.py.

## Paths
- ROM: `rom/Yu Yu Hakusho 2 - Kakutou no Shou (Japan).sfc` (gitignored). Mesen2: tools/mesen2, asar: tools/asar.
- Text: script/messages.json (M = $88 message table), substrings.json (S), other.json (B = $85 battle labels, T = $81 tally, P = $80 PAUSE). Tables: tbl/jp.tbl, tbl/credits.tbl (credits font swap $208-$2FF). Glossary + rulings: glossary.md. Briefs: docs/translator-brief.md, reviewer-brief.md, style-reference.md.
- RE notes: docs/re/text-engine.md, docs/re/vwf.md, docs/re/menus.md (cell grids).

## Rulings
- Official EN names (Funimation dub), Western order, no honorifics (also in staff credits). Credits in English. No abbreviations (flagged exception: tally "EXP", 3-cell label). Specs/plans pre-approved.
- Review agents: multi-openai gpt-6-astra (Agent dispatch was often blocked by the classifier; self-review then).

## Status
- Done: VWF + relocation, all script text translated (b01-b03 + menus, move lists, battle labels, substrings, credits), astra review b01, self-review b02/b03, story autoplay tour + credits checked in-game.
- Next: graphics text (fight HUD names, attract-mode name kanji, option screen, title copyright), M0F8/M0F9 hints (layout unknown), M000 (probably unused), sampled whole-project review, release (BPS + README).
- Known issues: staff roll "Ma Ma"/"E ri ri n" spacing (original tilemap reuses cells); credit "Nitta" lacks the one-cell given name 石.
