local ticks=0
Events.OnTick.Add(function()
    if not getSpecificPlayer(0) then return end
    ticks=ticks+1
    if ticks~=240 then return end
    local ok,err=pcall(function()
        local c=SarahFoundation.controller
        assert(c and c.npc,'NPC absent')
        local npc=c.npc
        print('[SarahFoundationProbe] START worn='..npc:getWornItems():size()..' npc='..tostring(npc:isNpc())..' name='..npc:getDescriptor():getForename())
        assert(c:ensure()); assert(c.npc==npc); assert(#c.adapter.listNPCs()==1)
        print('[SarahFoundationProbe] DUPLICATE PASS')
        assert(c:save()); assert(c:save()); assert(#c.adapter.meta.checkpoints==2)
        assert(c:unload()); assert(c.npc==nil)
        -- Engine removal is queued; restore on a later tick, not in this callback.
        print('[SarahFoundationProbe] SAVE_UNLOAD PASS')
    end)
    if not ok then print('[SarahFoundationProbe] FAIL '..tostring(err)) end
end)
local restoreTicks=0
Events.OnTick.Add(function()
    if not getSpecificPlayer(0) then return end
    restoreTicks=restoreTicks+1
    if restoreTicks~=360 then return end
    local ok,err=pcall(function()
        local c=SarahFoundation.controller
        assert(c:ensure()); assert(c.npc,'restore absent'); assert(#c.adapter.listNPCs()==1)
        assert(c.npc:getWornItems():size()>=3,'clothing missing')
        assert(c:save())
        print('[SarahFoundationProbe] RESTORE PASS worn='..c.npc:getWornItems():size())
    end)
    if not ok then print('[SarahFoundationProbe] FAIL '..tostring(err)) end
end)
