"""Minimal 65816 disassembler for LoROM recon. Tracks REP/SEP linearly (no flow analysis).

    python -X utf8 tools/dis65816.py ROM 80D960 [count] [--m8] [--x8]
"""
import sys

# mnemonic, mode per opcode
OPS = """
00 BRK imm8|01 ORA dpxi|02 COP imm8|03 ORA sr|04 TSB dp|05 ORA dp|06 ASL dp|07 ORA dpil|08 PHP|09 ORA immm|0A ASL A|0B PHD|0C TSB abs|0D ORA abs|0E ASL abs|0F ORA long
10 BPL rel|11 ORA dpiy|12 ORA dpi|13 ORA sriy|14 TRB dp|15 ORA dpx|16 ASL dpx|17 ORA dpily|18 CLC|19 ORA absy|1A INC A|1B TCS|1C TRB abs|1D ORA absx|1E ASL absx|1F ORA longx
20 JSR abs|21 AND dpxi|22 JSL long|23 AND sr|24 BIT dp|25 AND dp|26 ROL dp|27 AND dpil|28 PLP|29 AND immm|2A ROL A|2B PLD|2C BIT abs|2D AND abs|2E ROL abs|2F AND long
30 BMI rel|31 AND dpiy|32 AND dpi|33 AND sriy|34 BIT dpx|35 AND dpx|36 ROL dpx|37 AND dpily|38 SEC|39 AND absy|3A DEC A|3B TSC|3C BIT absx|3D AND absx|3E ROL absx|3F AND longx
40 RTI|41 EOR dpxi|42 WDM imm8|43 EOR sr|44 MVP mv|45 EOR dp|46 LSR dp|47 EOR dpil|48 PHA|49 EOR immm|4A LSR A|4B PHK|4C JMP abs|4D EOR abs|4E LSR abs|4F EOR long
50 BVC rel|51 EOR dpiy|52 EOR dpi|53 EOR sriy|54 MVN mv|55 EOR dpx|56 LSR dpx|57 EOR dpily|58 CLI|59 EOR absy|5A PHY|5B TCD|5C JML long|5D EOR absx|5E LSR absx|5F EOR longx
60 RTS|61 ADC dpxi|62 PER rell|63 ADC sr|64 STZ dp|65 ADC dp|66 ROR dp|67 ADC dpil|68 PLA|69 ADC immm|6A ROR A|6B RTL|6C JMP absi|6D ADC abs|6E ROR abs|6F ADC long
70 BVS rel|71 ADC dpiy|72 ADC dpi|73 ADC sriy|74 STZ dpx|75 ADC dpx|76 ROR dpx|77 ADC dpily|78 SEI|79 ADC absy|7A PLY|7B TDC|7C JMP absxi|7D ADC absx|7E ROR absx|7F ADC longx
80 BRA rel|81 STA dpxi|82 BRL rell|83 STA sr|84 STY dp|85 STA dp|86 STX dp|87 STA dpil|88 DEY|89 BIT immm|8A TXA|8B PHB|8C STY abs|8D STA abs|8E STX abs|8F STA long
90 BCC rel|91 STA dpiy|92 STA dpi|93 STA sriy|94 STY dpx|95 STA dpx|96 STX dpy|97 STA dpily|98 TYA|99 STA absy|9A TXS|9B TXY|9C STZ abs|9D STA absx|9E STZ absx|9F STA longx
A0 LDY immx|A1 LDA dpxi|A2 LDX immx|A3 LDA sr|A4 LDY dp|A5 LDA dp|A6 LDX dp|A7 LDA dpil|A8 TAY|A9 LDA immm|AA TAX|AB PLB|AC LDY abs|AD LDA abs|AE LDX abs|AF LDA long
B0 BCS rel|B1 LDA dpiy|B2 LDA dpi|B3 LDA sriy|B4 LDY dpx|B5 LDA dpx|B6 LDX dpy|B7 LDA dpily|B8 CLV|B9 LDA absy|BA TSX|BB TYX|BC LDY absx|BD LDA absx|BE LDX absy|BF LDA longx
C0 CPY immx|C1 CMP dpxi|C2 REP imm8|C3 CMP sr|C4 CPY dp|C5 CMP dp|C6 DEC dp|C7 CMP dpil|C8 INY|C9 CMP immm|CA DEX|CB WAI|CC CPY abs|CD CMP abs|CE DEC abs|CF CMP long
D0 BNE rel|D1 CMP dpiy|D2 CMP dpi|D3 CMP sriy|D4 PEI dp|D5 CMP dpx|D6 DEC dpx|D7 CMP dpily|D8 CLD|D9 CMP absy|DA PHX|DB STP|DC JML absil|DD CMP absx|DE DEC absx|DF CMP longx
E0 CPX immx|E1 SBC dpxi|E2 SEP imm8|E3 SBC sr|E4 CPX dp|E5 SBC dp|E6 INC dp|E7 SBC dpil|E8 INX|E9 SBC immm|EA NOP|EB XBA|EC CPX abs|ED SBC abs|EE INC abs|EF SBC long
F0 BEQ rel|F1 SBC dpiy|F2 SBC dpi|F3 SBC sriy|F4 PEA abs|F5 SBC dpx|F6 INC dpx|F7 SBC dpily|F8 SED|F9 SBC absy|FA PLX|FB XCE|FC JSR absxi|FD SBC absx|FE INC absx|FF SBC longx
"""
TABLE = {}
for item in OPS.replace("\n", "|").split("|"):
    if item.strip():
        p = item.split()
        TABLE[int(p[0], 16)] = (p[1], p[2] if len(p) > 2 else "")

