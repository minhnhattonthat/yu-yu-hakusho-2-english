Yu Yu Hakusho 2: Kakutou no Shou (SNES) - English Translation v{VERSION}
=========================================================================

An unofficial fan translation of Namco/TOSE's 1994 Super Famicom fighting game
"Yuu Yuu Hakusho 2 - Kakutou no Shou" into English.

Translated:
- Story mode: the full recap of the anime (Spirit Detective to the Dark Tournament),
  every story page and character quote, the ending.
- Win/lose quotes, the character-select and tournament announcer, tournament endings.
- Menus (mode select, sub-menus, sound test), the Options screen, the training move
  lists, battle labels (Round 1, Fight!, Winner...), fight HUD names, the story
  result tally and the punching mini-game (with its rage gauge).
- The title screen (logo, subtitle, copyright lines) and the attract-mode fighter names.
- Staff credits and the voice cast.

Names follow the English anime dub (Yusuke Urameshi, Kuwabara, Kurama, Hiei, Genkai,
Toguro, the Spirit Gun, the Dark Tournament...). A variable-width font replaces the
Japanese 16x16 text.

Applying the patch
------------------
Apply YuYuHakusho2_KakutouNoShou_EN_v{VERSION}.bps to an unmodified, unheadered dump with
Flips, Beat or RomPatcher.js (https://www.marcrobledo.com/RomPatcher.js/).

Base ROM: Yu Yu Hakusho 2 - Kakutou no Shou (Japan).sfc (No-Intro), 2,097,152 bytes
  {BASE}
Patched ROM:
  {PATCHED}

If your file is 2,097,664 bytes it has a 512-byte copier header: remove it first.

Notes
-----
- Tested in Mesen 2. Start from a fresh boot; save states made with the Japanese
  game or an older version of this patch carry the old text engine.
- The secret codes are unchanged: on the title screen, Down Up L L R R Y X A Y makes
  every character selectable in Battle mode.

Known issues
------------
- The brush-calligraphy series logo behind the mode select and story pages is still
  the Japanese artwork.
- The story tally screen has room for three letters' worth of label, so "Experience"
  reads "EXP".
- The staff roll reuses letter cells of the original Japanese layout, so two
  nicknames ("E ri ri n", "Ma Ma") have uneven spacing, and the programmer credited
  as 仁田 石 reads "Nitta".

Credits
-------
Translation, hacking and tools: minhnhattonthat, with AI assistance (Anthropic Claude
for the engine work and translation, OpenAI models for review).

This is an unofficial fan work, not affiliated with Namco, Shueisha, Fuji TV, Studio
Pierrot or Yoshihiro Togashi. Do not distribute pre-patched ROMs.
