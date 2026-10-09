; Yu Yu Hakusho 2 English patch: text relocation + VWF. Assembled by tools/build.py (asar) onto a copy of the
; original ROM. Design notes: docs/re/vwf.md.
lorom

; ---- addresses shared with tools/build.py (keep in sync) ----
!msg_table   = $88AB77              ; 296 x 24-bit pointers (main messages)
!sub_table   = $88AB77+(296*3)      ; 64 x 24-bit pointers (substrings)

; ---- WRAM never written by the original (tools/lua/wramuse.lua) ----
!vwf_px   = $0AF0           ; byte: pen pixel offset inside the pen cell (0-15)
!vwf_col  = $0AF1           ; $0B00/$0B01 after the last glyph: a mismatch means the pen was moved
!vwf_row  = $0AF2
!cell     = $09B0           ; word: linear cell index of the pen
!tbase    = $09B2           ; word: mirror offset of the pen's 8-px tile column (top tile)
!dmalo    = $09B4           ; word: first mirror byte touched by this call
!dmahi    = $09B6           ; word: end of the mirror bytes touched
!w        = $09B8           ; byte: glyph width
!cnt      = $09B9           ; byte: loop counter
!sub      = $09BA           ; word (high byte 0): pen pixel offset inside its 8-px tile
!mul      = $09BC           ; byte: 1 << (8 - sub)
!side     = $09BD           ; byte: pen in the right tile column of its cell
!code     = $09BE           ; word
; asar sizes immediates by how they are written, not by the M/X flags: use $xx in 8-bit code, $xxxx in 16-bit.

!mirror   = $5800           ; $7E5800-$7E7FFF: WRAM mirror of 160 text cells at VRAM $6000 (64 bytes per cell:
                            ; TL, TR, BL, BR 2bpp tiles). Free after boot in story, battle, training
                            ; (wramuse.lua). Zeroed by the box clear and per cell when the pen first enters it.
!mirror_end = $2800         ; 160 cells (mode select uses cells 1-77, move lists 1-132)
!staging  = $8000           ; $7E8000: the original upload buffer read by the NMI routine
!base     = $0AF4           ; word: mirror offset that staging byte 0 holds while an upload is pending

; ---- hooks ----
org $80D966                 ; main stream pointer lookup (after JSR $DA4B; M8 X16, DB=$80)
    jml main_ptr

org $80D8BA                 ; substring stream pointer lookup (same state)
    jml sub_ptr

org $80DAAE                 ; glyph draw (A16 X16, A = code >= $0100), replaces JSR $DB3A + col/DMA bookkeeping
    jsl vwf_glyph
    plp
    rts

org $80D88A                 ; box clear: was STZ $0B00 : STZ $0B01 (M8)
    jsl vwf_clear
    nop #2

org $A0E100                 ; bank $A0 free tail (0xFF fill)
main_ptr:
    rep #$30
    lda $0B07
    asl
    clc
    adc $0B07
    tax
    sep #$20
    lda.l !msg_table+2,x
    pha
    plb
    rep #$20
    lda.l !msg_table,x
    clc
    adc $0B09
    tay
    jml $80D979

sub_ptr:
    rep #$30
    lda $0B0E
    asl
    clc
    adc $0B0E
    tax
    sep #$20
    lda.l !sub_table+2,x
    pha
    plb
    rep #$20
    lda.l !sub_table,x
    clc
    adc $0B10
    tay
    jml $80D979

vwf_clear:                  ; M8 (DB is a WRAM-mirroring bank here): reset position, pen and mirror
    stz $0B00
    stz $0B01
    lda #$00
    sta.l $7E0000+!vwf_px
    php
    rep #$30
    phx
    phy
    phb
    lda #$0000
    sta.l $7E0000+!mirror
    ldx #!mirror
    ldy #!mirror+2
    lda #!mirror_end-3
    mvn $7E,$7E             ; overlapping forward copy = fill with zero
    plb
    ply
    plx
    plp
    rtl

