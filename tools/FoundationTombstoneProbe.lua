-- Run instead of the live/death probes after saving Sarah's death.
local ticks=0
Events.OnTick.Add(function()
    if not getSpecificPlayer(0) then return end
    ticks=ticks+1
    if ticks~=240 then return end
    local ok,err=pcall(function()
        local c=SarahFoundation.controller
        assert(c and c.adapter.meta.dead,'death metadata missing after restart')
        assert(c.npc==nil,'NPC restored despite tombstone')
        local ensured,npc=c:ensure()
        assert(ensured and npc==nil,'spawn request resurrected Sarah')
        assert(#c.adapter.listNPCs()==0,'live tagged Sarah remains')
        print('[SarahTombstoneProbe] RESTART_NO_RESURRECTION PASS')
    end)
    if not ok then print('[SarahTombstoneProbe] FAIL '..tostring(err)) end
end)
