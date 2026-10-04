-- Only disposable SarahWriteFailureRetest; pair with hold-checkpoint-lock.ps1 once.
local ticks,failed,phase=0,false,nil
local oldNPC,oldRecords
local function log(message) print('[SarahWriteFailureProbe] '..message) end
Events.OnGameStart.Add(function() ticks=0; failed=false; phase=nil end)
Events.OnTick.Add(function()
    if not getSpecificPlayer(0) or failed then return end
    ticks=ticks+1
    if ticks~=240 and ticks~=600 and ticks~=840 then return end
    local ok,err=pcall(function()
        assert(getWorld():getWorld()=='SarahWriteFailureRetest','wrong disposable world')
        local c=SarahFoundation.controller
        assert(c and c.npc and #c.adapter.listNPCs()==1,'NPC absent or duplicated')
        assert(IsoPlayer.getInstance()==getSpecificPlayer(0),'player changed')
        if ticks==240 then
            if c.adapter.meta.WriteFailureProbeDone then
                assert(c.npc:getModData().SarahWriteToken=='WriteFailure-20261004','restart loaded stale contents')
                phase='verified'
                log('PASS FULL_RESTART tagged=1 newContentsPreserved=true playerPreserved=true')
                return
            end
            assert(c.adapter.meta.checkpoints[1].slot=='b','expected b to restore; lock must target next slot a')
            assert(c.adapter.exists('a'),'stale destination absent')
            oldNPC=c.npc; oldRecords=c.adapter.meta.checkpoints
            oldNPC:getModData().SarahWriteToken='WriteFailure-20261004'
            local unloaded,reason=c:unload()
            assert(not unloaded,'locked existing-file write falsely succeeded')
            assert(c.npc==oldNPC and c.adapter.meta.checkpoints==oldRecords,'failed save changed NPC or metadata')
            assert(c.adapter.exists('a'),'old destination no longer exists')
            assert(#c.adapter.listNPCs()==1 and not c.busy,'failure left duplicates or transaction lock')
            log('PASS FAILED_UNLOAD npcRetained=true metadataRetained=true oldTargetExists=true tagged=1 transactionReleased=true reason='..tostring(reason))
            local writer=getFileWriter('SarahWriteLock-retest-20261004.txt',true,false)
            assert(writer,'release writer absent'); writer:write('release'); writer:close()
            phase='retry'
        elseif ticks==600 and phase=='retry' then
            assert(c:unload(),'retry unload failed after release')
            assert(c.npc==nil and #c.adapter.listNPCs()==0,'retry cleanup incomplete')
            assert(c.adapter.meta.checkpoints[1].slot=='a','successful retry did not publish a')
            assert(c:ensure(),'restore of retry checkpoint failed')
            phase='restored'
        elseif ticks==840 and phase=='restored' then
            assert(c.npc:getModData().SarahWriteToken=='WriteFailure-20261004','retry loaded stale existing file')
            assert(c.npc:getWornItems():size()==3,'clothing lost')
            assert(c:save(),'post-recovery save failed')
            c.adapter.meta.WriteFailureProbeDone=true; phase='done'
            log('PASS RETRY_AND_RESTORE tagged=1 newContentsPreserved=true clothes=3 playerPreserved=true saved=true')
        end
    end)
    if not ok then failed=true; log('FAIL '..tostring(err)) end
end)
