"""Exercise the actual engine adapter's world-render boundaries with fake objects."""
from pathlib import Path
import sys
root = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(root / 'tools/dependencies/python'))
from lupa import LuaRuntime
lua = LuaRuntime(unpack_returned_tuples=True)
lua.globals().Engine = lua.execute((root / 'foundation/SarahFoundation/42/media/lua/client/Sarah/Engine.lua').read_text())
lua.execute(r'''
Core={getMyDocumentFolder=function() return 'G:/Codex/Project Sarah/runtime/isolated' end}
ModData={getOrCreate=function() return {} end}
local count=0
local function fixture()
    local f={draws=0,shadows=0,registered=true,removing=false,visible=true,light={},client=false,server=false}
    local player={x=10,y=20,z=0}
    player.getZ=function() return player.z end; player.getX=function() return player.x end; player.getY=function() return player.y end
    local npc={data={SarahFoundationId='Sarah'},z=0,dead=false,onScreen=true,npc=true}
    local square={isCanSee=function() return f.visible end,getLightInfo=function() return f.light end}
    square.isFree=function() return f.free~=false end
    npc.square=square
    npc.isDead=function() return npc.dead end
    npc.isNpc=function() return npc.npc end
    npc.getModData=function() return npc.data end
    npc.isOnScreen=function() return npc.onScreen end
    npc.getCurrentSquare=function() return npc.square end
    npc.getX=function() return 10 end; npc.getY=function() return 20 end; npc.getZ=function() return npc.z end
    npc.renderShadow=function(self,x,y,z) assert(self==npc and x==10 and y==20 and z==npc.z); f.shadows=f.shadows+1 end
    npc.render=function(self,x,y,z,light,opaque,translucent,shader)
        assert(self==npc and x==10 and y==20 and z==npc.z and light==f.light)
        assert(opaque==true and translucent==false and shader==nil)
        f.draws=f.draws+1
    end
    PerformanceSettings={fboRenderChunk=true}
    isClient=function() return f.client end; isServer=function() return f.server end
    getSpecificPlayer=function(index) assert(index==0); return f.player end
    getCell=function() return {
        getGridSquare=function() if f.loaded==false then return nil else return square end end,
        getObjectList=function() return {contains=function(_,object) assert(object==npc); return f.registered end} end,
        getAddList=function() return {contains=function() return f.pending end} end,
        getRemoveList=function() return {contains=function(_,object) assert(object==npc); return f.removing end} end
    } end
    f.player=player; f.npc=npc; f.adapter=Engine.new()
    return f
end
local function test(name,run) run(); count=count+1; print('PASS '..name) end
local function skipped(change,index)
    local f=fixture(); change(f)
    assert(f.adapter.render(f.npc,index or 0)==false)
    assert(f.draws==0 and f.shadows==0)
end
test('visible actual NPC drawn with its square lighting',function()
    local f=fixture(); local player=f.player
    assert(f.adapter.render(f.npc,0)); assert(f.draws==1 and f.shadows==1 and f.player==player)
end)
test('no player or NPC produces no drawing',function()
    skipped(function(f) f.player=nil end); skipped(function(f) f.npc=nil end)
end)
test('local player never drawn through NPC path',function() skipped(function(f) f.player=f.npc end) end)
test('legacy renderer and other player views skipped',function()
    skipped(function() PerformanceSettings.fboRenderChunk=false end); skipped(function() end,1)
end)
test('network modes skipped',function()
    skipped(function(f) f.client=true end); skipped(function(f) f.server=true end)
end)
test('dead partial and unrelated characters skipped',function()
    skipped(function(f) f.npc.dead=true end); skipped(function(f) f.npc.data.SarahFoundationPartial=true end)
    skipped(function(f) f.npc.data.SarahFoundationId='Other' end); skipped(function(f) f.npc.npc=false end)
end)
test('unregistered or removal-pending NPC skipped',function()
    skipped(function(f) f.registered=false end); skipped(function(f) f.removing=true end)
end)
test('offscreen hidden or other-floor NPC skipped',function()
    skipped(function(f) f.npc.onScreen=false end); skipped(function(f) f.visible=false end)
    skipped(function(f) f.npc.z=1 end)
end)
test('missing square or lighting skipped',function()
    skipped(function(f) f.npc.square=nil end); skipped(function(f) f.light=nil end)
end)
print('RESULT '..count..' rendering checks passed')
test('travel hysteresis uses 32-tile suspension and 16-tile return',function()
    local f=fixture(); local p=f.player; local r={x=10,y=20,z=0}
    p.x=42; assert(not f.adapter.shouldUnload(f.npc)); assert(not f.adapter.nearCheckpoint(r))
    p.x=43; assert(f.adapter.shouldUnload(f.npc))
    p.x=26; assert(f.adapter.nearCheckpoint(r)); p.x=27; assert(not f.adapter.nearCheckpoint(r))
end)
test('different floors never restore and suspend active NPC',function()
    local f=fixture(); f.player.z=1
    assert(f.adapter.shouldUnload(f.npc)); assert(not f.adapter.nearCheckpoint({x=10,y=20,z=0}))
end)
test('residency includes pending add but excludes pending removal or missing square',function()
    local f=fixture(); assert(f.adapter.isResident(f.npc))
    f.registered=false; f.pending=true; assert(f.adapter.isResident(f.npc))
    f.removing=true; assert(not f.adapter.isResident(f.npc))
    f.removing=false; f.npc.square=nil; assert(not f.adapter.isResident(f.npc))
end)
test('restore requires a nearby loaded free saved square',function()
    local f=fixture(); local r={x=10,y=20,z=0}
    assert(f.adapter.canRestore(r)); f.loaded=false; assert(not f.adapter.canRestore(r))
    f.loaded=true; f.free=false; assert(not f.adapter.canRestore(r))
    f.free=true; f.player.x=50; assert(not f.adapter.canRestore(r))
end)
test('validateTarget checks coordinates, floor, distance, square status and target equality',function()
    local f=fixture()
    local ok,err=f.adapter.validateTarget(f.npc,nil)
    assert(not ok and err=='Invalid target coordinates.')
    ok,err=f.adapter.validateTarget(f.npc,{x='bad',y=20,z=0})
    assert(not ok and err=='Invalid target coordinates.')
    ok,err=f.adapter.validateTarget(f.npc,{x=0/0,y=20,z=0})
    assert(not ok and err=='Invalid target coordinates.')
    ok,err=f.adapter.validateTarget(f.npc,{x=math.huge,y=20,z=0})
    assert(not ok and err=='Invalid target coordinates.')
    ok,err=f.adapter.validateTarget(f.npc,{x=12,y=20,z=1})
    assert(not ok and err=='Target is on a different floor.')
    ok,err=f.adapter.validateTarget(f.npc,{x=25,y=20,z=0})
    assert(not ok and err=='Target is too far (maximum 8 tiles).')
    ok,err=f.adapter.validateTarget(f.npc,{x=10,y=20,z=0})
    assert(not ok and err:find('Already at target'))
    f.loaded=false
    ok,err=f.adapter.validateTarget(f.npc,{x=12,y=20,z=0})
    assert(not ok and err=='Target square is not loaded.')
    f.loaded=true
    f.free=false
    ok,err=f.adapter.validateTarget(f.npc,{x=12,y=20,z=0})
    assert(not ok and err=='Target square is occupied or blocked.')
    f.free=true
    local sq
    ok,sq=f.adapter.validateTarget(f.npc,{x=12,y=20,z=0})
    assert(ok and sq)
end)
test('adapter walk queues walk action with callbacks',function()
    local f=fixture()
    local queuedAction=nil
    ISTimedActionQueue={add=function(act) queuedAction=act end}
    ISWalkToTimedAction={
        new=function(self,char,sq)
            local o={character=char,location=sq}
            setmetatable(o,self)
            return o
        end,
        derive=function(self,name)
            local cls={}
            cls.__index=cls
            setmetatable(cls,{__index=self})
            return cls
        end,
        perform=function(self) end,
        stop=function(self) end
    }
    local successCalled,failCalled=false,false
    local ok,act=f.adapter.walk(f.npc,f.npc.square,function() successCalled=true end,function() failCalled=true end)
    assert(ok and act and queuedAction==act)
    act:perform()
    assert(successCalled and not failCalled)
    local ok2,act2=f.adapter.walk(f.npc,f.npc.square,function() end,function(_,reason) failCalled=reason end)
    assert(ok2 and act2)
    act2:stop()
    assert(failCalled=='stopped')
end)
print('RESULT '..count..' total engine adapter checks passed')
''')