; vwf_glyph: draw one code at ($0B00,$0B01) into the mirror and queue the upload. A16 X16 on entry.
;   $0300        tab: move the pen to the next cell boundary
;   $0320-$037E  one ASCII char (code & $7F)
;   >= $2020     two ASCII chars, low byte first
;   else         Japanese 16x16 glyph from the WRAM font (cell aligned)
vwf_glyph:
    phb
    sta.l $7E0000+!code
    sep #$20
    lda #$7E
    pha
    plb
    lda $0B00
    cmp !vwf_col
    bne .moved
    lda $0B01
    cmp !vwf_row
    beq .same
.moved:
    stz !vwf_px
.same:
    rep #$30
    jsr calc_cell
    lda !cell
    asl #6
    sta !dmalo
    sta !dmahi
    lda !code
    cmp #$2020
    bcs .pair
    cmp #$0320
    bcs .single
    cmp #$0300
    beq .tab
    jsr draw_jp
    bra .done
.tab:
    jsr align
    bra .done
.pair:
    and #$00FF
    jsr draw_ascii
    lda !code
    xba
    and #$00FF
    jsr draw_ascii
    bra .done
.single:
    and #$007F
    jsr draw_ascii
.done:
    sep #$20
    lda $0B00
    sta !vwf_col
    lda $0B01
    sta !vwf_row
    rep #$20
    jsr queue_dma
    plb
    rtl

; !cell = $0B01 * 11 + $0B00 (A16)
calc_cell:
    lda $0B01
    and #$00FF
    sta !cell
    asl
    clc
    adc !cell               ; 3r
    sta !tbase
    lda !cell
    asl #3                  ; 8r
    clc
    adc !tbase
    sta !cell               ; 11r
    lda $0B00
    and #$00FF
    clc
    adc !cell
    sta !cell
    rts

; pen to the next cell boundary (A16 in/out)
align:
    sep #$20
    lda !vwf_px
    beq +
    stz !vwf_px
    inc $0B00
+   rep #$20
    jmp calc_cell

; Japanese glyph: align, copy 64 bytes from $7F0000 + (code-$100)*64 to the pen cell, advance one cell.
draw_jp:
    jsr align
    lda !code
    sec
    sbc #$0100
    asl #6
    tax
    lda !cell
    asl #6
    tay
    sep #$20
    lda #$40
    sta !cnt
-   lda.l $7F0000,x
    sta !mirror,y
    inx
    iny
    dec !cnt
    bne -
    inc $0B00
    rep #$20
    tya
    sta !dmahi
    rts

; zero the 64-byte mirror cell at mirror offset A (A16 X16)
clear_cell:
    tay
    ldx #$0020
-   lda #$0000
    sta !mirror,y
    iny
    iny
    dex
    bne -
    rts

; draw ASCII char A at the pen (A16 X16, DB=$7E)
draw_ascii:
    sec
    sbc #$0020
    bcs +
    rts
+   cmp #$0060
    bcc +
    rts
+   pha                     ; glyph index
    ; pen tile column
    lda !cell
    asl #6
    sta !tbase
    sep #$20
    lda !vwf_px
    bne +
    rep #$20
    lda !tbase              ; pen at a cell boundary: the cell is fresh
    jsr clear_cell
    sep #$20
    lda !vwf_px
+   and #$08
    sta !side
    beq +
    rep #$20
    lda !tbase
    clc
    adc #$0010
    sta !tbase
    sep #$20
+   rep #$20
    lda !vwf_px
    and #$0007
    sta !sub
    tax
    sep #$20
    lda.l mul_table,x
    sta !mul
    plx                     ; glyph index (X16)
    phx
    lda.l font_widths,x
    sta !w
    ; right column and sub + w > 8: the glyph spills into the next cell, which is fresh
    lda !side
    beq +
    lda !sub
    clc
    adc !w
    cmp #$09
    bcc +
    rep #$20
    lda !tbase
    clc
    adc #$0030
    jsr clear_cell
    sep #$20
