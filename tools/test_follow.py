"""Automated offline tests for Sarah's manual follow-player behavior.

Executes actual Lua against simulated fixtures using Lupa.
Covers command parsing, inner deadzone, adjacent targeting, leash limit,
floor change, lifecycle invalidation, stop cancellation mid-stride,
stop failure blocking, step timeout, path failure, and session reset.
"""
from pathlib import Path
import sys

root = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(root / "tools/dependencies/python"))
from lupa import LuaRuntime

lua = LuaRuntime(unpack_returned_tuples=True)
for name in ("Commands", "Observations"):
    lua.globals()[name] = lua.execute(
        (root / f"foundation/SarahFoundation/42/media/lua/client/Sarah/{name}.lua").read_text()
    )

lua.execute(r'''
local count = 0
local function test(name, fn)
    fn()
    count = count + 1
    print('PASS ' .. name)
end

local function makeFixture(opts)
    opts = opts or {}
    local npcPos = opts.npcPos or {x = 10, y = 10, z = 0}
    local playerPos = opts.playerPos or {x = 11, y = 10, z = 0}
    local npcState = opts.npcState or 'active'
    local npcObj = opts.npcObj or {
        getX = function() return npcPos.x end,
        getY = function() return npcPos.y end,
        getZ = function() return npcPos.z end,
        getInventory = function()
            local items = {
                size = function() return 1 end,
                get = function(_, i) return {getFullType = function() return 'Base.Bandage' end} end
            }
            return {getItems = function() return items end}
        end
    }
    local adapter = {
        meta = {},
        listNPCs = function() return {npcObj} end,
        isDead = function() return npcState == 'dead' end,
        isResident = function() return npcState ~= 'nonresident' end,
        isIncomplete = function() return npcState == 'incomplete' end,
        validateTarget = function(n, target)
            if opts.validateFail then return false, 'blocked' end
            if opts.invalidTargets and opts.invalidTargets[target.x .. ',' .. target.y] then
                return false, 'blocked'
            end
            if target.z ~= npcPos.z then return false, 'different floor' end
            local dx = target.x + 0.5 - npcPos.x
            local dy = target.y + 0.5 - npcPos.y
            if dx * dx + dy * dy > 64.0 then return false, 'too far' end
            return true, {x = target.x, y = target.y, z = target.z}
        end,
        walk = function(n, target, onComplete, onFail)
            if opts.walkFail then return false, 'walk start failed' end
            return true
        end,
        stop = function(n)
            if opts.stopFail then return false, 'stop failed' end
            return true
        end
    }
    local controller = {npc = npcObj, adapter = adapter}

    local observe = function(inv)
        if npcState ~= 'active' then
            return {state = npcState, inventory = nil}
        end
        local dead = (opts.playerDead == true) or (playerPos.dead == true) or (playerPos.isDead == true)
        return {
            state = 'active',
            npc = {x = npcPos.x, y = npcPos.y, z = npcPos.z},
            player = {
                x = playerPos.x, y = playerPos.y, z = playerPos.z,
                dead = dead,
                isDead = dead,
                alive = not dead
            },
            playerDead = dead,
            playerAlive = not dead,
            inventory = inv and {total = 1, items = {{type = 'Base.Bandage', count = 1}}} or nil
        }
    end

    return {
        controller = controller,
        npc = npcObj,
        adapter = adapter,
        npcPos = npcPos,
        playerPos = playerPos,
        observe = observe,
        identityProvider = function() return controller, npcObj end
    }
end

-- 1. Help listing and command recognition
test('follow command is documented in help and parsed cleanly', function()
    local f = makeFixture()
    local d = Commands.new(f.observe, nil, f.identityProvider)
    local h = d:execute('help')
    assert(h.state == 'completed')
    local found = false
    for _, l in ipairs(h.lines) do
        if l:find('follow') then found = true end
    end
    assert(found, 'follow missing from help output')

    local res = d:execute('   FOLLOW   ')
    assert(res.state == 'running')
    assert(d.active and d.active.command == 'follow')
end)

-- 2. Busy rejection when another action is running
test('follow is rejected when walk here is already running', function()
    local f = makeFixture({npcPos = {x = 10, y = 10, z = 0}, playerPos = {x = 14, y = 10, z = 0}})
    local d = Commands.new(f.observe, nil, f.identityProvider, function() return true end)
    local r1 = d:execute('walk here')
    assert(r1.state == 'running')
    assert(d.active and d.active.command == 'walk here')

    local r2 = d:execute('follow')
    assert(r2.state == 'rejected')
    assert(r2.lines[1]:find('busy'))
    assert(d.active.command == 'walk here')
end)

-- 3. Busy rejection when follow is already running
test('follow is rejected when another follow is already running', function()
    local f = makeFixture()
    local d = Commands.new(f.observe, nil, f.identityProvider)
    local r1 = d:execute('follow')
    assert(r1.state == 'running')

    local r2 = d:execute('follow')
    assert(r2.state == 'rejected')
    assert(r2.lines[1]:find('busy'))
    assert(d.active.id == 1)
end)

-- 4. Rejection on inactive Sarah (dead, unloaded, etc.)
test('follow is rejected when Sarah is dead or unloaded', function()
    local f = makeFixture({npcState = 'dead'})
    local d = Commands.new(f.observe, nil, f.identityProvider)
    local res = d:execute('follow')
    assert(res.state == 'rejected')
    assert(res.lines[1]:find('dead'))
    assert(d.active == nil)

    local f2 = makeFixture({npcState = 'unloaded'})
    local d2 = Commands.new(f2.observe, nil, f2.identityProvider)
    local res2 = d2:execute('follow')
    assert(res2.state == 'rejected')
    assert(res2.lines[1]:find('unloaded'))
    assert(d2.active == nil)
end)

-- 5. Rejection when coordinates unavailable
test('follow is rejected when coordinates are unavailable', function()
    local d = Commands.new(function() return {state = 'active'} end)
    local res = d:execute('follow')
    assert(res.state == 'rejected')
    assert(res.lines[1]:find('unavailable'))
    assert(d.active == nil)
end)

-- 6. Rejection when player is on different floor
test('follow is rejected when player is on a different floor', function()
    local f = makeFixture({npcPos = {x = 10, y = 10, z = 0}, playerPos = {x = 10, y = 10, z = 1}})
    local d = Commands.new(f.observe, nil, f.identityProvider)
    local res = d:execute('follow')
    assert(res.state == 'rejected')
    assert(res.lines[1]:find('different floor'))
    assert(d.active == nil)
end)

-- 7. Rejection when player is beyond initial 8-tile leash
test('follow is rejected when player is too far (> 8 tiles)', function()
    local f = makeFixture({npcPos = {x = 10, y = 10, z = 0}, playerPos = {x = 19, y = 10, z = 0}})
    local d = Commands.new(f.observe, nil, f.identityProvider)
    local res = d:execute('follow')
    assert(res.state == 'rejected')
    assert(res.lines[1]:find('too far'))
    assert(d.active == nil)
end)

-- 8. Inner deadzone (<= 2 tiles) leaves Sarah idle in follow mode
test('follow within 2-tile inner deadzone starts idle and does not walk', function()
    local f = makeFixture({npcPos = {x = 10, y = 10, z = 0}, playerPos = {x = 11, y = 10, z = 0}})
    local walked = false
    local d = Commands.new(f.observe, nil, f.identityProvider, function() walked = true; return true end)
    local res = d:execute('follow')
    assert(res.state == 'running')
    assert(res.lines[1]:find('already within 2 tiles'))
    assert(walked == false, 'walk should not be dispatched in inner deadzone')
    assert(d.active and d.active.command == 'follow')
    assert(d.active.stepState == 'idle')
    local h = d:getHistory()
    assert(#h == 1 and h[1].summary:find('in range'))
end)

-- 9. Repath beyond 2 tiles dispatches walk step to adjacent square
test('follow beyond 2 tiles dispatches walk to validated adjacent square', function()
    local f = makeFixture({npcPos = {x = 10, y = 10, z = 0}, playerPos = {x = 14, y = 10, z = 0}})
    local targetWalked = nil
    local d = Commands.new(f.observe, nil, f.identityProvider, function(target)
        targetWalked = target
        return true
    end)
    local res = d:execute('follow')
    assert(res.state == 'running')
    assert(targetWalked ~= nil)
    -- Player is at (14, 10). Closest adjacent square to Sarah (10, 10) is (13, 10).
    assert(targetWalked.x == 13 and targetWalked.y == 10 and targetWalked.z == 0)
    assert(d.active.stepState == 'walking')
    assert(d.active.currentTarget.x == 13)
end)

-- 10. Candidate sorting selects closest open square when some are blocked
test('adjacent candidate sorting falls back to next closest when nearest is blocked', function()
    local blocked = {['13,10'] = true} -- nearest tile blocked
    local f = makeFixture({
        npcPos = {x = 10, y = 10, z = 0},
        playerPos = {x = 14, y = 10, z = 0},
        invalidTargets = blocked
    })
    local targetWalked = nil
    local d = Commands.new(f.observe, nil, f.identityProvider, function(target)
        targetWalked = target
        return true
    end)
    local res = d:execute('follow')
    assert(res.state == 'running')
    assert(targetWalked ~= nil)
    assert(targetWalked.x ~= 13 or targetWalked.y ~= 10)
    -- Next closest diagonals: (13, 11) or (13, 9)
    assert(targetWalked.x == 13 and (targetWalked.y == 9 or targetWalked.y == 11))
end)

-- 11. Clean failure when all adjacent candidate squares are blocked
test('follow fails cleanly when no adjacent square near player is valid', function()
    local f = makeFixture({
        npcPos = {x = 10, y = 10, z = 0},
        playerPos = {x = 14, y = 10, z = 0},
        validateFail = true
    })
    local d = Commands.new(f.observe, nil, f.identityProvider, function() return true end)
    local res = d:execute('follow')
    assert(res.state == 'failed')
    assert(res.lines[1]:find('no valid target'))
    assert(d.active == nil)
    local h = d:getHistory()
    assert(#h == 1 and h[1].state == 'cancelled' and h[1].summary:find('no valid target'))
end)

-- 12. Read-only commands work during active follow
test('read-only commands execute without interrupting active follow', function()
    local f = makeFixture({npcPos = {x = 10, y = 10, z = 0}, playerPos = {x = 11, y = 10, z = 0}})
    local d = Commands.new(f.observe, nil, f.identityProvider)
    d:execute('follow')
    assert(d.active and d.active.command == 'follow')

    local st = d:execute('status')
    assert(st.state == 'completed')
    local hasFollow = false
    for _, l in ipairs(st.lines) do
        if l:find('follow %(running%)') then hasFollow = true end
    end
    assert(hasFollow, 'status should reflect active follow')
    assert(d.active and d.active.command == 'follow')

    local inv = d:execute('inventory')
    assert(inv.state == 'completed')
    assert(d.active and d.active.command == 'follow')

    local hist = d:execute('history')
    assert(hist.state == 'completed')
    assert(d.active and d.active.command == 'follow')
end)

-- 13. Repath on tick when player moves beyond deadzone
test('follow repaths on tick when player moves away', function()
    local f = makeFixture({npcPos = {x = 10, y = 10, z = 0}, playerPos = {x = 11, y = 10, z = 0}})
    local targetWalked = nil
    local d = Commands.new(f.observe, nil, f.identityProvider, function(target)
        targetWalked = target
        return true
    end)
    d:execute('follow')
    assert(d.active.stepState == 'idle')
    assert(targetWalked == nil)

    -- Player moves from (11, 10) to (14, 10)
    f.playerPos.x = 14
    d:tick()

    assert(targetWalked ~= nil)
    assert(targetWalked.x == 13 and targetWalked.y == 10)
    assert(d.active.stepState == 'walking')
end)

-- 14. Sequential steps, step completion, and cooldown throttling
test('step completion sets idle and cooldown throttles next dispatch', function()
    local f = makeFixture({npcPos = {x = 10, y = 10, z = 0}, playerPos = {x = 14, y = 10, z = 0}})
    local capturedComplete, capturedFail
    local walkCount = 0
    local d = Commands.new(f.observe, nil, f.identityProvider, function(target, onComplete, onFail)
        walkCount = walkCount + 1
        capturedComplete = onComplete
        capturedFail = onFail
        return true
    end)
    d:execute('follow')
    assert(walkCount == 1)
    assert(d.active.stepState == 'walking')

    -- Step arrives
    f.npcPos.x = 13
    capturedComplete()

    assert(d.active.stepState == 'idle')
    assert(d.active.cooldown == 15)

    -- Player moves further to (16, 10)
    f.playerPos.x = 16

    -- Tick during cooldown: should decrement without dispatching new walk
    d:tick()
    assert(walkCount == 1)
    assert(d.active.cooldown == 14)

    -- Run down remaining cooldown
    for _ = 1, 14 do d:tick() end
    assert(d.active.cooldown == 0)
    assert(walkCount == 1)

    -- Next tick dispatches subsequent walk
    d:tick()
    assert(walkCount == 2)
    assert(d.active.stepState == 'walking')
end)

-- 15. Leash limit (> 8 tiles) cancels follow immediately mid-stride
test('leash limit (> 8 tiles) cancels follow mid-stride and halts engine', function()
    local f = makeFixture({npcPos = {x = 10, y = 10, z = 0}, playerPos = {x = 14, y = 10, z = 0}})
    local stopped = false
    local d = Commands.new(f.observe, function() stopped = true; return true end, f.identityProvider, function() return true end)
    d:execute('follow')
    assert(d.active and d.active.stepState == 'walking')

    -- Player sprints to (20, 10) (> 8 tiles distance from Sarah at 10)
    f.playerPos.x = 20
    local ok, reason = d:tick()

    assert(ok == false)
    assert(reason:find('out of range'))
    assert(d.active == nil)
    assert(stopped == true)
    local h = d:getHistory()
    assert(h[#h].state == 'cancelled' and h[#h].summary:find('out of range'))
end)

-- 16. Floor change cancels follow mid-stride
test('floor change cancels follow mid-stride and halts engine', function()
    local f = makeFixture({npcPos = {x = 10, y = 10, z = 0}, playerPos = {x = 14, y = 10, z = 0}})
    local stopped = false
    local d = Commands.new(f.observe, function() stopped = true; return true end, f.identityProvider, function() return true end)
    d:execute('follow')
    assert(d.active and d.active.stepState == 'walking')

    -- Player climbs stairs to floor 1
    f.playerPos.z = 1
    local ok, reason = d:tick()

    assert(ok == false)
    assert(reason:find('floor'))
    assert(d.active == nil)
    assert(stopped == true)
end)

-- 17. Lifecycle invalidation on Sarah death or unload
test('Sarah death or unload invalidates follow immediately', function()
    local f = makeFixture({npcPos = {x = 10, y = 10, z = 0}, playerPos = {x = 11, y = 10, z = 0}})
    local d = Commands.new(f.observe, nil, f.identityProvider)
    d:execute('follow')
    assert(d.active ~= nil)

    -- Sarah dies
    f.controller.adapter.isDead = function() return true end
    -- observe returns dead
    local origObserve = f.observe
    f.observe = function(inv) return {state = 'dead'} end
    d.observe = f.observe

    local ok, reason = d:tick()
    assert(ok == false)
    assert(d.active == nil)
    assert(d.lastAction.reason == 'dead')
end)

-- 18. Controller replacement invalidates follow and leaves replacement untouched
test('controller replacement invalidates follow and leaves replacement untouched', function()
    local f = makeFixture({npcPos = {x = 10, y = 10, z = 0}, playerPos = {x = 11, y = 10, z = 0}})
    local currentCtrl = f.controller
    local d = Commands.new(f.observe, nil, function() return currentCtrl, f.npc end)
    d:execute('follow')
    assert(d.active ~= nil)

    -- Controller replaced
    local newCtrl = {npc = f.npc, adapter = f.adapter}
    currentCtrl = newCtrl

    local ok, reason = d:tick()
    assert(ok == false)
    assert(reason == 'controller replaced')
    assert(d.active == nil)
end)

-- 19. Stop command cancels follow mid-stride
test('stop command cancels follow mid-stride, halts engine, and records completed', function()
    local f = makeFixture({npcPos = {x = 10, y = 10, z = 0}, playerPos = {x = 14, y = 10, z = 0}})
    local stopReason = nil
    local d = Commands.new(f.observe, function(reason) stopReason = reason; return true end, f.identityProvider, function() return true end)
    d:execute('follow')
    assert(d.active and d.active.command == 'follow')

    local res = d:execute('stop')
    assert(res.state == 'completed')
    assert(res.lines[1]:find('Cancelled #1 %(follow%)'))
    assert(res.lines[2]:find('Sarah stopped'))
    assert(d.active == nil)
    assert(stopReason == 'stopped by user')
    local h = d:getHistory()
    assert(#h == 2 and h[2].command == 'stop' and h[2].state == 'completed')
end)

-- 20. Stop command cancels idle follow in deadzone
test('stop command cancels idle follow in deadzone', function()
    local f = makeFixture({npcPos = {x = 10, y = 10, z = 0}, playerPos = {x = 11, y = 10, z = 0}})
    local stopped = false
    local d = Commands.new(f.observe, function() stopped = true; return true end, f.identityProvider)
    d:execute('follow')
    assert(d.active and d.active.stepState == 'idle')

    local res = d:execute('stop')
    assert(res.state == 'completed')
    assert(d.active == nil)
    assert(stopped == true)
end)

-- 21. Stop failure blocks subsequent movement until stop recovers
test('stop failure sets stopFailed and blocks walk and follow until stop recovers', function()
    local f = makeFixture({npcPos = {x = 10, y = 10, z = 0}, playerPos = {x = 14, y = 10, z = 0}})
    local stopShouldFail = true
    local d = Commands.new(f.observe, function()
        if stopShouldFail then return false, 'engine error' end
        return true
    end, f.identityProvider, function() return true end)
    d:execute('follow')

    -- Stop fails
    local resStop = d:execute('stop')
    assert(resStop.state == 'failed')
    assert(resStop.lines[2]:find('Engine stop failed: engine error'))
    assert(d.stopFailed == 'engine error')

    -- Movement commands are blocked
    local resWalk = d:execute('walk here')
    assert(resWalk.state == 'rejected')
    assert(resWalk.lines[1]:find('movement blocked until stop recovers'))

    local resFollow = d:execute('follow')
    assert(resFollow.state == 'rejected')
    assert(resFollow.lines[1]:find('movement blocked until stop recovers'))

    -- Run stop again, now succeeding
    stopShouldFail = false
    local resStop2 = d:execute('stop')
    assert(resStop2.state == 'completed')
    assert(d.stopFailed == nil)

    -- Follow is allowed again
    local resFollow2 = d:execute('follow')
    assert(resFollow2.state == 'running')
    assert(d.active ~= nil)
end)

-- 22. Path failure on step cancels follow cleanly
test('engine path failure callback cancels follow cleanly', function()
    local f = makeFixture({npcPos = {x = 10, y = 10, z = 0}, playerPos = {x = 14, y = 10, z = 0}})
    local capturedFail = nil
    local d = Commands.new(f.observe, nil, f.identityProvider, function(target, onComplete, onFail)
        capturedFail = onFail
        return true
    end)
    d:execute('follow')
    assert(d.active and d.active.stepState == 'walking')

    capturedFail(nil, 'path blocked')
    assert(d.active == nil)
    local h = d:getHistory()
    assert(h[#h].state == 'cancelled' and h[#h].summary:find('path blocked'))
end)

-- 23. Step timeout cancels follow after 600 ticks
test('step timeout after 600 ticks cancels follow and halts engine', function()
    local f = makeFixture({npcPos = {x = 10, y = 10, z = 0}, playerPos = {x = 14, y = 10, z = 0}})
    local stopped = false
    local d = Commands.new(f.observe, function() stopped = true; return true end, f.identityProvider, function() return true end)
    d:execute('follow')
    assert(d.active and d.active.stepState == 'walking')

    for _ = 1, 599 do
        local ok = d:tick()
        assert(ok == true)
        assert(d.active ~= nil)
    end

    local ok, reason = d:tick()
    assert(ok == false)
    assert(reason == 'timeout')
    assert(d.active == nil)
    assert(stopped == true)
    local h = d:getHistory()
    assert(h[#h].state == 'cancelled' and h[#h].summary:find('timeout'))
end)

-- 24. Stale callbacks from superseded or cancelled steps are defused
test('stale callbacks from superseded steps cannot mutate active follow', function()
    local f = makeFixture({npcPos = {x = 10, y = 10, z = 0}, playerPos = {x = 14, y = 10, z = 0}})
    local cb1_complete, cb1_fail
    local cb2_complete
    local step = 0
    local d = Commands.new(f.observe, nil, f.identityProvider, function(target, onComplete, onFail)
        step = step + 1
        if step == 1 then
            cb1_complete = onComplete
            cb1_fail = onFail
        else
            cb2_complete = onComplete
        end
        return true
    end)
    d:execute('follow')
    assert(step == 1)

    -- Step 1 completes normally
    cb1_complete()
    assert(d.active.stepState == 'idle')
    d.active.cooldown = 0

    -- Player moves, dispatching Step 2
    f.playerPos.x = 15
    d:tick()
    assert(step == 2)
    assert(d.active.stepState == 'walking')
    assert(d.active.stepGen == 3)

    -- Late cb1_fail from Step 1 fires: must be ignored by stepGen guard and retirement flag
    cb1_fail(nil, 'late failure')
    assert(d.active ~= nil and d.active.stepGen == 3 and d.active.stepState == 'walking')

    -- Late cb1_complete from Step 1 fires: must be ignored
    cb1_complete()
    assert(d.active ~= nil and d.active.stepGen == 3 and d.active.stepState == 'walking')

    -- Current Step 2 completion works
    cb2_complete()
    assert(d.active ~= nil and d.active.stepState == 'idle' and d.active.stepGen == 4)
end)

-- 25. Synchronous step completion during start is handled safely
test('synchronous step completion during follow start is handled safely', function()
    local f = makeFixture({npcPos = {x = 10, y = 10, z = 0}, playerPos = {x = 14, y = 10, z = 0}})
    local d = Commands.new(f.observe, nil, f.identityProvider, function(target, onComplete)
        onComplete()
        return true
    end)
    local res = d:execute('follow')
    assert(res.state == 'running')
    assert(d.active ~= nil)
    assert(d.active.stepState == 'idle')
end)

-- 26. Synchronous step failure during start is handled safely
test('synchronous step failure during follow start is handled safely', function()
    local f = makeFixture({npcPos = {x = 10, y = 10, z = 0}, playerPos = {x = 14, y = 10, z = 0}})
    local d = Commands.new(f.observe, nil, f.identityProvider, function(target, onComplete, onFail)
        onFail(nil, 'immediate obstacle')
        return true
    end)
    local res = d:execute('follow')
    assert(res.state == 'failed')
    assert(d.active == nil)
    local h = d:getHistory()
    assert(#h == 1 and h[1].state == 'cancelled' and h[1].summary:find('immediate obstacle'))
end)

-- 27. Session reset cancels follow, increments session, resets sequence
test('session reset clears active follow and resets sequence counter', function()
    local f = makeFixture({npcPos = {x = 10, y = 10, z = 0}, playerPos = {x = 14, y = 10, z = 0}})
    local stopped = false
    local capturedComplete
    local d = Commands.new(f.observe, function() stopped = true; return true end, f.identityProvider, function(target, onComplete)
        capturedComplete = onComplete
        return true
    end)
    d:execute('follow')
    assert(d.active ~= nil and d.active.id == 1)
    local token1 = d.active.token

    d:reset()
    assert(d.active == nil)
    assert(d.sequence == 0)
    assert(#d:getHistory() == 0)
    assert(stopped == true)

    -- Late completion from session 1 cannot resurrect or affect state
    capturedComplete()
    assert(d.active == nil)

    -- New session starts with sequence #1 and different token
    d:execute('follow')
    assert(d.active ~= nil and d.active.id == 1)
    assert(d.active.token ~= token1)
    assert(d.active.session == 2)
end)

-- 28. requestFollow convenience method
test('requestFollow programmatic method executes follow command directly', function()
    local f = makeFixture()
    local d = Commands.new(f.observe, nil, f.identityProvider)
    local res = d:requestFollow()
    assert(res.state == 'running')
    assert(d.active and d.active.command == 'follow')
end)

-- 29. Follow activation is rejected when player is dead
test('follow activation is rejected when player is dead', function()
    local f = makeFixture({playerDead = true})
    local d = Commands.new(f.observe, nil, f.identityProvider)
    local res = d:execute('follow')
    assert(res.state == 'rejected')
    assert(res.lines[1] == 'Player is dead; cannot follow.')
    assert(d.active == nil)
    local h = d:getHistory()
    assert(#h == 1 and h[1].state == 'rejected' and h[1].summary == 'Player dead')
end)

-- 30. Player death during walking cancels follow and halts engine
test('player death during walking step cancels follow and halts engine', function()
    local f = makeFixture({npcPos = {x = 10, y = 10, z = 0}, playerPos = {x = 14, y = 10, z = 0}})
    local stopped = false
    local d = Commands.new(f.observe, function() stopped = true; return true end, f.identityProvider, function() return true end)
    local res = d:execute('follow')
    assert(res.state == 'running')
    assert(d.active and d.active.stepState == 'walking')

    -- Player dies mid-stride
    f.playerPos.dead = true
    local ok, reason = d:tick()
    assert(ok == false)
    assert(reason == 'player dead')
    assert(d.active == nil)
    assert(stopped == true)
    local h = d:getHistory()
    assert(h[#h].state == 'cancelled' and h[#h].summary:find('player dead'))
end)

-- 31. Player death during close-range waiting cancels follow
test('player death during close-range waiting cancels follow', function()
    local f = makeFixture({npcPos = {x = 10, y = 10, z = 0}, playerPos = {x = 11, y = 10, z = 0}})
    local d = Commands.new(f.observe, nil, f.identityProvider)
    local res = d:execute('follow')
    assert(res.state == 'running')
    assert(d.active and d.active.stepState == 'idle')

    -- Player dies while Sarah is idling in deadzone
    f.playerPos.dead = true
    local ok, reason = d:tick()
    assert(ok == false)
    assert(reason == 'player dead')
    assert(d.active == nil)
    local h = d:getHistory()
    assert(h[#h].state == 'cancelled' and h[#h].summary:find('player dead'))
end)

-- 32. Step completion followed by late failure during cooldown is defused
test('step completion followed by late failure during cooldown is defused', function()
    local f = makeFixture({npcPos = {x = 10, y = 10, z = 0}, playerPos = {x = 14, y = 10, z = 0}})
    local capturedComplete, capturedFail
    local d = Commands.new(f.observe, nil, f.identityProvider, function(target, onComplete, onFail)
        capturedComplete = onComplete
        capturedFail = onFail
        return true
    end)
    d:execute('follow')
    assert(d.active and d.active.stepState == 'walking')

    -- Step 1 completes normally
    capturedComplete()
    assert(d.active ~= nil and d.active.stepState == 'idle' and d.active.cooldown == 15)

    -- Late failure from completed Step 1 arrives during cooldown
    capturedFail(nil, 'late path error')
    assert(d.active ~= nil and d.active.stepState == 'idle' and d.active.cooldown == 15)
    local h = d:getHistory()
    assert(h[#h].state == 'running')
end)

-- 33. Duplicate step completion during cooldown does not reset cooldown
test('duplicate step completion during cooldown does not reset cooldown', function()
    local f = makeFixture({npcPos = {x = 10, y = 10, z = 0}, playerPos = {x = 14, y = 10, z = 0}})
    local capturedComplete
    local d = Commands.new(f.observe, nil, f.identityProvider, function(target, onComplete)
        capturedComplete = onComplete
        return true
    end)
    d:execute('follow')
    capturedComplete()
    assert(d.active and d.active.cooldown == 15)

    -- Cooldown decrements on tick
    d:tick()
    assert(d.active.cooldown == 14)

    -- Duplicate completion arrives: must NOT reset cooldown to 15
    capturedComplete()
    assert(d.active.cooldown == 14)

    d:tick()
    assert(d.active.cooldown == 13)
end)

-- 34. Callback identity disappearance and replacement cancel follow consistently on both callbacks
test('callback identity disappearance and replacement cancel follow consistently on both callbacks', function()
    -- 34a. Controller replacement on onStepComplete
    local f1 = makeFixture({npcPos = {x = 10, y = 10, z = 0}, playerPos = {x = 14, y = 10, z = 0}})
    local cb1_complete
    local currentOwner1 = f1.controller
    local d1 = Commands.new(f1.observe, function() return true end, function() return currentOwner1, f1.npc end, function(t, onC) cb1_complete = onC; return true end)
    d1:execute('follow')
    currentOwner1 = {npc = f1.npc, adapter = f1.adapter} -- replaced controller
    cb1_complete()
    assert(d1.active == nil)
    local h1 = d1:getHistory()
    assert(h1[#h1].state == 'cancelled' and h1[#h1].summary:find('controller replaced'))

    -- 34b. Controller disappearance on onStepComplete
    local f2 = makeFixture({npcPos = {x = 10, y = 10, z = 0}, playerPos = {x = 14, y = 10, z = 0}})
    local cb2_complete
    local currentOwner2 = f2.controller
    local d2 = Commands.new(f2.observe, function() return true end, function() return currentOwner2, f2.npc end, function(t, onC) cb2_complete = onC; return true end)
    d2:execute('follow')
    currentOwner2 = nil -- disappeared controller
    cb2_complete()
    assert(d2.active == nil)
    local h2 = d2:getHistory()
    assert(h2[#h2].state == 'cancelled' and h2[#h2].summary:find('controller unavailable'))

    -- 34c. NPC replacement on onStepFail
    local f3 = makeFixture({npcPos = {x = 10, y = 10, z = 0}, playerPos = {x = 14, y = 10, z = 0}})
    local cb3_fail
    local currentNpc3 = f3.npc
    local d3 = Commands.new(f3.observe, function() return true end, function() return f3.controller, currentNpc3 end, function(t, onC, onF) cb3_fail = onF; return true end)
    d3:execute('follow')
    currentNpc3 = {getX = function() return 10 end, getY = function() return 10 end, getZ = function() return 0 end} -- replaced NPC
    cb3_fail(nil, 'some error')
    assert(d3.active == nil)
    local h3 = d3:getHistory()
    assert(h3[#h3].state == 'cancelled' and h3[#h3].summary:find('npc replaced'))

    -- 34d. NPC disappearance on onStepFail
    local f4 = makeFixture({npcPos = {x = 10, y = 10, z = 0}, playerPos = {x = 14, y = 10, z = 0}})
    local cb4_fail
    local currentNpc4 = f4.npc
    local d4 = Commands.new(f4.observe, function() return true end, function() return f4.controller, currentNpc4 end, function(t, onC, onF) cb4_fail = onF; return true end)
    d4:execute('follow')
    currentNpc4 = nil -- disappeared NPC
    cb4_fail(nil, 'some error')
    assert(d4.active == nil)
    local h4 = d4:getHistory()
    assert(h4[#h4].state == 'cancelled' and h4[#h4].summary:find('npc unavailable'))
end)

-- 35. Stale callbacks after stop/restart and session reset cannot affect new actions
test('stale callbacks after stop/restart and session reset cannot affect new actions', function()
    -- 35a. Stale callbacks after user stop and restarted follow
    local f1 = makeFixture({npcPos = {x = 10, y = 10, z = 0}, playerPos = {x = 14, y = 10, z = 0}})
    local old_complete, old_fail
    local stepCount = 0
    local d1 = Commands.new(f1.observe, function() return true end, f1.identityProvider, function(t, onC, onF)
        stepCount = stepCount + 1
        if stepCount == 1 then
            old_complete = onC
            old_fail = onF
        end
        return true
    end)
    d1:execute('follow') -- action #1
    assert(d1.active and d1.active.id == 1)
    d1:execute('stop')   -- action #1 stopped
    assert(d1.active == nil)

    d1:execute('follow') -- action #3 (stop consumed sequence #2)
    assert(d1.active and d1.active.id == 3 and d1.active.stepState == 'walking')

    -- Stale callbacks from action #1 fire: must not touch action #3
    old_complete()
    assert(d1.active and d1.active.id == 3 and d1.active.stepState == 'walking')
    old_fail(nil, 'old fail')
    assert(d1.active and d1.active.id == 3 and d1.active.stepState == 'walking')

    -- 35b. Stale callbacks after session reset
    local f2 = makeFixture({npcPos = {x = 10, y = 10, z = 0}, playerPos = {x = 14, y = 10, z = 0}})
    local s1_complete, s1_fail
    local s2_complete, s2_fail
    local walks = 0
    local d2 = Commands.new(f2.observe, function() return true end, f2.identityProvider, function(t, onC, onF)
        walks = walks + 1
        if walks == 1 then
            s1_complete = onC
            s1_fail = onF
        else
            s2_complete = onC
            s2_fail = onF
        end
        return true
    end)
    d2:execute('follow') -- session 1, action #1
    assert(d2.active and d2.active.session == 1)
    d2:reset()
    assert(d2.active == nil)

    -- Stale callbacks fire on reset dispatcher: must do nothing
    s1_complete()
    assert(d2.active == nil)
    s1_fail(nil, 's1 fail')
    assert(d2.active == nil)

    -- New follow in session 2: stale callbacks from session 1 must not touch it
    d2:execute('follow') -- session 2, action #1
    assert(d2.active and d2.active.session == 2 and d2.active.stepState == 'walking')
    s1_complete()
    assert(d2.active and d2.active.session == 2 and d2.active.stepState == 'walking')
    s1_fail(nil, 's1 fail')
    assert(d2.active and d2.active.session == 2 and d2.active.stepState == 'walking')

    -- Active session 2 callback functions normally
    s2_complete()
    assert(d2.active and d2.active.session == 2 and d2.active.stepState == 'idle')
end)

-- 36. Observations.read extracts player liveness safely for alive and dead player
test('Observations.read extracts player liveness safely for alive and dead player', function()
    local mockNpc = {
        getX = function() return 10 end,
        getY = function() return 10 end,
        getZ = function() return 0 end
    }
    local mockAdapter = {
        meta = {},
        isDead = function() return false end,
        isResident = function() return true end,
        isIncomplete = function() return false end,
        listNPCs = function() return {mockNpc} end
    }
    local controller = {npc = mockNpc, adapter = mockAdapter}

    -- Alive player (with isDead function)
    local alivePlayer = {
        getX = function() return 12 end,
        getY = function() return 12 end,
        getZ = function() return 0 end,
        isDead = function() return false end
    }
    local dataAlive = Observations.read(controller, alivePlayer, false)
    assert(dataAlive.state == 'active')
    assert(dataAlive.player ~= nil)
    assert(dataAlive.player.x == 12 and dataAlive.player.y == 12 and dataAlive.player.z == 0)
    assert(dataAlive.player.dead == false)
    assert(dataAlive.player.isDead == false)
    assert(dataAlive.player.alive == true)
    assert(dataAlive.playerDead == false)
    assert(dataAlive.playerAlive == true)

    -- Dead player (with isDead function returning true)
    local deadPlayer = {
        getX = function() return 12 end,
        getY = function() return 12 end,
        getZ = function() return 0 end,
        isDead = function() return true end
    }
    local dataDead = Observations.read(controller, deadPlayer, false)
    assert(dataDead.state == 'active')
    assert(dataDead.player ~= nil)
    assert(dataDead.player.x == 12 and dataDead.player.y == 12 and dataDead.player.z == 0)
    assert(dataDead.player.dead == true)
    assert(dataDead.player.isDead == true)
    assert(dataDead.player.alive == false)
    assert(dataDead.playerDead == true)
    assert(dataDead.playerAlive == false)

    -- Dead player (with boolean dead = true table)
    local deadTable = {x = 14, y = 14, z = 0, dead = true}
    local dataTableDead = Observations.read(controller, deadTable, false)
    assert(dataTableDead.player ~= nil)
    assert(dataTableDead.player.dead == true)
    assert(dataTableDead.playerDead == true)
    assert(dataTableDead.playerAlive == false)
end)

print('RESULT ' .. count .. ' follow checks passed')
''')
