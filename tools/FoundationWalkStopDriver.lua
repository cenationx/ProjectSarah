-- Temporary native acceptance driver for Project Sarah.
-- Tests walk and stop commands via mouse interaction without manual typing.
-- Strictly restricted to isolated profile and SarahConsoleNativeCase.
-- Excluded from normal production mod deployment.

require 'ISUI/ISPanel'
require 'ISUI/ISButton'

local old = SarahWalkStopDriver
if old and old.teardown then
    old.teardown()
end

local driver = {
    panel = nil,
    phase = 'IDLE', -- 'IDLE', 'WAIT_MOVEMENT', 'WAIT_HALT', 'MONITOR_WALK'
    statusText = 'Ready (Idle)',
    currentRun = nil,
    runId = 0,
    sessionId = 1,
    lastResult = nil,
    monitoredWalkId = nil
}

function driver.allowed()
    if not Core or not Core.getMyDocumentFolder then return false end
    local okRoot, root = pcall(function() return Core.getMyDocumentFolder():gsub('\\','/'):gsub('/$','') end)
    if not okRoot or root ~= 'G:/Codex/Project Sarah/runtime/isolated' then return false end
    if isClient and isClient() then return false end
    if isServer and isServer() then return false end
    if not getWorld or not getWorld() or not getWorld().getWorld then return false end
    local okWorld, world = pcall(function() return getWorld():getWorld() end)
    if not okWorld or world ~= 'SarahConsoleNativeCase' then return false end
    if not getSpecificPlayer or not getSpecificPlayer(0) then return false end
    return true
end

local function getDispatch()
    if not SarahConsole or not SarahConsole.getDispatch then
        return nil
    end
    return SarahConsole.getDispatch()
end

function driver.isTestRunning()
    return driver.phase == 'WAIT_MOVEMENT' or driver.phase == 'WAIT_HALT'
end

function driver.getPhase()
    return driver.phase
end

function driver.getLastResult()
    return driver.lastResult
end

function driver.getPanel()
    return driver.panel
end

function driver.setStatusText(text)
    driver.statusText = text or 'Idle'
end

-- Button 1: Status & History
function driver.onStatusHistory()
    if not driver.allowed() then
        print('[SarahDriver] REFUSED: profile/world must be exact isolated SarahConsoleNativeCase')
        return
    end
    if driver.isTestRunning() then
        print('[SarahDriver] OVERLAP_REFUSED: driver test currently in progress (' .. driver.phase .. ')')
        return
    end
    local dispatch = getDispatch()
    if not dispatch then
        print('[SarahDriver] REFUSED: Sarah Console dispatch unavailable')
        driver.setStatusText('REFUSED: No dispatch')
        return
    end
    local st = dispatch:execute('status')
    local hist = dispatch:execute('history')
    local stLines = (st and st.lines and table.concat(st.lines, ' | ')) or 'nil'
    local histLines = (hist and hist.lines and table.concat(hist.lines, ' | ')) or 'nil'
    print('[SarahDriver] STATUS: id=#' .. tostring(st.id) .. ' state=' .. tostring(st.state) .. ' lines=' .. stLines)
    print('[SarahDriver] HISTORY: id=#' .. tostring(hist.id) .. ' state=' .. tostring(hist.state) .. ' lines=' .. histLines)
    driver.setStatusText('Status/History logged')
end

