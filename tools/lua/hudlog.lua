-- Every 300 frames log the HUD name tiles (BG3 tiles $240-$24F = VRAM words $7200-$727F) as hex.
L.on_frame(function(f)
  if f % 300 == 0 then
    local t = {}
    for a = 0x7200 * 2, 0x7280 * 2 - 1 do t[#t + 1] = string.format("%02X", emu.read(a, emu.memType.snesVideoRam)) end
    L.log("hud " .. f .. " " .. table.concat(t))
  end
end)
