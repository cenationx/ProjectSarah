-- Offline injected boundary policy; not native proof or production wiring.
-- Gemini-authored, reviewed by Codex.
local ObstructionNormalizer = {}

local REQUIRED_KEYS = {
    "Clear",
    "ClearThroughOpenDoor",
    "ClearThroughWindow",
    "Blocked",
    "ClearThroughClosedDoor",
}

function ObstructionNormalizer.new(bindings)
    local valid = true
    local bound = 0
    local ref_clear, ref_open_door, ref_window, ref_blocked, ref_closed_door

    if type(bindings) ~= "table" then
        valid = false
    else
        local refs = {}
        for i = 1, #REQUIRED_KEYS do
            local k = REQUIRED_KEYS[i]
            local v = rawget(bindings, k)
            if type(v) ~= "table" and type(v) ~= "userdata" then
                valid = false
                break
            end
            for j = 1, #refs do
                if rawequal(v, refs[j]) then
                    valid = false
                    break
                end
            end
            if not valid then break end
            refs[#refs + 1] = v
        end

        if valid and #refs == 5 then
            ref_clear = refs[1]
            ref_open_door = refs[2]
            ref_window = refs[3]
            ref_blocked = refs[4]
            ref_closed_door = refs[5]
            bound = 5
        else
            valid = false
            bound = 0
        end
    end

    local inst = {}

    local function normalize(self, rawResult, covered)
        if not valid then
            return { status = "unknown", reason = "invalid_bindings" }
        end

        if covered ~= true then
            return { status = "unknown", reason = "coverage_unknown" }
        end

        if rawequal(rawResult, ref_clear) then
            return { status = "clear", reason = "clear" }
        elseif rawequal(rawResult, ref_open_door) then
            return { status = "clear", reason = "open_door" }
        elseif rawequal(rawResult, ref_window) then
            return { status = "clear", reason = "window" }
        elseif rawequal(rawResult, ref_blocked) then
            return { status = "blocked", reason = "blocked" }
        elseif rawequal(rawResult, ref_closed_door) then
            return { status = "unknown", reason = "closed_door" }
        else
            return { status = "unknown", reason = "unknown_result" }
        end
    end

    local function invalidate(self)
        valid = false
        bound = 0
        ref_clear = nil
        ref_open_door = nil
        ref_window = nil
        ref_blocked = nil
        ref_closed_door = nil
    end

    local function snapshot(self)
        return {
            valid = valid,
            bound = bound,
        }
    end

    inst.normalize = normalize
    inst.invalidate = invalidate
    inst.snapshot = snapshot

    return inst
end

return ObstructionNormalizer
