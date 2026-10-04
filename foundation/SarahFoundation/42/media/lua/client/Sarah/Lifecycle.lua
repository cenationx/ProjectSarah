-- Engine-independent lifecycle policy; adapter owns all game objects and file I/O.
local Lifecycle = {}
function Lifecycle.new(adapter)
    local self = { adapter=adapter, npc=nil, busy=false }
    function self:transaction(fn)
        if self.busy then return false, "operation already in progress" end
        self.busy = true
        local ok, result = pcall(fn)
        self.busy = false
        if not ok then adapter.log("FAIL " .. tostring(result)) end
        return ok, result
    end
    function self:ensure()
        self.manualUnloaded=nil
        return self:transaction(function()
            local found = adapter.listNPCs()
            if #found > 1 then error("multiple Sarah objects; refusing to create another") end
            if #found == 1 then
                if adapter.isIncomplete and adapter.isIncomplete(found[1]) then error("partial NPC construction; refusing adoption") end
                self.npc = found[1]
                if adapter.isDead(self.npc) then adapter.meta.dead=true; return nil end
                return self.npc
            end
            if self.npc then error("previous object not fully removed; refusing duplicate") end
            if adapter.meta.dead then return nil end
            local checkpoints = adapter.meta.checkpoints
            if checkpoints then
                for _, record in ipairs(checkpoints) do
                    if adapter.exists(record.slot) then
                        if adapter.canRestore and not adapter.canRestore(record) then
                            adapter.log("RESTORE deferred; saved square unavailable")
                            return nil
                        end
                        local ok, npc = pcall(adapter.restore, record)
                        if ok and npc then
                            self.npc=npc
                            -- Promote the recovered good slot before the next save;
                            -- never overwrite it using stale failed-slot metadata.
                            adapter.meta.checkpoints={record}
                            adapter.log("RESTORED " .. record.slot)
                            return npc
                        end
                        adapter.log("RECOVERY rejected " .. record.slot .. ": " .. tostring(npc))
                        -- A failed restore may have left a game object behind. Never
                        -- try the older slot until cleanup is confirmed.
                        if #adapter.listNPCs() > 0 then error("restore cleanup incomplete; refusing replacement") end
                    end
                end
                error("no valid checkpoint; preserving metadata and refusing fresh replacement")
            end
            self.npc = adapter.create()
            return self.npc
        end)
    end
    function self:save()
        return self:transaction(function()
            if not self.npc then return false end
            if adapter.isDead(self.npc) then adapter.meta.dead=true; return false end
            if adapter.isResident and not adapter.isResident(self.npc) then error("NPC no longer resident; retaining reference and checkpoints") end
            local records = adapter.meta.checkpoints or {}
            local slot = records[1] and records[1].slot == "a" and "b" or "a"
            local record = adapter.snapshot(self.npc)
            record.slot = slot
            adapter.save(self.npc, slot)
            if not adapter.exists(slot) then error("checkpoint missing after save") end
            -- Publish metadata only after the file write succeeds. Keep the prior good slot.
            adapter.meta.checkpoints = {record, records[1]}
            adapter.log("SAVED " .. slot)
            return true
        end)
    end
    function self:unload(automatic)
        if self.npc and not adapter.isDead(self.npc) then
            local ok, saved = self:save()
            if not ok or not saved then return false, "save failed; NPC retained" end
        end
        return self:transaction(function()
            if not self.npc then return true end
            if adapter.isDead(self.npc) then adapter.meta.dead=true end
            adapter.stop(self.npc)
            adapter.remove(self.npc)
            -- Keep the reference if cleanup failed, preventing a replacement duplicate.
            self.npc=nil
            self.manualUnloaded=not automatic
            return true
        end)
    end
    function self:observeDeath()
        if self.npc and adapter.isDead(self.npc) then adapter.meta.dead=true end
    end
    function self:maintain()
        if self.busy or self.travelBlocked or adapter.meta.dead then return end
        local ok,err=pcall(function()
            if self.npc then
                if adapter.isResident and not adapter.isResident(self.npc) then
                    error("travel recovery blocked: NPC already removed; preserving reference and checkpoints")
                end
                if adapter.shouldUnload and adapter.shouldUnload(self.npc) then
                    local unloaded,reason=self:unload(true)
                    if not unloaded then error(reason or "automatic unload failed") end
                    adapter.log("TRAVEL suspended at saved location")
                end
            elseif not self.manualUnloaded and adapter.meta.checkpoints then
                local record=adapter.meta.checkpoints[1]
                if adapter.nearCheckpoint and adapter.nearCheckpoint(record)
                    and (not adapter.canRestore or adapter.canRestore(record)) then
                    local restored,reason=self:ensure()
                    if not restored or not self.npc then error(reason or "travel restore produced no NPC; preserving recovery state") end
                end
            end
        end)
        if not ok then self.travelBlocked=true; adapter.log("TRAVEL_BLOCKED " .. tostring(err)) end
    end
    return self
end
return Lifecycle
