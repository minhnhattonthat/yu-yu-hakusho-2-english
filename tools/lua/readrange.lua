-- Log unique PCs (with registers) that read CPU addresses LO..HI in banks $08/$88 (ROM data readers).
local lo, hi = LO or 0x9C00, HI or 0xA900
local seen = {}
local function hook(addr, value)
  local s = emu.getState()
  local pc = (s["cpu.k"] << 16) | s["cpu.pc"]
  if not seen[pc] then
    seen[pc] = true
    L.log(string.format("f%d pc=%06X read %06X A=%04X X=%04X Y=%04X DB=%02X", L.frame, pc, addr, s["cpu.a"],
      s["cpu.x"], s["cpu.y"], s["cpu.dbr"]))
  end
end
for _, bank in ipairs({ 0x08, 0x88 }) do
  emu.addMemoryCallback(L.safe(hook), emu.callbackType.read, (bank << 16) | lo, (bank << 16) | hi,
    emu.cpuType.snes, emu.memType.snesMemory)
end
