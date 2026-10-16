"""Actual adapter save/readback with simulated swallowed native I/O failures."""
from pathlib import Path
import sys
root=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(root/'tools/dependencies/python'))
from lupa import LuaRuntime
lua=LuaRuntime(unpack_returned_tuples=True)
for name in ('CandidateCollector','Coverage','Perception','ObstructionNormalizer','SessionIdentity','DiagnosticSampler'):
    lua.globals()[name]=lua.execute((root/f'foundation/SarahFoundation/42/media/lua/client/Sarah/{name}.lua').read_text())
lua.globals().Engine=lua.execute((root/'foundation/SarahFoundation/42/media/lua/client/Sarah/Engine.lua').read_text())
lua.execute(r'''
Core={getMyDocumentFolder=function() return 'G:/Codex/Project Sarah/runtime/isolated' end}
ModData={getOrCreate=function() return {} end}
getWorld=function() return {getGameMode=function() return 'Rising' end,getWorld=function() return 'Test' end} end
SurvivorFactory={SurvivorType={Neutral=0},CreateSurvivor=function() return {} end}
local count=0
local function fixture()
    local f={files={},created=0,removed=0,writes=0,sequence=0,player={}}
    f.instance=f.player
    local n={data={SarahFoundationId='Sarah',SarahCheckpointWriteToken='old-memory'},square=true}
    n.getModData=function() return n.data end
    n.getX=function() return 10 end; n.getY=function() return 20 end; n.getZ=function() return 0 end
    n.isDead=function() return false end
    n.getCurrentSquare=function() return n.square end
    n.getForwardDirectionX=function() return 1.0 end
    n.getForwardDirectionY=function() return 0.0 end
    n.removeFromWorld=function() f.npcRemovedWorld=(f.npcRemovedWorld or 0)+1 end
    n.removeFromSquare=function() n.square=nil; f.npcRemovedSquare=(f.npcRemovedSquare or 0)+1 end
    n.save=function(_,path)
        f.writes=f.writes+1
        if f.writeThrow then error('write error') end
        if f.silent then return end
        f.files[path]={SarahFoundationId=n.data.SarahFoundationId,SarahCheckpointWriteToken=n.data.SarahCheckpointWriteToken}
    end
    local zombieList={}
    for i=1,10 do
        zombieList[i]={
            isZombie=function() return true end,
            isDead=function() return false end,
            isAlive=function() return true end,
            getX=function() return 12.0 end,
            getY=function() return 20.0 end,
            getZ=function() return 0.0 end,
            getOnlineID=function() return 100+i end,
        }
    end
    local targetSq={
        getX=function() return 12 end,
        getY=function() return 20 end,
        getZ=function() return 0 end,
        getMovingObjects=function()
            return {
                size=function() return #zombieList end,
                get=function(_,idx) return zombieList[idx+1] end,
            }
        end,
    }
    local cellObj={
        getObjectList=function() return {contains=function(_,who)
            if who==n then return true end
            return f.registered
        end} end,
        getAddList=function() return {contains=function() return false end} end,
        getRemoveList=function() return {contains=function() return false end} end,
        getGridSquare=function(_,x,y,z)
            if x==12 and y==20 and z==0 then return targetSq end
            return nil
        end,
    }
    f.cellObj=cellObj
    getCell=function() return cellObj end
    getRandomUUID=function() f.sequence=f.sequence+1; return 'unique-attempt-'..f.sequence end
    IsoPlayer={getInstance=function() return f.instance end,setInstance=function(p) f.instance=p end}
    IsoPlayer.new=function(cell,desc,x,y,z)
        assert(x==10 and y==20 and z==0)
        f.created=f.created+1
        local v={data={},square=true}; f.registered=true
        v.getCurrentSquare=function() return v.square end
        f.instance=v
        v.setNpc=function() end; v.isDead=function() return false end
        v.getModData=function() return v.data end
        v.load=function(_,path)
            if f.loadThrow then error('read error') end
            if f.files[path] then
                v.data={}; for k,value in pairs(f.files[path]) do v.data[k]=value end
            end
        end
        v.removeFromWorld=function()
            if f.cleanupThrow then error('cleanup error') end
            if not f.silentCleanup then f.registered=false end
        end
        v.removeFromSquare=function()
            if not f.silentCleanup then v.square=nil; f.removed=f.removed+1 end
        end
        return v
    end
    f.npc=n; f.adapter=Engine.new()
    Engine.setOwnership(f.npc,{adapter=f.adapter})
    return f
end
local function sampleNextTargetPass(adapter,npc)
    for step=1,30 do
        local res=adapter.samplePerception(npc)
        if res and res.results and #res.results>0 then return res,step end
    end
    error('timed out waiting for target square to be sampled')
end
local function seedLivePerception(f)
    assert(f.adapter.ensurePerceptionModules())
    f.adapter.sampleGeneration=7
    local sample,steps=sampleNextTargetPass(f.adapter,f.npc)
    assert(#sample.results==10,'expected 10 candidates in first target pass')
    assert(steps==5,'expected target square (12,20,0) on sweep pass 5 from initial cursor')
    local firstPassFirstId=sample.results[1].id
    local snapToken=f.adapter.snapshots['12,20,0'] and f.adapter.snapshots['12,20,0'].token
    assert(type(snapToken)=='string' and #snapToken>0,'expected square snapshot token before save')
    local idSnapBefore=f.adapter.sessionIdentity:snapshot()
    local dsSnapBefore=f.adapter.diagnosticSampler:snapshot()
    assert(idSnapBefore.epoch==1 and idSnapBefore.issued==10 and idSnapBefore.retained==10)
    assert(dsSnapBefore.collector_cursors>0,'expected active collector cursor before save')
    assert(#f.adapter.snapshotFIFO>0 and next(f.adapter.snapshots)~=nil,'expected square snapshots before save')
    assert(#f.adapter.entityFIFO==10 and next(f.adapter.entityTracker)~=nil,'expected entity tracker entries before save')
    return {
        generation=f.adapter.sampleGeneration,
        firstPassFirstId=firstPassFirstId,
        snapToken=snapToken,
        epoch=idSnapBefore.epoch,
        issued=idSnapBefore.issued,
        retained=idSnapBefore.retained,
        cursors=dsSnapBefore.collector_cursors,
        snapCount=#f.adapter.snapshotFIFO,
        entityCount=#f.adapter.entityFIFO,
    }
end
local function assertPerceptionPreserved(f,before)
    assert(f.adapter.sampleGeneration==before.generation,'sampleGeneration must be preserved across verifier cleanup')
    local idSnap=f.adapter.sessionIdentity:snapshot()
    local dsSnap=f.adapter.diagnosticSampler:snapshot()
    assert(idSnap.epoch==before.epoch and idSnap.issued==before.issued and idSnap.retained==before.retained,
        'sessionIdentity epoch/identities must be preserved across verifier cleanup')
    assert(dsSnap.collector_cursors==before.cursors,'collector cursors must be preserved across verifier cleanup')
    assert(#f.adapter.snapshotFIFO==before.snapCount and f.adapter.snapshots['12,20,0'] and f.adapter.snapshots['12,20,0'].token==before.snapToken,
        'square snapshots and tokens must be preserved across verifier cleanup')
    assert(#f.adapter.entityFIFO==before.entityCount and next(f.adapter.entityTracker)~=nil,
        'entity tracker must be preserved across verifier cleanup')
    local nextSample,steps=sampleNextTargetPass(f.adapter,f.npc)
    assert(steps==10,'preserved sweep offset must reach target square in 10 passes (wrapping 625 offsets), not 5 as after reset')
    assert(#nextSample.results==10,'second pass must read 10 candidates')
    assert(nextSample.results[1].id==before.firstPassFirstId,'same entity must retain session identity after verifier cleanup')
    assert(f.adapter.snapshots['12,20,0'].token==before.snapToken,'unchanged square must retain its snapshot token')
end
local function test(name,run) run(); count=count+1; print('PASS '..name) end
test('new checkpoint requires readback token and cleans verifier',function()
    local f=fixture(); f.adapter.save(f.npc,'a')
    assert(f.created==1 and f.removed==1 and f.instance==f.player and not f.adapter.verificationNPC)
    assert(f.npc.data.SarahCheckpointWriteToken=='unique-attempt-1')
end)
test('overwrite must read the current unique attempt',function()
    local f=fixture(); f.adapter.save(f.npc,'a'); f.adapter.save(f.npc,'a')
    assert(f.npc.data.SarahCheckpointWriteToken=='unique-attempt-2' and f.removed==2)
end)
test('swallowed failed overwrite rejects stale file',function()
    local f=fixture(); f.adapter.save(f.npc,'a'); local old=f.npc.data.SarahCheckpointWriteToken
    f.silent=true; assert(not pcall(f.adapter.save,f.npc,'a'))
    assert(f.npc.data.SarahCheckpointWriteToken==old and f.removed==2 and f.instance==f.player)
end)
test('swallowed missing write rejects absent binary',function()
    local f=fixture(); f.silent=true; assert(not pcall(f.adapter.save,f.npc,'a'))
    assert(f.npc.data.SarahCheckpointWriteToken=='old-memory' and f.removed==1)
end)
test('explicit write exception preserves token and player',function()
    local f=fixture(); f.writeThrow=true; assert(not pcall(f.adapter.save,f.npc,'a'))
    assert(f.created==0 and f.instance==f.player and f.npc.data.SarahCheckpointWriteToken=='old-memory')
end)
test('read failure still cleans temporary NPC',function()
    local f=fixture(); f.loadThrow=true; assert(not pcall(f.adapter.save,f.npc,'a'))
    assert(f.removed==1 and f.instance==f.player and not f.adapter.verificationNPC)
end)
test('cleanup failure pins verifier and blocks further writes',function()
    local f=fixture(); f.cleanupThrow=true; assert(not pcall(f.adapter.save,f.npc,'a'))
    assert(f.adapter.verificationNPC and f.instance==f.player and f.npc.data.SarahCheckpointWriteToken=='old-memory')
    assert(not pcall(f.adapter.save,f.npc,'b')); assert(f.writes==1)
end)
test('silent cleanup failure also pins reference and blocks writes',function()
    local f=fixture(); f.silentCleanup=true; assert(not pcall(f.adapter.save,f.npc,'a'))
    assert(f.adapter.verificationNPC and f.instance==f.player)
    assert(not pcall(f.adapter.save,f.npc,'b')); assert(f.writes==1)
end)
test('successful checkpoint save preserves live perception session, snapshots, identities and cursors',function()
    local f=fixture()
    local before=seedLivePerception(f)
    f.adapter.save(f.npc,'a')
    assert(f.created==1 and f.removed==1 and f.instance==f.player and not f.adapter.verificationNPC)
    assert(f.npc.data.SarahCheckpointWriteToken=='unique-attempt-1')
    assertPerceptionPreserved(f,before)
end)
test('failed checkpoint saves preserve live perception state across verifier cleanup and pin failures',function()
    -- Case 1: Swallowed write failure (verifier created and cleaned up)
    local f1=fixture()
    local b1=seedLivePerception(f1)
    f1.silent=true
    assert(not pcall(f1.adapter.save,f1.npc,'a'))
    assert(f1.removed==1 and not f1.adapter.verificationNPC and f1.instance==f1.player)
    assertPerceptionPreserved(f1,b1)

    -- Case 2: Verifier load exception (verifier created and cleaned up)
    local f2=fixture()
    local b2=seedLivePerception(f2)
    f2.loadThrow=true
    assert(not pcall(f2.adapter.save,f2.npc,'a'))
    assert(f2.removed==1 and not f2.adapter.verificationNPC and f2.instance==f2.player)
    assertPerceptionPreserved(f2,b2)

    -- Case 3: Verifier cleanup failure (verifier pinned, perception still preserved)
    local f3=fixture()
    local b3=seedLivePerception(f3)
    f3.cleanupThrow=true
    assert(not pcall(f3.adapter.save,f3.npc,'a'))
    assert(f3.adapter.verificationNPC and f3.instance==f3.player)
    assertPerceptionPreserved(f3,b3)
end)
test('actual Sarah adapter.remove resets live perception session, snapshots, identities and cursors',function()
    local f=fixture()
    local before=seedLivePerception(f)
    f.adapter.remove(f.npc)
    assert(f.npcRemovedWorld==1 and f.npcRemovedSquare==1)
    assert(f.adapter.sampleGeneration==before.generation+1,'adapter.remove(npc) must increment sampleGeneration')
    assert(next(f.adapter.snapshots)==nil and #f.adapter.snapshotFIFO==0,'adapter.remove(npc) must clear snapshots')
    assert(next(f.adapter.entityTracker)==nil and #f.adapter.entityFIFO==0,'adapter.remove(npc) must clear entityTracker')
    local idSnap=f.adapter.sessionIdentity:snapshot()
    local dsSnap=f.adapter.diagnosticSampler:snapshot()
    assert(idSnap.epoch==before.epoch+1 and idSnap.issued==0 and idSnap.retained==0,
        'adapter.remove(npc) must reset sessionIdentity and rotate epoch')
    assert(dsSnap.collector_cursors==0,'adapter.remove(npc) must reset collector cursors')
end)
print('RESULT '..count..' checkpoint readback checks passed')
''')
