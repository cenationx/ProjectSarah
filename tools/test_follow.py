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

-- 14. Normal arrival waits in range, then follows on the first departure tick
test('normal arrival resumes on first departure tick without cooldown', function()
    local f = makeFixture({npcPos = {x = 10, y = 10, z = 0}, playerPos = {x = 14, y = 10, z = 0}})
    local capturedComplete
    local walkCount = 0
    local d = Commands.new(f.observe, nil, f.identityProvider, function(target, onComplete)
        walkCount = walkCount + 1
        capturedComplete = onComplete
        return true
    end)
    d:execute('follow')
    f.npcPos.x = 13
    capturedComplete()
    assert(d.active.stepState == 'idle' and d.active.cooldown == 0)
    for _ = 1, 20 do d:tick() end
    assert(walkCount == 1 and d.active.stepState == 'idle')
    f.playerPos.x = 16
    d:tick()
    assert(walkCount == 2 and d.active.stepState == 'walking')
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
    assert(d.active ~= nil and d.active.stepState == 'idle' and d.active.cooldown == 0)

    -- Late failure from completed Step 1 arrives during cooldown
    capturedFail(nil, 'late path error')
    assert(d.active ~= nil and d.active.stepState == 'idle' and d.active.cooldown == 0)
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
    assert(d.active and d.active.cooldown == 0)

    -- An explicit cooldown fixture still protects against duplicate completion.
    d.active.cooldown = 15
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

local function hasLine(lines, pattern)
    for _, l in ipairs(lines) do
        if l:find(pattern) then return true end
    end
    return false
end

-- 37. Follow status clearly distinguishes walking, waiting in range, and disengaged with reason
test('follow status clearly distinguishes walking, waiting in range, and disengaged with reason', function()
    local f = makeFixture({npcPos = {x = 10, y = 10, z = 0}, playerPos = {x = 14, y = 10, z = 0}})
    local d = Commands.new(f.observe, function() return true end, f.identityProvider, function() return true end)

    -- Case A: Following while walking
    local followRes = d:execute('follow')
    assert(followRes.state == 'running')
    assert(d.active and d.active.command == 'follow' and d.active.stepState == 'walking')
    local statusWalking = d:execute('status')
    assert(statusWalking.state == 'completed')
    assert(statusWalking.lines[2] == 'Action: #1 follow (running)')
    assert(statusWalking.lines[3]:find('^Follow: following while walking to %('))
    -- Query commands have no gameplay side effects
    local seqBefore = d.sequence
    local histRes = d:execute('history')
    assert(histRes.state == 'completed')
    assert(d.active and d.active.stepState == 'walking')

    -- Case B: Follow engaged but waiting within range
    f.playerPos.x = 11; f.playerPos.y = 10
    d.active.stepState = 'idle'
    d.active.currentTarget = nil
    local statusWaiting = d:execute('status')
    assert(statusWaiting.state == 'completed')
    assert(statusWaiting.lines[2]:find('Action: #1 follow %(running%)'))
    assert(statusWaiting.lines[3] == 'Follow: follow engaged but waiting within range')

    -- Case C: Follow disengaged, with its reason
    f.playerPos.x = 25; f.playerPos.y = 10
    d:tick()
    assert(d.active == nil)
    assert(d.lastAction and d.lastAction.state == 'cancelled')
    local statusDisengaged = d:execute('status')
    assert(statusDisengaged.state == 'completed')
    assert(statusDisengaged.lines[2]:find('Action: idle %(last: #1 cancelled%)'))
    assert(statusDisengaged.lines[3] == 'Follow: disengaged (player out of range (>8 tiles))')
end)

-- 38. Unknown player liveness is rejected at activation and disengages follow on tick without assuming alive
test('unknown player liveness is rejected at activation and disengages follow on tick without assuming alive', function()
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

    -- 38a. Observations.read handles player with throwing isDead without assuming alive
    local errorPlayer = {
        getX = function() return 12 end,
        getY = function() return 12 end,
        getZ = function() return 0 end,
        isDead = function() error('native isDead crash') end
    }
    local dataUnknown = Observations.read(controller, errorPlayer, false)
    assert(dataUnknown.state == 'active')
    assert(dataUnknown.player ~= nil)
    assert(dataUnknown.player.liveness == 'unknown')
    assert(dataUnknown.player.dead == false)
    assert(dataUnknown.player.alive == false)
    assert(dataUnknown.playerDead == false)
    assert(dataUnknown.playerAlive == false)
    assert(dataUnknown.playerLiveness == 'unknown')

    -- 38b. Follow activation is rejected when player liveness is unknown
    local f1 = makeFixture({npcPos = {x = 10, y = 10, z = 0}, playerPos = {x = 14, y = 10, z = 0}})
    local d1 = Commands.new(function()
        return {
            state = 'active',
            npc = {x = 10, y = 10, z = 0},
            player = {x = 14, y = 10, z = 0, liveness = 'unknown', dead = false, alive = false},
            playerDead = false,
            playerAlive = false,
            playerLiveness = 'unknown'
        }
    end, function() return true end, f1.identityProvider, function() return true end)
    local actRes = d1:execute('follow')
    assert(actRes.state == 'rejected')
    assert(actRes.lines[1] == 'Player liveness query failed; cannot follow.')
    local h1 = d1:getHistory()
    assert(h1[#h1].state == 'rejected' and h1[#h1].summary == 'Player liveness unknown')
    assert(d1.active == nil)

    -- 38c. Active follow disengages when player liveness query fails on tick
    local livenessState = 'alive'
    local d2 = Commands.new(function()
        local isAlive = (livenessState == 'alive')
        local isUnknown = (livenessState == 'unknown')
        local isDead = (livenessState == 'dead')
        return {
            state = 'active',
            npc = {x = 10, y = 10, z = 0},
            player = {x = 14, y = 10, z = 0, liveness = livenessState, dead = isDead, alive = isAlive},
            playerDead = isDead,
            playerAlive = isAlive,
            playerLiveness = livenessState
        }
    end, function() return true end, f1.identityProvider, function() return true end)
    local startRes = d2:execute('follow')
    assert(startRes.state == 'running' and d2.active ~= nil)

    -- Transition liveness to unknown
    livenessState = 'unknown'
    d2:tick()
    assert(d2.active == nil)
    assert(d2.lastAction and d2.lastAction.state == 'cancelled' and d2.lastAction.reason == 'player liveness unknown')
    local statusRes = d2:execute('status')
    assert(statusRes.lines[3] == 'Follow: disengaged (player liveness unknown)')
end)

-- 39. Invalid and nonfinite coordinates are rejected without arithmetic errors
test('invalid and nonfinite coordinates are rejected without arithmetic errors', function()
    local f = makeFixture({npcPos = {x = 10, y = 10, z = 0}, playerPos = {x = 14, y = 10, z = 0}})

    -- 39a. Observations.read rejects NaN and infinite coordinates in position
    local nanNpc = {
        getX = function() return 0/0 end,
        getY = function() return 10 end,
        getZ = function() return 0 end
    }
    local infNpc = {
        getX = function() return math.huge end,
        getY = function() return 10 end,
        getZ = function() return 0 end
    }
    assert(Observations.read({adapter = f.adapter, npc = nanNpc}, nil, false).npc == nil)
    assert(Observations.read({adapter = f.adapter, npc = infNpc}, nil, false).npc == nil)

    -- 39b. Follow activation rejects NaN and infinite player coordinates
    local badCoordType = 'nan'
    local d = Commands.new(function()
        local px = (badCoordType == 'nan' and 0/0) or (badCoordType == 'inf' and math.huge) or (badCoordType == 'str' and 'invalid') or 14
        return {
            state = 'active',
            npc = {x = 10, y = 10, z = 0},
            player = {x = px, y = 10, z = 0, alive = true, dead = false},
            playerAlive = true,
            playerDead = false
        }
    end, function() return true end, f.identityProvider, function() return true end)

    badCoordType = 'nan'
    local nanRes = d:execute('follow')
    assert(nanRes.state == 'rejected' and nanRes.lines[1] == 'Player position unavailable.')

    badCoordType = 'inf'
    local infRes = d:execute('follow')
    assert(infRes.state == 'rejected' and infRes.lines[1] == 'Player position unavailable.')

    badCoordType = 'str'
    local strRes = d:execute('follow')
    assert(strRes.state == 'rejected' and strRes.lines[1] == 'Player position unavailable.')

    -- 39c. Active follow tick disengages cleanly if coordinates become NaN/infinite without arithmetic error
    badCoordType = 'valid'
    local okStart = d:execute('follow')
    assert(okStart.state == 'running')
    badCoordType = 'nan'
    local tickOk, tickReason = d:tick()
    assert(tickOk == false)
    assert(d.active == nil)
    assert(d.lastAction.state == 'cancelled' and d.lastAction.reason == 'player unavailable')

    -- 39d. dispatchFollowStep directly rejects invalid coords
    local d2 = Commands.new(f.observe, function() return true end, f.identityProvider, function() return true end)
    d2:execute('follow')
    local dispOk, dispErr = d2:dispatchFollowStep({}, 0/0, 10, 0, 14, 10, 0)
    assert(dispOk == false and dispErr == 'invalid coordinates')
    assert(d2.active == nil)
end)

-- 40. Engine stop failure status warning blocks movement until recovery clears it
test('engine stop failure status warning blocks movement until recovery clears it', function()
    local stopShouldFail = false
    local stopCount = 0
    local f = makeFixture({npcPos = {x = 10, y = 10, z = 0}, playerPos = {x = 14, y = 10, z = 0}})
    local d = Commands.new(f.observe, function(reason, act)
        stopCount = stopCount + 1
        if stopShouldFail then return false, 'engine jammed' end
        return true
    end, f.identityProvider, function() return true end)

    -- Start follow
    local startRes = d:execute('follow')
    assert(startRes.state == 'running')

    -- Stop fails
    stopShouldFail = true
    local stopFailRes = d:execute('stop')
    assert(stopFailRes.state == 'failed')
    assert(stopFailRes.lines[1] == 'Cancelled #1 (follow).')
    assert(stopFailRes.lines[2] == 'Engine stop failed: engine jammed.')
    assert(not hasLine(stopFailRes.lines, 'Sarah stopped'))
    assert(d.stopFailed == 'engine jammed')

    -- Status reports stop failure warning
    local statusWarn = d:execute('status')
    assert(statusWarn.state == 'completed')
    assert(hasLine(statusWarn.lines, 'Warning: engine stop failed %(engine jammed%); movement blocked pending recovery%.'))

    -- Subsequent follow and walk here are rejected
    local followBlock = d:execute('follow')
    assert(followBlock.state == 'rejected')
    assert(followBlock.lines[1]:find('Prior engine stop failed %(engine jammed%); movement blocked until stop recovers%.'))

    local walkBlock = d:execute('walk here')
    assert(walkBlock.state == 'rejected')
    assert(walkBlock.lines[1]:find('Prior engine stop failed %(engine jammed%); movement blocked until stop recovers%.'))

    -- Stop recovery: engine stop succeeds
    stopShouldFail = false
    local recoverStopRes = d:execute('stop')
    assert(recoverStopRes.state == 'completed')
    assert(hasLine(recoverStopRes.lines, 'Prior engine stop failure cleared; movement recovered%.'))
    assert(hasLine(recoverStopRes.lines, 'Sarah stopped; nothing active%.'))
    assert(d.stopFailed == nil)

    -- Status warning is gone
    local statusClean = d:execute('status')
    assert(not hasLine(statusClean.lines, 'Warning: engine stop failed'))

    -- Movement is recovered and succeeds
    local followRecovered = d:execute('follow')
    assert(followRecovered.state == 'running')
    assert(d.active and d.active.command == 'follow')
end)

-- 41. Asynchronous follow disengagement enqueues one-time notice and user stop does not spam
test('asynchronous follow disengagement enqueues one-time notice and user stop does not spam', function()
    local f = makeFixture({npcPos = {x = 10, y = 10, z = 0}, playerPos = {x = 14, y = 10, z = 0}})
    local d = Commands.new(f.observe, function() return true end, f.identityProvider, function() return true end)

    -- 41a. User stop does NOT enqueue notice into noticeQueue
    d:execute('follow')
    assert(d.active ~= nil)
    d:execute('stop')
    assert(d.active == nil)
    local userNotices = d:consumeNotices()
    assert(#userNotices == 0)

    -- 41b. Asynchronous disengagement enqueues exactly one notice
    d:execute('follow')
    assert(d.active ~= nil)
    -- Leash break (>8 tiles)
    f.playerPos.x = 25; f.playerPos.y = 10
    d:tick()
    assert(d.active == nil)
    assert(d.lastAction.state == 'cancelled')

    local notices = d:consumeNotices()
    assert(#notices == 1)
    assert(notices[1].id == 3)
    assert(notices[1].command == 'follow')
    assert(notices[1].state == 'cancelled')
    assert(notices[1].message == 'Follow disengaged: player out of range (>8 tiles).')
    assert(notices[1].isBad == true)

    -- Draining again yields empty queue (no per-tick duplicate notices)
    local emptyNotices = d:consumeNotices()
    assert(#emptyNotices == 0)
    for i = 1, 5 do d:tick() end
    local stillEmpty = d:consumeNotices()
    assert(#stillEmpty == 0)

    -- 41c. Session reset clears notice queue
    f.playerPos.x = 14; f.playerPos.y = 10
    d:execute('follow')
    d:cancelActive('path failed')
    assert(#d.noticeQueue == 1)
    d:reset()
    assert(#d.noticeQueue == 0)
    assert(#d:consumeNotices() == 0)
end)

-- 42. Follow status during cooldown distinguishes inside vs outside deadzone
test('follow status during cooldown distinguishes inside vs outside deadzone', function()
    local f = makeFixture({npcPos = {x = 10, y = 10, z = 0}, playerPos = {x = 14, y = 10, z = 0}})
    local d = Commands.new(f.observe, function() return true end, f.identityProvider, function() return true end)

    local startRes = d:execute('follow')
    assert(startRes.state == 'running')
    assert(d.active and d.active.command == 'follow')

    -- Enter cooldown
    d.active.stepState = 'idle'
    d.active.currentTarget = nil
    d.active.cooldown = 15

    -- 42a. Inside deadzone (<= 2 tiles): reports waiting within range
    f.playerPos.x = 11; f.playerPos.y = 10; f.playerPos.z = 0
    local stInRange = d:execute('status')
    assert(stInRange.state == 'completed')
    assert(stInRange.lines[2] == 'Action: #1 follow (running)')
    assert(stInRange.lines[3] == 'Follow: follow engaged but waiting within range')

    -- Exactly on 2-tile boundary (dx=2, dy=0, distSq=4.0): waiting within range
    f.playerPos.x = 12; f.playerPos.y = 10; f.playerPos.z = 0
    local stBoundary = d:execute('status')
    assert(stBoundary.lines[3] == 'Follow: follow engaged but waiting within range')

    -- 42b. Outside deadzone (> 2 tiles, e.g. 3 tiles away): reports waiting before next walk
    f.playerPos.x = 13; f.playerPos.y = 10; f.playerPos.z = 0
    local stOutside = d:execute('status')
    assert(stOutside.state == 'completed')
    assert(stOutside.lines[2] == 'Action: #1 follow (running)')
    assert(stOutside.lines[3] == 'Follow: follow engaged but waiting before next walk')

    -- 42c. Different floor during cooldown: reports waiting before next walk
    f.playerPos.x = 11; f.playerPos.y = 10; f.playerPos.z = 1
    local stDiffFloor = d:execute('status')
    assert(stDiffFloor.lines[3] == 'Follow: follow engaged but waiting before next walk')

    -- 42d. Missing coordinates during status: lifecycle cancels with player unavailable
    f.playerPos.x = 11; f.playerPos.y = 10; f.playerPos.z = 0
    local dMissing = Commands.new(function()
        return {
            state = 'active',
            npc = {x = 10, y = 10, z = 0},
            player = nil
        }
    end, function() return true end, f.identityProvider, function() return true end)
    dMissing.active = {
        id = 1,
        session = dMissing.session,
        command = 'follow',
        state = 'running',
        token = 1,
        stepState = 'idle',
        cooldown = 15
    }
    local stMissing = dMissing:execute('status')
    assert(stMissing.lines[2]:find('Action: idle %(last: #1 cancelled%)'))
    assert(stMissing.lines[3] == 'Follow: disengaged (player unavailable)')
end)

-- 43. Repeated Status calls leave follow state, cooldown, and queues completely unchanged
test('repeated status calls leave follow state cooldown and queues completely unchanged', function()
    local f = makeFixture({npcPos = {x = 10, y = 10, z = 0}, playerPos = {x = 14, y = 10, z = 0}})
    local d = Commands.new(f.observe, function() return true end, f.identityProvider, function() return true end)

    d:execute('follow')
    d.active.stepState = 'idle'
    d.active.currentTarget = nil
    d.active.cooldown = 15
    d.active.stepTicks = 0
    d.active.stepGen = 1

    local initId = d.active.id
    local initToken = d.active.token
    local initGen = d.active.stepGen
    local initCooldown = d.active.cooldown
    local initSummary = d.active.summary

    -- Call status 5 times in succession
    for i = 1, 5 do
        local st = d:execute('status')
        assert(st.state == 'completed')
    end

    -- Verify follow state is completely untouched
    assert(d.active ~= nil)
    assert(d.active.id == initId)
    assert(d.active.token == initToken)
    assert(d.active.stepGen == initGen)
    assert(d.active.stepState == 'idle')
    assert(d.active.cooldown == initCooldown)
    assert(d.active.stepTicks == 0)
    assert(d.active.currentTarget == nil)
    assert(d.active.summary == initSummary)
    assert(#d.noticeQueue == 0)
    assert(#d:consumeNotices() == 0)
    assert(d.stopFailed == nil)
end)

-- 44. Asynchronous leash break combined with failed engine stop enqueues one unified notice
test('asynchronous leash break combined with failed engine stop enqueues one unified notice', function()
    local stopShouldFail = true
    local stopCallCount = 0
    local f = makeFixture({npcPos = {x = 10, y = 10, z = 0}, playerPos = {x = 14, y = 10, z = 0}})
    local d = Commands.new(f.observe, function(reason, act)
        stopCallCount = stopCallCount + 1
        if stopShouldFail then return false, 'engine jammed' end
        return true
    end, f.identityProvider, function() return true end)

    local startRes = d:execute('follow')
    assert(startRes.state == 'running')
    assert(d.active.id == 1)

    -- Leash break (> 8 tiles)
    f.playerPos.x = 25; f.playerPos.y = 10
    local tickOk, tickErr = d:tick()
    assert(tickOk == false)
    assert(d.active == nil)

    -- Preserves original cancellation reason and request ID
    assert(d.lastAction.id == 1)
    assert(d.lastAction.state == 'cancelled')
    assert(d.lastAction.reason == 'player out of range (>8 tiles)')
    assert(d.stopFailed == 'engine jammed')

    -- Exactly one notification carrying both disengagement and stop-failure information
    local notices = d:consumeNotices()
    assert(#notices == 1)
    local n = notices[1]
    assert(n.id == 1)
    assert(n.command == 'follow')
    assert(n.state == 'cancelled')
    assert(n.reason == 'player out of range (>8 tiles)')
    assert(n.stopFailed == 'engine jammed')
    assert(n.isBad == true)
    assert(n.message:find('Follow disengaged: player out of range %(>8 tiles%)%.'))
    assert(n.message:find('Warning: engine stop failed %(engine jammed%)'))
    assert(n.message:find('movement blocked pending recovery%.'))
    assert(not n.message:find('Sarah stopped'))

    -- No duplicate notices on subsequent ticks
    assert(#d:consumeNotices() == 0)
    for i = 1, 5 do d:tick() end
    assert(#d:consumeNotices() == 0)

    -- Status reports idle cancelled and stop failure warning
    local st = d:execute('status')
    assert(st.lines[2] == 'Action: idle (last: #1 cancelled)')
    assert(st.lines[3] == 'Follow: disengaged (player out of range (>8 tiles))')
    assert(hasLine(st.lines, 'Warning: engine stop failed %(engine jammed%); movement blocked pending recovery%.'))

    -- Movement is blocked pending recovery
    local followBlock = d:execute('follow')
    assert(followBlock.state == 'rejected')
    assert(followBlock.lines[1]:find('Prior engine stop failed %(engine jammed%); movement blocked until stop recovers%.'))

    local walkBlock = d:execute('walk here')
    assert(walkBlock.state == 'rejected')
    assert(walkBlock.lines[1]:find('Prior engine stop failed %(engine jammed%); movement blocked until stop recovers%.'))
end)

-- 45. Asynchronous path failure combined with failed engine stop enqueues one unified notice
test('asynchronous path failure combined with failed engine stop enqueues one unified notice', function()
    local lastFailCallback = nil
    local stopShouldFail = true
    local f = makeFixture({npcPos = {x = 10, y = 10, z = 0}, playerPos = {x = 14, y = 10, z = 0}})
    local d = Commands.new(f.observe, function(reason, act)
        if stopShouldFail then return false, 'actuator locked' end
        return true
    end, f.identityProvider, function(tgt, onComp, onFail)
        lastFailCallback = onFail
        return true, {}
    end)

    d:execute('follow')
    assert(d.active and d.active.command == 'follow' and d.active.stepState == 'walking')
    assert(type(lastFailCallback) == 'function')

    -- Asynchronous path failure arrives from engine
    lastFailCallback(nil, 'path blocked')
    assert(d.active == nil)

    -- Preserves original cancellation reason and request ID
    assert(d.lastAction.id == 1)
    assert(d.lastAction.state == 'cancelled')
    assert(d.lastAction.reason == 'path blocked')
    assert(d.stopFailed == 'actuator locked')

    -- Exactly one notification carrying both path failure and stop failure
    local notices = d:consumeNotices()
    assert(#notices == 1)
    local n = notices[1]
    assert(n.id == 1)
    assert(n.command == 'follow')
    assert(n.state == 'cancelled')
    assert(n.reason == 'path blocked')
    assert(n.stopFailed == 'actuator locked')
    assert(n.message:find('Follow disengaged: path blocked%.'))
    assert(n.message:find('Warning: engine stop failed %(actuator locked%)'))
    assert(n.message:find('movement blocked pending recovery%.'))
    assert(not n.message:find('Sarah stopped'))

    -- Subsequent status reflects path failure and warning
    local st = d:execute('status')
    assert(st.lines[2] == 'Action: idle (last: #1 cancelled)')
    assert(st.lines[3] == 'Follow: disengaged (path blocked)')
    assert(hasLine(st.lines, 'Warning: engine stop failed %(actuator locked%); movement blocked pending recovery%.'))
end)

-- 46. Successful recovery clears failure and stale callbacks after recovery are ignored
test('successful recovery clears failure and stale callbacks after recovery are ignored', function()
    local lastCompleteCb = nil
    local lastFailCb = nil
    local stopShouldFail = true
    local f = makeFixture({npcPos = {x = 10, y = 10, z = 0}, playerPos = {x = 14, y = 10, z = 0}})
    local d = Commands.new(f.observe, function(reason, act)
        if stopShouldFail then return false, 'engine jammed' end
        return true
    end, f.identityProvider, function(tgt, onComp, onFail)
        lastCompleteCb = onComp
        lastFailCb = onFail
        return true, {}
    end)

    -- Start follow (#1)
    d:execute('follow')
    assert(d.active and d.active.id == 1)

    -- Leash break with failed stop
    f.playerPos.x = 30; f.playerPos.y = 10
    d:tick()
    assert(d.active == nil)
    assert(d.stopFailed == 'engine jammed')
    d:consumeNotices()

    -- Later stop succeeds: clears failure and reports recovery
    stopShouldFail = false
    local recRes = d:execute('stop')
    assert(recRes.state == 'completed')
    assert(hasLine(recRes.lines, 'Prior engine stop failure cleared; movement recovered%.'))
    assert(hasLine(recRes.lines, 'Sarah stopped; nothing active%.'))
    assert(d.stopFailed == nil)

    -- Status reports clean idle without warnings
    local stClean = d:execute('status')
    assert(not hasLine(stClean.lines, 'Warning: engine stop failed'))

    -- Stale callbacks from action #1 are defused
    local staleFailCb = lastFailCb
    local staleCompleteCb = lastCompleteCb

    staleFailCb(nil, 'late path failure')
    assert(d.active == nil)
    assert(d.stopFailed == nil)
    assert(#d.noticeQueue == 0)

    staleCompleteCb()
    assert(d.active == nil)
    assert(d.stopFailed == nil)
    assert(#d.noticeQueue == 0)

    -- New follow action starts cleanly
    f.playerPos.x = 14; f.playerPos.y = 10
    local newRes = d:execute('follow')
    assert(newRes.state == 'running')
    assert(d.active ~= nil and d.active.id == newRes.id)
    assert(d.active.command == 'follow')

    -- Stale callbacks from action #1 fire again: cannot mutate active follow
    staleFailCb(nil, 'late path failure')
    assert(d.active ~= nil and d.active.id == newRes.id and d.active.command == 'follow')
    assert(d.stopFailed == nil)
    assert(#d.noticeQueue == 0)

    staleCompleteCb()
    assert(d.active ~= nil and d.active.id == newRes.id and d.active.command == 'follow')
    assert(d.stopFailed == nil)
    assert(#d.noticeQueue == 0)
end)

-- 47. Moving target retargets mid-walk to new forward position
test('moving target retargets mid-walk to new forward position', function()
    local lastStopReason = nil
    local walkCalls = {}
    local f = makeFixture({npcPos = {x = 10, y = 10, z = 0}, playerPos = {x = 14, y = 10, z = 0}})
    local d = Commands.new(f.observe, function(reason, act)
        lastStopReason = reason
        return true
    end, f.identityProvider, function(tgt, onComp, onFail)
        walkCalls[#walkCalls + 1] = {tgt = tgt, onComp = onComp, onFail = onFail}
        return true
    end)

    d:execute('follow')
    assert(#walkCalls == 1)
    assert(d.active and d.active.stepState == 'walking')
    assert(d.active.currentTarget.x == 13 and d.active.currentTarget.y == 10)
    local step1Gen = d.active.stepGen

    -- Player moves forward to (16, 10) (2 tiles forward)
    f.playerPos.x = 16

    -- Ticks 1..5: bounded frequency prevents premature retargeting
    for i = 1, 5 do
        d:tick()
        assert(#walkCalls == 1)
        assert(d.active.currentTarget.x == 13 and d.active.currentTarget.y == 10)
        assert(d.active.stepGen == step1Gen)
    end

    -- Tick 6: minRetargetTicks reached, mid-walk retarget triggers
    d:tick()
    assert(#walkCalls == 2)
    assert(lastStopReason == 'retarget')
    assert(d.active and d.active.stepState == 'walking')
    assert(d.active.currentTarget.x == 15 and d.active.currentTarget.y == 10)
    assert(d.active.stepGen > step1Gen)
    assert(d.active.summary:find('Following player to %(15, 10, 0%)'))
end)

-- 48. Turning target retargets mid-walk to orthogonal position
test('turning target retargets mid-walk to orthogonal position', function()
    local walkCalls = {}
    local f = makeFixture({npcPos = {x = 10, y = 10, z = 0}, playerPos = {x = 14, y = 10, z = 0}})
    local d = Commands.new(f.observe, function(reason) return true end, f.identityProvider, function(tgt, onComp, onFail)
        walkCalls[#walkCalls + 1] = {tgt = tgt, onComp = onComp, onFail = onFail}
        return true
    end)

    d:execute('follow')
    assert(#walkCalls == 1)
    assert(d.active.currentTarget.x == 13 and d.active.currentTarget.y == 10)

    -- Player turns 90 degrees North to (14, 13)
    f.playerPos.x = 14
    f.playerPos.y = 13

    for i = 1, 6 do d:tick() end

    assert(#walkCalls == 2)
    assert(d.active.stepState == 'walking')
    assert(d.active.currentTarget.y ~= 10)
    assert(d.active.currentTarget.x == 14 or d.active.currentTarget.x == 13)
    assert(d.active.currentTarget.y == 12 or d.active.currentTarget.y == 13)
end)

-- 49. Bounded retarget frequency throttles path restarts to minimum ticks
test('bounded retarget frequency throttles path restarts to minimum ticks', function()
    local stopCount = 0
    local walkCount = 0
    local f = makeFixture({npcPos = {x = 10, y = 10, z = 0}, playerPos = {x = 14, y = 10, z = 0}})
    local d = Commands.new(f.observe, function(reason)
        if reason == 'retarget' then stopCount = stopCount + 1 end
        return true
    end, f.identityProvider, function(tgt)
        walkCount = walkCount + 1
        return true
    end)

    d:execute('follow')
    assert(walkCount == 1)
    assert(stopCount == 0)

    -- Player moves further each tick within leash
    f.playerPos.x = 15; d:tick(); assert(walkCount == 1 and stopCount == 0)
    f.playerPos.x = 15.5; d:tick(); assert(walkCount == 1 and stopCount == 0)
    f.playerPos.x = 16; d:tick(); assert(walkCount == 1 and stopCount == 0)
    d:tick(); assert(walkCount == 1 and stopCount == 0)
    d:tick(); assert(walkCount == 1 and stopCount == 0)

    -- Tick 6: first retarget fires
    d:tick()
    assert(walkCount == 2 and stopCount == 1)

    -- Player moves again: next 5 ticks must NOT retarget
    f.playerPos.y = 12
    for _ = 1, 5 do
        d:tick()
        assert(walkCount == 2 and stopCount == 1)
    end

    -- Tick 12: second retarget fires
    d:tick()
    assert(walkCount == 3 and stopCount == 2)
end)

-- 50. Stale callbacks from step 1 are defused after mid-walk retargeting
test('stale callbacks from step 1 are defused after mid-walk retargeting', function()
    local capturedStep1Comp, capturedStep1Fail
    local capturedStep2Comp, capturedStep2Fail
    local walkCount = 0
    local f = makeFixture({npcPos = {x = 10, y = 10, z = 0}, playerPos = {x = 14, y = 10, z = 0}})
    local d = Commands.new(f.observe, function() return true end, f.identityProvider, function(tgt, onComp, onFail)
        walkCount = walkCount + 1
        if walkCount == 1 then
            capturedStep1Comp = onComp
            capturedStep1Fail = onFail
        elseif walkCount == 2 then
            capturedStep2Comp = onComp
            capturedStep2Fail = onFail
        end
        return true
    end)

    d:execute('follow')
    assert(walkCount == 1)

    -- Player moves to (16, 10) and 6 ticks elapse -> retarget
    f.playerPos.x = 16
    for _ = 1, 6 do d:tick() end
    assert(walkCount == 2)
    local step2Id = d.active.id
    local step2Gen = d.active.stepGen
    local step2Target = d.active.currentTarget

    -- Stale fail callback from step 1 arrives
    capturedStep1Fail(nil, 'stopped')
    assert(d.active ~= nil)
    assert(d.active.id == step2Id)
    assert(d.active.stepGen == step2Gen)
    assert(d.active.currentTarget.x == step2Target.x)
    assert(#d.noticeQueue == 0)

    -- Another stale fail callback from step 1 arrives
    capturedStep1Fail(nil, 'path failed')
    assert(d.active ~= nil)
    assert(d.active.id == step2Id)
    assert(d.active.stepGen == step2Gen)
    assert(#d.noticeQueue == 0)

    -- Stale complete callback from step 1 arrives
    capturedStep1Comp()
    assert(d.active ~= nil)
    assert(d.active.stepState == 'walking')
    assert(d.active.stepGen == step2Gen)

    -- Legitimate step 2 completion works normally
    capturedStep2Comp()
    assert(d.active.stepState == 'idle')
    assert(d.active.cooldown == 0)
end)

-- 51. Synchronous callbacks during retarget dispatch are handled safely
test('synchronous callbacks during retarget dispatch are handled safely', function()
    -- Part A: synchronous completion during retarget dispatch
    local walkCount = 0
    local f = makeFixture({npcPos = {x = 10, y = 10, z = 0}, playerPos = {x = 14, y = 10, z = 0}})
    local d = Commands.new(f.observe, function() return true end, f.identityProvider, function(tgt, onComp, onFail)
        walkCount = walkCount + 1
        if walkCount == 2 then
            onComp()
        end
        return true
    end)

    d:execute('follow')
    f.playerPos.x = 16
    for _ = 1, 6 do d:tick() end
    assert(walkCount == 2)
    assert(d.active ~= nil)
    assert(d.active.stepState == 'idle')
    assert(d.active.cooldown == 0)

    -- Part B: synchronous failure during retarget dispatch
    walkCount = 0
    local f2 = makeFixture({npcPos = {x = 10, y = 10, z = 0}, playerPos = {x = 14, y = 10, z = 0}})
    local d2 = Commands.new(f2.observe, function() return true end, f2.identityProvider, function(tgt, onComp, onFail)
        walkCount = walkCount + 1
        if walkCount == 2 then
            onFail(nil, 'path blocked')
        end
        return true
    end)

    d2:execute('follow')
    f2.playerPos.x = 16
    for _ = 1, 6 do d2:tick() end
    assert(walkCount == 2)
    assert(d2.active == nil)
    assert(d2.lastAction.state == 'cancelled')
    assert(d2.lastAction.reason == 'path blocked')
    assert(#d2.noticeQueue == 1)
end)

-- 52. User stop during tracking halts engine and stays stopped
test('user stop during tracking halts engine and stays stopped', function()
    local lastStopReason = nil
    local f = makeFixture({npcPos = {x = 10, y = 10, z = 0}, playerPos = {x = 14, y = 10, z = 0}})
    local d = Commands.new(f.observe, function(reason)
        lastStopReason = reason
        return true
    end, f.identityProvider, function() return true end)

    d:execute('follow')
    f.playerPos.x = 15
    d:tick()
    assert(d.active and d.active.stepState == 'walking')

    local stopRes = d:execute('stop')
    assert(stopRes.state == 'completed')
    assert(lastStopReason == 'stopped by user')
    assert(d.active == nil)

    -- Subsequent player moves and ticks do not restart follow
    f.playerPos.x = 16
    for _ = 1, 10 do d:tick() end
    assert(d.active == nil)

    local st = d:execute('status')
    assert(st.lines[2] == 'Action: idle (last: #1 cancelled)')
    assert(st.lines[3] == 'Follow: disengaged (stopped by user)')
end)

-- 53. Failed engine stop during retargeting blocks movement and sets stopFailed
test('failed engine stop during retargeting blocks movement and sets stopFailed', function()
    local stopShouldFail = false
    local f = makeFixture({npcPos = {x = 10, y = 10, z = 0}, playerPos = {x = 14, y = 10, z = 0}})
    local d = Commands.new(f.observe, function(reason)
        if stopShouldFail then return false, 'motor jammed' end
        return true
    end, f.identityProvider, function() return true end)

    d:execute('follow')
    assert(d.active and d.active.stepState == 'walking')

    f.playerPos.x = 16
    for _ = 1, 5 do d:tick() end

    -- Stop fails on retarget at tick 6
    stopShouldFail = true
    local ok, err = d:tick()
    assert(ok == false)
    assert(d.active == nil)
    assert(d.stopFailed == 'motor jammed')

    -- One notice enqueued with failure warning
    local notices = d:consumeNotices()
    assert(#notices == 1)
    assert(notices[1].message:find('Warning: engine stop failed %(motor jammed%)'))
    assert(notices[1].message:find('movement blocked pending recovery%.'))

    -- Follow and walk here rejected while stopFailed
    local folBlock = d:execute('follow')
    assert(folBlock.state == 'rejected')
    assert(folBlock.lines[1]:find('movement blocked until stop recovers%.'))

    local walkBlock = d:execute('walk here')
    assert(walkBlock.state == 'rejected')
    assert(walkBlock.lines[1]:find('movement blocked until stop recovers%.'))

    -- Recovery via successful stop
    stopShouldFail = false
    local recRes = d:execute('stop')
    assert(recRes.state == 'completed')
    assert(d.stopFailed == nil)
    assert(hasLine(recRes.lines, 'Prior engine stop failure cleared; movement recovered%.'))
    assert(hasLine(recRes.lines, 'Sarah stopped; nothing active%.'))
end)

-- 54. No movement restart after cancellation
test('no movement restart after cancellation', function()
    local f = makeFixture({npcPos = {x = 10, y = 10, z = 0}, playerPos = {x = 14, y = 10, z = 0}})
    local d = Commands.new(f.observe, function() return true end, f.identityProvider, function() return true end)

    d:execute('follow')
    assert(d.active ~= nil)

    -- Leash break cancels follow
    f.playerPos.x = 20
    d:tick()
    assert(d.active == nil)
    assert(d.lastAction.reason == 'player out of range (>8 tiles)')

    -- Player returns close to Sarah
    f.playerPos.x = 12
    for _ = 1, 10 do d:tick() end
    assert(d.active == nil)

    local st = d:execute('status')
    assert(st.lines[2] == 'Action: idle (last: #1 cancelled)')
    assert(st.lines[3] == 'Follow: disengaged (player out of range (>8 tiles))')
end)

-- 55. Deadzone entry mid-walk halts engine cleanly and transitions to idle in range
test('deadzone entry mid-walk halts engine cleanly and transitions to idle in range', function()
    local lastStopReason = nil
    local walkCount = 0
    local f = makeFixture({npcPos = {x = 10, y = 10, z = 0}, playerPos = {x = 13.5, y = 10, z = 0}})
    local d = Commands.new(f.observe, function(reason)
        lastStopReason = reason
        return true
    end, f.identityProvider, function(tgt)
        walkCount = walkCount + 1
        return true
    end)

    d:execute('follow')
    assert(walkCount == 1)
    assert(d.active.stepState == 'walking')

    -- Player steps closer into deadzone (dist = 1.5 tiles <= 2.0)
    f.playerPos.x = 11.5

    -- Ticks 1..5: bounded frequency lets current walk continue
    for _ = 1, 5 do
        d:tick()
        assert(d.active.stepState == 'walking')
    end

    -- Tick 6: minRetargetTicks reached while in deadzone -> halts cleanly
    d:tick()
    assert(d.active ~= nil)
    assert(d.active.stepState == 'idle')
    assert(d.active.currentTarget == nil)
    assert(d.active.summary == 'Following player (in range)')
    assert(lastStopReason == 'in range')

    -- Status reports waiting within range
    local st = d:execute('status')
    assert(st.lines[2] == 'Action: #1 follow (running)')
    assert(st.lines[3] == 'Follow: follow engaged but waiting within range')

    -- Player moves away to (15, 10) (dist = 5 tiles)
    f.playerPos.x = 15
    d:tick()
    assert(walkCount == 2)
    assert(d.active.stepState == 'walking')
    assert(d.active.currentTarget.x == 14 and d.active.currentTarget.y == 10)
end)


-- 56. Native stop may fire old callbacks synchronously before returning.
test('retarget retires callbacks before synchronous engine stop notifications', function()
    local oldComplete, oldFail
    local walks, stops = 0, 0
    local f = makeFixture({npcPos = {x = 10, y = 10, z = 0}, playerPos = {x = 14, y = 10, z = 0}})
    local d = Commands.new(f.observe, function(reason)
        if reason == 'retarget' then
            stops = stops + 1
            oldFail(nil, 'stopped')
            oldComplete()
        end
        return true
    end, f.identityProvider, function(target, onComplete, onFail)
        walks = walks + 1
        oldComplete, oldFail = onComplete, onFail
        return true
    end)
    d:execute('follow')
    f.playerPos.x = 16
    for _ = 1, 6 do d:tick() end
    assert(stops == 1 and walks == 2)
    assert(d.active and d.active.stepState == 'walking')
    assert(d.active.currentTarget.x == 15)
    assert(d.stopFailed == nil and #d.noticeQueue == 0)
end)

-- =========================================================================
-- Advancing NPC Simulation Fixture and Realistic Scenarios (Tests 57 - 66)
-- =========================================================================

local function makeAdvancingFixture(opts)
    opts = opts or {}
    local npcPos = opts.npcPos or {x = 10, y = 10, z = 0}
    local playerPos = opts.playerPos or {x = 14, y = 10, z = 0}
    local npcSpeed = opts.npcSpeed or 0.1
    local arrivalThreshold = opts.arrivalThreshold or 0.15
    local npcState = opts.npcState or 'active'
    local stalled = (opts.stalled == true)
    local stopShouldFail = (opts.stopFail == true)

    local activeWalk = nil
    local walkCalls = {}
    local stopCalls = {}

    local npcObj = {
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
            local record = {
                target = {x = target.x, y = target.y, z = target.z},
                onComplete = onComplete,
                onFail = onFail,
                ticks = 0
            }
            walkCalls[#walkCalls + 1] = record
            activeWalk = record
            return true
        end,
        stop = function(n)
            stopCalls[#stopCalls + 1] = true
            if stopShouldFail then return false, 'stop failed' end
            local old = activeWalk
            activeWalk = nil
            if opts.syncStopFail and old and old.onFail then
                old.onFail(nil, 'stopped')
            elseif opts.syncStopComplete and old and old.onComplete then
                old.onComplete()
            end
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

    local f = {
        controller = controller,
        npc = npcObj,
        adapter = adapter,
        npcPos = npcPos,
        playerPos = playerPos,
        observe = observe,
        identityProvider = function() return controller, npcObj end,
        walkCalls = walkCalls,
        stopCalls = stopCalls,
        getActiveWalk = function() return activeWalk end,
        setActiveWalk = function(w) activeWalk = w end,
        setStalled = function(s) stalled = s end,
        isStalled = function() return stalled end,
        setNpcState = function(s) npcState = s end,
        setStopFail = function(sf) stopShouldFail = sf end
    }

    function f:advancePhysical()
        if activeWalk and not stalled then
            local tgt = activeWalk.target
            local tx = tgt.x + 0.5
            local ty = tgt.y + 0.5
            local dx = tx - npcPos.x
            local dy = ty - npcPos.y
            local dist = math.sqrt(dx * dx + dy * dy)
            if dist <= arrivalThreshold or dist <= npcSpeed then
                npcPos.x = tx
                npcPos.y = ty
                local walk = activeWalk
                activeWalk = nil
                if walk.onComplete then
                    walk.onComplete()
                end
            else
                npcPos.x = npcPos.x + (dx / dist) * npcSpeed
                npcPos.y = npcPos.y + (dy / dist) * npcSpeed
            end
        end
    end

    function f:step(d, n, playerFn)
        n = n or 1
        for i = 1, n do
            if playerFn then playerFn(i, self) end
            self:advancePhysical()
            d:tick()
        end
    end

    return f
end

-- 57. Advancing NPC tracks player in steady forward movement with bounded retargets
test('advancing NPC tracks player in steady forward movement with bounded retargets', function()
    local f = makeAdvancingFixture({npcPos = {x = 10, y = 10, z = 0}, playerPos = {x = 14, y = 10, z = 0}, npcSpeed = 0.1})
    local d = Commands.new(f.observe, function(r) return f.adapter.stop() end, f.identityProvider, function(t, onC, onF) return f.adapter.walk(nil, t, onC, onF) end)
    local res = d:execute('follow')
    assert(res.state == 'running')
    assert(#f.walkCalls == 1)

    -- Player walks East at 0.05 tiles/tick for 80 ticks
    f:step(d, 80, function(i, fix)
        fix.playerPos.x = fix.playerPos.x + 0.05
    end)

    -- Sarah advanced significantly
    assert(f.npcPos.x > 15.0)
    -- Follow is still active
    assert(d.active and d.active.command == 'follow' and d.active.stepState == 'walking')
    -- Distance between Sarah and player stayed well within 8-tile leash
    local dist = math.abs(f.playerPos.x - f.npcPos.x)
    assert(dist <= 4.0 and dist >= 1.0)
    -- Retargeting is bounded (not every tick; ~4-10 walk calls over 80 ticks)
    assert(#f.walkCalls >= 4 and #f.walkCalls <= 10)
    assert(#d.noticeQueue == 0)
end)

-- 58. Advancing NPC tracks player through repeated 90-degree orthogonal turns
test('advancing NPC tracks player through repeated 90-degree orthogonal turns', function()
    local f = makeAdvancingFixture({npcPos = {x = 10, y = 10, z = 0}, playerPos = {x = 13, y = 10, z = 0}, npcSpeed = 0.1})
    local d = Commands.new(f.observe, function(r) return f.adapter.stop() end, f.identityProvider, function(t, onC, onF) return f.adapter.walk(nil, t, onC, onF) end)
    d:execute('follow')

    -- Leg 1: East for 25 ticks (delta X = +2.0)
    f:step(d, 25, function(i, fix) fix.playerPos.x = fix.playerPos.x + 0.08 end)
    assert(d.active and d.active.command == 'follow')

    -- Leg 2: North for 25 ticks (delta Y = +2.0)
    f:step(d, 25, function(i, fix) fix.playerPos.y = fix.playerPos.y + 0.08 end)
    assert(d.active and d.active.command == 'follow')

    -- Leg 3: West for 25 ticks (delta X = -2.0)
    f:step(d, 25, function(i, fix) fix.playerPos.x = fix.playerPos.x - 0.08 end)
    assert(d.active and d.active.command == 'follow')

    -- Leg 4: South for 25 ticks (delta Y = -2.0)
    f:step(d, 25, function(i, fix) fix.playerPos.y = fix.playerPos.y - 0.08 end)
    assert(d.active and d.active.command == 'follow')

    -- Sarah successfully navigated around the loop
    local dx = f.playerPos.x - f.npcPos.x
    local dy = f.playerPos.y - f.npcPos.y
    local distSq = dx * dx + dy * dy
    assert(distSq <= 16.0, 'Sarah stayed within tracking range across turns')
    assert(#f.walkCalls >= 4 and #f.walkCalls <= 15)
    assert(d.active ~= nil)
end)

-- 59. Advancing NPC halts upon entering 2-tile deadzone and resumes on departure
test('advancing NPC halts upon entering 2-tile deadzone and resumes on departure', function()
    local f = makeAdvancingFixture({npcPos = {x = 10, y = 10, z = 0}, playerPos = {x = 14, y = 10, z = 0}, npcSpeed = 0.1})
    local d = Commands.new(f.observe, function(r) return f.adapter.stop() end, f.identityProvider, function(t, onC, onF) return f.adapter.walk(nil, t, onC, onF) end)
    d:execute('follow')

    -- Player stays stationary at (14, 10). Sarah advances toward (13, 10).
    -- After ~25-35 ticks, Sarah enters deadzone (dist <= 2.0) and minRetargetTicks elapses
    f:step(d, 35)

    -- Sarah halted cleanly into idle state within deadzone
    assert(d.active and d.active.stepState == 'idle')
    assert(d.active.summary == 'Following player (in range)')
    local walksBeforeRest = #f.walkCalls
    local stoppedNpcX = f.npcPos.x

    -- Player stays stationary for another 30 ticks: Sarah stays put, no new walks
    f:step(d, 30)
    assert(d.active and d.active.stepState == 'idle')
    assert(#f.walkCalls == walksBeforeRest)
    assert(f.npcPos.x == stoppedNpcX)

    -- Player departs to (17, 10): Sarah resumes on first tick!
    f.playerPos.x = 17
    d:tick()
    assert(#f.walkCalls == walksBeforeRest + 1)
    assert(d.active and d.active.stepState == 'walking')
    assert(d.active.currentTarget.x == 16 and d.active.currentTarget.y == 10)
end)

-- 60. Deadzone boundary oscillations do not cause path thrashing
test('deadzone boundary oscillations do not cause path thrashing', function()
    local f = makeAdvancingFixture({npcPos = {x = 10, y = 10, z = 0}, playerPos = {x = 12.05, y = 10, z = 0}, npcSpeed = 0.05})
    local d = Commands.new(f.observe, function(r) return f.adapter.stop() end, f.identityProvider, function(t, onC, onF) return f.adapter.walk(nil, t, onC, onF) end)
    d:execute('follow')
    local initWalks = #f.walkCalls

    -- Player oscillates back and forth across 2-tile boundary (x = 12.05 <-> 11.95) every 2 ticks
    f:step(d, 40, function(i, fix)
        fix.playerPos.x = (i % 2 == 0) and 12.05 or 11.95
    end)

    -- Retarget budget is strictly throttled, no thrashing
    local addedWalks = #f.walkCalls - initWalks
    assert(addedWalks <= 4, 'boundary oscillations throttled to <= 4 walk steps')
    assert(d.active ~= nil)
end)

-- 61. Minor player movement within same target square continues walking without restarting step
test('minor player movement within same target square continues walking without restarting step', function()
    local f = makeAdvancingFixture({npcPos = {x = 10, y = 10, z = 0}, playerPos = {x = 14.1, y = 10.1, z = 0}, npcSpeed = 0.05})
    local d = Commands.new(f.observe, function(r) return f.adapter.stop() end, f.identityProvider, function(t, onC, onF) return f.adapter.walk(nil, t, onC, onF) end)
    d:execute('follow')
    assert(#f.walkCalls == 1)
    local initialTarget = d.active.currentTarget

    -- Player shifts slightly within square 14, 10 (target candidate square 13, 10 remains unchanged)
    f:step(d, 20, function(i, fix)
        fix.playerPos.x = 14.1 + (i % 3) * 0.05
        fix.playerPos.y = 10.1 + (i % 2) * 0.05
    end)

    -- Zero path restarts: step 1 continues undisturbed
    assert(#f.walkCalls == 1)
    assert(d.active.currentTarget.x == initialTarget.x and d.active.currentTarget.y == initialTarget.y)
    assert(f.npcPos.x > 10.5, 'Sarah advanced without interruption')
end)

-- 62. Stalled movement while player causes retargets times out cleanly at 600 ticks
test('stalled movement while player causes retargets times out cleanly at 600 ticks', function()
    local f = makeAdvancingFixture({npcPos = {x = 10, y = 10, z = 0}, playerPos = {x = 14, y = 10, z = 0}, stalled = true})
    local d = Commands.new(f.observe, function(r) return f.adapter.stop() end, f.identityProvider, function(t, onC, onF) return f.adapter.walk(nil, t, onC, onF) end)
    d:execute('follow')
    assert(d.active and d.active.command == 'follow')

    -- Player alternates between (14, 10) and (14, 13) every 6 ticks (shift = 3 tiles, triggering retarget each time)
    -- Sarah is stalled (position remains at 10, 10)
    for tick = 1, 599 do
        f:step(d, 1, function(i, fix)
            if tick % 6 == 0 then
                fix.playerPos.y = (fix.playerPos.y == 10) and 13 or 10
            end
        end)
        assert(d.active ~= nil, 'still active at tick ' .. tick)
        assert(d.active.stepTicks <= 6, 'stepTicks kept resetting on retarget')
        assert(d.active.stallTicks == tick, 'stallTicks accumulated across retargets')
    end

    -- Tick 600: stallTicks reaches 600 -> timeout cancellation fires!
    f:step(d, 1)
    assert(d.active == nil, 'follow timed out at tick 600')
    assert(d.lastAction.state == 'cancelled')
    assert(d.lastAction.reason == 'timeout')
    local notices = d:consumeNotices()
    assert(#notices == 1)
    assert(notices[1].reason == 'timeout')
    assert(notices[1].message:find('Follow disengaged: timeout%.'))
end)

-- 63. Healthy long-running follow runs for 1200 ticks without false timeout
test('healthy long-running follow runs for 1200 ticks without false timeout', function()
    local f = makeAdvancingFixture({npcPos = {x = 10, y = 10, z = 0}, playerPos = {x = 14, y = 10, z = 0}, npcSpeed = 0.1})
    local d = Commands.new(f.observe, function(r) return f.adapter.stop() end, f.identityProvider, function(t, onC, onF) return f.adapter.walk(nil, t, onC, onF) end)
    d:execute('follow')

    -- Player walks East at 0.06 tiles/tick for 1200 ticks (twice the maxStallTicks bound)
    f:step(d, 1200, function(i, fix)
        fix.playerPos.x = fix.playerPos.x + 0.06
    end)

    -- Follow is still running healthily
    assert(d.active ~= nil)
    assert(d.active.command == 'follow')
    assert(d.active.stallTicks < 20, 'stallTicks continuously reset by progress')
    assert(f.npcPos.x > 70.0, 'Sarah traveled distance with player')
    assert(#d.noticeQueue == 0)
end)

-- 64. Synchronous engine stop callbacks during user stop, retarget, and in-range halting are defused
test('synchronous engine stop callbacks during user stop, retarget, and in-range halting are defused', function()
    -- Part A: synchronous fail callback during retarget
    local f1 = makeAdvancingFixture({npcPos = {x = 10, y = 10, z = 0}, playerPos = {x = 14, y = 10, z = 0}, syncStopFail = true})
    local d1 = Commands.new(f1.observe, function(r) return f1.adapter.stop() end, f1.identityProvider, function(t, onC, onF) return f1.adapter.walk(nil, t, onC, onF) end)
    d1:execute('follow')
    -- Player moves at tick 6 to trigger retarget
    f1:step(d1, 6, function(i, fix) fix.playerPos.x = 16 end)
    -- Retarget succeeded, synchronous fail was defused
    assert(d1.active and d1.active.stepState == 'walking' and d1.active.currentTarget.x == 15)
    assert(#d1.noticeQueue == 0)

    -- Part B: synchronous complete callback during in-range halt
    local f2 = makeAdvancingFixture({npcPos = {x = 10, y = 10, z = 0}, playerPos = {x = 13.5, y = 10, z = 0}, syncStopComplete = true})
    local d2 = Commands.new(f2.observe, function(r) return f2.adapter.stop() end, f2.identityProvider, function(t, onC, onF) return f2.adapter.walk(nil, t, onC, onF) end)
    d2:execute('follow')
    f2.playerPos.x = 11.5 -- move inside deadzone
    f2:step(d2, 6)
    assert(d2.active and d2.active.stepState == 'idle')
    assert(d2.active.summary == 'Following player (in range)')

    -- Part C: synchronous fail callback during user stop command
    local f3 = makeAdvancingFixture({npcPos = {x = 10, y = 10, z = 0}, playerPos = {x = 14, y = 10, z = 0}, syncStopFail = true})
    local d3 = Commands.new(f3.observe, function(r) return f3.adapter.stop() end, f3.identityProvider, function(t, onC, onF) return f3.adapter.walk(nil, t, onC, onF) end)
    d3:execute('follow')
    local stopRes = d3:execute('stop')
    assert(stopRes.state == 'completed')
    assert(d3.active == nil)
    assert(d3.lastAction.reason == 'stopped by user')
    assert(#d3.noticeQueue == 0)
end)

-- 65. Failed engine stop during deadzone halting blocks movement pending recovery
test('failed engine stop during deadzone halting blocks movement pending recovery', function()
    local f = makeAdvancingFixture({npcPos = {x = 10, y = 10, z = 0}, playerPos = {x = 13.5, y = 10, z = 0}})
    local d = Commands.new(f.observe, function(r) return f.adapter.stop() end, f.identityProvider, function(t, onC, onF) return f.adapter.walk(nil, t, onC, onF) end)
    d:execute('follow')
    assert(d.active and d.active.stepState == 'walking')

    -- Player enters deadzone
    f.playerPos.x = 11.5
    f:step(d, 5)
    -- Next tick triggers in-range stop; make engine stop fail
    f.setStopFail(true)
    d:tick()

    -- Follow disengages with stop failed
    assert(d.active == nil)
    assert(d.stopFailed == 'stop failed')
    local notices = d:consumeNotices()
    assert(#notices == 1)
    assert(notices[1].message:find('Warning: engine stop failed %(stop failed%)'))
    assert(notices[1].message:find('movement blocked pending recovery%.'))

    -- Subsequent follow is blocked
    local blkRes = d:execute('follow')
    assert(blkRes.state == 'rejected')
    assert(blkRes.lines[1]:find('movement blocked until stop recovers%.'))

    -- Recovery via successful stop
    f.setStopFail(false)
    local recRes = d:execute('stop')
    assert(recRes.state == 'completed')
    assert(d.stopFailed == nil)
    assert(hasLine(recRes.lines, 'Prior engine stop failure cleared; movement recovered%.'))
end)

-- 66. Lifecycle events during active advancing tracking cancel follow cleanly
test('lifecycle events during active advancing tracking cancel follow cleanly', function()
    -- Case A: Controller replacement during advancing tracking
    local f1 = makeAdvancingFixture({npcPos = {x = 10, y = 10, z = 0}, playerPos = {x = 14, y = 10, z = 0}, npcSpeed = 0.1})
    local currentCtrl1 = f1.controller
    local d1 = Commands.new(f1.observe, function(r) return f1.adapter.stop() end, function() return currentCtrl1, f1.npc end, function(t, onC, onF) return f1.adapter.walk(nil, t, onC, onF) end)
    d1:execute('follow')
    f1:step(d1, 3)
    assert(d1.active ~= nil)
    -- Controller replaced
    currentCtrl1 = {npc = f1.npc, adapter = f1.adapter}
    d1:tick()
    assert(d1.active == nil)
    assert(d1.lastAction.reason == 'controller replaced')

    -- Case B: NPC replacement during advancing tracking
    local f2 = makeAdvancingFixture({npcPos = {x = 10, y = 10, z = 0}, playerPos = {x = 14, y = 10, z = 0}, npcSpeed = 0.1})
    local currentNpc2 = f2.npc
    local d2 = Commands.new(f2.observe, function(r) return f2.adapter.stop() end, function() return f2.controller, currentNpc2 end, function(t, onC, onF) return f2.adapter.walk(nil, t, onC, onF) end)
    d2:execute('follow')
    f2:step(d2, 3)
    assert(d2.active ~= nil)
    -- NPC replaced
    currentNpc2 = {getX = function() return 10 end, getY = function() return 10 end, getZ = function() return 0 end}
    d2:tick()
    assert(d2.active == nil)
    assert(d2.lastAction.reason == 'npc replaced')

    -- Case C: Session reset during advancing tracking
    local f3 = makeAdvancingFixture({npcPos = {x = 10, y = 10, z = 0}, playerPos = {x = 14, y = 10, z = 0}, npcSpeed = 0.1})
    local d3 = Commands.new(f3.observe, function(r) return f3.adapter.stop() end, f3.identityProvider, function(t, onC, onF) return f3.adapter.walk(nil, t, onC, onF) end)
    d3:execute('follow')
    f3:step(d3, 3)
    local s1Walk = f3.getActiveWalk()
    d3:reset()
    assert(d3.active == nil)
    assert(d3.sequence == 0)
    -- Old callback from session 1 cannot mutate session 2
    if s1Walk and s1Walk.onComplete then s1Walk.onComplete() end
    assert(d3.active == nil)
    d3:execute('follow')
    assert(d3.active and d3.active.session == 2 and d3.active.id == 1)
end)

print('RESULT ' .. count .. ' follow checks passed')
''')
