-- Dump VRAM (64 KB) and PPU state keys at frame DUMP_AT (default: end of route) to OUT/vram.bin, OUT/ppu.txt.
local function dump()
  local t = {}
  for a = 0, 0xFFFF do t[#t + 1] = string.char(emu.read(a, emu.memType.snesVideoRam)) end
  L.write_file(OUT .. "vram.bin", table.concat(t))
  local s = emu.getState()
  local keys = {}
  for k, v in pairs(s) do if k:find("^ppu") then keys[#keys + 1] = k .. "=" .. tostring(v) end end
  table.sort(keys)
  L.write_file(OUT .. "ppu.txt", table.concat(keys, "\n"))
end
L.on_frame(function(f) if f == (DUMP_AT or FRAMES - 3) then dump() end end)