FMT = {"dp": "${:02X}", "dpx": "${:02X},x", "dpy": "${:02X},y", "dpi": "(${:02X})", "dpxi": "(${:02X},x)",
       "dpiy": "(${:02X}),y", "dpil": "[${:02X}]", "dpily": "[${:02X}],y", "sr": "${:02X},s", "sriy": "(${:02X},s),y",
       "abs": "${:04X}", "absx": "${:04X},x", "absy": "${:04X},y", "absi": "(${:04X})", "absxi": "(${:04X},x)",
       "absil": "[${:04X}]", "long": "${:06X}", "longx": "${:06X},x", "imm8": "#${:02X}"}
SIZE = {"": 0, "A": 0, "dp": 1, "dpx": 1, "dpy": 1, "dpi": 1, "dpxi": 1, "dpiy": 1, "dpil": 1, "dpily": 1, "sr": 1,
        "sriy": 1, "abs": 2, "absx": 2, "absy": 2, "absi": 2, "absxi": 2, "absil": 2, "long": 3, "longx": 3,
        "imm8": 1, "rel": 1, "rell": 2, "mv": 2}


def rom_off(addr):
    return ((addr & 0x7F0000) >> 1) | (addr & 0x7FFF)


def disasm(rom, addr, count, m8=False, x8=False):
    out = []
    for _ in range(count):
        off = rom_off(addr)
        op = rom[off]
        mn, mode = TABLE[op]
        if mode == "immm":
            n, fmt = (1, "#${:02X}") if m8 else (2, "#${:04X}")
        elif mode == "immx":
            n, fmt = (1, "#${:02X}") if x8 else (2, "#${:04X}")
        else:
            n, fmt = SIZE[mode], FMT.get(mode)
        val = int.from_bytes(rom[off + 1: off + 1 + n], "little")
        if mode == "rel":
            arg = "${:04X}".format((addr + 2 + (val - 256 if val > 127 else val)) & 0xFFFF)
        elif mode == "rell":
            arg = "${:04X}".format((addr + 3 + (val - 65536 if val > 32767 else val)) & 0xFFFF)
        elif mode == "mv":
            arg = "${:02X},${:02X}".format(val & 0xFF, val >> 8)
        elif mode == "A":
            arg = "A"
        else:
            arg = fmt.format(val) if fmt else ""
        if mn == "REP":
            m8 = m8 and not (val & 0x20); x8 = x8 and not (val & 0x10)
        if mn == "SEP":
            m8 = m8 or bool(val & 0x20); x8 = x8 or bool(val & 0x10)
        out.append(f"{addr:06X}  {rom[off:off + 1 + n].hex(' '):12s} {mn} {arg}")
        addr = (addr & 0xFF0000) | ((addr + 1 + n) & 0xFFFF)
    return out


if __name__ == "__main__":
    rom = open(sys.argv[1], "rb").read()
    count = int(sys.argv[3]) if len(sys.argv) > 3 and not sys.argv[3].startswith("--") else 40
    print("\n".join(disasm(rom, int(sys.argv[2], 16), count, "--m8" in sys.argv, "--x8" in sys.argv)))
