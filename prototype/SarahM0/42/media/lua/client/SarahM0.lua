-- Minimal engine probe, deliberately independent of PZNS's jobs and AI.
require "TimedActions/WalkToTimedAction"
require "TimedActions/ISTimedActionQueue"
SarahM0 = { npc = nil, ticks = 0, attempted = false }
local function log(message) print("[SarahM0] " .. tostring(message)) end
local function protected(label, fn)
    local ok, err = pcall(fn)
    if not ok then log("FAIL " .. label .. ": " .. tostring(err)) end
    return ok
end
local function spawn()
    local player = getSpecificPlayer(0)
    if not player or not player:getSquare() then return end
    local square = getCell():getGridSquare(player:getX() + 2, player:getY(), player:getZ())
    if not square or not square:isFree(false) then
        log("SKIP: adjacent square is blocked; use the context menu to retry elsewhere")
        return
    end
    local previous = IsoPlayer.getInstance()
    protected("spawn", function()
        local stored = player:getModData().SarahM0Checkpoint
        local canRestore = stored and fileExists(stored.file)
        local desc = SurvivorFactory.CreateSurvivor(SurvivorFactory.SurvivorType.Neutral, true)
        desc:setForename("Sarah")
        desc:setSurname("M0")
        local npc = IsoPlayer.new(getCell(), desc, square:getX(), square:getY(), square:getZ())
        SarahM0.npc = npc -- keep a reference even if a later probe fails
        npc:setNpc(true)
        npc:setSceneCulled(false)
        npc:getModData().SarahM0 = true
        if canRestore then
            desc:setForename("Unloaded")
            npc:load(stored.file)
            npc:setNpc(true)
            npc:setSceneCulled(false)
            log("RESTORED name=" .. npc:getDescriptor():getForename() .. " inventory=" .. npc:getInventory():getItems():size() .. " dead=" .. tostring(npc:isDead()))
            log("RESTORED_TOKEN " .. npc:getInventory():getItems():get(0):getName())
        end
        log("SPAWN npc=" .. tostring(npc:isNpc()) .. " name=" .. npc:getDescriptor():getForename())
        local item = nil
        if not canRestore then item = npc:getInventory():AddItem("Base.Bandage") end
        log("INVENTORY add=" .. tostring(item ~= nil) .. " count=" .. npc:getInventory():getItems():size())
        log("POSITION " .. npc:getX() .. "," .. npc:getY() .. "," .. npc:getZ())
    end)
    IsoPlayer.setInstance(previous)
    log("LOCAL_PLAYER preserved=" .. tostring(IsoPlayer.getInstance() == previous))
end
local function exercise(label, fn)
    if SarahM0.npc then protected(label, fn) end
end
local function remove()
    if not SarahM0.npc then return end
    protected("remove", function()
        SarahM0.npc:removeFromWorld()
        SarahM0.npc:removeFromSquare()
        SarahM0.npc = nil
        log("REMOVED")
    end)
end
Events.OnGameStart.Add(function()
    log("GAME_START version=" .. getCore():getVersion())
end)
Events.OnTick.Add(function()
    SarahM0.ticks = SarahM0.ticks + 1
    if SarahM0.ticks == 180 and not SarahM0.attempted then
        SarahM0.attempted = true
        spawn()
    end
    if SarahM0.ticks == 360 then
        exercise("walk", function()
            local npc = SarahM0.npc
            SarahM0.startX, SarahM0.startY = npc:getX(), npc:getY()
            ISTimedActionQueue.add(ISWalkToTimedAction:new(npc, getSpecificPlayer(0):getSquare()))
            log("WALK_QUEUED from=" .. npc:getX() .. "," .. npc:getY())
        end)
    end
    if SarahM0.ticks == 900 then
        exercise("walk-result", function()
            local npc = SarahM0.npc
            log("WALK_RESULT moved=" .. tostring(npc:getX() ~= SarahM0.startX or npc:getY() ~= SarahM0.startY) .. " position=" .. npc:getX() .. "," .. npc:getY())
            local inv, playerInv = npc:getInventory(), getSpecificPlayer(0):getInventory()
            local item = inv:getItems():get(0)
            inv:Remove(item)
            playerInv:AddItem(item)
            log("TRANSFER_TO_PLAYER contains=" .. tostring(playerInv:contains(item)))
            playerInv:Remove(item)
            inv:AddItem(item)
            item:setName("Sarah M0 persistence token")
            log("TRANSFER_TO_NPC contains=" .. tostring(inv:contains(item)))
        end)
    end
    if SarahM0.ticks == 1200 then
        exercise("save", function()
            local file = Core.getMyDocumentFolder() .. getFileSeparator() .. "Saves" .. getFileSeparator() .. getWorld():getGameMode() .. getFileSeparator() .. getWorld():getWorld() .. getFileSeparator() .. "SarahM0-checkpoint"
            if not string.find(file, "runtime", 1, true) or not string.find(file, "isolated", 1, true) then error("Refusing save outside isolated profile") end
            SarahM0.npc:save(file)
            getSpecificPlayer(0):getModData().SarahM0Checkpoint = {file=file}
            log("SAVED file=" .. file)
        end)
    end
    if SarahM0.ticks == 1800 then
        exercise("checkpoint", function()
            local stored = getSpecificPlayer(0):getModData().SarahM0Checkpoint
            log("CHECKPOINT_EXISTS " .. tostring(stored and fileExists(stored.file)))
            log("TOKEN " .. SarahM0.npc:getInventory():getItems():get(0):getName())
        end)
        remove()
        log("TEST_SEQUENCE_FINISHED")
    end
    if SarahM0.npc and SarahM0.ticks % 300 == 0 then
        protected("heartbeat", function()
            log("HEARTBEAT dead=" .. tostring(SarahM0.npc:isDead()) .. " position=" .. SarahM0.npc:getX() .. "," .. SarahM0.npc:getY())
        end)
    end
end)
Events.OnFillWorldObjectContextMenu.Add(function(playerIndex, context, worldobjects, test)
    if test or playerIndex ~= 0 then return end
    if not SarahM0.npc then
        context:addOption("Sarah M0: spawn probe", nil, spawn)
    else
        context:addOption("Sarah M0: inspect", nil, function()
            protected("inspect", function()
                local npc = SarahM0.npc
                log("INSPECT npc=" .. tostring(npc:isNpc()) .. " dead=" .. tostring(npc:isDead()) .. " inventory=" .. npc:getInventory():getItems():size())
            end)
        end)
        context:addOption("Sarah M0: remove probe", nil, remove)
    end
end)
log("LOADED; isolated spawn probe; no AI layer")