+   rep #$20
    pla                     ; glyph index
    asl #5
    tax                     ; font offset
    ldy !tbase
    sep #$20
    lda #$20
    sta !cnt
.byte:
    lda.l font_data,x
    beq .next
    xba
    lda !sub
    beq .plain
    xba
    sta.l $004202
    lda !mul
    sta.l $004203
    nop #4                  ; 8-cycle multiply latency
    lda.l $004217           ; b >> sub
    ora !mirror,y
    sta !mirror,y
    lda !side
    bne .right
    lda.l $004216           ; bits shifted out -> right column of the same cell
    ora !mirror+16,y
    sta !mirror+16,y
    bra .next
.right:
    lda.l $004216           ; -> left column of the next cell
    ora !mirror+48,y
    sta !mirror+48,y
    bra .next
.plain:
    xba
    ora !mirror,y
    sta !mirror,y
.next:
    inx
    iny
    dec !cnt
    beq .advance
    lda !cnt
    cmp #$10
    bne .byte
    rep #$20                ; rows 8-15: bottom tiles are 32 bytes on (16 already stepped)
    tya
    clc
    adc #$0010
    tay
    sep #$20
    bra .byte
.advance:
    ; upload through the last cell inked: pen cell, or the next one if px + w - 1 >= 16
    lda !vwf_px
    clc
    adc !w
    pha                     ; new px, before wrapping
    dec
    cmp #$10                ; C = glyph reached the next cell
    rep #$20
    lda !cell
    inc
    bcc +
    inc
+   asl #6
    cmp #!mirror_end
    bcc +
    lda #!mirror_end
+   cmp !dmahi
    bcc +
    sta !dmahi
+   sep #$20
    pla
    cmp #$10
    bcc +
    sbc #$10
    inc $0B00
    rep #$20
    inc !cell
    sep #$20
+   sta !vwf_px
.ret:
    rep #$30
    rts

; Queue mirror bytes [dmalo, dmahi) for the NMI upload ($80:8C17 copies staging $7E8000 + $B9 .. $B7 to VRAM
; $B5 + $B9/2). While a text upload is pending, staging byte 0 = mirror offset !base, and later glyphs of the same
; frame (immediate strings) extend it; otherwise staging restarts at dmalo. (A16 X16, DB=$7E)
queue_dma:
    lda !dmahi
    cmp !dmalo
    bne +
    rts
+   sep #$20
    lda $B3
    rep #$20
    and #$0001
    beq .fresh
    lda !dmalo
    cmp !base
    bcc .refill
    ; extend: copy [dmalo, dmahi) to staging + (dmalo - base)
    sec
    sbc !base
    clc
    adc #!staging
    tay
    lda !dmahi
    sec
    sbc !base
    cmp $B7
    bcc +
    sta $B7
+   bra .copy
.refill:                    ; new range starts left of the pending one: restage [dmalo, max(dmahi, base+B7))
    lda !base
    clc
    adc $B7
    cmp !dmahi
    bcc .fresh
    sta !dmahi
.fresh:
    lda !dmalo
    sta !base
    lsr
    clc
    adc #$6000
    sta $B5
    stz $B9
    lda !dmahi
    sec
    sbc !dmalo
    sta $B7
    ldy #!staging
.copy:
    lda !dmalo
    clc
    adc #!mirror
    tax
    lda !dmahi
    sec
    sbc !dmalo
    dec
    phb
    mvn $7E,$7E
    plb
    lda #$0001
    tsb $B3
    rts

mul_table:                  ; 1 << (8 - sub), sub = 1..7 (entry 0 unused)
    db $00, $80, $40, $20, $10, $08, $04, $02
font_widths:
    incbin "../build/font_w.bin"
font_data:
    incbin "../build/font_en.bin"
end_of_code:
assert end_of_code <= $A0FFFF, "VWF code overflows bank $A0"
