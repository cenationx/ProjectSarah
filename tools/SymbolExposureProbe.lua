-- tools/SymbolExposureProbe.lua
-- Standalone inert symbol exposure inspection tool for Project Sarah.
-- Intended Lua 5.1-compatible source. No engine imports or direct native calls.
-- Injected callbacks may execute bridge work; attempt ceilings do not bound cost.

local SymbolExposureProbe = {}

local MAX_CAPTURES = 54
local MAX_SYMBOLS = 26

local PLAN = {
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

local ENUM_KEYS = {
    "enum_clear",
    "enum_open_door",
    "enum_window",
    "enum_blocked",
    "enum_closed_door",
}

local function is_valid_token(s)
    return type(s) == "string" and #s >= 1 and #s <= 96
end

local function check_type(kind, val)
    if kind == "function" then
        return type(val) == "function"
    elseif kind == "enum" then
        local t = type(val)
        return t == "table" or t == "userdata"
    end
    return false
end

local function make_outcome(status, reason, counts, results, enum_refs)
    return {
        status = status,
        reason = reason,
        evidenceScope = "supplied_reference_comparison",
        observerLiveness = "unassessed",
        residency = "unassessed",
        nativeIdentity = "unassessed",
        worldGeneration = "unassessed",
        methodInvocation = "unassessed",
        lighting = "unknown",
        nativeAcceptance = false,
        results = results or {},
        counts = counts or { captures = 0, symbols = 0 },
        enumReferences = enum_refs or "unknown",
    }
end

function SymbolExposureProbe.new()
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
            return make_outcome("reentrancy_rejected", "busy", { captures = 0, symbols = 0 }, {}, "unknown")
        end

        if type(api) ~= "table" then
            return make_outcome("aborted", "invalid_api", { captures = 0, symbols = 0 }, {}, "unknown")
        end

        local cb_capture = rawget(api, "captureMarker")
        local cb_read = rawget(api, "readSymbol")

        if type(cb_capture) ~= "function" or type(cb_read) ~= "function" then
            return make_outcome("aborted", "invalid_api", { captures = 0, symbols = 0 }, {}, "unknown")
        end

        busy = true
        t_attempts = t_attempts + 1

        local pass_rev = revision
        local n_captures = 0
        local n_symbols = 0
        local invalidated = false
        local abort_reason = nil

        local function mark_abort(r)
            if not invalidated then
                invalidated = true
                abort_reason = r
            end
        end

        local function do_capture()
            if revision ~= pass_rev then
                mark_abort("reset_during_probe")
                return nil
            end
            if invalidated then
                return nil
            end
            if n_captures >= MAX_CAPTURES then
                mark_abort("capture_limit_reached")
                return nil
            end

            n_captures = n_captures + 1
            local ok, ret = pcall(cb_capture)

            if revision ~= pass_rev then
                mark_abort("reset_during_probe")
                return nil
            end
            if not ok then
                mark_abort("marker_invalid")
                return nil
            end
            if type(ret) ~= "table" then
                mark_abort("marker_invalid")
                return nil
            end

            local fw = rawget(ret, "framework")
            local rev = rawget(ret, "revision")
            local cancelled = rawget(ret, "cancelled")

            if cancelled ~= false then
                mark_abort("marker_cancelled")
                return nil
            end
            if not is_valid_token(fw) or not is_valid_token(rev) then
                mark_abort("marker_invalid")
                return nil
            end

            return {
                framework = fw,
                revision = rev,
                cancelled = false,
            }
        end

        local run_ok, final_outcome = pcall(function()
            local anchor = do_capture()
            if not anchor then
                error({ abort = true, reason = abort_reason or "initial_marker_failed" })
            end

            local function chk_marker()
                if revision ~= pass_rev then
                    mark_abort("reset_during_probe")
                    return false
                end
                if invalidated then
                    return false
                end
                local m = do_capture()
                if revision ~= pass_rev then
                    mark_abort("reset_during_probe")
                    return false
                end
                if not m then
                    return false
                end
                if m.framework ~= anchor.framework or m.revision ~= anchor.revision then
                    mark_abort("marker_drift")
                    return false
                end
                return true
            end

            local results = {}
            local enum_matched_refs = {}

            for i = 1, #PLAN do
                local item = PLAN[i]
                local sym_key = item.key
                local sym_kind = item.kind

                local read_records = {}

                for attempt = 1, 2 do
                    if n_captures + 2 > MAX_CAPTURES then
                        mark_abort("capture_limit_reached")
                        break
                    end

                    if not chk_marker() then break end

                    if n_symbols >= MAX_SYMBOLS then
                        mark_abort("symbol_limit_reached")
                        break
                    end

                    n_symbols = n_symbols + 1
                    local ok, val = pcall(cb_read, sym_key)

                    if revision ~= pass_rev then
                        mark_abort("reset_during_probe")
                        break
                    end

                    read_records[attempt] = { ok = ok, val = val }

                    if not chk_marker() then break end
                end

                if invalidated then break end

                local r1 = read_records[1]
                local r2 = read_records[2]

                local row_status = "unknown"
                local val_type = "nil"

                if r1 and r1.ok and r1.val ~= nil then
                    val_type = type(r1.val)
                elseif r2 and r2.ok and r2.val ~= nil then
                    val_type = type(r2.val)
                end

                if not (r1 and r2) then
                    row_status = "query_error"
                elseif not r1.ok or not r2.ok then
                    row_status = "query_error"
                elseif r1.val == nil or r2.val == nil then
                    row_status = "missing"
                elseif not check_type(sym_kind, r1.val) or not check_type(sym_kind, r2.val) then
                    row_status = "type_mismatch"
                elseif not rawequal(r1.val, r2.val) then
                    row_status = "unstable_reference"
                else
                    row_status = "reference_matched"
                    if sym_kind == "enum" then
                        enum_matched_refs[sym_key] = r1.val
                    end
                end

                results[#results + 1] = {
                    key = sym_key,
                    status = row_status,
                    valueType = val_type,
                }
            end

            if invalidated then
                error({ abort = true, reason = abort_reason or "probe_aborted" })
            end

            if not chk_marker() then
                error({ abort = true, reason = abort_reason or "final_marker_failed" })
            end

            local enum_references = "unknown"
            local all_enums_matched = true
            local enum_list = {}

            for _, ek in ipairs(ENUM_KEYS) do
                local ev = enum_matched_refs[ek]
                if ev == nil then
                    all_enums_matched = false
                    break
                end
                for _, prior in ipairs(enum_list) do
                    if rawequal(ev, prior) then
                        all_enums_matched = false
                        break
                    end
                end
                if not all_enums_matched then break end
                enum_list[#enum_list + 1] = ev
            end

            if all_enums_matched and #enum_list == 5 then
                enum_references = "distinct_references"
            end

            enum_matched_refs = nil
            enum_list = nil

            t_completed = t_completed + 1
            return make_outcome(
                "completed",
                "plan_completed",
                { captures = n_captures, symbols = n_symbols },
                results,
                enum_references
            )
        end)

        busy = false

        if not run_ok then
            t_aborted = t_aborted + 1
            local err_reason = abort_reason
            if type(final_outcome) == "table" and final_outcome.abort then
                err_reason = final_outcome.reason
            elseif not err_reason then
                err_reason = "internal_error"
            end
            return make_outcome(
                "aborted",
                err_reason,
                { captures = n_captures, symbols = n_symbols },
                {},
                "unknown"
            )
        end

        return final_outcome
    end

    inst.run = run
    inst.reset = reset
    inst.snapshot = snapshot

    return inst
end

return SymbolExposureProbe
