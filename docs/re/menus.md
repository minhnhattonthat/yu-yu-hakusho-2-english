# Cell-grid screens

Several screens print a message into consecutive 16-px text cells and let a fixed BG3 tilemap place (and reuse)
those cells. English for them is written as `row | row | ...`, one entry per run of cells (build.GRIDS); `>` right-
aligns, `^` centres, extra leading spaces indent 4 px each. Find a layout with `tools/build.py --cells` (each cell
shows its stream index) or a VRAM dump + `tools/cellmap.py DUMP --map 4800|7800 --rows`.

| Message | Screen | Runs (cells) | Notes |
|---|---|---|---|
| M004 / M005 | mode select, submenus, sound mode, battle submenu | 5,3,4,3,6,4,7,5,4,6,5,2,2,5,4,4,1,1,2,1,3 | every mode item = its label + the shared "Mode" run (left blank in English); "2P" = cell 74 + the P of "1P"; "Press B / to exit" split by a tilemap gap |
| M01E, M01F, M064-M06F | training move lists | 11,9,8,9,11,10,12,12,12,13,13,12 | row x: 6,4,4,6,4,6,4,6,4,4,4,6 tiles; Hiei's list is shifted down a row so "Fist of the Mortal Flame" fits |
| M0FA, M0FB | staff roll | see build.GRIDS | くん = cells 20+49, ちゃん = 47-49, ママ = 39 twice, えりりん = 116,117,117,118, けんじろう = 119,118,120-122 |
| M11C-M127 | voice cast | 7, 5 | English puts the actor on the 7-cell row, the character on the 5-cell row |
| T01-T04 | story tally | 8, 1 | only 3 cells of the label show (the score overwrites the rest) |

Battle labels (other.json B): drawn at cell 55/59 over the fight; 5 cells visible; `$85:B3DA` holds a BG3 scroll
offset per label that centres it, recomputed by the build from the width change.
