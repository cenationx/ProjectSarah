-- Bounded six-minute idle-room test, only in the backed-up disposable case.
local ticks,failed,started,nextCycle,cycles,pending,wrapped,finalizing=0,false,nil,nil,0,{},false,false
local verifierCount=0
local function log(s) print('[SarahLongSessionProbe] '..s) end
local function checkRemoved()
    local cell=getCell()
    for _,npc in ipairs(pending) do
        assert(npc:getCurrentSquare()==nil,'removed object still has square')
        assert(not cell:getObjectList():contains(npc) and not cell:getAddList():contains(npc)
            and not cell:getRemoveList():contains(npc),'removed object remains in world lists after ticks')
    end
    pending={}
    for _,list in ipairs({cell:getObjectList(),cell:getAddList(),cell:getRemoveList()}) do
        local it=list:iterator()
        while it:hasNext() do
            local obj=it:next()
            if instanceof(obj,'IsoPlayer') then
                assert(obj:getModData().SarahFoundationId~='CheckpointVerifier','verifier remains registered')
            end
        end
    end
end
Events.OnGameStart.Add(function()
    ticks=0; failed=false; started=nil; nextCycle=nil; cycles=0; pending={}; wrapped=false; finalizing=false; verifierCount=0
end)
Events.OnTick.Add(function()
    if failed or not getSpecificPlayer(0) then return end
    ticks=ticks+1
    if ticks<240 or ticks%60~=0 then return end
    local ok,err=pcall(function()
        assert(getWorld():getWorld()=='SarahLongSessionCase','wrong disposable world')
        local c=SarahFoundation.controller
        assert(c and c.npc and #c.adapter.listNPCs()==1,'Sarah absent or duplicated')
        assert(IsoPlayer.getInstance()==getSpecificPlayer(0),'local player changed')
        assert(not c.busy and not c.travelBlocked and not c.adapter.verificationNPC,'transaction/verifier retained')
        assert(c.npc:getWornItems():size()==3,'clothing lost')
        checkRemoved()
        if c.adapter.meta.LongSessionDone then
            assert(c.npc:getModData().SarahLongCycle==12,'latest cycle did not persist')
            if finalizing then
                log('PASS COMPLETE cycles=12 verifiedSaves=25 verifiersRemoved='..verifierCount..' elapsedMs='..(getTimestampMs()-started)..' tagged=1 playerPreserved=true')
            else
                log('PASS FULL_RESTART cycle=12 tagged=1 clothes=3 playerPreserved=true')
            end
            failed=true -- finished; no more driver actions in this process
            return
        end
        if not wrapped then
            local remove=c.adapter.remove
            c.adapter.remove=function(npc)
                if npc:getModData().SarahFoundationId=='CheckpointVerifier' then verifierCount=verifierCount+1 end
                pending[#pending+1]=npc
                return remove(npc)
            end
            wrapped=true; started=getTimestampMs(); nextCycle=started+30000
            log('START durationMs=360000 cycles=12 intervalMs=30000')
        end
        local now=getTimestampMs()
        if now<nextCycle then return end
        cycles=cycles+1
        c.npc:getModData().SarahLongCycle=cycles
        local prior=c.npc:getModData().SarahCheckpointWriteToken
        local saved,result=c:save(); assert(saved and result,'cycle save failed')
        assert(c.npc:getModData().SarahCheckpointWriteToken~=prior,'save marker not fresh')
        local unloaded,removed=c:unload(); assert(unloaded and removed and not c.npc,'unload failed')
        assert(#c.adapter.listNPCs()==0,'unload retained registered Sarah')
        local restored,npc=c:ensure(); assert(restored and npc==c.npc and npc,'restore failed')
        assert(c.npc:getModData().SarahLongCycle==cycles,'restore used stale cycle')
        assert(#c.adapter.listNPCs()==1 and IsoPlayer.getInstance()==getSpecificPlayer(0),'duplicate/player changed after cycle')
        log('PASS CYCLE '..cycles..' elapsedMs='..(now-started)..' verifiersCreated='..verifierCount..' tagged=1 contentsPreserved=true')
        if cycles==12 then
            c.adapter.meta.LongSessionDone=true
            local done,result=c:save(); assert(done and result,'completion save failed')
            finalizing=true
        else nextCycle=now+30000 end
    end)
    if not ok then failed=true; log('FAIL '..tostring(err)) end
end)
