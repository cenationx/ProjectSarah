-- Read/mark disposable session metadata; does not kill or automatically unload.
local ticks=0
Events.OnGameStart.Add(function() ticks=0 end)
Events.OnTick.Add(function()
    if not getSpecificPlayer(0) then return end
    ticks=ticks+1
    if ticks~=240 then return end
    local ok,err=pcall(function()
        local c=SarahFoundation.controller
        assert(c,'controller absent')
        local world=getWorld():getWorld()
        local meta=c.adapter.meta
        assert(not meta.SarahSessionWorld or meta.SarahSessionWorld==world,'metadata crossed worlds')
        assert(IsoPlayer.getInstance()==getSpecificPlayer(0),'player instance changed')
        if world=='SarahSessionAlive' then
            assert(not meta.dead,'death flag crossed into alive world')
            assert(c.npc and not c.npc:isDead(),'alive Sarah missing')
            assert(c:ensure()); assert(#c.adapter.listNPCs()==1,'duplicate Sarah')
            assert(c:save())
        else
            assert(world=='2026-10-04_04-21-54','unexpected test world')
            assert(meta.dead and c.npc==nil,'death state lost')
            local ensured,npc=c:ensure(); assert(ensured and npc==nil,'dead Sarah resurrected')
            assert(#c.adapter.listNPCs()==0,'live Sarah crossed worlds')
        end
        meta.SarahSessionWorld=world
        print('[SarahSessionProbe] PASS world='..world..' dead='..tostring(meta.dead)..' tagged='..#c.adapter.listNPCs()..' playerPreserved=true')
    end)
    if not ok then print('[SarahSessionProbe] FAIL '..tostring(err)) end
end)
