local Engine = {}
local function log(message) print("[SarahFoundation] " .. tostring(message)) end

local function loadModule(name)
    local mod = rawget(_G, name)
    if not mod and type(require) == "function" then
        local ok, m = pcall(require, "Sarah/" .. name)
        if ok and m then return m end
        local ok2, m2 = pcall(require, name)
        if ok2 and m2 then return m2 end
    end
    return mod
end

if type(_G) == "table" then
    _G._SarahRuntimeOwnership = _G._SarahRuntimeOwnership or {}
    Engine.runtimeOwnership = _G._SarahRuntimeOwnership
else
    Engine.runtimeOwnership = Engine.runtimeOwnership or {}
end

function Engine.getOwnership(npc)
    if not npc then return nil end
    local ok, rec = pcall(function()
        return Engine.runtimeOwnership[npc]
    end)
    if not ok or type(rec) ~= "table" then return nil end
    return rec
end

function Engine.setOwnership(npc, record)
    if not npc then return false, "missing npc" end
    if type(record) ~= "table" then return false, "invalid record" end
    local ok, err = pcall(function()
        Engine.runtimeOwnership[npc] = record
    end)
    if not ok then return false, tostring(err) end
    return true
end

function Engine.clearOwnership(npc, expectedRecord)
    if not npc then return false, "missing npc" end
    local ok, err = pcall(function()
        if expectedRecord == nil or Engine.runtimeOwnership[npc] == expectedRecord then
            Engine.runtimeOwnership[npc] = nil
        end
    end)
    if not ok then return false, tostring(err) end
    return true
end

function Engine.isCurrentOwner(npc, adapter)
    if not npc or not adapter then return false end
    local rec = Engine.getOwnership(npc)
    if rec and rec.adapter then
        return rec.adapter == adapter
    end
    return true
end

local function getWalkActionClass()
    if not Engine.SarahWalkAction and ISWalkToTimedAction then
        local cls = ISWalkToTimedAction:derive("SarahWalkAction")
        function cls:new(character, location, onSuccess, onFail, pace, token, adapter)
            local o = ISWalkToTimedAction.new(self, character, location)
            o.onSuccess = onSuccess
            o.onFail = onFail
            o.finished = false
            o.pace = pace or "walk"
            o.token = token
            o.adapter = adapter
            return o
        end
        function cls:isCurrentOwner()
            if self.finished then return false end
            if not self.adapter or not self.token then return false end
            if self.adapter.actionToken ~= self.token then return false end
            if self.adapter.currentAction ~= self then return false end
            if not self.character then return false end
            if self.adapter.isDead and self.adapter.isDead(self.character) then return false end

            local rec = Engine.getOwnership(self.character)
            -- Ownership checks must fail closed when the required record is missing or unreadable
            if not rec or type(rec) ~= "table" then
                return false
            end
            if rec.action ~= self or rec.token ~= self.token or rec.adapter ~= self.adapter then
                return false
            end
            return true
        end
        function cls:setPace(pace)
            local newPace = pace or "walk"
            if self.finished then return false, "finished" end
            if not self:isCurrentOwner() then
                return false, "retired"
            end
            self.pace = newPace
            pcall(self.character.setRunning, self.character, newPace == "run")
            return true
        end
        function cls:update()
            if not self.finished and self:isCurrentOwner() then
                local shouldRun = (self.pace == "run")
                pcall(self.character.setRunning, self.character, shouldRun)
                ISWalkToTimedAction.update(self)
            end
        end
        function cls:perform()
            if self.finished then return end
            local isOwner = self:isCurrentOwner()
            if isOwner then
                pcall(self.character.setRunning, self.character, false)
                if self.adapter and self.adapter.actionToken == self.token then
                    self.adapter.currentAction = nil
                end
                Engine.clearOwnership(self.character, Engine.getOwnership(self.character))
                ISWalkToTimedAction.perform(self)
            end
            if not self.finished then
                self.finished = true
                if self.onSuccess then
                    local ok, err = pcall(self.onSuccess, self)
                    if not ok then log("walk onSuccess error: " .. tostring(err)) end
                end
            end
        end
        function cls:stop()
            if self.finished then return end
            local isOwner = self:isCurrentOwner()
            local isFailed = (BehaviorResult and self.result == BehaviorResult.Failed)
            if isOwner then
                pcall(self.character.setRunning, self.character, false)
                if self.adapter and self.adapter.actionToken == self.token then
                    self.adapter.currentAction = nil
                end
                Engine.clearOwnership(self.character, Engine.getOwnership(self.character))
                ISWalkToTimedAction.stop(self)
            end
            if not self.finished then
                self.finished = true
                if self.onFail then
                    local ok, err = pcall(self.onFail, self, isFailed and "path failed" or "stopped")
                    if not ok then log("walk onFail error: " .. tostring(err)) end
                end
            end
        end
        Engine.SarahWalkAction = cls
    end
    return Engine.SarahWalkAction
