# Translator brief - Yu Yu Hakusho 2: Kakutou no Shou (SNES, 1994)

You translate part of the Japanese script of this YuYu Hakusho fighting game into English for a fan patch. The text
is: a story-mode recap of the anime (Spirit Detective arc through the Dark Tournament), characters' win/lose quotes,
an announcer at character select, and tournament endings. Work only on the batch named in your dispatch. Do all
translation yourself; do not dispatch subagents. Repo root: H:/translation/yu-yu-hakusho-2.

## Read first
1. `docs/style-reference.md` - voices and approved example pairs. Match this voice.
2. `work/tl/terms_<batch>.txt` - binding glossary rows for this batch (`glossary.md` has the full table and rulings).

## Input: `work/tl/<batch>.tsv`
`id<TAB>form<TAB>limit<TAB>Japanese`. ` / ` marks the Japanese line breaks: ignore them, translate the box as one
utterance. Lines are in game order; use neighbours for context.
- `story`: one page of the story recap, up to 5 lines x 176 px (~150 characters). Several pages often continue one
  sentence (e.g. a page ending in "...と" / "は"): keep the split so each page reads on in sequence.
  `『...』` pages are character quotes inside the story: write them as "..." with straight quotes.
- `quote`: a fighter's win/lose line, up to 3 lines x 176 px (~85 characters). The speaker is not given: infer it from
  voice and content (the roster: Yusuke, Kuwabara, Kurama, Hiei, Genkai, Suzaku, Chu, Jin, Shishiwakamaru, Toguro,
  the Masked Fighter / Young Genkai). Consecutive ids usually belong to the same fighter (about 5 each).
- `bubble`: the announcer at character select / tournament mode, up to 2 lines x 176 px (~55 characters).
- Control codes in `{}` (`{clr}`, `{name2}`, `{name3}`): copy every one exactly, in place. `{name2}` is a fighter's
  name, `{name3}` a special-move name: no suffix glued on, no a/an before them.

## Output: `work/tl/<batch>.out.tsv`, written with your file-write tool (never a shell heredoc)
`id<TAB>English`, every input id exactly once, same order. Plain ASCII: straight quotes, `...`, `--`; no tabs inside
the English, no Japanese or fullwidth characters. Write prose: the build word-wraps each page to the box. Only write
`{n}` to force a line break where the layout needs one (rare).

## Validate
- Dry run one line: `python -X utf8 tools/fit.py M070 "{clr}your text"` (shows the wrapped lines and pixel widths).
- Whole batch: `python -X utf8 tools/batches.py check <batch>`; fix every reported id until it prints OK.

## Style
- Faithful: keep the information and order of ideas; adapt idiom, not meaning. Don't add details the Japanese doesn't
  state; don't summarise or skip. Wordplay and jokes keep their punch (no translator notes).
- Names and terms exactly as in the glossary. Never abbreviate to fit; if a line can't fit without losing meaning,
  keep the meaning, rephrase tighter, and report `LONG: id` if it still fails.
- Honorifics dropped, Western name order. Punctuation: ……… -> `...`, ‼ -> `!!`, ！？ -> `!?`, ― -> `--`.
- Fighting-game quotes are short and punchy: no padding, no "I think that".

## Consistency
Never edit `glossary.md` or any file other than your output. For a recurring name or term not in the glossary, pick a
form, use it consistently, and report it.

## Report (reply with only this)
Files written and entry count; then any lines: `NEW TERM: jp -> en`, `UNSURE: id - note`, `LONG: id - note`.
