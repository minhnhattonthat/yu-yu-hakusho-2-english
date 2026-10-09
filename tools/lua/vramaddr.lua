-- Log code that points the VRAM port ($2116/7) at LO..HI (word addresses), with DMA source registers: finds who
-- uploads a tilemap. Set LO/HI before use (defaults: BG3 map $7800-$7BFF). Watches the $00 and $80 bank mirrors.
local lo, hi = LO or 0x7800, HI or 0x7BFF
local mem = emu.memType.snesMemory
local reg = { [0] = 0, [1] = 0 }
local seen = {}
local function check()
  local a = (reg[1] << 8) | reg[0]
  if a < lo or a > hi then return end
  local s = emu.getState()
  local pc = (s["cpu.k"] << 16) | s["cpu.pc"]
  local key = pc .. ":" .. a
  if seen[key] then return end
  seen[key] = true
  local t = {}
  for ch = 0, 7 do
    local b = 0x4300 + ch * 16
    t[#t + 1] = string.format("ch%d %02X%02X%02X n=%02X%02X", ch, emu.read(b + 4, mem), emu.read(b + 3, mem),
      emu.read(b + 2, mem), emu.read(b + 6, mem), emu.read(b + 5, mem))
  end
  L.log(string.format("f%d pc=%06X vram=%04X %s", L.frame, pc, a, table.concat(t, " ")))
end
for _, bank in ipairs({ 0x000000, 0x800000 }) do
  emu.addMemoryCallback(L.safe(function(addr, value)
    reg[addr & 1] = value
    if addr & 1 == 1 then check() end
  end), emu.callbackType.write, bank + 0x2116, bank + 0x2117, emu.cpuType.snes, mem)
end
