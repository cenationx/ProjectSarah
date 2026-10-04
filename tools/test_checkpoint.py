"""Actual adapter save/readback with simulated swallowed native I/O failures."""
from pathlib import Path
import sys
root=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(root/'tools/dependencies/python'))
from lupa import LuaRuntime
lua=LuaRuntime(unpack_returned_tuples=True)
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
    local n={data={SarahFoundationId='Sarah',SarahCheckpointWriteToken='old-memory'}}
    n.getModData=function() return n.data end
    n.getX=function() return 10 end; n.getY=function() return 20 end; n.getZ=function() return 0 end
    n.save=function(_,path)
        f.writes=f.writes+1
        if f.writeThrow then error('write error') end
        if f.silent then return end
        f.files[path]={SarahFoundationId=n.data.SarahFoundationId,SarahCheckpointWriteToken=n.data.SarahCheckpointWriteToken}
    end
    getCell=function() return {
        getObjectList=function() return {contains=function() return f.registered end} end,
        getAddList=function() return {contains=function() return false end} end,
        getRemoveList=function() return {contains=function() return false end} end
    } end
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
    return f
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
print('RESULT '..count..' checkpoint readback checks passed')
''')
