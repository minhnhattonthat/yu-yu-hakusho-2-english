-- Log unique ROM->VRAM DMAs made by $81:96B2 (A = source address, X = source bank, Y = VRAM word address,
-- $00 = byte count). Optional VRAM_LO/VRAM_HI filter on the destination.
local lo, hi = VRAM_LO or 0, VRAM_HI or 0xFFFF
local seen = {}
L.on_exec(0x8196B2, 0x8196B2, function()
  local s = emu.getState()
  local y = s["cpu.y"]
  if y < lo or y > hi then return end
  local key = string.format("%02X%04X>%04X", s["cpu.x"] & 0xFF, s["cpu.a"], y)
  if seen[key] then return end
  seen[key] = true
  local n = emu.read(0x7E0000, emu.memType.snesMemory) | emu.read(0x7E0001, emu.memType.snesMemory) << 8
  L.log(string.format("f%d dma src=%02X:%04X vram=%04X n=%04X", L.frame, s["cpu.x"] & 0xFF, s["cpu.a"], y, n))
end)
