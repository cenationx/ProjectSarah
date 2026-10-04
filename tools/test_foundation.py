"""Fault-injection tests of the actual Lua lifecycle policy (no game launch)."""
from pathlib import Path
import sys
root = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(root / 'tools/dependencies/python'))
from lupa import LuaRuntime
lua = LuaRuntime(unpack_returned_tuples=True)
source = root / 'foundation/SarahFoundation/42/media/lua/client'
for path in source.rglob('*.lua'):
    lua.execute('assert(load(...))', path.read_text(encoding='utf-8'))
lua.globals().Lifecycle = lua.execute((source / 'Sarah/Lifecycle.lua').read_text())
lua.execute(r'''
local count=0
local function test(name,run)
    run(); count=count+1; print('PASS '..name)
end
local function fixture()
    local a={meta={},objects={},files={},created=0,restored=0,logs={}}
    a.log=function(m) a.logs[#a.logs+1]=m end
    a.listNPCs=function() return a.objects end
    a.isDead=function(n) return n.dead end
    a.exists=function(s) return a.files[s] end
    a.create=function() a.created=a.created+1; local n={}; a.objects={n}; return n end
    a.restore=function(r) a.restored=a.restored+1; if r.bad then error('corrupt') end; return a.create() end
    a.snapshot=function(n) return {x=10,y=20,z=0} end
    a.save=function(n,s) a.files[s]=true end
    a.stop=function() end
    a.remove=function() a.objects={} end
    return a,Lifecycle.new(a)
end
test('repeated ensure adopts exactly one NPC',function()
    local a,c=fixture(); assert(c:ensure()); assert(c:ensure()); assert(a.created==1)
end)
test('duplicate objects block creation',function()
    local a,c=fixture(); a.objects={{},{}}; assert(not c:ensure()); assert(a.created==0)
end)
test('failed operation releases lock',function()
    local a,c=fixture(); a.create=function() error('injected') end
    assert(not c:ensure()); assert(not c.busy)
end)
test('nested operations are rejected',function()
    local a,c=fixture(); assert(c:transaction(function() assert(not c:ensure()) end)); assert(a.created==0)
end)
test('alternating slots retain previous checkpoint',function()
    local a,c=fixture(); c:ensure(); assert(c:save()); assert(a.meta.checkpoints[1].slot=='a')
    assert(c:save()); assert(a.meta.checkpoints[1].slot=='b'); assert(a.meta.checkpoints[2].slot=='a')
end)
test('failed save retains metadata and active NPC',function()
    local a,c=fixture(); c:ensure(); c:save(); local old=a.meta.checkpoints
    a.save=function() error('disk failure') end; assert(not c:unload()); assert(c.npc); assert(a.meta.checkpoints==old)
end)
test('missing write is not published',function()
    local a,c=fixture(); c:ensure(); a.save=function() end
    assert(not c:save()); assert(a.meta.checkpoints==nil)
end)
test('cleanup failure retains reference and blocks replacement',function()
    local a,c=fixture(); c:ensure(); a.remove=function() a.objects={}; error('cleanup') end
    assert(not c:unload()); assert(c.npc); assert(not c:ensure()); assert(a.created==1)
end)
test('corrupt current checkpoint falls back after clean removal',function()
    local a,c=fixture(); a.files={a=true,b=true}; a.meta.checkpoints={{slot='b',bad=true},{slot='a'}}
    assert(c:ensure()); assert(a.restored==2); assert(a.created==1)
    assert(a.meta.checkpoints[1].slot=='a'); assert(c:save())
    assert(a.meta.checkpoints[1].slot=='b'); assert(a.meta.checkpoints[2].slot=='a')
end)
test('partially constructed NPC is never adopted',function()
    local a,c=fixture(); a.objects={{partial=true}}; a.isIncomplete=function(n) return n.partial end
    assert(not c:ensure()); assert(c.npc==nil); assert(a.created==0)
end)
test('corrupt checkpoints never create fresh replacement',function()
    local a,c=fixture(); a.files={a=true,b=true}; a.meta.checkpoints={{slot='b',bad=true},{slot='a',bad=true}}
    assert(not c:ensure()); assert(a.created==0)
end)
test('missing checkpoints preserve recovery metadata',function()
    local a,c=fixture(); local records={{slot='a'}}; a.meta.checkpoints=records
    assert(not c:ensure()); assert(a.meta.checkpoints==records); assert(a.created==0)
end)
test('unloaded saved square defers without older fallback',function()
    local a,c=fixture(); a.files={a=true,b=true}; a.meta.checkpoints={{slot='b'},{slot='a'}}
    a.canRestore=function() return false end; local ok,n=c:ensure(); assert(ok and n==nil); assert(a.restored==0)
end)
test('partial restore cleanup failure blocks fallback',function()
    local a,c=fixture(); a.files={a=true,b=true}; a.meta.checkpoints={{slot='b'},{slot='a'}}
    a.restore=function() a.restored=a.restored+1; a.objects={{}}; error('partial') end
    assert(not c:ensure()); assert(a.restored==1)
end)
test('death survives unload and prevents resurrection',function()
    local a,c=fixture(); c:ensure(); c.npc.dead=true; c:observeDeath(); assert(a.meta.dead)
    assert(c:unload()); local ok,n=c:ensure(); assert(ok and n==nil); assert(a.created==1)
end)
test('successful unload restores same checkpoint',function()
    local a,c=fixture(); c:ensure(); assert(c:unload()); assert(c.npc==nil)
    assert(c:ensure()); assert(a.restored==1)
end)
test('travel unload saves first and restores only near saved square',function()
    local a,c=fixture(); c:ensure(); local far=true; local available=false
    a.shouldUnload=function() return far end
    a.nearCheckpoint=function() return not far end
    a.canRestore=function() return available end
    c:maintain(); assert(c.npc==nil and a.files.a and not c.manualUnloaded)
    c:maintain(); assert(a.restored==0)
    far=false; c:maintain(); assert(a.restored==0)
    available=true; c:maintain(); assert(c.npc and a.restored==1 and a.created==2)
end)
test('manual unload remains dormant until explicit ensure',function()
    local a,c=fixture(); c:ensure(); assert(c:unload())
    a.nearCheckpoint=function() return true end
    c:maintain(); assert(c.npc==nil and a.restored==0)
    assert(c:ensure()); assert(c.npc and a.restored==1)
end)
test('failed travel save retains NPC and stops automatic retries',function()
    local a,c=fixture(); c:ensure(); c:save(); local old=a.meta.checkpoints; local npc=c.npc; local writes=0
    a.shouldUnload=function() return true end
    a.save=function() writes=writes+1; error('disk failure') end
    c:maintain(); c:maintain()
    assert(c.npc==npc and c.travelBlocked and writes==1 and a.meta.checkpoints==old)
end)
test('engine-removed NPC cannot overwrite checkpoint or be replaced',function()
    local a,c=fixture(); c:ensure(); c:save(); local old=a.meta.checkpoints; local npc=c.npc
    a.objects={}; a.isResident=function() return false end
    c:maintain(); assert(c.travelBlocked and c.npc==npc)
    assert(not c:save()); assert(a.meta.checkpoints==old)
    assert(not c:ensure()); assert(a.created==1)
end)
test('travel restore refuses duplicates and stops retries',function()
    local a,c=fixture(); c:ensure(); c:unload(true)
    a.objects={{},{}}; a.nearCheckpoint=function() return true end
    c:maintain(); assert(c.travelBlocked and c.npc==nil and a.restored==0)
end)
test('deferred older fallback stops repeated corrupt-slot attempts',function()
    local a,c=fixture(); a.files={a=true,b=true}; a.meta.checkpoints={{slot='b',bad=true},{slot='a'}}
    a.nearCheckpoint=function() return true end
    a.canRestore=function(r) return r.slot=='b' end
    c:maintain(); c:maintain()
    assert(c.travelBlocked and c.npc==nil and a.restored==1 and a.meta.checkpoints[1].slot=='b')
end)
test('death flag prevents travel recovery',function()
    local a,c=fixture(); c:ensure(); c.npc.dead=true; c:observeDeath(); c:unload(true)
    a.nearCheckpoint=function() return true end
    c:maintain(); assert(c.npc==nil and a.restored==0 and a.meta.dead)
end)
print('RESULT '..count..' lifecycle tests passed')
''')
lua.execute(r'''
Events={}
for _,name in ipairs({'OnTick','OnFillWorldObjectContextMenu','OnSave','OnPlayerDeath','OnGameStart','OnMainMenuEnter','RenderOpaqueObjectsInWorld'}) do
    local handlers={}
    Events[name]={handlers=handlers,
        Add=function(fn) handlers[fn]=true end,
        Remove=function(fn) handlers[fn]=nil end}
end
require=function(name) if name=='Sarah/Lifecycle' then return Lifecycle else return {} end end
''')
main = (source / 'SarahFoundation.lua').read_text()
lua.execute(main)
lua.execute('SarahFoundation.controller={sentinel=true}')
lua.execute(main)
lua.execute(r'''
assert(SarahFoundation.controller.sentinel)
for _,event in pairs(Events) do
    local count=0; for _ in pairs(event.handlers) do count=count+1 end
    assert(count==1,'duplicate callback registration')
end
print('PASS Lua script reload retains controller with one callback per event')
for callback in pairs(Events.OnMainMenuEnter.handlers) do callback() end
assert(SarahFoundation.controller==nil and SarahFoundation.ticks==0)
print('PASS main menu resets controller')
SarahFoundation.controller={}; SarahFoundation.disabled=true; SarahFoundation.ticks=100
for callback in pairs(Events.OnGameStart.handlers) do callback() end
assert(SarahFoundation.controller==nil and SarahFoundation.disabled==nil and SarahFoundation.ticks==0)
print('PASS new game clears old session state')
local failures=0
SarahFoundation.controller={npc={},adapter={render=function() failures=failures+1; error('render failure') end}}
SarahFoundation.render(0); SarahFoundation.render(0)
assert(failures==1 and SarahFoundation.renderDisabled)
SarahFoundation.reset()
assert(SarahFoundation.renderDisabled==nil)
print('PASS rendering failure stops retries until session reset')
isClient=function() return false end
isServer=function() return false end
getSpecificPlayer=function() return {Say=function() end} end
local queuedAction=false
ISTimedActionQueue={add=function() queuedAction=true end}
SarahFoundation.controller={npc={},ensure=function() end,unload=function() end}
SarahConsole=nil
local ctx={options={},addOption=function(self,text,target,fn) self.options[text]=fn end}
SarahFoundation.menu(0,ctx,{},false)
assert(ctx.options["Sarah: walk here"]~=nil)
ctx.options["Sarah: walk here"]()
assert(SarahFoundation.lastFeedback~=nil)
assert(SarahFoundation.lastFeedback.message:find("Sarah Console unavailable"))
assert(SarahFoundation.lastFeedback.isBad==true)
assert(not queuedAction)
SarahConsole={getDispatch=function() return nil end}
SarahFoundation.lastFeedback=nil
ctx.options["Sarah: walk here"]()
assert(SarahFoundation.lastFeedback~=nil)
assert(SarahFoundation.lastFeedback.message:find("Sarah dispatch unavailable"))
assert(SarahFoundation.lastFeedback.isBad==true)
assert(not queuedAction)
print('PASS context menu with unavailable dispatcher queues no engine action and records refusal')
local mockOutcome={state='rejected',lines={'Sarah is busy.'}}
SarahConsole={getDispatch=function()
    return {execute=function() return mockOutcome end}
end}
ctx.options["Sarah: walk here"]()
assert(SarahFoundation.lastFeedback.message=='Sarah is busy.' and SarahFoundation.lastFeedback.isBad==true)
mockOutcome={state='failed',lines={'Walk failed to start: path offline.'}}
ctx.options["Sarah: walk here"]()
assert(SarahFoundation.lastFeedback.message=='Walk failed to start: path offline.' and SarahFoundation.lastFeedback.isBad==true)
mockOutcome={state='running',lines={'Walking to player.'}}
ctx.options["Sarah: walk here"]()
assert(SarahFoundation.lastFeedback.message=='Walking to player.' and SarahFoundation.lastFeedback.isBad==false)
mockOutcome={state='completed',lines={'Already at target.'}}
ctx.options["Sarah: walk here"]()
assert(SarahFoundation.lastFeedback.message=='Already at target.' and SarahFoundation.lastFeedback.isBad==false)
print('PASS context menu provides visible feedback on walk rejection, failure, running, and completion')
print('RESULT 29 total foundation checks passed')
''')
