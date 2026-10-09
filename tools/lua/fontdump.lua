-- Log the code that writes the WRAM font ($7F0000+) and dump it, to find the font source in ROM.
local seen, n = {}, 0
emu.addMemoryCallback(L.safe(function(addr, value)
  local s = emu.getState()
  local pc = (s["cpu.k"] << 16) | s["cpu.pc"]
  if not seen[pc] and n < 40 then
    seen[pc] = true; n = n + 1
    L.log(string.format("f%d pc=%06X write %06X = %02X X=%04X Y=%04X DB=%02X", L.frame, pc, addr, value,
      s["cpu.x"], s["cpu.y"], s["cpu.dbr"]))
  end
end), emu.callbackType.write, 0x7F0000, 0x7F0100, emu.cpuType.snes, emu.memType.snesMemory)
L.on_frame(function(f)
  if f == (DUMP_AT or 2600) then
    local t = {}
    for a = 0x7F0000, 0x7FFFFF do t[#t + 1] = string.char(emu.read(a, emu.memType.snesMemory)) end
    L.write_file(OUT .. "wram7f.bin", table.concat(t))
  end
end)
