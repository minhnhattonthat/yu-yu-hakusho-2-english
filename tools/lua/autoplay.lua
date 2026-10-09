-- Story autoplay for QA: during a fight (both HP bytes > 0) keep P1 HP ($7E0C0A) at 50 and the opponent
-- ($7E110A) at 1 so the next hit wins; never revive (0 stays 0, so the post-fight tally can drain P1's HP).
-- Input: cycles A (advance text) / Y (attack) while walking right. Use without --mash.
-- Logs each message index the printer starts ($0B07).
local mem = emu.memType.snesMemory
local last = -1
emu.addEventCallback(function()
  local f = L.frame
  if f > (AUTOPLAY_FROM or 1500) then
    local p1, p2 = emu.read(0x7E0C0A, mem), emu.read(0x7E110A, mem)
    if p1 > 0 and p2 > 0 then
      emu.write(0x7E0C0A, 50, mem)
      emu.write(0x7E110A, 1, mem)
    end
    local p = f % 24
    emu.setInput({ a = p < 4, y = p >= 12 and p < 16, right = p >= 4 }, 0)
  end
end, emu.eventType.inputPolled)
L.on_frame(function(f)
  local m = emu.read(0x7E0B07, mem) | emu.read(0x7E0B08, mem) << 8
  if m ~= last then
    last = m
    L.log(string.format("f%d msg %03X", f, m))
  end
end)
