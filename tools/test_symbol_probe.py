"""Actual-Lua narrowed symbol policy fixtures; no native acceptance."""
from pathlib import Path
import sys
root = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(root / "tools/dependencies/python"))
from lupa import LuaRuntime
lua = LuaRuntime(unpack_returned_tuples=True)
source = (root / "tools/SymbolExposureProbe.lua").read_text(encoding="utf-8")
lua.globals().SymbolProbeSource = source
lua.globals().opaque1 = object()
lua.globals().opaque2 = object()
lua.globals().SymbolExposureProbe = lua.execute(source)
lua.execute(r"""
-- tests/SymbolExposureProbe_spec.lua
-- Comprehensive actual-module Lua fixtures for SymbolExposureProbe.
-- Pure Lua 5.1-compatible, executed via Lupa Lua55.

local SymbolExposureProbe = assert(SymbolExposureProbe)

local test_count = 0

local function run_test(name, fn)
    test_count = test_count + 1
    local ok, err = pcall(fn)
    if not ok then
        error(string.format("FAIL in test [%s]: %s", name, tostring(err)))
    end
    print(string.format("PASS: %s", name))
end

local function make_valid_marker(fw, rev)
    return {
        framework = fw or "fw_token_v1",
        revision = rev or "rev_token_v1",
        cancelled = false,
    }
end

local function make_default_symbols()
    return {
        forward_x = function() return 1.0 end,
        forward_y = function() return 0.0 end,
        cell_get_square = function() return {} end,
        square_get_moving_objects = function() return {} end,
        list_size = function() return 0 end,
        list_get = function() return nil end,
        los_line_clear = function() return {} end,
        get_cell = function() return {} end,
        enum_clear = { name = "Clear" },
        enum_open_door = { name = "ClearThroughOpenDoor" },
        enum_window = { name = "ClearThroughWindow" },
        enum_blocked = { name = "Blocked" },
        enum_closed_door = { name = "ClearThroughClosedDoor" },
    }
end

-- =========================================================================
-- Test Group 1: Completion, Ceilings & Metadata
-- =========================================================================

run_test("01_valid_completion_exact_ceilings", function()
    local p = SymbolExposureProbe.new()
    local syms = make_default_symbols()
    local cap_count = 0
    local sym_count = 0

    local api = {
        captureMarker = function()
            cap_count = cap_count + 1
            return make_valid_marker()
        end,
        readSymbol = function(k)
            sym_count = sym_count + 1
            return syms[k]
        end,
    }

    local res = p:run(api)
    assert(res.status == "completed", "Expected status completed")
    assert(res.reason == "plan_completed", "Expected plan_completed")
    assert(res.counts.captures == 54, "Expected exactly 54 captures")
    assert(res.counts.symbols == 26, "Expected exactly 26 symbol reads")
    assert(cap_count == 54, "Actual capture callback count should be 54")
    assert(sym_count == 26, "Actual read callback count should be 26")
    assert(#res.results == 13, "Expected 13 rows")
    assert(res.enumReferences == "distinct_references", "Expected distinct_references")
    for _, r in ipairs(res.results) do
        assert(r.status == "reference_matched", "Row status must be reference_matched")
    end
end)

run_test("02_all_outcomes_contain_required_metadata", function()
    local p = SymbolExposureProbe.new()
    local res = p:run({})
    local keys = {
        evidenceScope = "supplied_reference_comparison",
        observerLiveness = "unassessed",
        residency = "unassessed",
        nativeIdentity = "unassessed",
        worldGeneration = "unassessed",
        methodInvocation = "unassessed",
        lighting = "unknown",
        nativeAcceptance = false,
        enumReferences = "unknown",
    }
    for k, expected in pairs(keys) do
        assert(res[k] == expected, string.format("Field [%s] mismatch: got %s, expected %s", k, tostring(res[k]), tostring(expected)))
    end
end)

-- =========================================================================
-- Test Group 2: Marker Validation & Injected Geometry Ignored
-- =========================================================================

run_test("03_marker_ignores_injected_geometry_and_residency", function()
    local p = SymbolExposureProbe.new()
    local syms = make_default_symbols()
    local api = {
        captureMarker = function()
            local m = make_valid_marker()
            m.x = 999.0
            m.y = 888.0
            m.z = 0.0
            m.fx = 1.0
            m.fy = 0.0
            m.alive = false       -- Even false liveness injected must be ignored
            m.resident = false    -- Injected resident false must be ignored
            m.npc = "fake_npc"
            m.cell = "fake_cell"
            m.controller = "fake_ctrl"
            return m
        end,
        readSymbol = function(k) return syms[k] end,
    }
    local res = p:run(api)
    assert(res.status == "completed", "Injected fields must not abort probe")
    assert(res.counts.captures == 54, "Captures must still reach 54")
end)

run_test("04_marker_validation_rejects_missing_fields", function()
    local p = SymbolExposureProbe.new()
    local cases = {
        { revision = "r", cancelled = false }, -- missing framework
        { framework = "f", cancelled = false }, -- missing revision
        { framework = "f", revision = "r" },    -- missing cancelled
    }
    for _, m in ipairs(cases) do
        local res = p:run({
            captureMarker = function() return m end,
            readSymbol = function() return function() end end,
        })
        assert(res.status == "aborted", "Missing marker fields must abort")
        assert(res.reason == "marker_invalid" or res.reason == "marker_cancelled", "Reason must match invalid marker")
        assert(#res.results == 0, "Results must be empty on abort")
    end
end)

run_test("05_marker_validation_rejects_invalid_types_and_lengths", function()
    local p = SymbolExposureProbe.new()
    local cases = {
        { framework = "", revision = "r", cancelled = false },
        { framework = string.rep("a", 97), revision = "r", cancelled = false },
        { framework = 123, revision = "r", cancelled = false },
        { framework = "f", revision = "", cancelled = false },
        { framework = "f", revision = string.rep("b", 97), cancelled = false },
        { framework = "f", revision = {}, cancelled = false },
        "not_a_table",
        12345,
    }
    for _, m in ipairs(cases) do
        local res = p:run({
            captureMarker = function() return m end,
            readSymbol = function() return function() end end,
        })
        assert(res.status == "aborted", "Bad token types/lengths must abort")
        assert(#res.results == 0, "Results must be empty on abort")
    end
end)

run_test("06_marker_cancelled_true_aborts", function()
    local p = SymbolExposureProbe.new()
    local res = p:run({
        captureMarker = function()
            return { framework = "f", revision = "r", cancelled = true }
        end,
        readSymbol = function() return function() end end,
    })
    assert(res.status == "aborted", "Cancelled marker must abort")
    assert(res.reason == "marker_cancelled", "Reason must be marker_cancelled")
    assert(#res.results == 0, "Results must be empty on abort")
end)

run_test("07_marker_throw_aborts", function()
    local p = SymbolExposureProbe.new()
    local res = p:run({
        captureMarker = function() error("marker_failure") end,
        readSymbol = function() return function() end end,
    })
    assert(res.status == "aborted", "Marker throw must abort")
    assert(res.reason == "marker_invalid" or res.reason == "initial_marker_failed", "Reason must be marker_invalid")
    assert(#res.results == 0, "Results must be empty on abort")
end)

-- =========================================================================
-- Test Group 3: Drift & Reset Sweeps Across Boundaries
-- =========================================================================

run_test("08_marker_drift_framework_aborts", function()
    local p = SymbolExposureProbe.new()
    local syms = make_default_symbols()
    local count = 0
    local res = p:run({
        captureMarker = function()
            count = count + 1
            if count == 5 then
                return make_valid_marker("fw_mutated", "rev_token_v1")
            end
            return make_valid_marker()
        end,
        readSymbol = function(k) return syms[k] end,
    })
    assert(res.status == "aborted", "Framework drift must abort")
    assert(res.reason == "marker_drift", "Reason must be marker_drift")
    assert(#res.results == 0, "Results must be empty")
end)

run_test("09_marker_drift_revision_aborts", function()
    local p = SymbolExposureProbe.new()
    local syms = make_default_symbols()
    local count = 0
    local res = p:run({
        captureMarker = function()
            count = count + 1
            if count == 10 then
                return make_valid_marker("fw_token_v1", "rev_mutated")
            end
            return make_valid_marker()
        end,
        readSymbol = function(k) return syms[k] end,
    })
    assert(res.status == "aborted", "Revision drift must abort")
    assert(res.reason == "marker_drift", "Reason must be marker_drift")
    assert(#res.results == 0, "Results must be empty")
end)

run_test("10_sweep_all_54_marker_boundaries_drift", function()
    -- Assert that drift injected at ANY boundary 2..54 immediately aborts and halts subsequent callbacks
    for trigger = 2, 54 do
        local p = SymbolExposureProbe.new()
        local syms = make_default_symbols()
        local call_count = 0
        local res = p:run({
            captureMarker = function()
                call_count = call_count + 1
                if call_count == trigger then
                    return make_valid_marker("fw_drifted", "rev_token_v1")
                end
                return make_valid_marker()
            end,
            readSymbol = function(k) return syms[k] end,
        })
        assert(res.status == "aborted", "Drift at boundary " .. trigger .. " must abort")
        assert(res.reason == "marker_drift", "Reason must be marker_drift at boundary " .. trigger)
        assert(call_count == trigger, "Callbacks must halt immediately after boundary " .. trigger)
        assert(#res.results == 0, "Results must be empty")
    end
end)

run_test("11_sweep_all_54_marker_boundaries_reset", function()
    -- Calling probe:reset() at any capture boundary 1..54 aborts immediately
    for trigger = 1, 54 do
        local p = SymbolExposureProbe.new()
        local syms = make_default_symbols()
        local call_count = 0
        local res = p:run({
            captureMarker = function()
                call_count = call_count + 1
                if call_count == trigger then
                    p:reset()
                end
                return make_valid_marker()
            end,
            readSymbol = function(k) return syms[k] end,
        })
        assert(res.status == "aborted", "Reset at capture boundary " .. trigger .. " must abort")
        assert(res.reason == "reset_during_probe", "Reason must be reset_during_probe at boundary " .. trigger)
        assert(#res.results == 0, "Results must be empty")
    end
end)

run_test("12_sweep_all_26_read_boundaries_reset", function()
    -- Calling probe:reset() at any read boundary 1..26 aborts at next marker
    for trigger = 1, 26 do
        local p = SymbolExposureProbe.new()
        local syms = make_default_symbols()
        local read_count = 0
        local res = p:run({
            captureMarker = function() return make_valid_marker() end,
            readSymbol = function(k)
                read_count = read_count + 1
                if read_count == trigger then
                    p:reset()
                end
                return syms[k]
            end,
        })
        assert(res.status == "aborted", "Reset at read boundary " .. trigger .. " must abort")
        assert(res.reason == "reset_during_probe", "Reason must be reset_during_probe at read " .. trigger)
        assert(#res.results == 0, "Results must be empty")
    end
end)

-- =========================================================================
-- Test Group 4: Row Status Hierarchy & Resolution
-- =========================================================================

run_test("13_resolver_query_error_priority_and_continuation", function()
    local p = SymbolExposureProbe.new()
    local syms = make_default_symbols()
    syms.forward_x = function() error("native_bridge_fault") end

    local res = p:run({
        captureMarker = function() return make_valid_marker() end,
        readSymbol = function(k)
            if k == "forward_x" then error("read_error") end
            return syms[k]
        end,
    })
    assert(res.status == "completed", "Row errors must continue pass unless marker invalid")
    assert(res.counts.captures == 54 and res.counts.symbols == 26, "All reads/captures completed")
    local row1 = res.results[1]
    assert(row1.key == "forward_x", "Key is forward_x")
    assert(row1.status == "query_error", "Status must be query_error on throw")
    assert(res.enumReferences == "distinct_references", "Enums still distinct")
end)

run_test("14_resolver_missing_priority", function()
    local p = SymbolExposureProbe.new()
    local syms = make_default_symbols()
    local read_calls = 0
    local res = p:run({
        captureMarker = function() return make_valid_marker() end,
        readSymbol = function(k)
            if k == "cell_get_square" then
                read_calls = read_calls + 1
                if read_calls == 1 then return nil end -- One nil, one function
                return function() end
            end
            return syms[k]
        end,
    })
    assert(res.status == "completed", "Pass completed")
    local target_row = nil
    for _, r in ipairs(res.results) do
        if r.key == "cell_get_square" then target_row = r break end
    end
    assert(target_row ~= nil, "Row exists")
    assert(target_row.status == "missing", "Missing priority when either read is nil")
end)

run_test("15_resolver_type_mismatch_function_and_enum", function()
    local p = SymbolExposureProbe.new()
    local syms = make_default_symbols()
    syms.forward_x = { not_a_func = true } -- table instead of function
    syms.enum_clear = "string_not_table_or_userdata" -- string instead of enum

    local res = p:run({
        captureMarker = function() return make_valid_marker() end,
        readSymbol = function(k) return syms[k] end,
    })
    assert(res.status == "completed", "Pass completed")
    for _, r in ipairs(res.results) do
        if r.key == "forward_x" or r.key == "enum_clear" then
            assert(r.status == "type_mismatch", "Expected type_mismatch for " .. r.key)
        end
    end
    assert(res.enumReferences == "unknown", "Enum mismatch must yield unknown references")
end)

run_test("16_resolver_unstable_reference", function()
    local p = SymbolExposureProbe.new()
    local syms = make_default_symbols()
    local call_count = 0
    local res = p:run({
        captureMarker = function() return make_valid_marker() end,
        readSymbol = function(k)
            if k == "los_line_clear" then
                call_count = call_count + 1
                return function() return call_count end -- fresh function reference each time
            end
            return syms[k]
        end,
    })
    assert(res.status == "completed", "Pass completed")
    local target_row = nil
    for _, r in ipairs(res.results) do
        if r.key == "los_line_clear" then target_row = r break end
    end
    assert(target_row ~= nil and target_row.status == "unstable_reference", "Expected unstable_reference")
end)

run_test("17_enums_duplicate_references_yields_unknown", function()
    local p = SymbolExposureProbe.new()
    local syms = make_default_symbols()
    local shared_enum = { name = "Shared" }
    syms.enum_clear = shared_enum
    syms.enum_blocked = shared_enum -- Duplicate reference

    local res = p:run({
        captureMarker = function() return make_valid_marker() end,
        readSymbol = function(k) return syms[k] end,
    })
    assert(res.status == "completed", "Pass completed")
    assert(res.enumReferences == "unknown", "Duplicate enum references must yield unknown")
end)

run_test("18_enums_missing_or_mismatch_yields_unknown", function()
    local p = SymbolExposureProbe.new()
    local syms = make_default_symbols()
    syms.enum_closed_door = nil -- missing 5th enum

    local res = p:run({
        captureMarker = function() return make_valid_marker() end,
        readSymbol = function(k) return syms[k] end,
    })
    assert(res.status == "completed", "Pass completed")
    assert(res.enumReferences == "unknown", "Missing enum yields unknown")
end)

-- =========================================================================
-- Test Group 5: Non-Invocation & Hostile Metamethod Isolation
-- =========================================================================

run_test("19_returned_functions_and_objects_never_invoked", function()
    local p = SymbolExposureProbe.new()
    local invocations = 0
    local guarded_fn = function()
        invocations = invocations + 1
        error("ILLEGAL_INVOCATION: returned function must never be called!")
    end
    local syms = make_default_symbols()
    syms.forward_x = guarded_fn
    syms.get_cell = guarded_fn

    local res = p:run({
        captureMarker = function() return make_valid_marker() end,
        readSymbol = function(k) return syms[k] end,
    })
    assert(res.status == "completed", "Pass completed")
    assert(invocations == 0, "Zero invocations must occur on supplied functions")
end)

run_test("20_hostile_metamethods_uncalled", function()
    local p = SymbolExposureProbe.new()
    local hostile_mt = {
        __index = function(_, k) error("HOSTILE __index called: " .. tostring(k)) end,
        __eq = function(_, _) error("HOSTILE __eq called!") end,
        __tostring = function(_) error("HOSTILE __tostring called!") end,
    }
    local hostile_enum1 = setmetatable({ id = 1 }, hostile_mt)
    local hostile_enum2 = setmetatable({ id = 2 }, hostile_mt)
    local hostile_enum3 = setmetatable({ id = 3 }, hostile_mt)
    local hostile_enum4 = setmetatable({ id = 4 }, hostile_mt)
    local hostile_enum5 = setmetatable({ id = 5 }, hostile_mt)

    local syms = make_default_symbols()
    syms.enum_clear = hostile_enum1
    syms.enum_open_door = hostile_enum2
    syms.enum_window = hostile_enum3
    syms.enum_blocked = hostile_enum4
    syms.enum_closed_door = hostile_enum5

    local res = p:run({
        captureMarker = function() return make_valid_marker() end,
        readSymbol = function(k) return syms[k] end,
    })
    assert(res.status == "completed", "Hostile metamethods must never be triggered")
    assert(res.enumReferences == "distinct_references", "rawequal comparison does not trigger __eq")
end)

run_test("21_frozen_api_tamper_resistance", function()
    local p = SymbolExposureProbe.new()
    local syms = make_default_symbols()
    local api = {}
    api.captureMarker = function()
        -- Attempt to tamper with API after probe starts
        api.readSymbol = nil
        api.captureMarker = nil
        return make_valid_marker()
    end
    api.readSymbol = function(k) return syms[k] end

    local res = p:run(api)
    assert(res.status == "completed", "Tampered api table must not affect frozen callbacks")
    assert(res.counts.captures == 54 and res.counts.symbols == 26, "All 54 captures and 26 reads executed")
end)

run_test("22_reentrancy_rejected_preserves_outer_pass", function()
    local p = SymbolExposureProbe.new()
    local syms = make_default_symbols()
    local inner_res = nil
    local api = {
        captureMarker = function() return make_valid_marker() end,
        readSymbol = function(k)
            if k == "get_cell" and not inner_res then
                -- Attempt reentrant run
                inner_res = p:run({})
            end
            return syms[k]
        end,
    }
    local res = p:run(api)
    assert(res.status == "completed", "Outer run must complete cleanly")
    assert(inner_res ~= nil, "Inner run attempted")
    assert(inner_res.status == "reentrancy_rejected", "Inner run must be reentrancy_rejected")
    assert(inner_res.reason == "busy", "Inner reason must be busy")
    assert(p:snapshot().completed == 1, "Completed attempts count must be exactly 1")
    assert(p:snapshot().attempts == 1, "Reentrancy rejected must not increment started attempts")
end)

run_test("23_mutable_marker_table_tampering_detected", function()
    local p = SymbolExposureProbe.new()
    local syms = make_default_symbols()
    local shared_marker_table = make_valid_marker()
    local calls = 0

    local res = p:run({
        captureMarker = function()
            calls = calls + 1
            if calls == 15 then
                -- Mutate the table object previously returned
                shared_marker_table.framework = "tampered_framework"
            end
            return shared_marker_table
        end,
        readSymbol = function(k) return syms[k] end,
    })
    -- Because the probe copied scalar fields immediately on anchor, subsequent reads of the mutated table drift!
    assert(res.status == "aborted", "Tampered marker table must drift and abort")
    assert(res.reason == "marker_drift", "Reason must be marker_drift")
end)

-- =========================================================================
-- Test Group 6: Memory Safety, Scalar Privacy & Reusability
-- =========================================================================

run_test("24_no_retained_handles_actual_lua_gc", function()
    local p = SymbolExposureProbe.new()
    local weak = setmetatable({}, { __mode = "v" })

    do
        local candidate_func = function() return 42 end
        local candidate_enum = { tag = "gc_target" }
        weak.fn = candidate_func
        weak.enum = candidate_enum

        local res = p:run({
            captureMarker = function() return make_valid_marker() end,
            readSymbol = function(k)
                if k == "forward_x" then return candidate_func end
                if k == "enum_clear" then return candidate_enum end
                return function() end
            end,
        })
        assert(res.status == "completed", "Pass completed")
        res = nil -- Drop outcome reference
    end

    collectgarbage("collect")
    collectgarbage("collect")
    assert(weak.fn == nil, "Probe must not retain reference to candidate function after return")
    assert(weak.enum == nil, "Probe must not retain reference to candidate enum after return")
end)

local function check_scalars_only(tbl)
    for k, v in pairs(tbl) do
        local tv = type(v)
        if tv == "table" then
            check_scalars_only(v)
        else
            assert(tv == "string" or tv == "number" or tv == "boolean" or tv == "nil",
                "Disallowed non-scalar type: " .. tv .. " at key " .. tostring(k))
        end
    end
end

run_test("25_scalar_output_recursively", function()
    local p = SymbolExposureProbe.new()
    local syms = make_default_symbols()
    local res = p:run({
        captureMarker = function() return make_valid_marker() end,
        readSymbol = function(k) return syms[k] end,
    })
    assert(res.status == "completed", "Pass completed")
    check_scalars_only(res)
end)

run_test("26_private_counter_isolation_and_snapshot", function()
    local p = SymbolExposureProbe.new()
    local syms = make_default_symbols()

    -- Invalid API does not increment attempts
    p:run("not_an_api")
    local s1 = p:snapshot()
    assert(s1.attempts == 0 and s1.completed == 0 and s1.aborted == 0, "Invalid API must not advance attempts")

    -- Completed run increments attempts and completed
    p:run({
        captureMarker = function() return make_valid_marker() end,
        readSymbol = function(k) return syms[k] end,
    })
    local s2 = p:snapshot()
    assert(s2.attempts == 1 and s2.completed == 1 and s2.aborted == 0, "Completed run increments attempts & completed")

    -- Aborted run increments attempts and aborted
    p:run({
        captureMarker = function() return { cancelled = true } end,
        readSymbol = function(k) return syms[k] end,
    })
    local s3 = p:snapshot()
    assert(s3.attempts == 2 and s3.completed == 1 and s3.aborted == 1, "Aborted run increments attempts & aborted")
end)

run_test("27_reuse_after_abort_and_reset", function()
    local p = SymbolExposureProbe.new()
    local syms = make_default_symbols()

    -- First: abort
    local r1 = p:run({
        captureMarker = function() return { cancelled = true } end,
        readSymbol = function() return function() end end,
    })
    assert(r1.status == "aborted", "Run 1 aborted")

    -- Reset
    p:reset()

    -- Second: valid complete run
    local r2 = p:run({
        captureMarker = function() return make_valid_marker() end,
        readSymbol = function(k) return syms[k] end,
    })
    assert(r2.status == "completed", "Run 2 completed cleanly")
    assert(r2.counts.captures == 54 and r2.counts.symbols == 26, "Full run counts satisfied")
end)

run_test("28_invalid_api_handling", function()
    local p = SymbolExposureProbe.new()
    assert(p:run(nil).reason == "invalid_api")
    local cases = {
        "string",
        123,
        {},
        { captureMarker = function() end }, -- missing readSymbol
        { readSymbol = function() end },    -- missing captureMarker
    }
    for _, c in ipairs(cases) do
        local res = p:run(c)
        assert(res.status == "aborted", "Invalid API must abort")
        assert(res.reason == "invalid_api", "Reason must be invalid_api")
        assert(res.counts.captures == 0 and res.counts.symbols == 0, "Zero counts on invalid api")
    end
end)

run_test("29_guarded_environment_no_engine_access", function()
    -- Actual guarded environment load; unknown globals/registrations fail.
    local env = setmetatable({type=type,rawget=rawget,rawequal=rawequal,pcall=pcall,error=error,ipairs=ipairs}, {__index=function(_,k) error("unexpected global: "..k) end,__newindex=function(_,k) error("global write: "..k) end})
    local isolated = assert(load(SymbolProbeSource,"guarded","t",env))()
    local p = isolated.new()
    local syms = make_default_symbols()
    local res = p:run({
        captureMarker = function() return make_valid_marker() end,
        readSymbol = function(k) return syms[k] end,
    })
    assert(res.status == "completed", "Probe requires zero engine globals")
    assert(res.results[1].status == "reference_matched", "First row matched")
end)

-- =========================================================================
-- Summary Report
-- =========================================================================

local function api_for(symbols)
    return {captureMarker=function() return make_valid_marker() end,
        readSymbol=function(k) return symbols[k] end}
end
local function check_envelope(r)
    assert(r.evidenceScope=='supplied_reference_comparison')
    for _,k in ipairs({'observerLiveness','residency','nativeIdentity','worldGeneration','methodInvocation'}) do
        assert(r[k]=='unassessed')
    end
    assert(r.lighting=='unknown' and r.nativeAcceptance==false)
    check_scalars_only(r)
end
run_test('review01_every_outcome_envelope',function()
    local p=SymbolExposureProbe.new()
    check_envelope(p:run(nil))
    check_envelope(p:run(api_for(make_default_symbols())))
    local api=api_for(make_default_symbols())
    api.captureMarker=function()
        local inner=p:run(api_for({}))
        assert(inner.status=='reentrancy_rejected' and inner.counts.captures==0)
        check_envelope(inner)
        return {framework='f',revision='r',cancelled=true}
    end
    local r=p:run(api)
    assert(r.status=='aborted' and #r.results==0)
    check_envelope(r)
end)
for _,mode in ipairs({'cancel','throw','reset'}) do
    run_test('review_boundary_sweep_'..mode,function()
        for trigger=1,54 do
            local p=SymbolExposureProbe.new()
            local symbols=make_default_symbols()
            local captures,reads=0,0
            local r=p:run({captureMarker=function()
                captures=captures+1
                if captures==trigger then
                    if mode=='throw' then error({secret='never export'}) end
                    if mode=='reset' then p:reset() end
                    if mode=='cancel' then return {framework='f',revision='r',cancelled=true} end
                end
                return make_valid_marker()
            end,readSymbol=function(k) reads=reads+1; return symbols[k] end})
            assert(r.status=='aborted' and #r.results==0)
            assert(captures==trigger and r.counts.captures==trigger)
            assert(reads==math.floor((trigger-1)/2) and r.counts.symbols==reads)
            check_envelope(r)
            assert(p:run(api_for(symbols)).status=='completed')
        end
    end)
end
run_test('review05_reset_read_exact_counts',function()
    for trigger=1,26 do
        local p=SymbolExposureProbe.new()
        local symbols=make_default_symbols()
        local captures,reads=0,0
        local r=p:run({captureMarker=function() captures=captures+1; return make_valid_marker() end,
            readSymbol=function(k) reads=reads+1; if reads==trigger then p:reset() end; return symbols[k] end})
        assert(r.status=='aborted' and r.reason=='reset_during_probe')
        assert(reads==trigger and captures==trigger*2)
        assert(r.counts.symbols==reads and r.counts.captures==captures)
    end
end)
run_test('review06_raw_api_marker_no_meta',function()
    local mt={__index=function() error('index forbidden') end,__tostring=function() error('string forbidden') end}
    local p=SymbolExposureProbe.new()
    assert(p:run(setmetatable({},mt)).reason=='invalid_api')
    local api=api_for(make_default_symbols())
    api.captureMarker=function() return setmetatable(make_valid_marker(),mt) end
    assert(p:run(setmetatable(api,mt)).status=='completed')
    api.captureMarker=function() return setmetatable({revision='r',cancelled=false},mt) end
    assert(p:run(api).reason=='marker_invalid')
end)
run_test('review07_priority_cross_pairs',function()
    local values={false,{},function() end}
    for _,v in ipairs(values) do
        for _,swap in ipairs({false,true}) do
            local p=SymbolExposureProbe.new()
            local api=api_for(make_default_symbols())
            local n=0
            api.readSymbol=function(k)
                if k~='forward_x' then return nil end
                n=n+1
                if (n==1)==swap then return v end
                error(setmetatable({secret='raw'},{__tostring=function() error('must not stringify') end}))
            end
            local r=p:run(api)
            assert(r.status=='completed' and r.results[1].status=='query_error')
            check_envelope(r)
        end
    end
    local p=SymbolExposureProbe.new()
    local n=0
    local r=p:run({captureMarker=function() return make_valid_marker() end,readSymbol=function(k)
        if k=='forward_x' then n=n+1; if n==1 then return false end; return nil end
    end})
    assert(r.results[1].status=='missing' and r.results[1].valueType=='boolean')
end)
run_test('review08_opaque_userdata_not_native_proof',function()
    local symbols=make_default_symbols()
    symbols.forward_x=opaque1
    symbols.enum_clear=opaque1; symbols.enum_blocked=opaque2
    local r=SymbolExposureProbe.new():run(api_for(symbols))
    assert(r.results[1].status=='type_mismatch' and r.results[1].valueType=='userdata')
    assert(r.results[9].status=='reference_matched' and r.enumReferences=='distinct_references')
    check_envelope(r)
end)
run_test('review09_callbacks_and_handles_released_after_abort',function()
    local p=SymbolExposureProbe.new()
    local weak=setmetatable({},{__mode='v'})
    do
        local candidate={}
        local count=0
        local capture=function() count=count+1; if count==38 then error('abort') end; return make_valid_marker() end
        local read=function(k) if k=='enum_clear' then return candidate end; return nil end
        weak.capture=capture; weak.read=read; weak.candidate=candidate
        assert(p:run({captureMarker=capture,readSymbol=read}).status=='aborted')
    end
    collectgarbage('collect'); collectgarbage('collect')
    assert(weak.capture==nil and weak.read==nil and weak.candidate==nil)
end)
run_test('review10_private_state_output_isolation',function()
    local p=SymbolExposureProbe.new()
    p.attempts=999; p.busy=true; p.revision=-1
    local r=p:run(api_for(make_default_symbols()))
    assert(r.status=='completed')
    r.results[1].status='corrupted'; r.counts.symbols=999
    local s=p:snapshot(); s.attempts=999
    assert(p:snapshot().attempts==1)
    assert(p:run(api_for(make_default_symbols())).results[1].status=='reference_matched')
end)
run_test('review11_token_boundary_and_marker_reentry',function()
    local p=SymbolExposureProbe.new()
    local api=api_for(make_default_symbols())
    local n=0
    api.captureMarker=function()
        n=n+1
        local inner=p:run(api)
        assert(inner.status=='reentrancy_rejected')
        return {framework=string.rep('f',96),revision=string.rep('r',96),cancelled=false}
    end
    assert(p:run(api).status=='completed' and n==54)
    assert(p:snapshot().attempts==1)
end)
run_test('review12_fixed_alias_order_and_pairs',function()
    local expected={'forward_x','forward_y','cell_get_square','square_get_moving_objects','list_size','list_get','los_line_clear','get_cell','enum_clear','enum_open_door','enum_window','enum_blocked','enum_closed_door'}
    local api=api_for(make_default_symbols())
    local n=0
    api.plan={'arbitrary'}
    api.readSymbol=function(k) n=n+1; assert(k==expected[math.ceil(n/2)]); return nil end
    local r=SymbolExposureProbe.new():run(api)
    assert(r.status=='completed' and n==26 and #r.results==13)
    for i,row in ipairs(r.results) do assert(row.key==expected[i] and row.status=='missing') end
end)

print(string.format("RESULT %d symbol checks passed", test_count))
return true

""")
