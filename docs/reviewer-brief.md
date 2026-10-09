# Translation reviewer brief - Yu Yu Hakusho 2: Kakutou no Shou

You review one batch of a JP->EN fan translation of a 1994 YuYu Hakusho SNES fighting game. Read-only: no edits, no
git, no subagents. Mechanical validity (ids, control codes, ASCII, width, glossary names) is already enforced by the
check tool - judge translation quality.

## Inputs (repo root H:/translation/yu-yu-hakusho-2)
- Pairs file `work/tl/<batch>.pairs.txt`: every translated entry as `>> id | JP` / `EN` with +-2 context lines. Read
  ALL of it, in passes if large. `{n}` in JP is a line break, `{clr}` a page start, `{name2}`/`{name3}` a fighter or
  move name filled in by the game.
- `glossary.md` (rulings at the top), `docs/style-reference.md`, and the translator's notes in your dispatch
  (unverified claims).

## Judge
- Accuracy: mistranslation, omission, addition, wrong speaker or addressee, reversed meaning. Quote the JP and say
  what it means.
- Consistency: glossary names/terms exactly; voice matches the style reference (Yusuke brash, Kurama polite, Hiei
  curt, Genkai gruff, Toguro cold, Chu drunk, Jin folksy).
- Things players caught that reviewers missed before: jokes/wordplay losing their punch; ordinal suffix after a
  variable ("1th"); abbreviated names or terms; stock phrases that read awkwardly in English.
- Naturalness: would a fan-translation reader stumble?

## Report (reply with only this)
### Issues
#### Critical (meaning reversed, broken placeholder grammar, wrong speaker)
#### Important (clear mistranslation, glossary inconsistency, abbreviation)
#### Minor (style - deferred to one polish pass)
Each: `id - JP gist - problem - suggested EN`.
### Assessment
Approved | Needs fixes - one sentence why.
