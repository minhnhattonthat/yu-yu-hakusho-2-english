-- Record which WRAM bytes get written after frame START (skips the boot-time clear); dump bitmaps at the end:
-- OUT/wramuse.txt ($7E0000-$7EFFFF, low WRAM via $00/$80 mirrors) and OUT/wramuse7f.txt ($7F0000-$7FFFFF).
local START = START or 600
local used, used7f = {}, {}
local function rec(t, mask) return function(addr) if L.frame > START then t[addr & mask] = true end end end
local snes, mem = emu.cpuType.snes, emu.memType.snesMemory
emu.addMemoryCallback(rec(used, 0xFFFF), emu.callbackType.write, 0x7E0000, 0x7EFFFF, snes, mem)
emu.addMemoryCallback(rec(used7f, 0xFFFF), emu.callbackType.write, 0x7F0000, 0x7FFFFF, snes, mem)
emu.addMemoryCallback(rec(used, 0x1FFF), emu.callbackType.write, 0x000000, 0x001FFF, snes, mem)
emu.addMemoryCallback(rec(used, 0x1FFF), emu.callbackType.write, 0x800000, 0x801FFF, snes, mem)
local function bits(t)
  local s = {}
  for a = 0, 0xFFFF do s[#s + 1] = t[a] and "1" or "0" end
  return table.concat(s)
end
L.on_frame(function(f)
  if f == FRAMES - 2 then
    L.write_file(OUT .. "wramuse.txt", bits(used))
    L.write_file(OUT .. "wramuse7f.txt", bits(used7f))
  end
end)
