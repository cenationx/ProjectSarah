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
        return self:transaction(function()
            local found = adapter.listNPCs()
            if #found > 1 then error("multiple Sarah objects; refusing to create another") end
            if #found == 1 then
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
                        if ok and npc then self.npc=npc; adapter.log("RESTORED " .. record.slot); return npc end
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
    function self:unload()
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
            return true
        end)
    end
    function self:observeDeath()
        if self.npc and adapter.isDead(self.npc) then adapter.meta.dead=true end
    end
    return self
end
return Lifecycle