end
function Engine.new()
    local root = Core.getMyDocumentFolder():gsub("\\", "/"):gsub("/$", "")
    if root ~= "G:/Codex/Project Sarah/runtime/isolated" then error("experimental foundation requires isolated profile") end
    local adapter = {meta=ModData.getOrCreate("SarahFoundationV1"), log=log}
    adapter.snapshots = {}
    adapter.snapshotFIFO = {}
    adapter.snapSeq = 0
    local function file(slot)
        if slot ~= "a" and slot ~= "b" then error("invalid checkpoint slot") end
        return root .. "/Saves/" .. getWorld():getGameMode() .. "/" .. getWorld():getWorld() .. "/SarahFoundation-" .. slot .. ".bin"
    end
    function adapter.exists(slot) return fileExists(file(slot)) end
    function adapter.isDead(npc) return npc:isDead() end
    function adapter.isIncomplete(npc) return npc:getModData().SarahFoundationPartial == true end
    function adapter.isResident(npc)
        return npc:getCurrentSquare()~=nil and (getCell():getObjectList():contains(npc) or getCell():getAddList():contains(npc))
            and not getCell():getRemoveList():contains(npc)
    end
    local function nearPlayer(x,y,z,radius)
        local player=getSpecificPlayer(0)
        if not player or math.floor(player:getZ())~=math.floor(z) then return false end
        local dx,dy=player:getX()-x,player:getY()-y
        return dx*dx+dy*dy<=radius*radius
    end
    function adapter.shouldUnload(npc)
        return not nearPlayer(npc:getX(),npc:getY(),npc:getZ(),32)
    end
    function adapter.nearCheckpoint(record)
        return record and type(record.x)=="number" and type(record.y)=="number" and type(record.z)=="number"
            and nearPlayer(record.x,record.y,record.z,16)
    end
    -- B42 FBO skips IsoPlayer in the moving-object pass, but its player pass
    -- only draws local player slots. Draw our NPC through the world event.
    function adapter.render(npc, playerIndex)
        if playerIndex ~= 0 or not PerformanceSettings.fboRenderChunk or isClient() or isServer() then return false end
        local player=getSpecificPlayer(0)
        if not player or not npc or npc==player or not npc:isNpc() or npc:isDead() then return false end
        local data=npc:getModData()
        if data.SarahFoundationId~="Sarah" or data.SarahFoundationPartial or not npc:isOnScreen() then return false end
        local cell=getCell()
        if not cell:getObjectList():contains(npc) or cell:getRemoveList():contains(npc) then return false end
        local square=npc:getCurrentSquare()
        -- Conservative scope: visible squares on the local player's floor.
        if not square or math.floor(npc:getZ())~=math.floor(player:getZ()) or not square:isCanSee(playerIndex) then return false end
        local light=square:getLightInfo(playerIndex)
        if not light then return false end
        npc:renderShadow(npc:getX(),npc:getY(),npc:getZ())
        npc:render(npc:getX(),npc:getY(),npc:getZ(),light,true,false,nil)
        return true
    end
    function adapter.listNPCs()
        local result, seen = {}, {}
        for _, list in ipairs({getCell():getObjectList(), getCell():getAddList()}) do
            local iterator=list:iterator()
            while iterator:hasNext() do
                local object = iterator:next()
                if instanceof(object,"IsoPlayer") and object:getModData().SarahFoundationId == "Sarah" and not seen[object] and not getCell():getRemoveList():contains(object) then
                    seen[object]=true; result[#result+1]=object
                end
            end
        end
        return result
    end
    function adapter.validateTarget(npc, target)
        if not npc or type(target) ~= "table" then return false, "Invalid target coordinates." end
        local x, y, z = target.x, target.y, target.z
        if type(x) ~= "number" or type(y) ~= "number" or type(z) ~= "number" then
            return false, "Invalid target coordinates."
        end
        if x ~= x or y ~= y or z ~= z or x == math.huge or x == -math.huge or y == math.huge or y == -math.huge or z == math.huge or z == -math.huge then
            return false, "Invalid target coordinates."
        end
        local tx, ty, tz = math.floor(x), math.floor(y), math.floor(z)
        local sx, sy, sz = npc:getX(), npc:getY(), npc:getZ()
        if math.floor(sz) ~= tz then
            return false, "Target is on a different floor."
        end
        local dx = tx + 0.5 - sx
        local dy = ty + 0.5 - sy
        if (dx * dx + dy * dy) > 64 then
            return false, "Target is too far (maximum 8 tiles)."
        end
        if math.floor(sx) == tx and math.floor(sy) == ty then
            return false, "Already at target (" .. tx .. ", " .. ty .. ", " .. tz .. ")."
        end
        local cell = getCell()
        if not cell then return false, "World cell is unavailable." end
        local sq = cell:getGridSquare(tx, ty, tz)
        if not sq then return false, "Target square is not loaded." end
        if not sq:isFree(false) then return false, "Target square is occupied or blocked." end
        return true, sq
    end
    function adapter.walk(npc, square, onSuccess, onFail, pace)
        if not npc or not square then return false, "NPC or target square missing." end
        local walkCls = getWalkActionClass()
        if not walkCls then
            if ISWalkToTimedAction and ISTimedActionQueue then
                local act = ISWalkToTimedAction:new(npc, square)
                if onSuccess then act:setOnComplete(onSuccess) end
                ISTimedActionQueue.add(act)
                return true, act
            end
            return false, "Walk action class unavailable."
        end
        adapter.actionToken = (adapter.actionToken or 0) + 1
        local token = adapter.actionToken
        local a = walkCls:new(npc, square, onSuccess, onFail, pace, token, adapter)
        adapter.currentAction = a
        local rec = { adapter = adapter, action = a, token = token, character = npc }
        local okOwner, errOwner = Engine.setOwnership(npc, rec)
        if not okOwner then
            a.finished = true
            if adapter.actionToken == token and adapter.currentAction == a then
                adapter.currentAction = nil
            end
            return false, "failed to set ownership: " .. tostring(errOwner)
        end

        local ok, err = pcall(function()
            ISTimedActionQueue.add(a)
        end)
        if not ok then
            a.finished = true
            local currentRec = Engine.getOwnership(npc)
            if currentRec and currentRec.action == a and currentRec.token == token and currentRec.adapter == adapter then
                Engine.clearOwnership(npc, currentRec)
                pcall(npc.setRunning, npc, false)
                if npc.getPathFindBehavior2 then
                    local okPf, pf = pcall(npc.getPathFindBehavior2, npc)
                    if okPf and pf and pf.cancel then pcall(pf.cancel, pf) end
                end
                if npc.setPath2 then pcall(npc.setPath2, npc, nil) end
            end
            if adapter.actionToken == token and adapter.currentAction == a then
                adapter.currentAction = nil
            end
            return false, tostring(err)
        end
        if a.finished then
            local currentRec = Engine.getOwnership(npc)
            if currentRec and currentRec.action == a then
                Engine.clearOwnership(npc, currentRec)
            end
            if adapter.actionToken == token and adapter.currentAction == a then
                adapter.currentAction = nil
            end
        end
        return true, a
    end
    function adapter.stop(npc)
        adapter.actionToken = (adapter.actionToken or 0) + 1
        adapter.currentAction = nil
        if not npc then return true end

        local rec = Engine.getOwnership(npc)
        if rec and rec.adapter and rec.adapter ~= adapter then
            -- Stale adapter: do not touch newer adapter's same-NPC ownership, running flag, queue or path
            return true
        end

        local failures = {}
        local okClear, errClear = Engine.clearOwnership(npc, rec)
        if not okClear then
            failures[#failures+1] = "clearOwnership: " .. tostring(errClear)
        end

        if npc.setRunning then
            local okRun, errRun = pcall(npc.setRunning, npc, false)
            if not okRun then
                failures[#failures+1] = "setRunning: " .. tostring(errRun)
            end
        end

        if ISTimedActionQueue and ISTimedActionQueue.clear then
            local okQ, errQ = pcall(ISTimedActionQueue.clear, npc)
            if not okQ then
                failures[#failures+1] = "queue.clear: " .. tostring(errQ)
            end
        end

        if npc.getPathFindBehavior2 then
            local okPf, pf = pcall(npc.getPathFindBehavior2, npc)
            if okPf and pf and pf.cancel then
                local okCancel, errCancel = pcall(pf.cancel, pf)
                if not okCancel then
                    failures[#failures+1] = "path.cancel: " .. tostring(errCancel)
                end
            elseif not okPf then
                failures[#failures+1] = "getPathFindBehavior2: " .. tostring(pf)
            end
        end

        if npc.setPath2 then
            local okP2, errP2 = pcall(npc.setPath2, npc, nil)
            if not okP2 then
                failures[#failures+1] = "setPath2: " .. tostring(errP2)
            end
        end

        if #failures > 0 then
            return false, table.concat(failures, "; ")
        end
        return true
    end
    function adapter.ensurePerceptionModules()
        if adapter.diagnosticSampler and adapter.sessionIdentity then
            return true
        end
        local CC = loadModule("CandidateCollector")
        local Cov = loadModule("Coverage")
        local Perc = loadModule("Perception")
        local Obs = loadModule("ObstructionNormalizer")
        local SI = loadModule("SessionIdentity")
        local DS = loadModule("DiagnosticSampler")

        if not adapter.sessionIdentity and SI and type(SI.new) == "function" then
            local ok, inst = pcall(SI.new, "sarah_obs")
            if ok and inst then adapter.sessionIdentity = inst end
        end

        if not adapter.diagnosticSampler and DS and type(DS.new) == "function" and CC and Cov and Perc and Obs then
            local ok, inst = pcall(DS.new, {
                CandidateCollector = CC,
                Coverage = Cov,
                Perception = Perc,
                ObstructionNormalizer = Obs,
            })
            if ok and inst then adapter.diagnosticSampler = inst end
        end

        return (adapter.diagnosticSampler ~= nil and adapter.sessionIdentity ~= nil)
    end
    function adapter.resetPerception()
        adapter.sampleGeneration = (adapter.sampleGeneration or 1) + 1
        adapter.entityTracker = {}
        adapter.entityFIFO = {}
        adapter.snapshots = {}
        adapter.snapshotFIFO = {}
        if adapter.sessionIdentity and adapter.sessionIdentity.reset then
            pcall(adapter.sessionIdentity.reset, adapter.sessionIdentity)
        end
        if adapter.diagnosticSampler and adapter.diagnosticSampler.reset then
            pcall(adapter.diagnosticSampler.reset, adapter.diagnosticSampler)
        end
    end
    function adapter.samplePerception(npc)
        if not npc then return nil, "missing npc" end
        if adapter.isDead(npc) then return nil, "npc dead" end
        if adapter.isResident and not adapter.isResident(npc) then return nil, "npc not resident" end
        if not Engine.isCurrentOwner(npc, adapter) then return nil, "adapter not current owner" end
        if not adapter.ensurePerceptionModules() then
            return nil, "perception modules unavailable"
        end

        local api = {}
        adapter.snapshots = adapter.snapshots or {}
        adapter.snapshotFIFO = adapter.snapshotFIFO or {}
        api.snapshots = adapter.snapshots
        api.snapSeq = adapter.snapSeq or 0
        api.nativeReads = 0
        local MAX_LIST_SIZE = 64
        local READ_BUDGET = adapter.readBudget or 512

        api.capture = function()
            if not npc or adapter.isDead(npc) or (adapter.isResident and not adapter.isResident(npc)) then
                return nil
            end
            if not Engine.isCurrentOwner(npc, adapter) then
                return nil
            end
            local fx, fy
            if npc.getForwardDirectionX and npc.getForwardDirectionY then
                local okX, rx = pcall(npc.getForwardDirectionX, npc)
                local okY, ry = pcall(npc.getForwardDirectionY, npc)
                if okX and okY and type(rx) == "number" and type(ry) == "number" and (rx == rx) and (ry == ry) and (rx ~= 0 or ry ~= 0) then
                    fx, fy = rx, ry
                end
            end
            if not fx or not fy then
                return nil
            end
            local okX, x = pcall(npc.getX, npc)
            local okY, y = pcall(npc.getY, npc)
            local okZ, z = pcall(npc.getZ, npc)
            if not okX or not okY or not okZ or type(x) ~= "number" or type(y) ~= "number" or type(z) ~= "number"
               or x ~= x or y ~= y or z ~= z or math.abs(x) > 1e6 or math.abs(y) > 1e6 or math.abs(z) > 1e6 then
                return nil
            end
            local curGen = adapter.sampleGeneration or 1
            local genToken = "gen_" .. tostring(curGen)
            if #genToken > 96 then genToken = genToken:sub(1, 96) end

            local curCell = getCell and getCell()
            if not curCell then return nil end
            local cellToken = tostring(curCell)
            if #cellToken > 96 then cellToken = cellToken:sub(1, 96) end

            local ctrlToken = "ctrl_" .. tostring(adapter)
            if #ctrlToken > 96 then ctrlToken = ctrlToken:sub(1, 96) end

            local npcToken = "npc_" .. tostring(npc)
            if #npcToken > 96 then npcToken = npcToken:sub(1, 96) end

            return {
                controller = ctrlToken,
                npc = npcToken,
                cell = cellToken,
                generation = genToken,
                alive = true,
                resident = true,
                cancelled = false,
                x = x + 0.0,
                y = y + 0.0,
                z = z + 0.0,
                fx = fx + 0.0,
                fy = fy + 0.0,
            }
        end

        api.getSquare = function(x, y, z)
            local c = getCell and getCell()
            if not c or not c.getGridSquare then return nil end
            local ok, sq = pcall(c.getGridSquare, c, math.floor(x), math.floor(y), math.floor(z))
            if ok and sq then return sq end
            return nil
        end

        api.listInfo = function(sq)
            if not sq or not sq.getMovingObjects then
                error("invalid square")
            end
            local okList, list = pcall(sq.getMovingObjects, sq)
            if not okList or not list or not list.size then
                error("failed to get moving objects: " .. tostring(list))
            end
            local okSz, sz = pcall(list.size, list)
            if not okSz or type(sz) ~= "number" or sz < 0 then
                error("invalid moving objects size: " .. tostring(sz))
            end
            sz = math.floor(sz)
            local okX, sx = pcall(sq.getX, sq)
            local okY, sy = pcall(sq.getY, sq)
            local okZ, szCoord = pcall(sq.getZ, sq)
            if not okX or not okY or not okZ or type(sx) ~= "number" or type(sy) ~= "number" or type(szCoord) ~= "number" then
                error("square coordinates unavailable")
            end
            if sz > MAX_LIST_SIZE then
                error("unsupported oversized list: " .. tostring(sz))
            end
            local coordKey = string.format("%d,%d,%d", sx, sy, szCoord)
            local MAX_SNAPSHOTS = 128
            if sz == 0 then
                local prev = adapter.snapshots[coordKey]
                if prev and prev.size == 0 then
                    return 0, prev.token
                end
                local tok = string.format("sq:%s:0:empty", coordKey)
                if not adapter.snapshots[coordKey] then
                    if #adapter.snapshotFIFO >= MAX_SNAPSHOTS then
                        local oldest = table.remove(adapter.snapshotFIFO, 1)
                        adapter.snapshots[oldest] = nil
                    end
                    adapter.snapshotFIFO[#adapter.snapshotFIFO + 1] = coordKey
                end
                adapter.snapshots[coordKey] = {
                    size = 0,
                    refs = {},
                    token = tok
                }
                return 0, tok
            end

            -- Account for fingerprint/snapshot reads in native work budget
            local readLimit = adapter.readBudget or 512
            if (api.nativeReads + sz) > readLimit then
                error("native read budget exhausted")
            end

            local currentRefs = {}
            for i = 0, sz - 1 do
                local okObj, obj = pcall(list.get, list, i)
                if not okObj or not obj then
                    error("list element read error at index " .. i)
                end
                currentRefs[i + 1] = obj
            end
            api.nativeReads = api.nativeReads + sz

            -- Bounded exact-reference snapshot comparison
            local prev = adapter.snapshots[coordKey]
            local match = false
            if prev and prev.size == sz and #prev.refs == sz then
                match = true
                for i = 1, sz do
                    if prev.refs[i] ~= currentRefs[i] then
                        match = false
                        break
                    end
                end
            end

            if match then
                return sz, prev.token
            end

            adapter.snapSeq = (adapter.snapSeq or 0) + 1
            api.snapSeq = adapter.snapSeq
            local tok = string.format("sq:%s:v%d:sz%d", coordKey, adapter.snapSeq, sz)
            if #tok > 96 then tok = tok:sub(1, 96) end

            if not adapter.snapshots[coordKey] then
                if #adapter.snapshotFIFO >= MAX_SNAPSHOTS then
                    local oldest = table.remove(adapter.snapshotFIFO, 1)
                    adapter.snapshots[oldest] = nil
                end
                adapter.snapshotFIFO[#adapter.snapshotFIFO + 1] = coordKey
            end

            adapter.snapshots[coordKey] = {
                size = sz,
                refs = currentRefs,
                token = tok
            }
            return sz, tok
        end

        api.readObject = function(sq, index)
            if not sq or not sq.getMovingObjects then return nil end
            local okList, list = pcall(sq.getMovingObjects, sq)
            if not okList or not list or not list.get then return nil end

            -- Account for read in native work budget
            local readLimit = adapter.readBudget or 512
            if (api.nativeReads + 1) > readLimit then
                return nil
            end
            api.nativeReads = api.nativeReads + 1

            local okObj, obj = pcall(list.get, list, index)
            if not okObj or not obj or obj == npc then return nil end

            -- Reject unknown liveness
            if not obj.isDead then return nil end
            local okDead, dead = pcall(obj.isDead, obj)
            if not okDead or type(dead) ~= "boolean" or dead == true then
                return nil
            end
            if obj.isAlive then
                local okAlive, alive = pcall(obj.isAlive, obj)
                if not okAlive or type(alive) ~= "boolean" or alive ~= true then
                    return nil
                end
            end
            if obj.getHealth then
                local okH, h = pcall(obj.getHealth, obj)
                if okH and type(h) == "number" and h <= 0 then
                    return nil
                end
            end

            local kind = nil
            if instanceof and (instanceof(obj, "IsoPlayer") or instanceof(obj, "IsoZombie")) then
                if instanceof(obj, "IsoPlayer") then kind = "player" else kind = "zombie" end
            elseif obj.isPlayer and type(obj.isPlayer) == "function" and obj:isPlayer() then
                kind = "player"
            elseif obj.isZombie and type(obj.isZombie) == "function" and obj:isZombie() then
                kind = "zombie"
            end
            if not kind then return nil end

            local okX, ox = pcall(obj.getX, obj)
            local okY, oy = pcall(obj.getY, obj)
            local okZ, oz = pcall(obj.getZ, obj)
            if not okX or not okY or not okZ or type(ox) ~= "number" or type(oy) ~= "number" or type(oz) ~= "number"
               or ox ~= ox or oy ~= oy or oz ~= oz or math.abs(ox) > 1e6 or math.abs(oy) > 1e6 or math.abs(oz) > 1e6 then
                return nil
            end

            -- Bounded collision-safe session identity tracking
            adapter.entityTracker = adapter.entityTracker or {}
            adapter.entityFIFO = adapter.entityFIFO or {}
            local seq = adapter.entityTracker[obj]
            if not seq then
                adapter.entitySeq = (adapter.entitySeq or 0) + 1
                seq = adapter.entitySeq
                if #adapter.entityFIFO >= 64 then
                    local oldest = table.remove(adapter.entityFIFO, 1)
                    adapter.entityTracker[oldest] = nil
                end
                adapter.entityFIFO[#adapter.entityFIFO + 1] = obj
                adapter.entityTracker[obj] = seq
            end

            local oidStr = "none"
            if obj.getOnlineID then
                local okId, val = pcall(obj.getOnlineID, obj)
                if okId and type(val) == "number" and val >= 0 then
                    oidStr = tostring(math.floor(val))
                end
            end

            local curGen = adapter.sampleGeneration or 1
            local token = string.format("so:e%d:s%d:%s:%s", curGen, seq, kind, oidStr)
            if #token > 96 then token = token:sub(1, 96) end

            local res = adapter.sessionIdentity:resolve(token, kind)
            if not res or not res.id then return nil end
            return {
                id = res.id,
                kind = kind,
                x = ox + 0.0,
                y = oy + 0.0,
                z = oz + 0.0,
            }
        end

        if LosUtil and LosUtil.lineClear then
            api.obstruction = function(obs, cand)
                local c = getCell and getCell()
                if not c then return nil end
                local ok, r = pcall(LosUtil.lineClear, c, math.floor(obs.x), math.floor(obs.y), math.floor(obs.z), math.floor(cand.x), math.floor(cand.y), math.floor(cand.z), false)
                if ok then return r end
                return nil
            end
        end

        if LosUtil and type(LosUtil.TestResults) == "table" then
            local tr = LosUtil.TestResults
            api.bindings = {
                Clear = tr.Clear,
                ClearThroughOpenDoor = tr.ClearThroughOpenDoor,
                ClearThroughWindow = tr.ClearThroughWindow,
                Blocked = tr.Blocked,
                ClearThroughClosedDoor = tr.ClearThroughClosedDoor,
            }
        end

        local res = adapter.diagnosticSampler:sample(api)
        return res
    end
    function adapter.remove(npc)
        Engine.clearOwnership(npc)
        if adapter.resetPerception then adapter.resetPerception() end
        npc:removeFromWorld()
        npc:removeFromSquare()
    end
    local function construct(square, record)
        if not square or not square:isFree(false) then error("spawn square unavailable") end
        local previous, npc = IsoPlayer.getInstance(), nil
        local ok, err = pcall(function()
            local desc=SurvivorFactory.CreateSurvivor(SurvivorFactory.SurvivorType.Neutral,true)
            desc:setForename("Sarah"); desc:setSurname("M0")
            npc=IsoPlayer.new(getCell(),desc,square:getX(),square:getY(),square:getZ())
            npc:getModData().SarahFoundationId="Sarah"
            npc:getModData().SarahFoundationPartial=true
            npc:setNpc(true); npc:setSceneCulled(false)
            if record then
                npc:getModData().SarahFoundationId="PendingRestore"
                npc:load(file(record.slot))
                if npc:isDead() or npc:getModData().SarahFoundationId ~= "Sarah" then error("invalid restored identity or dead checkpoint") end
            else
                npc:getModData().SarahFoundationId="Sarah"
                local inv=npc:getInventory()
                for _, type in ipairs({"Base.Tshirt_WhiteTINT", "Base.Trousers_DefaultTEXTURE_TINT", "Base.Shoes_TrainerTINT"}) do
                    local item=inv:AddItem(type)
                    if not item then error("clothing item unavailable: " .. type) end
                    npc:setWornItem(item:getBodyLocation(),item)
                end
                inv:AddItem("Base.Bandage")
            end
            npc:setNpc(true); npc:setSceneCulled(false); npc:resetModel()
            npc:getModData().SarahFoundationPartial=nil
        end)
        IsoPlayer.setInstance(previous)
        if not ok then
            if npc then
                npc:getModData().SarahFoundationId="Sarah"
                npc:getModData().SarahFoundationPartial=true
                local cleaned, cleanupError=pcall(adapter.remove,npc)
                if not cleaned then error("construction failed and cleanup failed: " .. tostring(cleanupError)) end
            end
            error(err)
        end
        if adapter.resetPerception then adapter.resetPerception() end
        log("ACTIVE npc=" .. tostring(npc:isNpc()) .. " worn=" .. npc:getWornItems():size() .. " localPlayerPreserved=" .. tostring(IsoPlayer.getInstance()==previous))
        return npc
    end
    function adapter.create()
        local player=getSpecificPlayer(0)
        for _, offset in ipairs({{2,0},{-2,0},{0,2},{0,-2}}) do
            local square=getCell():getGridSquare(math.floor(player:getX())+offset[1],math.floor(player:getY())+offset[2],math.floor(player:getZ()))
            if square and square:isFree(false) then return construct(square) end
        end
        error("no free nearby spawn square")
    end
    function adapter.restore(record)
        if type(record.x)~="number" or type(record.y)~="number" or type(record.z)~="number" then error("invalid saved coordinates") end
        local square=getCell():getGridSquare(math.floor(record.x),math.floor(record.y),math.floor(record.z))
        return construct(square,record)
    end
    function adapter.canRestore(record)
        if type(record.x)~="number" or type(record.y)~="number" or type(record.z)~="number" then return true end
        local square=getCell():getGridSquare(math.floor(record.x),math.floor(record.y),math.floor(record.z))
        return adapter.nearCheckpoint(record) and square ~= nil and square:isFree(false)
    end
    function adapter.snapshot(npc) return {x=npc:getX(),y=npc:getY(),z=npc:getZ()} end
    function adapter.save(npc,slot)
        if adapter.verificationNPC then error("previous checkpoint verifier cleanup incomplete") end
        local data=npc:getModData()
        local oldToken=data.SarahCheckpointWriteToken
        local token=getRandomUUID()
        local previous=IsoPlayer.getInstance()
        data.SarahCheckpointWriteToken=token
        local ok,err=pcall(function()
            -- Java I/O errors may be logged without failing Lua pcall. A fresh
            -- UUID read back from the binary rejects missing/stale writes.
            npc:save(file(slot))
            local desc=SurvivorFactory.CreateSurvivor(SurvivorFactory.SurvivorType.Neutral,true)
            local verifier=IsoPlayer.new(getCell(),desc,math.floor(npc:getX()),math.floor(npc:getY()),math.floor(npc:getZ()))
            assert(verifier,"checkpoint verifier construction failed")
            adapter.verificationNPC=verifier
            verifier:setNpc(true)
            verifier:getModData().SarahFoundationId="CheckpointVerifier"
            verifier:load(file(slot))
            assert(verifier:getModData().SarahFoundationId=="Sarah" and
                verifier:getModData().SarahCheckpointWriteToken==token and not verifier:isDead(),
                "checkpoint write verification failed; old file is not a new save")
        end)
        IsoPlayer.setInstance(previous)
        local cleaned,cleanupError=pcall(function()
            if adapter.verificationNPC then
                adapter.verificationNPC:getModData().SarahFoundationId="CheckpointVerifier"
                adapter.remove(adapter.verificationNPC)
                local cell=getCell()
                assert(adapter.verificationNPC:getCurrentSquare()==nil and
                    not cell:getAddList():contains(adapter.verificationNPC) and
                    (not cell:getObjectList():contains(adapter.verificationNPC) or
                        cell:getRemoveList():contains(adapter.verificationNPC)),
                    "checkpoint verifier still registered after cleanup")
                adapter.verificationNPC=nil
            end
        end)
        if not ok or not cleaned then
            data.SarahCheckpointWriteToken=oldToken
            error(not cleaned and ("checkpoint verifier cleanup failed: "..tostring(cleanupError)) or err)
        end
    end
    return adapter
end
return Engine