-- Button 2: Walk to Player
function driver.onWalk()
    if not driver.allowed() then
        print('[SarahDriver] REFUSED: profile/world must be exact isolated SarahConsoleNativeCase')
        return
    end
    if driver.isTestRunning() then
        print('[SarahDriver] OVERLAP_REFUSED: driver test currently in progress (' .. driver.phase .. ')')
        return
    end
    local dispatch = getDispatch()
    if not dispatch then
        print('[SarahDriver] REFUSED: Sarah Console dispatch unavailable')
        driver.setStatusText('REFUSED: No dispatch')
        return
    end
    local obs = dispatch.observe(false)
    local sx = obs and obs.npc and obs.npc.x or 0
    local sy = obs and obs.npc and obs.npc.y or 0
    local px = obs and obs.player and obs.player.x or 0
    local py = obs and obs.player and obs.player.y or 0
    local res = dispatch:execute('walk here')
    local resLines = (res and res.lines and table.concat(res.lines, ' | ')) or 'nil'
    print(string.format('[SarahDriver] WALK_START id=#%d state=%s sarah=(%.2f,%.2f) player=(%.2f,%.2f) lines=%s',
        res.id, res.state, sx, sy, px, py, resLines))
    driver.setStatusText('Walk #' .. res.id .. ': ' .. res.state)
    if res.state == 'running' then
        driver.phase = 'MONITOR_WALK'
        driver.monitoredWalkId = res.id
    end
end

-- Button 3: Manual Stop
function driver.onStop()
    if not driver.allowed() then
        print('[SarahDriver] REFUSED: profile/world must be exact isolated SarahConsoleNativeCase')
        return
    end
    if driver.isTestRunning() then
        print('[SarahDriver] OVERLAP_REFUSED: automated walk-then-stop in progress (' .. driver.phase .. ')')
        return
    end
    local dispatch = getDispatch()
    if not dispatch then
        print('[SarahDriver] REFUSED: Sarah Console dispatch unavailable')
        driver.setStatusText('REFUSED: No dispatch')
        return
    end
    local res = dispatch:execute('stop')
    local obs = dispatch.observe(false)
    local sx = obs and obs.npc and obs.npc.x or 0
    local sy = obs and obs.npc and obs.npc.y or 0
    local resLines = (res and res.lines and table.concat(res.lines, ' | ')) or 'nil'
    print(string.format('[SarahDriver] STOP_MANUAL id=#%d state=%s sarah=(%.2f,%.2f) lines=%s',
        res.id, res.state, sx, sy, resLines))
    driver.setStatusText('Stop #' .. res.id .. ': ' .. res.state)
    driver.phase = 'IDLE'
end

-- Button 4: Automated Walk-then-Stop
function driver.onWalkThenStop()
    if not driver.allowed() then
        print('[SarahDriver] REFUSED: profile/world must be exact isolated SarahConsoleNativeCase')
        return
    end
    if driver.isTestRunning() then
        print('[SarahDriver] OVERLAP_REFUSED: driver test currently in progress (' .. driver.phase .. ')')
        return
    end
    local dispatch = getDispatch()
    if not dispatch then
        print('[SarahDriver] REFUSED: Sarah Console dispatch unavailable')
        driver.setStatusText('REFUSED: No dispatch')
        return
    end
    local obs = dispatch.observe(false)
    if not obs or obs.state ~= 'active' or not obs.npc or not obs.player then
        local err = (obs and obs.state) or 'unavailable'
        print('[SarahDriver] WALK_THEN_STOP REFUSED: Sarah state is ' .. err .. ' or position missing')
        driver.setStatusText('REFUSED: Sarah ' .. err)
        return
    end
    if dispatch.active then
        print(string.format('[SarahDriver] WALK_THEN_STOP REFUSED: dispatch busy with #%d %s', dispatch.active.id, dispatch.active.command))
        driver.setStatusText('REFUSED: Busy with #' .. dispatch.active.id)
        return
    end
    local sx, sy, sz = obs.npc.x, obs.npc.y, obs.npc.z
    local px, py, pz = obs.player.x, obs.player.y, obs.player.z
    local tx, ty, tz = math.floor(px), math.floor(py), math.floor(pz)
    if math.floor(sx) == tx and math.floor(sy) == ty and math.floor(sz) == tz then
        print(string.format('[SarahDriver] WALK_THEN_STOP REFUSED: Sarah already at target square (%d,%d,%d); manually reposition player first.', tx, ty, tz))
        driver.setStatusText('REFUSED: Already at target')
        return
    end
    local res = dispatch:execute('walk here')
    if res.state ~= 'running' then
        local linesStr = (res.lines and table.concat(res.lines, ' | ')) or 'nil'
        print(string.format('[SarahDriver] WALK_THEN_STOP FAILED: walk command returned %s: %s', res.state, linesStr))
        driver.setStatusText('FAILED: Walk ' .. res.state)
        driver.lastResult = 'FAILED'
        return
    end
    driver.phase = 'WAIT_MOVEMENT'
    driver.runId = (driver.runId or 0) + 1
    driver.currentRun = {
        sessionId = driver.sessionId,
        runId = driver.runId,
        walkId = res.id,
        startSarah = {x = sx, y = sy, z = sz},
        startPlayer = {x = px, y = py, z = pz},
        target = {x = tx, y = ty, z = tz},
        tickCount = 0,
        maxWaitMovementTicks = 180,
        stopPos = nil,
        stopRes = nil,
        haltTicks = 0
    }
    print(string.format('[SarahDriver] WALK_THEN_STOP STARTED: run=%d walkId=#%d target=(%d,%d,%d) startSarah=(%.2f,%.2f,%.0f) player=(%.2f,%.2f,%.0f)',
        driver.runId, res.id, tx, ty, tz, sx, sy, sz, px, py, pz))
    driver.setStatusText('Walk #' .. res.id .. ' running, awaiting movement...')
