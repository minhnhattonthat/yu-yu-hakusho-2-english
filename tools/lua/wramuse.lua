-- Record which low-WRAM bytes ($0000-$1FFF) and $7E2000-$7EFFFF pages get written; dump bitmap at the end.
local used = {}
emu.addMemoryCallback(function(addr) used[addr & 0xFFFF] = true end, emu.callbackType.write, 0x7E0000, 0x7EFFFF,
  emu.cpuType.snes, emu.memType.snesMemory)
emu.addMemoryCallback(function(addr) used[addr & 0x1FFF] = true end, emu.callbackType.write, 0x000000, 0x001FFF,
  emu.cpuType.snes, emu.memType.snesMemory)
emu.addMemoryCallback(function(addr) used[addr & 0x1FFF] = true end, emu.callbackType.write, 0x800000, 0x801FFF,
  emu.cpuType.snes, emu.memType.snesMemory)
L.on_frame(function(f)
  if f == FRAMES - 2 then
    local t = {}
    for a = 0, 0xFFFF do t[#t + 1] = used[a] and "1" or "0" end
    L.write_file(OUT .. "wramuse.txt", table.concat(t))
  end
end)
