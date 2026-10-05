-- Gemini authored; Codex reviewed. Inert symbol inspection only, no native invocation.
local NativeExposureProbe = {}

local MAX_CAPTURES = 54
local MAX_SYMBOLS = 26

local ALLOWLIST = {
    { key = "forward_x", kind = "function" },
    { key = "forward_y", kind = "function" },
    { key = "cell_get_square", kind = "function" },
    { key = "square_get_moving_objects", kind = "function" },
    { key = "list_size", kind = "function" },
    { key = "list_get", kind = "function" },
    { key = "los_line_clear", kind = "function" },
    { key = "get_cell", kind = "function" },
    { key = "enum_clear", kind = "enum" },
    { key = "enum_open_door", kind = "enum" },
    { key = "enum_window", kind = "enum" },
    { key = "enum_blocked", kind = "enum" },
    { key = "enum_closed_door", kind = "enum" },
}

local function is_finite(n)
    return type(n) == "number" and n == n and n ~= 1/0 and n ~= -1/0
end

local function is_str96(s)
    return type(s) == "string" and #s > 0 and #s <= 96
end

local function val_cap(c)
    if type(c) ~= "table" then return false end
    local fx, fy = rawget(c, "fx"), rawget(c, "fy")
    local x, y, z = rawget(c, "x"), rawget(c, "y"), rawget(c, "z")
    return is_str96(rawget(c, "controller")) and is_str96(rawget(c, "npc")) and
           is_str96(rawget(c, "cell")) and is_str96(rawget(c, "generation")) and
           rawget(c, "alive") == true and rawget(c, "resident") == true and rawget(c, "cancelled") == false and
           is_finite(x) and math.abs(x) <= 1e6 and is_finite(y) and math.abs(y) <= 1e6 and is_finite(z) and math.abs(z) <= 1e6 and
           is_finite(fx) and math.abs(fx) <= 1e6 and is_finite(fy) and math.abs(fy) <= 1e6 and (fx ~= 0 or fy ~= 0)
end

local function cp_cap(c)
    return {
        controller = rawget(c, "controller"),
        npc = rawget(c, "npc"),
        cell = rawget(c, "cell"),
        generation = rawget(c, "generation"),
        alive = true,
        resident = true,
        cancelled = false,
        x = rawget(c, "x") + 0.0,
        y = rawget(c, "y") + 0.0,
        z = rawget(c, "z") + 0.0,
        fx = rawget(c, "fx") + 0.0,
        fy = rawget(c, "fy") + 0.0,
    }
end

local function cap_eq(a, b)
    if not a or not b then return false end
    return a.controller == b.controller and a.npc == b.npc and a.cell == b.cell and a.generation == b.generation and
           a.alive == b.alive and a.resident == b.resident and a.cancelled == b.cancelled and
           a.x == b.x and a.y == b.y and a.z == b.z and a.fx == b.fx and a.fy == b.fy
end

local function check_expected_type(kind, val)
    if kind == "function" then
        return type(val) == "function"
    elseif kind == "enum" then
        local t = type(val)
        return t == "table" or t == "userdata"
    end
    return false
end