end

function driver.tick()
    if not driver.allowed() then return end
    local dispatch = getDispatch()
    if not dispatch then return end

    if driver.phase == 'WAIT_MOVEMENT' then
        local run = driver.currentRun
        if not run or run.sessionId ~= driver.sessionId then
            driver.phase = 'IDLE'
            return
        end
        run.tickCount = run.tickCount + 1
        local obs = dispatch.observe(false)
        if not obs or obs.state ~= 'active' or not obs.npc then
            print(string.format('[SarahDriver] WALK_THEN_STOP FAILED: Sarah inactive/unloaded at tick %d', run.tickCount))
            driver.setStatusText('FAILED: Inactive/unloaded')
            driver.lastResult = 'FAILED'
            driver.phase = 'IDLE'
            return
        end
        local cx, cy, cz = obs.npc.x, obs.npc.y, obs.npc.z

        -- Check if active action finished before movement was observed
        if not dispatch.active or dispatch.active.id ~= run.walkId then
            local last = dispatch.lastAction
            if last and last.state == 'completed' then
                print(string.format('[SarahDriver] WALK_THEN_STOP INVALID: Sarah arrived too soon before stop could be tested (early arrival at tick %d). Walk distance too short.', run.tickCount))
                driver.setStatusText('INVALID: Arrived too soon')
                driver.lastResult = 'INVALID'
            else
                local st = last and last.state or 'unknown'
                local re = last and last.reason or ''
                print(string.format('[SarahDriver] WALK_THEN_STOP FAILED: Action ended before movement at tick %d (state=%s reason=%s)', run.tickCount, st, re))
                driver.setStatusText('FAILED: Action ended (' .. st .. ')')
                driver.lastResult = 'FAILED'
            end
            driver.phase = 'IDLE'
            return
        end

        -- Check if Sarah reached target square already
        if math.floor(cx) == run.target.x and math.floor(cy) == run.target.y then
            print(string.format('[SarahDriver] WALK_THEN_STOP INVALID: Sarah reached target square before stop at tick %d (early arrival).', run.tickCount))
            driver.setStatusText('INVALID: Arrived too soon')
            driver.lastResult = 'INVALID'
            driver.phase = 'IDLE'
            return
        end

        -- Check observable movement (at least 0.2 tiles)
        local dx = cx - run.startSarah.x
        local dy = cy - run.startSarah.y
        local movedSq = dx * dx + dy * dy
        if movedSq >= 0.04 then
            local movedDist = math.sqrt(movedSq)
            print(string.format('[SarahDriver] WALK_THEN_STOP MOVEMENT_OBSERVED: tick=%d moved=%.2f tiles to (%.2f,%.2f,%.0f)', run.tickCount, movedDist, cx, cy, cz))
            run.stopPos = {x = cx, y = cy, z = cz}
            run.stopRes = dispatch:execute('stop')
            local stopLines = (run.stopRes.lines and table.concat(run.stopRes.lines, ' | ')) or 'nil'
            print(string.format('[SarahDriver] WALK_THEN_STOP STOP_ISSUED: walkId=#%d stopId=#%d stopState=%s stopPos=(%.2f,%.2f,%.0f) lines=%s',
                run.walkId, run.stopRes.id, run.stopRes.state, cx, cy, cz, stopLines))
            driver.phase = 'WAIT_HALT'
            driver.setStatusText('Stop #' .. run.stopRes.id .. ' issued, waiting halt...')
            return
        end

        -- Check movement timeout
        if run.tickCount >= run.maxWaitMovementTicks then
            print(string.format('[SarahDriver] WALK_THEN_STOP TIMEOUT: No movement observed after %d ticks (stayed at %.2f,%.2f).', run.tickCount, cx, cy))
            driver.setStatusText('FAILED: Movement timeout')
            driver.lastResult = 'TIMEOUT'
            dispatch:execute('stop')
            driver.phase = 'IDLE'
            return
        end

    elseif driver.phase == 'WAIT_HALT' then
        local run = driver.currentRun
        if not run or run.sessionId ~= driver.sessionId then
            driver.phase = 'IDLE'
            return
        end
        run.haltTicks = run.haltTicks + 1
        if run.haltTicks < 5 then return end

        local obs = dispatch.observe(false)
        local finalPos = (obs and obs.npc) or run.stopPos
        local atTarget = (math.floor(finalPos.x) == run.target.x and math.floor(finalPos.y) == run.target.y)
        local actionCancelled = (dispatch.lastAction and dispatch.lastAction.id == run.walkId and dispatch.lastAction.state == 'cancelled')
        local stopCompleted = (run.stopRes and run.stopRes.state == 'completed')
        local movedTotal = math.sqrt((finalPos.x - run.startSarah.x)^2 + (finalPos.y - run.startSarah.y)^2)
        local distToTarget = math.sqrt(((run.target.x + 0.5) - finalPos.x)^2 + ((run.target.y + 0.5) - finalPos.y)^2)

        if actionCancelled and stopCompleted and not atTarget then
            print(string.format('[SarahDriver] WALK_THEN_STOP PASS: Mid-walk cancellation verified. walkId=#%d stopId=#%d start=(%.2f,%.2f) stoppedAt=(%.2f,%.2f) target=(%d,%d) moved=%.2f distToTarget=%.2f',
                run.walkId, run.stopRes.id, run.startSarah.x, run.startSarah.y, finalPos.x, finalPos.y, run.target.x, run.target.y, movedTotal, distToTarget))
            driver.setStatusText('PASS: Mid-walk cancelled')
            driver.lastResult = 'PASS'
        elseif atTarget then
            print('[SarahDriver] WALK_THEN_STOP INVALID: Sarah reached target square despite stop (arrival too fast or stop late).')
            driver.setStatusText('INVALID: Reached target')
            driver.lastResult = 'INVALID'
        else
            print(string.format('[SarahDriver] WALK_THEN_STOP FAILED: cancellation check failed (actionCancelled=%s stopCompleted=%s atTarget=%s)',
                tostring(actionCancelled), tostring(stopCompleted), tostring(atTarget)))
            driver.setStatusText('FAILED: Stop check failed')
            driver.lastResult = 'FAILED'
        end
        driver.phase = 'IDLE'

    elseif driver.phase == 'MONITOR_WALK' then
        local obs = dispatch.observe(false)
        if not dispatch.active or dispatch.active.id ~= driver.monitoredWalkId then
            local last = dispatch.lastAction
            local st = last and last.state or 'unknown'
            local re = last and last.reason or ''
            local sx = obs and obs.npc and obs.npc.x or 0
            local sy = obs and obs.npc and obs.npc.y or 0
            print(string.format('[SarahDriver] WALK_ENDED id=#%d state=%s reason=%s sarah=(%.2f,%.2f)',
                driver.monitoredWalkId, st, re, sx, sy))
            driver.setStatusText('Walk #' .. driver.monitoredWalkId .. ' ' .. st)
            driver.phase = 'IDLE'
        end
    end
