"""Exercise the actual engine adapter's world-render boundaries with fake objects."""
from pathlib import Path
import sys
root = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(root / 'tools/dependencies/python'))
from lupa import LuaRuntime
lua = LuaRuntime(unpack_returned_tuples=True)
lua.globals().EngineSource = (root / 'foundation/SarahFoundation/42/media/lua/client/Sarah/Engine.lua').read_text()
lua.globals().CommandsSource = (root / 'foundation/SarahFoundation/42/media/lua/client/Sarah/Commands.lua').read_text()
lua.globals().ConsoleSource = (root / 'foundation/SarahFoundation/42/media/lua/client/Sarah/Console.lua').read_text()
lua.globals().ObservationsSource = (root / 'foundation/SarahFoundation/42/media/lua/client/Sarah/Observations.lua').read_text()
for name in ('CandidateCollector', 'Coverage', 'Perception', 'ObstructionNormalizer', 'SessionIdentity', 'DiagnosticSampler', 'Knowledge'):
    lua.globals()[name] = lua.execute((root / f'foundation/SarahFoundation/42/media/lua/client/Sarah/{name}.lua').read_text())
lua.globals().Engine = lua.execute(lua.globals().EngineSource)
lua.execute(r'''
Commands = assert(load(CommandsSource))()
Observations = assert(load(ObservationsSource))()
require = function(n)
    if n == 'Sarah/Commands' then return Commands
    elseif n == 'Sarah/Observations' then return Observations
    end
end
keyBinding = {{value = 'Forward', key = 17}}
Keyboard = {KEY_F9 = 67, KEY_F8 = 66, KEY_ESCAPE = 1}
ToggleEscapeMenu = function() end
Events = {
    OnKeyPressed = {Add = function() end, Remove = function() end},
    OnTick = {Add = function() end, Remove = function() end},
    OnGameStart = {Add = function() end, Remove = function() end},
    OnMainMenuEnter = {Add = function() end, Remove = function() end},
    OnFillWorldObjectContextMenu = {Add = function() end, Remove = function() end},
    OnResolutionChange = {Add = function() end, Remove = function() end}
}
local Base = {
    derive = function(self)
        local c = {}
        c.__index = c
        return setmetatable(c, {__index = self})
    end,
    new = function(self)
        return setmetatable({items = {}, visible = true}, {__index = self})
    end
}
for _, m in ipairs({'initialise', 'instantiate', 'setWantKeyEvents', 'addChild', 'addToUIManager', 'removeFromUIManager', 'setMaxTextLength', 'prerender', 'drawText', 'setFont', 'focus', 'unfocus', 'setVisible', 'setX', 'setY', 'setHeight', 'addItem', 'setYScroll'}) do
    Base[m] = function() end
end
ISPanel = Base
ISButton = Base:derive()
function ISButton:new(x, y, w, h, title, target, onclick)
    local o = Base.new(self)
    o.title = title; o.target = target; o.onclick = onclick
    return o
end
ISTextEntryBox = Base:derive()
ISScrollingListBox = Base:derive()
getCore = function()
    return {
        getKey = function() return 0 end,
        getAltKey = function() return 0 end,
        getScreenWidth = function() return 1280 end,
        getScreenHeight = function() return 720 end
    }
end
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
        stop=function(self) end,
        update=function(self) end
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
test('adapter recreation with SAME NPC isolates actions and prevents stale action mutation', function()
    local f = fixture()
    local queuedAction = nil
    local pathfindCancelled = 0
    local queueReset = 0
    f.npc.running = false
    f.npc.setRunning = function(self, r) self.running = r end
    f.npc.getPathFindBehavior2 = function(self)
        return {cancel = function() pathfindCancelled = pathfindCancelled + 1 end}
    end
    f.npc.setPath2 = function(self, p) end

    ISTimedActionQueue = {
        add = function(act) queuedAction = act end,
        clear = function(c) queueReset = queueReset + 1 end
    }
    ISWalkToTimedAction = {
        new = function(self, char, sq)
            local o = {character = char, location = sq}
            setmetatable(o, self)
            return o
        end,
        derive = function(self, name)
            local cls = {}
            cls.__index = cls
            setmetatable(cls, {__index = self})
            return cls
        end,
        perform = function(self) end,
        stop = function(self) end,
        update = function(self) end
    }

    local adapter1 = f.adapter
    local ok1, act1 = adapter1.walk(f.npc, f.npc.square, nil, nil, 'run')
    assert(ok1 and act1 and act1.token == 1 and act1.adapter == adapter1)
    act1:update()
    assert(f.npc.running == true)
    -- Purity check: live action object must NEVER be in NPC modData
    assert(f.npc:getModData().SarahActiveAction == nil)
    local rec1 = Engine.getOwnership(f.npc)
    assert(rec1 ~= nil and rec1.action == act1 and rec1.adapter == adapter1)

    -- Recreate adapter with the SAME NPC (simulating world reload or adapter reset)
    local adapter2 = Engine.new()
    local ok2, act2 = adapter2.walk(f.npc, f.npc.square, nil, nil, 'run')
    assert(ok2 and act2 and act2.token == 1 and act2.adapter == adapter2)
    assert(act1 ~= act2)
    assert(act1.character == act2.character)
    act2:update()
    assert(f.npc.running == true)
    -- Newer owner active in runtime record; modData remains clean
    assert(f.npc:getModData().SarahActiveAction == nil)
    local rec2 = Engine.getOwnership(f.npc)
    assert(rec2 ~= nil and rec2.action == act2 and rec2.adapter == adapter2)

    -- act1 stopping must NOT clear running on the same NPC or mutate adapter2
    act1:stop()
    assert(f.npc.running == true)
    assert(adapter2.currentAction == act2)
    assert(act2:isCurrentOwner() == true)

    -- Stale adapter1.stop(npc) must NOT clear newer adapter's ownership, running flag, queue or path
    local queueCleared = 0
    local pathCancelled = 0
    local pathCleared = 0
    f.npc.getPathFindBehavior2 = function() return {cancel = function() pathCancelled = pathCancelled + 1 end} end
    f.npc.setPath2 = function(self, p) if p == nil then pathCleared = pathCleared + 1 end end
    ISTimedActionQueue.clear = function(char) if char == f.npc then queueCleared = queueCleared + 1 end end

    adapter1.stop(f.npc)
    assert(adapter1.currentAction == nil)
    assert(adapter2.currentAction == act2) -- Newer action untouched
    assert(act2:isCurrentOwner() == true)  -- Ownership untouched
    assert(f.npc.running == true)          -- Running flag untouched
    assert(queueCleared == 0)              -- Queue NOT cleared by stale stop
    assert(pathCancelled == 0)             -- Path NOT cancelled by stale stop
    assert(pathCleared == 0)
    assert(Engine.getOwnership(f.npc).action == act2)

    -- Current-controller adapter2.stop(npc) DOES halt Sarah and clear queue/path/ownership
    adapter2.stop(f.npc)
    assert(adapter2.currentAction == nil)
    assert(act2:isCurrentOwner() == false)
    assert(f.npc.running == false)
    assert(queueCleared == 1)
    assert(pathCancelled == 1)
    assert(pathCleared == 1)
    assert(Engine.getOwnership(f.npc) == nil)
end)
test('ownership checks fail closed when record is missing or unreadable', function()
    local f = fixture()
    f.npc.running = false
    f.npc.setRunning = function(self, r) self.running = r end
    local adapter = f.adapter
    local ok, act = adapter.walk(f.npc, f.npc.square, nil, nil, 'run')
    assert(ok and act)
    assert(act:isCurrentOwner() == true)

    -- 1. Missing record -> fails closed
    Engine.clearOwnership(f.npc)
    assert(act:isCurrentOwner() == false)

    -- 2. Non-table record -> fails closed
    Engine.runtimeOwnership[f.npc] = "invalid_string"
    assert(act:isCurrentOwner() == false)

    -- 3. Wrong owner record -> fails closed
    Engine.setOwnership(f.npc, {action = {}, token = 999, adapter = {}})
    assert(act:isCurrentOwner() == false)

    -- 4. Unreadable record (indexing throws) -> fails closed
    local savedTbl = Engine.runtimeOwnership
    Engine.runtimeOwnership = setmetatable({}, {__index = function() error('unreadable table') end})
    assert(act:isCurrentOwner() == false)
    Engine.runtimeOwnership = savedTbl
end)
test('retired action does not invoke base methods that mutate pathfinding or queues', function()
    local f = fixture()
    local basePerformCalled = 0
    local baseStopCalled = 0
    f.npc.running = false
    f.npc.setRunning = function(self, r) self.running = r end

    ISTimedActionQueue = {add = function(act) end, clear = function() end}
    ISWalkToTimedAction = {
        new = function(self, char, sq)
            local o = {character = char, location = sq}
            setmetatable(o, self)
            return o
        end,
        derive = function(self, name)
            local cls = {}
            cls.__index = cls
            setmetatable(cls, {__index = self})
            return cls
        end,
        perform = function(self) basePerformCalled = basePerformCalled + 1 end,
        stop = function(self) baseStopCalled = baseStopCalled + 1 end,
        update = function(self) end
    }

    local adapter = f.adapter
    local ok1, act1 = adapter.walk(f.npc, f.npc.square, nil, nil, 'run')
    local ok2, act2 = adapter.walk(f.npc, f.npc.square, nil, nil, 'run')
    assert(act1:isCurrentOwner() == false)
    assert(act2:isCurrentOwner() == true)

    -- Retired act1 calling stop/perform does NOT invoke base methods that cancel pathfinding or reset queue
    local fail1Called = 0
    act1.onFail = function() fail1Called = fail1Called + 1 end
    act1:stop()
    assert(baseStopCalled == 0)
    assert(fail1Called == 1)

    -- Duplicate stop on retired act1 does not re-invoke callback (exactly once)
    act1:stop()
    assert(fail1Called == 1)

    -- Active act2 calling perform DOES invoke base perform
    local success2Called = 0
    act2.onSuccess = function() success2Called = success2Called + 1 end
    act2:perform()
    assert(basePerformCalled == 1)
    assert(success2Called == 1)

    -- Duplicate perform on act2 does not re-invoke callback
    act2:perform()
    assert(basePerformCalled == 1)
    assert(success2Called == 1)
end)
test('queue admission handles synchronous completion, failure, and re-entry safely', function()
    local f = fixture()
    f.npc.running = false
    f.npc.setRunning = function(self, r) self.running = r end
    local adapter = f.adapter

    -- Case 1: Synchronous completion during queue add
    local syncAct = nil
    ISTimedActionQueue = {
        add = function(act)
            syncAct = act
            act:perform() -- finishes synchronously during add!
        end
    }
    local ok1, act1 = adapter.walk(f.npc, f.npc.square, nil, nil, 'run')
    assert(ok1 and act1)
    assert(act1.finished == true)
    assert(adapter.currentAction == nil) -- NOT restored to stale action!

    -- Case 2: Partial queue-start failure with motion cleanup
    local cancelCalled = 0
    f.npc.getPathFindBehavior2 = function() return {cancel = function() cancelCalled = cancelCalled + 1 end} end
    f.npc.setPath2 = function(self, p) end
    ISTimedActionQueue = {
        add = function(act)
            f.npc.running = true -- motion started partially
            error('queue rejected action after starting')
        end
    }
    local ok2, err2 = adapter.walk(f.npc, f.npc.square, nil, nil, 'run')
    assert(ok2 == false)
    assert(adapter.currentAction == nil)
    assert(f.npc.running == false)       -- Motion safely cleaned up!
    assert(cancelCalled == 1)            -- Path cancelled!
    assert(Engine.getOwnership(f.npc) == nil)

    -- Case 3: Re-entrant queue add (newer owner survives, earlier failure protects newer owner)
    local act2 = nil
    local reentered = false
    ISTimedActionQueue = {
        add = function(act)
            if not reentered then
                reentered = true
                -- Re-entrantly start a newer walk action
                local okInner, inner = adapter.walk(f.npc, f.npc.square, nil, nil, 'run')
                act2 = inner
                error('first add throws after newer owner took over')
            end
        end
    }
    local ok3, err3 = adapter.walk(f.npc, f.npc.square, nil, nil, 'run')
    assert(ok3 == false)
    assert(act2 ~= nil)
    assert(adapter.currentAction == act2) -- Newer owner survived!
    assert(Engine.getOwnership(f.npc).action == act2)
    assert(act2:isCurrentOwner() == true)
end)
test('adapter.stop attempts all safe cleanups and propagates failures, enabling stopFailed blocking', function()
    local f = fixture()
    local adapter = f.adapter

    local setRunningCalled = 0
    local queueClearCalled = 0
    local pathCancelCalled = 0
    local setPath2Called = 0

    f.npc.setRunning = function(self, r)
        setRunningCalled = setRunningCalled + 1
        error('simulated native setRunning crash')
    end
    ISTimedActionQueue = {
        clear = function(char)
            queueClearCalled = queueClearCalled + 1
            error('simulated native queue.clear crash')
        end
    }
    f.npc.getPathFindBehavior2 = function(self)
        return {
            cancel = function(self)
                pathCancelCalled = pathCancelCalled + 1
                error('simulated native path.cancel crash')
            end
        }
    end
    f.npc.setPath2 = function(self, p)
        setPath2Called = setPath2Called + 1
        error('simulated native setPath2 crash')
    end

    -- 1. Direct adapter.stop call: returns false and concatenated failure reasons
    local stopOk, stopErr = adapter.stop(f.npc)
    assert(stopOk == false, 'adapter.stop must return false when native methods throw')
    assert(type(stopErr) == 'string')
    assert(setRunningCalled == 1, 'setRunning must be attempted')
    assert(queueClearCalled == 1, 'queue.clear must be attempted')
    assert(pathCancelCalled == 1, 'path.cancel must be attempted')
    assert(setPath2Called == 1, 'setPath2 must be attempted')
    assert(string.find(stopErr, 'setRunning'), 'error must mention setRunning')
    assert(string.find(stopErr, 'queue.clear'), 'error must mention queue.clear')
    assert(string.find(stopErr, 'path.cancel'), 'error must mention path.cancel')
    assert(string.find(stopErr, 'setPath2'), 'error must mention setPath2')

    -- 2. Pipeline integration with actual Console.lua and Commands.lua
    SarahFoundation = {
        controller = {
            npc = f.npc,
            adapter = adapter
        }
    }
    local consoleModule = assert(load(ConsoleSource))()
    local dispatch = consoleModule.getDispatch()

    -- Call stop through dispatch (which invokes Console.stopSarah -> adapter.stop)
    local stopResult = dispatch:execute('stop')
    assert(stopResult.state == 'failed')
    assert(dispatch.stopFailed ~= nil, 'dispatch.stopFailed must be set when engine stop fails')
    assert(string.find(dispatch.stopFailed, 'setRunning'), 'stopFailed reason must propagate')

    -- Movement is now blocked pending recovery!
    local walkRes = dispatch:execute('walk here', {x = 12, y = 20, z = 0})
    assert(walkRes.state == 'rejected')
    assert(string.find(walkRes.lines[1], 'Prior engine stop failed'), 'movement must be blocked by stopFailed')

    local followRes = dispatch:execute('follow')
    assert(followRes.state == 'rejected')
    assert(string.find(followRes.lines[1], 'Prior engine stop failed'), 'follow must be blocked by stopFailed')

    -- 3. Simulate engine recovery: native cleanup methods now succeed
    f.npc.setRunning = function(self, r) end
    ISTimedActionQueue.clear = function(char) end
    f.npc.getPathFindBehavior2 = function(self) return {cancel = function() end} end
    f.npc.setPath2 = function(self, p) end

    -- Re-running stop clears failure and reports recovery
    local recoverRes = dispatch:execute('stop')
    assert(recoverRes.state == 'completed')
    assert(dispatch.stopFailed == nil, 'successful stop must clear stopFailed')

    -- Movement is unblocked after recovery (no longer rejected by prior stop failure)
    local walkAfter = dispatch:execute('walk here', {x = 12, y = 20, z = 0})
    assert(walkAfter.state ~= 'rejected', 'movement must no longer be rejected by prior stop failure')
end)
test('adapter.walk rejects admission and does not queue ownerless action if setOwnership fails', function()
    local f = fixture()
    local adapter = f.adapter

    local queueAddCalled = 0
    ISTimedActionQueue = {
        add = function(act)
            queueAddCalled = queueAddCalled + 1
        end
    }

    -- Simulate setOwnership failure (e.g. registry write fails)
    local savedSet = Engine.setOwnership
    Engine.setOwnership = function(npc, rec)
        return false, 'simulated ownership registry write error'
    end

    local ok, err = adapter.walk(f.npc, f.npc.square, nil, nil, 'run')
    assert(ok == false, 'walk admission must be rejected when setOwnership fails')
    assert(string.find(tostring(err), 'failed to set ownership'), 'error must indicate setOwnership failure')
    assert(adapter.currentAction == nil, 'currentAction must be cleared on admission rejection')
    assert(queueAddCalled == 0, 'ownerless action must NOT be added to ISTimedActionQueue')

    -- Restore Engine.setOwnership
    Engine.setOwnership = savedSet
end)
test('runtime ownership continuity across Engine module reload on the SAME NPC prevents disruption by old adapters', function()
    local f = fixture()

    -- Load first Engine module
    local Engine1 = assert(load(EngineSource))()
    local adapter1 = Engine1.new()

    ISTimedActionQueue = {
        add = function(act) end,
        clear = function(char) end
    }
    ISWalkToTimedAction = {
        new = function(self, char, sq)
            local o = {character = char, location = sq}
            setmetatable(o, self)
            return o
        end,
        derive = function(self, name)
            local cls = {}
            cls.__index = cls
            setmetatable(cls, {__index = self})
            return cls
        end,
        perform = function(self) end,
        stop = function(self) end,
        update = function(self) end
    }

    f.npc.running = false
    f.npc.setRunning = function(self, r) self.running = r end

    -- Adapter 1 walks on f.npc
    local ok1, act1 = adapter1.walk(f.npc, f.npc.square, nil, nil, 'run')
    assert(ok1 and act1)
    assert(act1:isCurrentOwner() == true)
    assert(adapter1.currentAction == act1)

    -- Now simulate Engine.lua module reload in the same Lua state
    local Engine2 = assert(load(EngineSource))()
    assert(Engine2 ~= Engine1, 'Engine2 must be a distinct module table')
    local adapter2 = Engine2.new()
    assert(adapter2 ~= adapter1, 'adapter2 must be a distinct adapter')

    -- Adapter 2 walks on the SAME NPC
    local ok2, act2 = adapter2.walk(f.npc, f.npc.square, nil, nil, 'run')
    assert(ok2 and act2)
    assert(act2:isCurrentOwner() == true)
    assert(adapter2.currentAction == act2)

    -- act1 from adapter1 is now retired
    assert(act1:isCurrentOwner() == false)

    -- Crucial check: old adapter1 calling stop(f.npc) must NOT disrupt adapter2's ownership, running flag, or action
    local pathCancelled = 0
    f.npc.getPathFindBehavior2 = function(self)
        return {cancel = function() pathCancelled = pathCancelled + 1 end}
    end
    local queueCleared = 0
    ISTimedActionQueue.clear = function(char) queueCleared = queueCleared + 1 end

    local stopOk1 = adapter1.stop(f.npc)
    assert(stopOk1 == true)
    assert(pathCancelled == 0, 'old adapter stop must not cancel newer pathfinding')
    assert(queueCleared == 0, 'old adapter stop must not clear queue for newer action')
    assert(act2:isCurrentOwner() == true, 'newer action must remain current owner')
    assert(adapter2.currentAction == act2, 'newer adapter currentAction must remain intact')

    -- Now adapter2 stop(f.npc) cleanly stops and clears ownership
    local stopOk2 = adapter2.stop(f.npc)
    assert(stopOk2 == true)
    assert(act2:isCurrentOwner() == false)
    assert(adapter2.currentAction == nil)
    assert(Engine2.getOwnership(f.npc) == nil)
    assert(Engine1.getOwnership(f.npc) == nil)
end)
test('adapter.samplePerception fails safely on missing/dead NPC or invalid facing', function()
    local f = fixture()
    local adapter = f.adapter

    -- Missing NPC
    local r1, err1 = adapter.samplePerception(nil)
    assert(r1 == nil and err1 == 'missing npc')

    -- Dead NPC
    f.npc.dead = true
    local r2, err2 = adapter.samplePerception(f.npc)
    assert(r2 == nil and err2 == 'npc dead')
    f.npc.dead = false

    -- Missing forward vector methods -> capture aborts
    f.npc.getForwardDirectionX = nil
    f.npc.getForwardDirectionY = nil
    local r3 = adapter.samplePerception(f.npc)
    assert(r3 and r3.status == 'aborted', 'must abort when forward direction methods missing')

    -- Zero forward vector (0, 0) -> capture aborts
    f.npc.getForwardDirectionX = function() return 0 end
    f.npc.getForwardDirectionY = function() return 0 end
    local r4 = adapter.samplePerception(f.npc)
    assert(r4 and r4.status == 'aborted', 'must abort when forward vector is (0,0)')

    -- Non-numeric forward vector -> capture aborts
    f.npc.getForwardDirectionX = function() return "invalid" end
    f.npc.getForwardDirectionY = function() return 1 end
    local r5 = adapter.samplePerception(f.npc)
    assert(r5 and r5.status == 'aborted', 'must abort when forward vector is non-numeric')
end)
test('adapter.samplePerception enumerates candidates, filters invalid, and enforces unknown lighting', function()
    local f = fixture()
    local adapter = f.adapter

    -- Sarah facing East (1, 0)
    f.npc.getForwardDirectionX = function() return 1.0 end
    f.npc.getForwardDirectionY = function() return 0.0 end
    f.npc.getX = function() return 10.0 end
    f.npc.getY = function() return 20.0 end
    f.npc.getZ = function() return 0.0 end

    -- Setup grid square with moving objects
    local z1 = {
        isZombie = function() return true end,
        isDead = function() return false end,
        getX = function() return 12.0 end,
        getY = function() return 20.0 end,
        getZ = function() return 0.0 end,
        getOnlineID = function() return 101 end,
    }
    local deadZ = {
        isZombie = function() return true end,
        isDead = function() return true end,
        getX = function() return 11.0 end,
        getY = function() return 20.0 end,
        getZ = function() return 0.0 end,
        getOnlineID = function() return 102 end,
    }
    local vehicle = {
        isZombie = function() return false end,
        isPlayer = function() return false end,
        isDead = function() return false end,
        getX = function() return 11.0 end,
        getY = function() return 21.0 end,
        getZ = function() return 0.0 end,
    }
    local movingList = {z1, deadZ, vehicle, f.npc}
    local mockMovingObjects = {
        size = function() return #movingList end,
        get = function(self, idx) return movingList[idx + 1] end,
    }
    local testSq = {
        getX = function() return 12 end,
        getY = function() return 20 end,
        getZ = function() return 0 end,
        getMovingObjects = function() return mockMovingObjects end,
    }

    local oldGetCell = getCell
    local mockCell = {
        getGridSquare = function(self, x, y, z)
            return testSq
        end,
        getObjectList = function(self)
            return {contains = function(_, obj) return obj == f.npc end}
        end,
        getAddList = function(self)
            return {contains = function() return false end}
        end,
        getRemoveList = function(self)
            return {contains = function() return false end}
        end,
    }
    getCell = function()
        return mockCell
    end

    local resClear = {name = "Clear"}
    local resOpenDoor = {name = "ClearThroughOpenDoor"}
    local resWindow = {name = "ClearThroughWindow"}
    local resBlocked = {name = "Blocked"}
    local resClosedDoor = {name = "ClearThroughClosedDoor"}

    LosUtil = {
        TestResults = {
            Clear = resClear,
            ClearThroughOpenDoor = resOpenDoor,
            ClearThroughWindow = resWindow,
            Blocked = resBlocked,
            ClearThroughClosedDoor = resClosedDoor,
        },
        lineClear = function(cell, x1, y1, z1, x2, y2, z2, b)
            return resClear
        end
    }

    local res = adapter.samplePerception(f.npc)
    assert(res ~= nil, 'samplePerception must return result table')
    assert(res.status == 'sampled', 'sample status must be sampled')
    assert(res.lighting == 'unknown', 'lighting must remain strictly unknown')

    -- Only z1 is valid candidate (Sarah herself, dead zombie, and vehicle must be filtered)
    assert(res.counts.candidates == 1, 'exactly 1 candidate must be admitted')
    assert(#res.results == 1, 'exactly 1 candidate result')
    local cand = res.results[1]
    assert(cand.kind == 'zombie')
    assert(cand.geometric == 'visible')
    assert(cand.visual == 'unknown', 'unknown lighting must never imply sight (visual unknown)')

    getCell = oldGetCell
    LosUtil = nil
end)
test('adapter.resetPerception resets sampler generation and session identity, wired to remove', function()
    local f = fixture()
    local adapter = f.adapter

    adapter.ensurePerceptionModules()
    assert(adapter.sessionIdentity ~= nil)
    assert(adapter.diagnosticSampler ~= nil)

    local initialGen = adapter.sampleGeneration or 1
    local id1 = adapter.sessionIdentity:resolve('tok1', 'player')
    assert(id1.id and id1.reason == 'new')
    local snap1 = adapter.sessionIdentity:snapshot()
    assert(snap1.epoch == 1)

    -- Explicit resetPerception
    adapter.resetPerception()
    assert((adapter.sampleGeneration or 1) > initialGen, 'sampleGeneration must increment')
    local snap2 = adapter.sessionIdentity:snapshot()
    assert(snap2.epoch == 2, 'SessionIdentity epoch must advance on resetPerception')

    -- Wired into adapter.remove(npc)
    local curGen = adapter.sampleGeneration
    f.npc.removeFromWorld = function() end
    f.npc.removeFromSquare = function() end
    adapter.remove(f.npc)
    assert(adapter.sampleGeneration > curGen, 'remove must trigger resetPerception')
    local snap3 = adapter.sessionIdentity:snapshot()
    assert(snap3.epoch == 3, 'SessionIdentity epoch must advance on remove')
end)
test('adapter.samplePerception dynamic lifecycle capture detects cell drift and generation drift', function()
    local f = fixture()
    local adapter = f.adapter
    adapter.ensurePerceptionModules()

    f.npc.getForwardDirectionX = function() return 1.0 end
    f.npc.getForwardDirectionY = function() return 0.0 end
    f.npc.getX = function() return 10.0 end
    f.npc.getY = function() return 20.0 end
    f.npc.getZ = function() return 0.0 end

    local testSq = {
        getX = function() return 12 end,
        getY = function() return 20 end,
        getZ = function() return 0 end,
        getMovingObjects = function() return { size = function() return 0 end } end,
    }

    local currentCell = {
        getGridSquare = function(self, x, y, z) return testSq end,
        getObjectList = function(self) return {contains = function(_, obj) return obj == f.npc end} end,
        getAddList = function(self) return {contains = function() return false end} end,
        getRemoveList = function(self) return {contains = function() return false end} end,
    }

    local oldGetCell = getCell
    getCell = function() return currentCell end

    local driftCell = {
        getGridSquare = function(self, x, y, z) return testSq end,
        getObjectList = function(self) return {contains = function(_, obj) return obj == f.npc end} end,
        getAddList = function(self) return {contains = function() return false end} end,
        getRemoveList = function(self) return {contains = function() return false end} end,
    }

    -- Normal sample first
    local res1 = adapter.samplePerception(f.npc)
    assert(res1 ~= nil and res1.status == 'sampled', 'initial sample must succeed')

    -- Now cause cell drift during sample
    local getSquareCalls = 0
    local driftingCell = {
        getGridSquare = function(self, x, y, z)
            getSquareCalls = getSquareCalls + 1
            if getSquareCalls > 2 then
                currentCell = driftCell
            end
            return testSq
        end,
        getObjectList = function(self) return {contains = function(_, obj) return obj == f.npc end} end,
        getAddList = function(self) return {contains = function() return false end} end,
        getRemoveList = function(self) return {contains = function() return false end} end,
    }
    currentCell = driftingCell

    local resDrift = adapter.samplePerception(f.npc)
    assert(resDrift ~= nil, 'samplePerception must return result')
    assert(resDrift.status == 'aborted', 'cell drift during sampling must abort')
    assert(resDrift.reason == 'lifecycle_drift', 'abort reason must be lifecycle_drift')

    getCell = oldGetCell
end)
test('adapter.samplePerception enumeration query errors fail closed and same-size list mutation is detected', function()
    local f = fixture()
    local adapter = f.adapter
    adapter.ensurePerceptionModules()

    f.npc.getForwardDirectionX = function() return 1.0 end
    f.npc.getForwardDirectionY = function() return 0.0 end
    f.npc.getX = function() return 10.0 end
    f.npc.getY = function() return 20.0 end
    f.npc.getZ = function() return 0.0 end

    -- 1. Query error in getMovingObjects throws and causes query_error (never empty success)
    local failingSq = {
        getX = function() return 12 end,
        getY = function() return 20 end,
        getZ = function() return 0 end,
        getMovingObjects = function() error('native memory access violation') end,
    }

    local mockCell = {
        getGridSquare = function(self, x, y, z) return failingSq end,
        getObjectList = function(self) return {contains = function(_, obj) return obj == f.npc end} end,
        getAddList = function(self) return {contains = function() return false end} end,
        getRemoveList = function(self) return {contains = function() return false end} end,
    }

    local oldGetCell = getCell
    getCell = function() return mockCell end

    local resFail = adapter.samplePerception(f.npc)
    assert(resFail ~= nil)
    assert(resFail.counts.candidates == 0)

    -- 2. Same-size list replacement / reordering produces distinct tokens
    local zA = {
        isZombie = function() return true end,
        isDead = function() return false end,
        getX = function() return 12.0 end,
        getY = function() return 20.0 end,
        getZ = function() return 0.0 end,
        getOnlineID = function() return 201 end,
    }
    local zB = {
        isZombie = function() return true end,
        isDead = function() return false end,
        getX = function() return 12.0 end,
        getY = function() return 20.0 end,
        getZ = function() return 0.0 end,
        getOnlineID = function() return 202 end,
    }

    local list1 = { zA, zB }
    local mockList1 = {
        size = function() return #list1 end,
        get = function(self, idx) return list1[idx + 1] end,
    }
    local sq1 = {
        getX = function() return 12 end,
        getY = function() return 20 end,
        getZ = function() return 0 end,
        getMovingObjects = function() return mockList1 end,
    }

    local list2 = { zB, zA }
    local mockList2 = {
        size = function() return #list2 end,
        get = function(self, idx) return list2[idx + 1] end,
    }
    local sq2 = {
        getX = function() return 12 end,
        getY = function() return 20 end,
        getZ = function() return 0 end,
        getMovingObjects = function() return mockList2 end,
    }

    local origSample = adapter.diagnosticSampler.sample
    local capturedApi = nil
    adapter.diagnosticSampler.sample = function(self, api)
        capturedApi = api
        return origSample(self, api)
    end
    adapter.samplePerception(f.npc)
    adapter.diagnosticSampler.sample = origSample

    assert(capturedApi ~= nil, 'captured api must be available')
    local sz1, tok1 = capturedApi.listInfo(sq1)
    local sz2, tok2 = capturedApi.listInfo(sq2)
    assert(sz1 == 2 and sz2 == 2, 'both lists have size 2')
    assert(tok1 ~= tok2, 'same-size list with swapped order must have distinct tokens')

    -- 3. Unknown liveness rejection
    local zUnknownDead = {
        isZombie = function() return true end,
        isDead = function() return nil end,
        getX = function() return 12.0 end,
        getY = function() return 20.0 end,
        getZ = function() return 0.0 end,
    }
    local sqUnknown = {
        getMovingObjects = function()
            return {
                size = function() return 1 end,
                get = function() return zUnknownDead end,
            }
        end
    }
    local readRes = capturedApi.readObject(sqUnknown, 0)
    assert(readRes == nil, 'readObject must reject candidate with unknown/non-boolean liveness')

    getCell = oldGetCell
end)
test('enumeration integrity: exact snapshots, tail-change, collision, crowded-list, read-budget, and short tokens', function()
    local f = fixture()
    local adapter = f.adapter
    adapter.ensurePerceptionModules()

    f.npc.getForwardDirectionX = function() return 1.0 end
    f.npc.getForwardDirectionY = function() return 0.0 end
    f.npc.getX = function() return 10.0 end
    f.npc.getY = function() return 20.0 end
    f.npc.getZ = function() return 0.0 end

    local dummySq = {
        getX = function() return 12 end,
        getY = function() return 20 end,
        getZ = function() return 0 end,
        getMovingObjects = function() return { size = function() return 0 end } end,
    }

    local mockCell = {
        getGridSquare = function(self, x, y, z) return dummySq end,
        getObjectList = function(self) return {contains = function(_, obj) return obj == f.npc end} end,
        getAddList = function(self) return {contains = function() return false end} end,
        getRemoveList = function(self) return {contains = function() return false end} end,
    }

    local oldGetCell = getCell
    getCell = function() return mockCell end

    local origSample = adapter.diagnosticSampler.sample
    local capturedApi = nil
    adapter.diagnosticSampler.sample = function(self, api)
        capturedApi = api
        return origSample(self, api)
    end
    adapter.samplePerception(f.npc)
    adapter.diagnosticSampler.sample = origSample

    assert(capturedApi ~= nil, 'captured api must be available')

    -- 1. Crowded-list: >64 objects fails closed as unsupported oversized list
    local list65 = {}
    for i = 1, 65 do
        list65[i] = {
            isZombie = function() return true end,
            isDead = function() return false end,
            getX = function() return 12.0 end,
            getY = function() return 20.0 end,
            getZ = function() return 0.0 end,
        }
    end
    local sq65 = {
        getX = function() return 12 end,
        getY = function() return 20 end,
        getZ = function() return 0 end,
        getMovingObjects = function()
            return {
                size = function() return 65 end,
                get = function(self, idx) return list65[idx + 1] end,
            }
        end,
    }
    local ok65, err65 = pcall(capturedApi.listInfo, sq65)
    assert(not ok65, 'oversized list (>64) must fail closed')
    assert(tostring(err65):find('unsupported oversized list'), 'error must indicate unsupported oversized list')

    -- 2. Supported crowded-list (64 objects) succeeds
    local list64A = {}
    for i = 1, 64 do
        list64A[i] = list65[i]
    end
    local sq64A = {
        getX = function() return 12 end,
        getY = function() return 20 end,
        getZ = function() return 0 end,
        getMovingObjects = function()
            return {
                size = function() return 64 end,
                get = function(self, idx) return list64A[idx + 1] end,
            }
        end,
    }
    local sz64A, tok64A = capturedApi.listInfo(sq64A)
    assert(sz64A == 64 and type(tok64A) == 'string' and #tok64A <= 96, '64-object list succeeds with valid token')

    -- 3. Tail-change: change only element 64 (index 63)
    local list64B = {}
    for i = 1, 63 do
        list64B[i] = list64A[i]
    end
    list64B[64] = {
        isZombie = function() return true end,
        isDead = function() return false end,
        getX = function() return 12.0 end,
        getY = function() return 20.0 end,
        getZ = function() return 0.0 end,
    }
    local sq64B = {
        getX = function() return 12 end,
        getY = function() return 20 end,
        getZ = function() return 0 end,
        getMovingObjects = function()
            return {
                size = function() return 64 end,
                get = function(self, idx) return list64B[idx + 1] end,
            }
        end,
    }
    local sz64B, tok64B = capturedApi.listInfo(sq64B)
    assert(sz64B == 64)
    assert(tok64A ~= tok64B, 'tail element change at index 63 must produce distinct token')

    -- 4. Collision safety: two distinct lists of objects are not conflated
    local z1 = { isZombie = function() return true end, isDead = function() return false end, getX = function() return 14.0 end, getY = function() return 20.0 end, getZ = function() return 0.0 end }
    local z2 = { isZombie = function() return true end, isDead = function() return false end, getX = function() return 14.0 end, getY = function() return 20.0 end, getZ = function() return 0.0 end }
    local sqC1 = {
        getX = function() return 14 end, getY = function() return 20 end, getZ = function() return 0 end,
        getMovingObjects = function() return { size = function() return 1 end, get = function(self, idx) return z1 end } end,
    }
    local sqC2 = {
        getX = function() return 14 end, getY = function() return 20 end, getZ = function() return 0 end,
        getMovingObjects = function() return { size = function() return 1 end, get = function(self, idx) return z2 end } end,
    }
    local _, tokC1 = capturedApi.listInfo(sqC1)
    local _, tokC2 = capturedApi.listInfo(sqC2)
    assert(tokC1 ~= tokC2, 'different object references on same square must produce distinct tokens')

    -- 5. Native read budget accounting and exhaustion
    adapter.readBudget = 5
    capturedApi.nativeReads = 0
    local sqBudget = {
        getX = function() return 15 end, getY = function() return 20 end, getZ = function() return 0 end,
        getMovingObjects = function()
            return {
                size = function() return 3 end,
                get = function(self, idx) return z1 end,
            }
        end,
    }
    -- First read takes 3 native reads (nativeReads = 3 <= 5)
    local okB1, szB1 = pcall(capturedApi.listInfo, sqBudget)
    assert(okB1 and szB1 == 3, 'first read within budget succeeds')
    -- Second read would take 3 more (3 + 3 = 6 > 5) -> must fail closed
    local okB2, errB2 = pcall(capturedApi.listInfo, sqBudget)
    assert(not okB2, 'exceeding read budget must fail closed')
    assert(tostring(errB2):find('native read budget exhausted'), 'error must indicate budget exhausted')
    adapter.readBudget = nil -- reset

    -- 6. Short namespace/epoch/sequence identity token format
    local zToken = {
        isZombie = function() return true end,
        isDead = function() return false end,
        getX = function() return 12.0 end,
        getY = function() return 20.0 end,
        getZ = function() return 0.0 end,
        getOnlineID = function() return 999 end,
    }
    local sqToken = {
        getMovingObjects = function()
            return {
                size = function() return 1 end,
                get = function(self, idx) return zToken end,
            }
        end,
    }
    capturedApi.nativeReads = 0
    local readObj = capturedApi.readObject(sqToken, 0)
    assert(readObj ~= nil and readObj.id ~= nil, 'readObject must succeed')
    assert(type(readObj.id) == 'string' and #readObj.id <= 96, 'id must be <= 96 chars')

    getCell = oldGetCell
end)
test('repeated samplePerception cross-sample list identity: unchanged fairness, replacement, tail change, and reset', function()
    local f = fixture()
    local adapter = f.adapter
    adapter.ensurePerceptionModules()

    f.npc.getForwardDirectionX = function() return 1.0 end
    f.npc.getForwardDirectionY = function() return 0.0 end
    f.npc.getX = function() return 10.0 end
    f.npc.getY = function() return 20.0 end
    f.npc.getZ = function() return 0.0 end

    -- Helper to create mock zombie character
    local function makeZombie(id, ox, oy)
        return {
            isZombie = function() return true end,
            isDead = function() return false end,
            isAlive = function() return true end,
            getX = function() return ox or 12.0 end,
            getY = function() return oy or 20.0 end,
            getZ = function() return 0.0 end,
            getOnlineID = function() return id end,
        }
    end

    -- Create 20 distinct zombie objects
    local list1 = {}
    for i = 1, 20 do
        list1[i] = makeZombie(100 + i, 12.0, 20.0)
    end

    local currentList = list1
    local mockMovingObjects = {
        size = function() return #currentList end,
        get = function(self, idx) return currentList[idx + 1] end,
    }

    local targetSq = {
        getX = function() return 12 end,
        getY = function() return 20 end,
        getZ = function() return 0 end,
        getMovingObjects = function() return mockMovingObjects end,
    }

    local mockCell = {
        getGridSquare = function(self, x, y, z)
            if x == 12 and y == 20 and z == 0 then
                return targetSq
            end
            return nil
        end,
        getObjectList = function(self) return {contains = function(_, obj) return obj == f.npc end} end,
        getAddList = function(self) return {contains = function() return false end} end,
        getRemoveList = function(self) return {contains = function() return false end} end,
    }

    local oldGetCell = getCell
    getCell = function() return mockCell end

    adapter.readBudget = 2048

    local function sampleNextTargetPass()
        for attempts = 1, 30 do
            local res = adapter.samplePerception(f.npc)
            if res and res.results and #res.results > 0 then
                return res
            end
        end
        error('timed out waiting for target square to be sampled')
    end

    -- 1. Pass 1: initial read of target square (reads first 16 of 20 objects)
    local res1 = sampleNextTargetPass()
    assert(#res1.results == 16, 'first pass must read 16 candidates')
    local id_first_pass1 = res1.results[1].id
    local tok1 = adapter.snapshots['12,20,0'].token
    assert(type(tok1) == 'string' and #tok1 <= 96, 'valid snapshot token recorded')

    -- 2. Pass 2 (Unchanged-list fairness): target square visited again with identical objects
    local res2 = sampleNextTargetPass()
    local tok2 = adapter.snapshots['12,20,0'].token
    assert(tok2 == tok1, 'unchanged list retains stable token across sample calls')
    assert(#res2.results == 16, 'second pass must read 16 candidates')
    -- Cursor resumed at index 16 (fairness, no starvation of later candidates)
    local id_first_pass2 = res2.results[1].id
    assert(id_first_pass2 ~= id_first_pass1, 'cursor fairness must resume at index 16 without restarting')

    -- 3. Pass 3 (Same-size replacement/reordering): replace 20 objects with 20 new objects
    local list2 = {}
    for i = 1, 20 do
        list2[i] = makeZombie(300 + i, 12.0, 20.0)
    end
    currentList = list2
    local res3 = sampleNextTargetPass()
    local tok3 = adapter.snapshots['12,20,0'].token
    assert(tok3 ~= tok1, 'same-size replacement must allocate new nonreused token')
    assert(#res3.results == 16, 'third pass must read 16 candidates')
    -- Cursor was reset to 0 because token changed
    local id_first_pass3 = res3.results[1].id
    assert(id_first_pass3 ~= id_first_pass2, 'replacement list starts from beginning')

    -- 4. Pass 4 (Tail changes): keep items 1..19, change only element 20 (index 19)
    local list3 = {}
    for i = 1, 19 do list3[i] = list2[i] end
    list3[20] = makeZombie(9999, 12.0, 20.0)
    currentList = list3
    local res4 = sampleNextTargetPass()
    local tok4 = adapter.snapshots['12,20,0'].token
    assert(tok4 ~= tok3 and tok4 ~= tok1, 'tail change must allocate new nonreused token')

    -- 5. Pass 5 (Lifecycle reset): clears snapshot storage and resets cursors
    adapter.resetPerception()
    assert(next(adapter.snapshots) == nil, 'adapter.snapshots must be cleared on resetPerception')
    assert(#adapter.snapshotFIFO == 0, 'adapter.snapshotFIFO must be cleared on resetPerception')

    local res5 = sampleNextTargetPass()
    local tok5 = adapter.snapshots['12,20,0'].token
    assert(tok5 ~= tok4 and tok5 ~= tok3 and tok5 ~= tok1, 'post-reset token must be nonreused')
    assert(#res5.results == 16, 'post-reset sample reads 16 candidates')

    -- 6. Bounded snapshot storage verification
    local capturedApi = nil
    local origSample = adapter.diagnosticSampler.sample
    adapter.diagnosticSampler.sample = function(self, api)
        capturedApi = api
        return origSample(self, api)
    end
    adapter.samplePerception(f.npc)
    adapter.diagnosticSampler.sample = origSample

    assert(capturedApi ~= nil, 'captured api must be available')
    local dummyZombie = makeZombie(5555, 12.0, 20.0)
    local dummyList = {
        size = function() return 1 end,
        get = function(self, idx) return dummyZombie end,
    }
    -- Fill up beyond 128 snapshots
    for i = 1, 135 do
        local sq = {
            getX = function() return 200 + i end,
            getY = function() return 300 end,
            getZ = function() return 0 end,
            getMovingObjects = function() return dummyList end,
        }
        capturedApi.nativeReads = 0
        capturedApi.listInfo(sq)
    end
    assert(#adapter.snapshotFIFO <= 128, 'snapshotFIFO must be capped at 128')
    assert(adapter.snapshots['201,300,0'] == nil, 'oldest snapshot must be evicted when bounded limit exceeded')
    assert(adapter.snapshots['335,300,0'] ~= nil, 'newest snapshot must be retained')

    getCell = oldGetCell
end)
test('Perception read budget: charging before invocation bounds actual getter attempts under repeated late exceptions and nil returns', function()
    local f = fixture()
    local adapter = f.adapter
    adapter.ensurePerceptionModules()

    f.npc.getForwardDirectionX = function() return 1.0 end
    f.npc.getForwardDirectionY = function() return 0.0 end
    f.npc.getX = function() return 10.0 end
    f.npc.getY = function() return 20.0 end
    f.npc.getZ = function() return 0.0 end

    local origSample = adapter.diagnosticSampler.sample
    local capturedApi = nil
    adapter.diagnosticSampler.sample = function(self, api)
        capturedApi = api
        return origSample(self, api)
    end
    adapter.samplePerception(f.npc)
    adapter.diagnosticSampler.sample = origSample
    assert(capturedApi ~= nil, 'captured api must be available')

    -- Case 1: 64-entry lists whose final getter (idx 63) throws
    -- With readBudget = 512, previous code allowed 4,032 getter attempts across 63 listInfo calls.
    -- With pre-charging, exactly 512 attempts must be made across the 63 calls.
    capturedApi.nativeReads = 0
    adapter.readBudget = 512
    local actualGetterAttempts = 0
    local throwingList = {
        size = function() return 64 end,
        get = function(self, idx)
            actualGetterAttempts = actualGetterAttempts + 1
            if idx == 63 then
                error('simulated late getter exception at index 63')
            end
            return { isZombie = function() return true end, isDead = function() return false end }
        end,
    }
    for i = 1, 63 do
        local sq = {
            getX = function() return 1000 + i end,
            getY = function() return 2000 end,
            getZ = function() return 0 end,
            getMovingObjects = function() return throwingList end,
        }
        local ok, err = pcall(capturedApi.listInfo, sq)
        assert(not ok, 'listInfo must fail closed on element read error')
    end
    assert(actualGetterAttempts == 512, 'getter attempts must be bounded to readBudget (got ' .. actualGetterAttempts .. ', expected 512)')
    assert(capturedApi.nativeReads == 512, 'nativeReads must equal readBudget (512)')

    -- Case 2: 64-entry lists whose final getter (idx 63) returns nil
    capturedApi.nativeReads = 0
    actualGetterAttempts = 0
    local nilReturningList = {
        size = function() return 64 end,
        get = function(self, idx)
            actualGetterAttempts = actualGetterAttempts + 1
            if idx == 63 then
                return nil
            end
            return { isZombie = function() return true end, isDead = function() return false end }
        end,
    }
    for i = 1, 63 do
        local sq = {
            getX = function() return 3000 + i end,
            getY = function() return 4000 end,
            getZ = function() return 0 end,
            getMovingObjects = function() return nilReturningList end,
        }
        local ok, err = pcall(capturedApi.listInfo, sq)
        assert(not ok, 'listInfo must fail closed on nil element return')
    end
    assert(actualGetterAttempts == 512, 'nil return getter attempts must be bounded to readBudget (got ' .. actualGetterAttempts .. ', expected 512)')
    assert(capturedApi.nativeReads == 512, 'nativeReads must equal readBudget (512)')

    -- Case 3: Arbitrary budget boundary (readBudget = 100) stops exactly at budget
    capturedApi.nativeReads = 0
    adapter.readBudget = 100
    actualGetterAttempts = 0
    for i = 1, 63 do
        local sq = {
            getX = function() return 5000 + i end,
            getY = function() return 6000 end,
            getZ = function() return 0 end,
            getMovingObjects = function() return throwingList end,
        }
        local ok, err = pcall(capturedApi.listInfo, sq)
        assert(not ok, 'listInfo must fail closed')
    end
    assert(actualGetterAttempts == 100, 'getter attempts must stop exactly at budget 100 (got ' .. actualGetterAttempts .. ')')
    assert(capturedApi.nativeReads == 100, 'nativeReads must equal budget 100')

    adapter.readBudget = nil
end)
test('Integrated Engine / DiagnosticSampler / CandidateCollector full samplePerception bounds actual getter attempts under late exceptions and nil returns', function()
    local f = fixture()
    local adapter = f.adapter
    adapter.ensurePerceptionModules()

    local oldGetCell = getCell
    local actualGetterCalls = 0
    local shouldThrow = true

    local mockHostileList = {
        size = function() return 64 end,
        get = function(self, idx)
            actualGetterCalls = actualGetterCalls + 1
            if idx == 63 then
                if shouldThrow then
                    error('hostile late getter failure at index 63')
                else
                    return nil
                end
            end
            return {
                isZombie = function() return true end,
                isDead = function() return false end,
                isAlive = function() return true end,
                getX = function() return 10.0 end,
                getY = function() return 20.0 end,
                getZ = function() return 0.0 end,
            }
        end,
    }

    local mockCell = {
        getGridSquare = function(self, x, y, z)
            return {
                getX = function() return x end,
                getY = function() return y end,
                getZ = function() return z end,
                getMovingObjects = function() return mockHostileList end,
            }
        end,
        getObjectList = function() return { contains = function() return true end } end,
        getAddList = function() return { contains = function() return false end } end,
        getRemoveList = function() return { contains = function() return false end } end,
    }
    getCell = function() return mockCell end

    f.npc.getForwardDirectionX = function() return 1.0 end
    f.npc.getForwardDirectionY = function() return 0.0 end
    f.npc.getX = function() return 10.0 end
    f.npc.getY = function() return 20.0 end
    f.npc.getZ = function() return 0.0 end

    -- Run 1: Late exceptions with readBudget = 512
    adapter.readBudget = 512
    actualGetterCalls = 0
    shouldThrow = true
    local out1 = adapter.samplePerception(f.npc)
    assert(out1 ~= nil, 'samplePerception must return result')
    assert(actualGetterCalls == 512, 'integrated sweep must stop at readBudget=512 (got ' .. actualGetterCalls .. ')')

    -- Run 2: Late nil returns with readBudget = 512
    actualGetterCalls = 0
    shouldThrow = false
    local out2 = adapter.samplePerception(f.npc)
    assert(out2 ~= nil, 'samplePerception must return result')
    assert(actualGetterCalls == 512, 'integrated sweep with nil returns must stop at readBudget=512 (got ' .. actualGetterCalls .. ')')

    adapter.readBudget = nil
    getCell = oldGetCell
end)
print('RESULT '..count..' total engine adapter checks passed')
''')
