-- Disposable isolated world only. Kills Sarah to verify death tombstones.
local ticks=0
Events.OnTick.Add(function()
    if not getSpecificPlayer(0) then return end
    ticks=ticks+1
    local c=SarahFoundation and SarahFoundation.controller
    if ticks==480 then
        local ok,err=pcall(function()
            assert(c and c.npc,'Sarah absent')
            c.npc:getBodyDamage():setOverallBodyHealth(0)
            c.npc:setHealth(0)
            print('[SarahDeathProbe] HEALTH_ZERO')
        end)
        if not ok then print('[SarahDeathProbe] FAIL '..tostring(err)) end
    elseif ticks==720 then
        local ok,err=pcall(function()
            assert(c and c.npc and c.npc:isDead(),'death not observed')
            c:observeDeath(); assert(c.adapter.meta.dead)
            assert(c:unload())
            local ensured,npc=c:ensure()
            assert(ensured and npc==nil and c.npc==nil,'resurrected')
            print('[SarahDeathProbe] TOMBSTONE_NO_RESPAWN PASS')
        end)
        if not ok then print('[SarahDeathProbe] FAIL '..tostring(err)) end
    end
end)