function NativeExposureProbe.new()
    local busy = false
    local revision = 1

    local t_attempts = 0
    local t_completed = 0
    local t_aborted = 0

    local inst = {}

    local function reset(self)
        revision = revision + 1
    end

    local function snapshot(self)
        return {
            attempts = t_attempts,
            completed = t_completed,
            aborted = t_aborted,
        }
    end

    local function run(self, api_arg)
        local api = api_arg
        if api == nil and type(self) == "table" and rawget(self, "run") == nil then
            api = self
        end
        if busy then
            return {
                status = "reentrancy_rejected",
                reason = "reentrant_call",
                lighting = "unknown",
                nativeAcceptance = false,
                results = {},
                counts = { symbols = 0, captures = 0 },
                enumBindings = "unknown",
            }
        end

        local counts = { symbols = 0, captures = 0 }

        if type(api) ~= "table" then
            return {
                status = "aborted",
                reason = "invalid_api",
                lighting = "unknown",
                nativeAcceptance = false,
                results = {},
                counts = counts,
                enumBindings = "unknown",
            }
        end

        local api_cap = rawget(api, "capture")
        local api_read = rawget(api, "readSymbol")

        if type(api_cap) ~= "function" or type(api_read) ~= "function" then
            return {
                status = "aborted",
                reason = "invalid_api",
                lighting = "unknown",
                nativeAcceptance = false,
                results = {},
                counts = counts,
                enumBindings = "unknown",
            }
        end

        busy = true
        t_attempts = t_attempts + 1
        local pass_rev = revision
        local invalidated = false
        local first_abort_reason = nil
        local ret_val = nil

        local function mark_invalid(r)
            if not invalidated then
                invalidated = true
                first_abort_reason = r or "lifecycle_invalidated"
            end
        end

        local function do_capture()
            if revision ~= pass_rev then
                mark_invalid("reset_during_probe")
                return nil
            end
            if invalidated then
                return nil
            end
            if counts.captures >= MAX_CAPTURES then
                mark_invalid("capture_limit_reached")
                return nil
            end
            counts.captures = counts.captures + 1
            local ok, res = pcall(api_cap)
            if revision ~= pass_rev then
                mark_invalid("reset_during_probe")
                return nil
            end
            if not ok or not val_cap(res) then
                mark_invalid("capture_invalid")
                return nil
            end
            return cp_cap(res)
        end

        local run_ok, run_err = pcall(function()
            local anchor = do_capture()
            if not anchor then
                error({ abort = true, reason = first_abort_reason or "initial_capture_failed" })
            end

            local function chk_life()
                if revision ~= pass_rev then
                    mark_invalid("reset_during_probe")
                    return false
                end
                if invalidated then
                    return false
                end
                local c = do_capture()
                if revision ~= pass_rev then
                    mark_invalid("reset_during_probe")
                    return false
                end
                if not c then
                    return false
                end
                if not cap_eq(anchor, c) then
                    mark_invalid("lifecycle_drift")
                    return false
                end
                return true
            end

            local results = {}
            local exposed_enums = {}

            for i = 1, #ALLOWLIST do
                local item = ALLOWLIST[i]
                local sym_key = item.key
                local sym_kind = item.kind

                local read_records = {}

                for attempt = 1, 2 do
                    if counts.captures + 2 + 1 > MAX_CAPTURES then
                        mark_invalid("capture_limit_reached")
                        break
                    end
                    if not chk_life() then break end

                    if counts.symbols >= MAX_SYMBOLS then
                        mark_invalid("symbol_limit_reached")
                        break
                    end
                    counts.symbols = counts.symbols + 1
                    local ok, val = pcall(api_read, sym_key)

                    if revision ~= pass_rev then
                        mark_invalid("reset_during_probe")
                        break
                    end

                    read_records[attempt] = { ok = ok, val = val }

                    if not chk_life() then break end
                end

                if invalidated then
                    break
                end

                local r1 = read_records[1]
                local r2 = read_records[2]

                local sym_status = "unknown"
                local val_type = "unknown"

                if r1 and r1.ok then
                    val_type = type(r1.val)
                end

                if not (r1 and r2) then
                    sym_status = "query_error"
                elseif not r1.ok or not r2.ok then
                    sym_status = "query_error"
                elseif r1.val == nil or r2.val == nil then
                    sym_status = "missing"
                elseif not check_expected_type(sym_kind, r1.val) or not check_expected_type(sym_kind, r2.val) then
                    sym_status = "type_mismatch"
                elseif not rawequal(r1.val, r2.val) then
                    sym_status = "unstable_reference"
                else
                    sym_status = "exposed"
                    if sym_kind == "enum" then
                        exposed_enums[sym_key] = r1.val
                    end
                end

                results[#results + 1] = {
                    key = sym_key,
                    status = sym_status,
                    valueType = val_type,
                }
            end

            if invalidated then
                error({ abort = true, reason = first_abort_reason })
            end

            if not chk_life() then
                error({ abort = true, reason = first_abort_reason or "final_check_failed" })
            end

            local enum_bindings = "unknown"
            local required_enums = {
                "enum_clear",
                "enum_open_door",
                "enum_window",
                "enum_blocked",
                "enum_closed_door",
            }
            local all_enums_exposed = true
            local enum_refs = {}
            for _, ek in ipairs(required_enums) do
                local ev = exposed_enums[ek]
                if ev == nil then
                    all_enums_exposed = false
                    break
                end
                for _, prior in ipairs(enum_refs) do
                    if rawequal(ev, prior) then
                        all_enums_exposed = false
                        break
                    end
                end
                if not all_enums_exposed then break end
                enum_refs[#enum_refs + 1] = ev
            end

            if all_enums_exposed and #enum_refs == 5 then
                enum_bindings = "distinct_references"
            end

            t_completed = t_completed + 1
            ret_val = {
                status = "completed",
                reason = "plan_completed",
                lighting = "unknown",
                nativeAcceptance = false,
                results = results,
                counts = counts,
                enumBindings = enum_bindings,
            }
        end)

        busy = false

        if not run_ok then
            t_aborted = t_aborted + 1
            local abort_reason = first_abort_reason
            if type(run_err) == "table" and run_err.abort then
                abort_reason = run_err.reason
            elseif not abort_reason then
                abort_reason = "internal_error"
            end
            return {
                status = "aborted",
                reason = abort_reason,
                lighting = "unknown",
                nativeAcceptance = false,
                results = {},
                counts = counts,
                enumBindings = "unknown",
            }
        end

        return ret_val
    end

    inst.run = run
    inst.reset = reset
    inst.snapshot = snapshot

    return inst
end

return NativeExposureProbe
