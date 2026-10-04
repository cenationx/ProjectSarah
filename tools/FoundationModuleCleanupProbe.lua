-- Disposable real-object reload test; the removal interruption is injected Lua.
local ticks,failed,controller,npc,partial=0,false,nil,nil,false
local function log(s) print('[SarahModuleCleanupProbe] '..s) end
local function reloadAll()
    local engine=reloadLuaFile('media/lua/client/Sarah/Engine.lua')
    local lifecycle=reloadLuaFile('media/lua/client/Sarah/Lifecycle.lua')
    assert(engine and type(engine.new)=='function' and lifecycle and type(lifecycle.new)=='function','module reload did not return constructors')
    reloadLuaFile('media/lua/client/SarahFoundation.lua')
end
Events.OnGameStart.Add(function() ticks=0; failed=false; controller=nil; npc=nil; partial=false end)
Events.OnTick.Add(function()
    if failed or not getSpecificPlayer(0) then return end
    ticks=ticks+1
    if ticks~=240 and ticks~=600 and ticks~=960 then return end
    local ok,err=pcall(function()
        assert(getWorld():getWorld()=='SarahModuleCleanupCase','wrong disposable world')
        local c=SarahFoundation.controller
        assert(c and IsoPlayer.getInstance()==getSpecificPlayer(0),'controller/player invalid')
        if ticks==240 then
            if c.adapter.meta.ModuleCleanupDone then
                assert(c.npc and #c.adapter.listNPCs()==1,'restart absent/duplicate')
                assert(c.npc:getModData().SarahModuleToken=='ModuleCleanup-20261004','restart stale checkpoint')
                assert(c.npc:getWornItems():size()==3,'restart clothes lost')
                log('PASS FULL_RESTART tagged=1 contentsPreserved=true clothes=3 playerPreserved=true')
                failed=true; return
            end
            controller=c; npc=c.npc
            assert(npc and #c.adapter.listNPCs()==1,'Sarah absent/duplicate')
            npc:getModData().SarahModuleToken='ModuleCleanup-20261004'
            reloadAll(); reloadAll()
            assert(SarahFoundation.controller==c and c.npc==npc,'healthy reload lost reference')
            log('RELOADED Engine+Lifecycle+main twice sameController=true sameNPC=true')
        elseif ticks==600 then
            assert(c==controller and c.npc==npc and #c.adapter.listNPCs()==1,'healthy reload duplicate/reference loss')
            assert(SarahFoundation.ticks==360,'healthy reload tick rate incorrect')
            local writes=0
            local save=c.adapter.save
            c.adapter.save=function(...) writes=writes+1; return save(...) end
            local eventOK,eventError=pcall(function() triggerEvent('OnSave') end)
            c.adapter.save=save
            assert(eventOK,tostring(eventError)); assert(writes==1,'healthy save callback absent/duplicated')
            assert(not c.adapter.verificationNPC and not c.busy,'healthy verifier/transaction retained')
            log('PASS HEALTHY_RELOAD tickRate=1 saveCallbacks=1 tagged=1 playerPreserved=true')
            local remove=c.adapter.remove
            c.adapter.remove=function(target)
                if target==npc then
                    target:removeFromWorld()
                    error('controlled interruption after native removeFromWorld')
                end
                return remove(target)
            end
            local ran,unloaded,reason=pcall(function() return c:unload() end)
            c.adapter.remove=remove -- restore the adapter even if the assertions fail
            assert(ran and not unloaded,'interrupted removal falsely succeeded: '..tostring(reason))
            assert(c.npc==npc and not c.busy,'failed cleanup lost reference/transaction')
            assert(not c.adapter.isResident(npc) and #c.adapter.listNPCs()==0,'interruption did not leave a nonresident object')
            local ensured=c:ensure()
            assert(not ensured and c.npc==npc,'replacement allowed before cleanup completed')
            reloadAll()
            assert(SarahFoundation.controller==c and c.npc==npc,'partial cleanup reference lost during module reload')
            partial=true
            log('PASS PARTIAL_CLEANUP injected=true nativeRemovalStarted=true referenceRetained=true replacementRefused=true reloaded=true')
        elseif ticks==960 then
            assert(partial and c==controller and c.npc==npc,'partial reference no longer retained')
            assert(SarahFoundation.ticks==360,'partial reload tick rate incorrect')
            assert(#c.adapter.listNPCs()==0,'replacement created after partial cleanup')
            local ensured=c:ensure(); assert(not ensured and c.npc==npc,'replacement allowed after later ticks')
            local prior=c.adapter.meta.checkpoints
            local writes=0; local save=c.adapter.save
            c.adapter.save=function(...) writes=writes+1; return save(...) end
            local eventOK,eventError=pcall(function() triggerEvent('OnSave') end)
            c.adapter.save=save
            assert(eventOK,tostring(eventError))
            assert(writes==0 and c.adapter.meta.checkpoints==prior,'nonresident NPC overwrote good checkpoint')
            c.adapter.meta.ModuleCleanupDone=true
            log('PASS RETAINED_AFTER_TICKS tickRate=1 replacementRefused=true checkpointRetained=true writes=0 playerPreserved=true restartRequired=true')
            failed=true
        end
    end)
    if not ok then failed=true; log('FAIL '..tostring(err)) end
end)
