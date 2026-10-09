-- Log calls to the two graphics decompressors ($81:8CF3, $81:8C35): source = X:A, plus the caller (return address).
local mem = emu.memType.snesMemory
for _, entry in ipairs({ 0x818CF3, 0x818C35 }) do
  L.on_exec(entry, entry, function()
    local s = emu.getState()
    local sp = s["cpu.sp"]
    local ret = emu.read(0x000000 + sp + 3, mem) << 16 | emu.read(sp + 2, mem) << 8 | emu.read(sp + 1, mem)
    L.log(string.format("f%d decomp %06X src=%02X:%04X caller=%06X", L.frame, entry, s["cpu.x"] & 0xFF, s["cpu.a"],
      ret - 3))
  end)
end
