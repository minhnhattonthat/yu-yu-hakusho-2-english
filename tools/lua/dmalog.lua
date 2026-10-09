-- Log every general DMA (write to $420B): channel source, size, B-bus register, and caller PC.
-- SRC_LO/SRC_HI (24-bit) filter the source range (default: everything).
local mem = emu.memType.snesMemory
local lo, hi = SRC_LO or 0, SRC_HI or 0xFFFFFF
for _, bank in ipairs({ 0x000000, 0x800000 }) do
  emu.addMemoryCallback(L.safe(function(addr, value)
    local s = emu.getState()
    local pc = (s["cpu.k"] << 16) | s["cpu.pc"]
    for ch = 0, 7 do
      if value & (1 << ch) ~= 0 then
        local b = 0x4300 + ch * 16
        local src = emu.read(b + 4, mem) << 16 | emu.read(b + 3, mem) << 8 | emu.read(b + 2, mem)
        if src >= lo and src <= hi then
          L.log(string.format("f%d pc=%06X ch%d src=%06X n=%04X bbus=21%02X ctl=%02X", L.frame, pc, ch, src,
            emu.read(b + 6, mem) << 8 | emu.read(b + 5, mem), emu.read(b + 1, mem), emu.read(b, mem)))
        end
      end
    end
  end), emu.callbackType.write, bank + 0x420B, bank + 0x420B, emu.cpuType.snes, mem)
end
