-- tools/CaptureAccounting.lua
-- Standalone inert capture ledger for Project Sarah.
-- Pure Lua 5.1 compatible. Fixed budgets, no callbacks, no refill.

local CaptureAccounting = {}

local HARD_MAX_CAPTURES = 512
local HARD_MAX_OPERATIONS = 16384

local DEFAULT_CAPTURES = 54
local DEFAULT_OPERATIONS = 1024

local function is_valid_pos_int(n, hard_max)
    if type(n) ~= "number" then return false end
    if n ~= n or n == 1/0 or n == -1/0 then return false end
    if math.floor(n) ~= n then return false end
    if n <= 0 or n > hard_max then return false end
    return true
end

function CaptureAccounting.new(config)
    local cap_limit = DEFAULT_CAPTURES
    local op_limit = DEFAULT_OPERATIONS

    if config ~= nil then
        if type(config) ~= "table" then
            error("CaptureAccounting.new: invalid config")
        end
        local raw_cap = rawget(config, "captureLimit")
        if raw_cap ~= nil then
            if not is_valid_pos_int(raw_cap, HARD_MAX_CAPTURES) then
                error("CaptureAccounting.new: invalid captureLimit")
            end
            cap_limit = raw_cap
        end
        local raw_op = rawget(config, "operationLimit")
        if raw_op ~= nil then
            if not is_valid_pos_int(raw_op, HARD_MAX_OPERATIONS) then
                error("CaptureAccounting.new: invalid operationLimit")
            end
            op_limit = raw_op
        end
    end

    local captures = 0
    local operations = 0
    local is_invalid = false
    local first_reason = nil

    local g_world = 0
    local g_membership = 0
    local g_state = 0
    local g_symbol = 0

    local inst = {}

    local function mark_invalid(r)
        if not is_invalid then
            is_invalid = true
            first_reason = r
        end
    end

    local function beginCapture(self)
        if is_invalid then
            return false
        end
        if captures >= cap_limit then
            mark_invalid("capture_budget")
            return false
        end
        captures = captures + 1
        return true
    end

    local function charge(self, kind_arg)
        local kind = kind_arg
        if kind == nil and type(self) == "string" then
            kind = self
        end

        if kind ~= "world" and kind ~= "membership" and kind ~= "state" and kind ~= "symbol" then
            mark_invalid("invalid_kind")
            return false
        end

        if is_invalid then
            return false
        end

        if operations >= op_limit then
            mark_invalid("operation_budget")
            return false
        end

        operations = operations + 1
        if kind == "world" then
            g_world = g_world + 1
        elseif kind == "membership" then
            g_membership = g_membership + 1
        elseif kind == "state" then
            g_state = g_state + 1
        elseif kind == "symbol" then
            g_symbol = g_symbol + 1
        end
        return true
    end

    local function invalidate(self)
        mark_invalid("cancelled")
        return false
    end

    local function snapshot(self)
        return {
            captures = captures,
            operations = operations,
            captureLimit = cap_limit,
            operationLimit = op_limit,
            remainingCaptures = (cap_limit - captures > 0) and (cap_limit - captures) or 0,
            remainingOperations = (op_limit - operations > 0) and (op_limit - operations) or 0,
            valid = not is_invalid,
            reason = first_reason,
            world = g_world,
            membership = g_membership,
            state = g_state,
            symbol = g_symbol,
        }
    end

    inst.beginCapture = beginCapture
    inst.charge = charge
    inst.invalidate = invalidate
    inst.snapshot = snapshot

    return inst
end

return CaptureAccounting
