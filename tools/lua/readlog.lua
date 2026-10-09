-- Log unique PCs that read the story text bank (bank $08/$88, $A92B-$F5FF): finds the script reader.
local seen = {}
local function hook(addr, value)
  local s = emu.getState()
  local pc = (s["cpu.k"] << 16) | s["cpu.pc"]
  local key = pc
  if not seen[key] then
    seen[key] = true
    L.log(string.format("f%d pc=%06X read %06X = %02X  A=%04X X=%04X Y=%04X DB=%02X", L.frame, pc, addr, value,
      s["cpu.a"], s["cpu.x"], s["cpu.y"], s["cpu.dbr"]))
  end
end
for _, bank in ipairs({ 0x08, 0x88 }) do
  emu.addMemoryCallback(L.safe(hook), emu.callbackType.read, (bank << 16) | 0xA92B, (bank << 16) | 0xF5FF,
    emu.cpuType.snes, emu.memType.snesMemory)
end
