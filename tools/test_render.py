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
print('RESULT '..count..' total engine adapter checks passed')
''')