end

-- Panel creation & UI setup
local Panel = ISPanel:derive('SarahWalkStopDriverPanel')
function Panel:new(x, y, w, h, d)
    local o = ISPanel.new(self, x, y, w, h)
    o.driver = d
    return o
end

function Panel:initialise()
    ISPanel.initialise(self)
    local btnW = self.width - 20

    local btnStatus = ISButton:new(10, 48, btnW, 22, 'Status & History', self, function(target)
        target.driver.onStatusHistory()
    end)
    btnStatus:initialise()
    self:addChild(btnStatus)

    local btnWalk = ISButton:new(10, 74, btnW, 22, 'Walk to Player', self, function(target)
        target.driver.onWalk()
    end)
    btnWalk:initialise()
    self:addChild(btnWalk)

    local btnStop = ISButton:new(10, 100, btnW, 22, 'Stop', self, function(target)
        target.driver.onStop()
    end)
    btnStop:initialise()
    self:addChild(btnStop)

    local btnWalkStop = ISButton:new(10, 126, btnW, 22, 'Walk then Stop', self, function(target)
        target.driver.onWalkThenStop()
    end)
    btnWalkStop:initialise()
    self:addChild(btnWalkStop)

    local btnClose = ISButton:new(10, 152, btnW, 22, 'Close Driver', self, function(target)
        target:setVisible(false)
    end)
    btnClose:initialise()
    self:addChild(btnClose)
