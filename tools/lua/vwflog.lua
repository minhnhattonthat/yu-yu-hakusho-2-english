-- Log every vwf_glyph call (code, $0B00/$0B01, pen px) and the upload state at queue_dma entry.
-- VWF_GLYPH / QUEUE_DMA = label addresses from asar --symbols.
local mem = emu.memType.snesMemory
local function w(a) return emu.read(a, mem) | emu.read(a + 1, mem) << 8 end
L.on_exec(VWF_GLYPH or 0xA0E151, VWF_GLYPH or 0xA0E151, function()
  local s = emu.getState()
  L.log(string.format("f%d code=%04X col=%d row=%d px=%d", L.frame, s["cpu.a"], emu.read(0x7E0B00, mem),
    emu.read(0x7E0B01, mem), emu.read(0x7E0AF0, mem)))
end)
L.on_exec(QUEUE_DMA or 0xA0E382, QUEUE_DMA or 0xA0E382, function()
  L.log(string.format("   queue lo=%04X hi=%04X B3=%02X B5=%04X B7=%04X B9=%04X base=%04X", w(0x7E09B4), w(0x7E09B6),
    emu.read(0x7E00B3, mem), w(0x7E00B5), w(0x7E00B7), w(0x7E00B9), w(0x7E0AF4)))
end)
