-- Snapshot low WRAM ($7E0000-$7E1FFF) every SNAP_EVERY frames to OUT/snap_<frame>.bin (for finding HP etc.).
local every = SNAP_EVERY or 60
L.on_frame(function(f)
  if f % every == 0 then
    local t = {}
    for a = 0x7E0000, 0x7E1FFF do t[#t + 1] = string.char(emu.read(a, emu.memType.snesMemory)) end
    L.write_file(string.format("%ssnap_%06d.bin", OUT, f), table.concat(t))
  end
end)
