-- Temporary live test. Deploy only to the isolated disposable alive world.
local ticks=0
local before, middle, controller, npc, beforeTicks, middleTicks
local failed=false
Events.OnTick.Add(function()
    if failed or not getSpecificPlayer(0) then return end
    ticks=ticks+1
    local ok,err=pcall(function()
        if ticks==240 then
            assert(getWorld():getWorld()=='SarahSessionAlive','unexpected world')
            before=SarahFoundation; controller=before.controller
            assert(controller and controller.npc and not controller.npc:isDead())
            npc=controller.npc
            assert(#controller.adapter.listNPCs()==1)
            reloadLuaFile('media/lua/client/SarahFoundation.lua')
            middle=SarahFoundation
            assert(middle~=before and middle.controller==controller,'first reload lost controller')
            reloadLuaFile('media/lua/client/SarahFoundation.lua')
            assert(SarahFoundation~=middle and SarahFoundation.controller==controller,'second reload lost controller')
            beforeTicks=before.ticks; middleTicks=middle.ticks
            print('[SarahReloadProbe] RELOADED twice sameController=true sameNPC=true')
        elseif ticks==241 then
            -- B42 forwards old tables to replacement tables on reload. Values
            -- read through retired references cannot measure retired callbacks.
            print('[SarahReloadProbe] SETTLED oldDelta='..(before.ticks-beforeTicks)..' middleDelta='..(middle.ticks-middleTicks)..' newTicks='..SarahFoundation.ticks)
            beforeTicks=before.ticks; middleTicks=middle.ticks
        elseif ticks==600 then
            print('[SarahReloadProbe] COUNTS oldDelta='..(before.ticks-beforeTicks)..' middleDelta='..(middle.ticks-middleTicks)..' newTicks='..SarahFoundation.ticks..' oldIsCurrent='..tostring(before==SarahFoundation)..' middleIsCurrent='..tostring(middle==SarahFoundation)..' oldEqualsMiddle='..tostring(before==middle)..' hooks='..tostring(SarahFoundationHooks~=nil))
            assert(SarahFoundation.controller==controller and controller.npc==npc)
            assert(SarahFoundation.ticks==360,'current tick callback count incorrect')
            assert(#controller.adapter.listNPCs()==1,'duplicate NPC after reload')
            assert(IsoPlayer.getInstance()==getSpecificPlayer(0),'player instance changed')
            local writes=0
            local originalSave=controller.adapter.save
            controller.adapter.save=function(...)
                writes=writes+1
                return originalSave(...)
            end
            local saved,saveError=pcall(function() triggerEvent('OnSave') end)
            controller.adapter.save=originalSave
            print('[SarahReloadProbe] SAVES writes='..writes..' eventOK='..tostring(saved))
            assert(saved,tostring(saveError)); assert(writes==1,'save callback duplicated or absent')
            print('[SarahReloadProbe] PASS tickRate=1 saveCallbacks=1 tagged=1 sameController=true sameNPC=true playerPreserved=true')
        end
    end)
    if not ok then failed=true; print('[SarahReloadProbe] FAIL '..tostring(err)) end
end)
