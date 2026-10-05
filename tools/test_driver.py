"""Offline automated tests for FoundationWalkStopDriver."""
from pathlib import Path
import sys

root = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(root / 'tools/dependencies/python'))
from lupa import LuaRuntime

lua = LuaRuntime(unpack_returned_tuples=True)
source = root / 'foundation/SarahFoundation/42/media/lua/client/Sarah'
lua.globals().CommandsSource = (source / 'Commands.lua').read_text()
lua.globals().DriverSource = (root / 'tools/FoundationWalkStopDriver.lua').read_text()

lua.execute(r'''
local count = 0
local function test(name, fn)
    fn()
    count = count + 1
    print('PASS ' .. name)
end

local function makeEvent()
    local e = {callbacks = {}}
    e.Add = function(fn) e.callbacks[#e.callbacks + 1] = fn end
    e.Remove = function(fn)
        for i = #e.callbacks, 1, -1 do
            if e.callbacks[i] == fn then
                table.remove(e.callbacks, i)
            end
        end
    end
    return e
end

Events = {
    OnTick = makeEvent(),
    OnGameStart = makeEvent(),
    OnMainMenuEnter = makeEvent(),
    OnFillWorldObjectContextMenu = makeEvent()
}

local Base = {}
function Base:derive(name)
    local c = {}
    c.__index = c
    return setmetatable(c, {__index = self})
end
function Base:new(x, y, w, h)
    return setmetatable({x = x, y = y, width = w, height = h, children = {}, visible = true}, {__index = self})
end
for _, name in ipairs({'initialise', 'addToUIManager', 'removeFromUIManager', 'drawRect', 'drawRectBorder', 'drawText'}) do
    Base[name] = function() end
end
function Base:addChild(c)
    self.children[#self.children + 1] = c
end
function Base:setVisible(v)
    self.visible = v
end

ISPanel = Base:derive('ISPanel')
ISButton = Base:derive('ISButton')
function ISButton:new(x, y, w, h, title, target, onClick)
    local o = Base.new(self, x, y, w, h)
    o.title = title
    o.target = target
    o.onClick = onClick
    return o
end
function ISButton:click()
    if self.onClick then
        if self.target then
            self.onClick(self.target, self)
        else
            self.onClick(self)
        end
    end
end

require = function(n)
    if n == 'ISUI/ISPanel' then return ISPanel end
    if n == 'ISUI/ISButton' then return ISButton end
end

UIFont = {Small = 1, Medium = 2}

local isolatedRoot = 'G:/Codex/Project Sarah/runtime/isolated'
local currentRoot = isolatedRoot
local currentWorld = 'SarahConsoleNativeCase'
local isClientMode = false
local isServerMode = false
local specificPlayer = {x = 12, y = 20, z = 0}

Core = {
    getMyDocumentFolder = function() return currentRoot end
}
getWorld = function()
    return {
        getWorld = function() return currentWorld end
    }
end
isClient = function() return isClientMode end
isServer = function() return isServerMode end
getSpecificPlayer = function(idx)
    if idx == 0 then return specificPlayer end
    return nil
end

local Commands = assert(load(CommandsSource))()
local currentSarah = {x = 10, y = 20, z = 0}
local currentCtrl = {npc = currentSarah}
local lastWalkSuccessCb = nil
local lastWalkFailCb = nil
local lastStoppedNpc = nil

local function resetDispatch()
    lastWalkSuccessCb = nil
    lastWalkFailCb = nil
    lastStoppedNpc = nil
    local dispatch = Commands.new(function(inventory)
        return {
            state = 'active',
            npc = {x = currentSarah.x, y = currentSarah.y, z = currentSarah.z},
            player = {x = specificPlayer.x, y = specificPlayer.y, z = specificPlayer.z}
        }
    end, function(reason, action)
        lastStoppedNpc = action and action.npc or currentCtrl.npc
        return true
    end, function()
        return currentCtrl, currentCtrl.npc
    end, function(target, onComplete, onFail, action)
        lastWalkSuccessCb = onComplete
        lastWalkFailCb = onFail
        return true
    end)
    SarahConsole = {
        getDispatch = function() return dispatch end
    }
    return dispatch
end

local function loadDriver()
    return assert(load(DriverSource))()
end

test('driver refuses outside exact isolated profile or world', function()
    local d = loadDriver()
    assert(d.allowed() == true)

    currentRoot = 'C:/Users/Someone/Zomboid'
    assert(d.allowed() == false)
    currentRoot = isolatedRoot

    currentWorld = 'Survival'
    assert(d.allowed() == false)
    currentWorld = 'SarahConsoleNativeCase'

    isClientMode = true
    assert(d.allowed() == false)
    isClientMode = false

    local oldPlayer = specificPlayer
    specificPlayer = nil
    assert(d.allowed() == false)
    specificPlayer = oldPlayer
    assert(d.allowed() == true)
end)

test('driver panel initialization creates mouse buttons and starts in idle state without executing commands', function()
    local dispatch = resetDispatch()
    local d = loadDriver()
    local panel = d.init(20, 200)
    assert(panel ~= nil)
    assert(#panel.children == 5) -- 4 action buttons + close
    assert(d.getPhase() == 'IDLE')
    assert(d.isTestRunning() == false)
    assert(dispatch.sequence == 0)
    assert(dispatch.active == nil)
    d.teardown()
end)

test('status and history button executes status and history through real dispatch and logs concise outcomes', function()
    local dispatch = resetDispatch()
    local d = loadDriver()
    d.init()
    d.onStatusHistory()
    assert(dispatch.sequence == 2) -- status is #1, history is #2
    local h = dispatch:getHistory()
    assert(#h == 2)
    assert(h[1].command == 'status' and h[1].state == 'completed')
    assert(h[2].command == 'history' and h[2].state == 'completed')
    assert(d.getPhase() == 'IDLE')
    d.teardown()
end)

test('walk button dispatches walk here to player position, records observed start/target, and transitions state', function()
    currentSarah.x, currentSarah.y, currentSarah.z = 10, 20, 0
    specificPlayer.x, specificPlayer.y, specificPlayer.z = 12, 20, 0
    local dispatch = resetDispatch()
    local d = loadDriver()
    d.init()
    d.onWalk()
    assert(dispatch.active ~= nil and dispatch.active.command == 'walk here')
    assert(dispatch.active.id == 1 and dispatch.active.state == 'running')
    assert(d.getPhase() == 'MONITOR_WALK')

    -- Simulate arrival
    currentSarah.x, currentSarah.y = 12, 20
    assert(lastWalkSuccessCb ~= nil)
    lastWalkSuccessCb()
    assert(dispatch.active == nil)
    assert(dispatch.lastAction.state == 'completed')

    -- Driver tick detects walk finished and returns to idle
    d.tick()
    assert(d.getPhase() == 'IDLE')
    d.teardown()
end)

test('walk-then-stop verifies observable movement before issuing stop and confirms mid-walk cancellation', function()
    currentSarah.x, currentSarah.y, currentSarah.z = 10, 20, 0
    specificPlayer.x, specificPlayer.y, specificPlayer.z = 15, 20, 0
    local dispatch = resetDispatch()
    local d = loadDriver()
    d.init()

    d.onWalkThenStop()
    assert(d.getPhase() == 'WAIT_MOVEMENT')
    assert(d.isTestRunning() == true)
    assert(dispatch.active ~= nil and dispatch.active.command == 'walk here')

    -- Tick 1: stationary -> no movement observed yet (< 0.2 tiles)
    d.tick()
    assert(d.getPhase() == 'WAIT_MOVEMENT')
    assert(dispatch.active ~= nil)

    -- Tick 2: small movement (0.1 tiles) -> still < 0.2 tiles
    currentSarah.x = 10.1
    d.tick()
    assert(d.getPhase() == 'WAIT_MOVEMENT')
    assert(dispatch.active ~= nil)

    -- Tick 3: moved 0.3 tiles (>= 0.2 tiles) -> movement verified! Stop issued!
    currentSarah.x = 10.3
    d.tick()
    assert(d.getPhase() == 'WAIT_HALT')
    assert(dispatch.active == nil)
    assert(dispatch.lastAction.state == 'cancelled')
    assert(lastStoppedNpc ~= nil)

    -- Settle halt over 5 ticks
    for i = 1, 5 do d.tick() end
    assert(d.getPhase() == 'IDLE')
    assert(d.getLastResult() == 'PASS')
    assert(d.isTestRunning() == false)
    d.teardown()
end)

test('walk-then-stop reports invalid early arrival if Sarah reaches target square before movement threshold can be stopped', function()
    currentSarah.x, currentSarah.y, currentSarah.z = 10, 20, 0
    specificPlayer.x, specificPlayer.y, specificPlayer.z = 11, 20, 0
    local dispatch = resetDispatch()
    local d = loadDriver()
    d.init()

    d.onWalkThenStop()
    assert(d.getPhase() == 'WAIT_MOVEMENT')

    -- On first tick, Sarah immediately arrives at target square (11, 20, 0)
    currentSarah.x = 11.0
    d.tick()
    assert(d.getPhase() == 'IDLE')
    assert(d.getLastResult() == 'INVALID')
    assert(d.isTestRunning() == false)
    d.teardown()
end)

test('walk-then-stop handles timeout if Sarah fails to move within bounded tick limit', function()
    currentSarah.x, currentSarah.y, currentSarah.z = 10, 20, 0
    specificPlayer.x, specificPlayer.y, specificPlayer.z = 15, 20, 0
    local dispatch = resetDispatch()
    local d = loadDriver()
    d.init()

    d.onWalkThenStop()
    assert(d.getPhase() == 'WAIT_MOVEMENT')

    -- Tick 180 times with Sarah stationary
    for i = 1, 180 do d.tick() end
    assert(d.getPhase() == 'IDLE')
    assert(d.getLastResult() == 'TIMEOUT')
    assert(dispatch.active == nil)
    d.teardown()
end)

test('driver refuses overlapping test runs while walk-then-stop is in progress', function()
    currentSarah.x, currentSarah.y, currentSarah.z = 10, 20, 0
    specificPlayer.x, specificPlayer.y, specificPlayer.z = 15, 20, 0
    local dispatch = resetDispatch()
    local d = loadDriver()
    d.init()

    d.onWalkThenStop()
    assert(d.getPhase() == 'WAIT_MOVEMENT')

    -- Attempt overlapping calls
    d.onWalkThenStop()
    d.onWalk()
    d.onStatusHistory()

    -- State remains cleanly in WAIT_MOVEMENT for the original walk
    assert(d.getPhase() == 'WAIT_MOVEMENT')
    assert(dispatch.sequence == 1) -- Only the single walk command was run
    d.teardown()
end)

test('subsequent walk request succeeds after mid-walk cancellation', function()
    currentSarah.x, currentSarah.y, currentSarah.z = 10, 20, 0
    specificPlayer.x, specificPlayer.y, specificPlayer.z = 15, 20, 0
    local dispatch = resetDispatch()
    local d = loadDriver()
    d.init()

    -- 1. Perform walk-then-stop
    d.onWalkThenStop()
    currentSarah.x = 10.4 -- Moved 0.4 tiles
    d.tick() -- Movement observed, stop issued
    for i = 1, 5 do d.tick() end -- Settle halt
    assert(d.getLastResult() == 'PASS')
    assert(d.getPhase() == 'IDLE')

    -- 2. Reposition player and start another walk
    specificPlayer.x, specificPlayer.y, specificPlayer.z = 12, 22, 0
    d.onWalk()
    assert(dispatch.active ~= nil and dispatch.active.command == 'walk here')
    assert(dispatch.active.state == 'running')
    assert(dispatch.active.details.targetX == 12 and dispatch.active.details.targetY == 22)
    assert(d.getPhase() == 'MONITOR_WALK')
    d.teardown()
end)

test('session teardown removes UI panel, resets state, and rejects stale callbacks', function()
    currentSarah.x, currentSarah.y, currentSarah.z = 10, 20, 0
    specificPlayer.x, specificPlayer.y, specificPlayer.z = 15, 20, 0
    local dispatch = resetDispatch()
    local d = loadDriver()
    local panel = d.init()
    assert(d.getPanel() == panel)

    d.onWalkThenStop()
    assert(d.getPhase() == 'WAIT_MOVEMENT')

    -- Trigger teardown
    d.teardown()
    assert(d.getPanel() == nil)
    assert(d.getPhase() == 'IDLE')
    assert(d.isTestRunning() == false)

    -- Ticking now does not advance previous run
    d.tick()
    assert(d.getPhase() == 'IDLE')
end)

print('RESULT ' .. count .. ' driver tests passed')
''')