end

function Panel:prerender()
    if self.drawRect then
        self:drawRect(0, 0, self.width, self.height, 0.85, 0.1, 0.1, 0.1)
        self:drawRectBorder(0, 0, self.width, self.height, 0.9, 0.4, 0.4, 0.4)
    end
    if self.drawText then
        self:drawText('Sarah Walk/Stop Driver', 10, 8, 1, 1, 1, 1, (UIFont and UIFont.Small) or 1)
        local st = self.driver and self.driver.statusText or 'Idle'
        self:drawText(st:sub(1, 28), 10, 26, 0.8, 0.9, 0.8, 1, (UIFont and UIFont.Small) or 1)
    end
end

function driver.open(panelX, panelY)
    if not driver.allowed() then
        print('[SarahDriver] REFUSED: profile/world must be exact isolated SarahConsoleNativeCase')
        return
    end
    if driver.panel then
        driver.panel:setVisible(true)
        return driver.panel
    end
    local px = panelX or 20
    local py = panelY or 200
    local p = Panel:new(px, py, 200, 182, driver)
    p:initialise()
    p:addToUIManager()
    driver.panel = p
    return p
end

function driver.init(panelX, panelY)
    return driver.open(panelX, panelY)
end

function driver.teardown()
    if driver.panel then
        driver.panel:removeFromUIManager()
        driver.panel = nil
    end
    driver.phase = 'IDLE'
    driver.statusText = 'Ready (Idle)'
    driver.currentRun = nil
    driver.sessionId = driver.sessionId + 1
    driver.monitoredWalkId = nil
    print('[SarahDriver] TEARDOWN complete')
end

function driver.onGameStart()
    driver.teardown()
    if driver.allowed() then
        driver.open()
    end
end

function driver.onContextMenu(playerIndex, context, objects, test)
    if test or playerIndex ~= 0 or not driver.allowed() then return end
    context:addOption('Sarah: open test driver', nil, function()
        driver.open()
    end)
end

Events.OnTick.Add(driver.tick)
Events.OnGameStart.Add(driver.onGameStart)
Events.OnMainMenuEnter.Add(driver.teardown)
Events.OnFillWorldObjectContextMenu.Add(driver.onContextMenu)

SarahWalkStopDriver = driver
return driver
