-- Dump VRAM, CGRAM and OAM plus a screenshot every SEQ_STEP frames in [SEQ_FROM, SEQ_TO] to OUT/seq_<frame>.{vram,cgram,oam}.bin / .png.
-- Set SEQ_FROM/SEQ_TO/SEQ_STEP in a wrapper script before dofile()-ing this one (the run's timing varies, so sample a window).
local function dump(path, memtype, size)
  local t = {}
  for a = 0, size - 1 do t[#t + 1] = string.char(emu.read(a, memtype)) end
  L.write_file(path, table.concat(t))
end
L.on_frame(function(f)
  if f >= SEQ_FROM and f <= SEQ_TO and (f - SEQ_FROM) % SEQ_STEP == 0 then
    local p = string.format("%sseq_%06d", OUT, f)
    dump(p .. ".vram.bin", emu.memType.snesVideoRam, 0x10000)
    dump(p .. ".cgram.bin", emu.memType.snesCgRam, 0x200)
    dump(p .. ".oam.bin", emu.memType.snesSpriteRam, 0x220)
    L.write_file(p .. ".png", emu.takeScreenshot())
    local keys = {}
    for k, v in pairs(emu.getState()) do if k:find("^ppu") then keys[#keys + 1] = k .. "=" .. tostring(v) end end
    table.sort(keys)
    L.write_file(p .. ".ppu.txt", table.concat(keys, "\n"))
  end
end)
