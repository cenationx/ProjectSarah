-- Offline injected boundary policy; not native proof or production wiring.
-- Gemini-authored, reviewed by Codex.
local SessionIdentity = {}

local MAX_CAP = 64
local MAX_SEQ = 2147483647
local MAX_EPOCH = 2147483647

-- Caller obligation: namespace must be unique across all sessions and reloads.
-- SessionIdentity does not maintain an unbounded global namespace registry.
function SessionIdentity.new(namespace)
    if type(namespace) ~= "string" or #namespace < 1 or #namespace > 32 or not namespace:match("^[%w_-]+$") then
        error("SessionIdentity.new: invalid namespace (must be 1..32 chars matching ^[%w_-]+$)", 2)
    end

    local epoch = 1
    local sequence = 0
    local map = {}
    local fifo = {}
    local exhausted = false

    local inst = {}

    local function resolve(self, token, kind)
        if exhausted then
            return { reason = "exhausted" }
        end
        if type(token) ~= "string" or #token < 1 or #token > 96 then
            return { reason = "invalid_token" }
        end
        if kind ~= "player" and kind ~= "zombie" then
            return { reason = "invalid_kind" }
        end

        local existing = map[token]
        if existing then
            if existing.kind ~= kind then
                return { reason = "kind_conflict" }
            end
            return { id = existing.id, kind = existing.kind, reason = "existing" }
        end

        if sequence >= MAX_SEQ then
            exhausted = true
            map = {}
            fifo = {}
            return { reason = "exhausted" }
        end

        sequence = sequence + 1
        local id = namespace .. ":" .. epoch .. ":" .. sequence

        if #fifo >= MAX_CAP then
            local oldest = table.remove(fifo, 1)
            map[oldest] = nil
        end

        fifo[#fifo + 1] = token
        map[token] = { id = id, kind = kind }

        return { id = id, kind = kind, reason = "new" }
    end

    local function reset(self)
        if exhausted then
            return
        end
        map = {}
        fifo = {}
        sequence = 0
        if epoch >= MAX_EPOCH then
            exhausted = true
            epoch = MAX_EPOCH
        else
            epoch = epoch + 1
        end
    end

    local function snapshot(self)
        return {
            epoch = epoch,
            issued = sequence,
            retained = #fifo,
            exhausted = exhausted,
        }
    end

    inst.resolve = resolve
    inst.reset = reset
    inst.snapshot = snapshot

    return inst
end

return SessionIdentity
