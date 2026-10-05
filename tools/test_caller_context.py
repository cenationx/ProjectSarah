"""Actual Lua caller epoch/accounting policies and inert-probe composition."""
from pathlib import Path
import sys
root = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(root / "tools/dependencies/python"))
from lupa import LuaRuntime
lua = LuaRuntime(unpack_returned_tuples=True)
for name in ("CallerEpoch", "CaptureAccounting", "NativeExposureProbe"):
    source = (root / f"tools/{name}.lua").read_text(encoding="utf-8")
    if name == "CallerEpoch": lua.globals().epochSource = source
    if name == "CaptureAccounting": lua.globals().accountingSource = source
    lua.globals()[name] = lua.execute(source)
lua.globals().opaqueToken = object()
lua.execute(r"""
-- tests/CallerEpochAndCaptureAccounting_spec.lua
-- Test fixtures for CallerEpoch, CaptureAccounting, and composition with NativeExposureProbe.
-- Pure Lua 5.1 test suite.

local CallerEpoch = CallerEpoch or require("tools.CallerEpoch")
local CaptureAccounting = CaptureAccounting or require("tools.CaptureAccounting")
local NativeExposureProbe = NativeExposureProbe or require("tools.NativeExposureProbe")

local tests = {}
local passed_count = 0
local failed_count = 0

local function run_test(name, fn)
    local ok, err = pcall(fn)
    if ok then
        passed_count = passed_count + 1
        print("PASS " .. name)
    else
        failed_count = failed_count + 1
        error("FAIL [" .. name .. "]: " .. tostring(err))
    end
end

local function make_valid_state(suffix)
    local s = suffix or "1"
    return {
        framework = "fw_tok_" .. s,
        controller = "ctrl_tok_" .. s,
        npc = "npc_tok_" .. s,
        cell = "cell_tok_" .. s,
        worldRevision = "wrev_tok_" .. s,
    }
end

-- =========================================================================
-- CallerEpoch Test Suite
-- =========================================================================

tests["epoch_01_valid_namespaces"] = function()
    local ok1 = pcall(CallerEpoch.new, "valid_ns")
    local ok2 = pcall(CallerEpoch.new, "valid-ns-123")
    local ok3 = pcall(CallerEpoch.new, "A")
    local ok4 = pcall(CallerEpoch.new, string.rep("x", 32))
    assert(ok1 and ok2 and ok3 and ok4, "Valid namespaces should be accepted")
end

tests["epoch_02_invalid_namespaces"] = function()
    assert(not pcall(CallerEpoch.new, nil), "Explicit nil namespace must fail")
    local cases = {
        123, true, {}, "", string.rep("x", 33),
        "has space", "has.dot", "has!excl", "has$dollar"
    }
    for _, c in ipairs(cases) do
        local ok = pcall(CallerEpoch.new, c)
        assert(not ok, "Invalid namespace should throw: " .. tostring(c))
    end
end

tests["epoch_03_first_observe_ready"] = function()
    local ep = CallerEpoch.new("session_a")
    local st = make_valid_state("1")
    local r = ep:observe(st)
    assert(r.status == "ready", "First observe should be ready")
    assert(r.changed == true, "First observe changed true")
    assert(r.epoch == 1, "Epoch starts at 1")
    assert(r.generation == "session_a:1", "Generation formatted correctly")
    local s = ep:snapshot()
    assert(s.epoch == 1 and s.active == true and s.exhausted == false, "Snapshot reflects active state")
end

tests["epoch_04_identical_observe"] = function()
    local ep = CallerEpoch.new("session_a")
    local st = make_valid_state("1")
    ep:observe(st)
    local r2 = ep:observe(make_valid_state("1"))
    assert(r2.status == "ready", "Status remains ready")
    assert(r2.changed == false, "Changed false on identical state")
    assert(r2.epoch == 1, "Epoch remains unchanged")
    assert(r2.generation == "session_a:1", "Generation remains identical")
end

tests["epoch_05_framework_token_change"] = function()
    local ep = CallerEpoch.new("session_a")
    local st = make_valid_state("1")
    ep:observe(st)
    local st2 = make_valid_state("1")
    st2.framework = "fw_new_reload_token"
    local r = ep:observe(st2)
    assert(r.status == "ready", "Status ready on framework change")
    assert(r.changed == true, "Changed true on framework change")
    assert(r.epoch == 2, "Epoch incremented to 2")
    assert(r.generation == "session_a:2", "Generation updated to session_a:2")
end

tests["epoch_06_controller_token_change"] = function()
    local ep = CallerEpoch.new("session_a")
    ep:observe(make_valid_state("1"))
    local st = make_valid_state("1")
    st.controller = "ctrl_reassigned"
    local r = ep:observe(st)
    assert(r.changed == true and r.epoch == 2, "Controller change increments epoch")
end

tests["epoch_07_npc_token_change"] = function()
    local ep = CallerEpoch.new("session_a")
    ep:observe(make_valid_state("1"))
    local st = make_valid_state("1")
    st.npc = "npc_respawned"
    local r = ep:observe(st)
    assert(r.changed == true and r.epoch == 2, "NPC change increments epoch")
end

tests["epoch_08_cell_token_change"] = function()
    local ep = CallerEpoch.new("session_a")
    ep:observe(make_valid_state("1"))
    local st = make_valid_state("1")
    st.cell = "cell_reloaded"
    local r = ep:observe(st)
    assert(r.changed == true and r.epoch == 2, "Cell change increments epoch")
end

tests["epoch_09_world_revision_change"] = function()
    local ep = CallerEpoch.new("session_a")
    ep:observe(make_valid_state("1"))
    local st = make_valid_state("1")
    st.worldRevision = "wrev_bumped"
    local r = ep:observe(st)
    assert(r.changed == true and r.epoch == 2, "WorldRevision change increments epoch")
end

tests["epoch_10_invalid_observe_active_clears"] = function()
    local ep = CallerEpoch.new("session_a")
    ep:observe(make_valid_state("1"))
    local r = ep:observe({ framework = "f" }) -- missing required fields
    assert(r.status == "invalid", "Status invalid on malformed state")
    assert(r.changed == true, "Changed true on transition to invalid")
    assert(r.epoch == 2, "Epoch incremented on invalid while active")
    assert(r.generation == nil, "Generation nil on invalid")
    local s = ep:snapshot()
    assert(s.active == false, "Active cleared on invalid")
end

tests["epoch_11_repeated_invalid_no_increment"] = function()
    local ep = CallerEpoch.new("session_a")
    ep:observe(make_valid_state("1"))
    ep:observe(nil) -- epoch becomes 2, active false
    local r2 = ep:observe(nil)
    assert(r2.status == "invalid", "Status invalid")
    assert(r2.changed == false, "Repeated invalid does not change state")
    assert(r2.epoch == 2, "Repeated invalid does not increment epoch")
    assert(r2.generation == nil, "Generation nil")
end

tests["epoch_12_valid_observe_after_invalid_binds_current"] = function()
    local ep = CallerEpoch.new("session_a")
    ep:observe(make_valid_state("1")) -- epoch 1
    ep:observe(nil) -- epoch 2, unbound
    local r = ep:observe(make_valid_state("recovered"))
    assert(r.status == "ready", "Status ready after recovery")
    assert(r.changed == true, "Changed true on new binding")
    assert(r.epoch == 2, "Binds CURRENT epoch 2 without extra increment")
    assert(r.generation == "session_a:2", "Generation matches current epoch")
end

tests["epoch_13_reset_unbound_increments"] = function()
    local ep = CallerEpoch.new("session_a")
    local r = ep:reset() -- starts unbound at epoch 1
    assert(r.status == "reset", "Status reset")
    assert(r.changed == true, "Changed true on reset")
    assert(r.epoch == 2, "Reset increments epoch even unbound")
    assert(r.generation == nil, "Generation nil on reset")
    local s = ep:snapshot()
    assert(s.active == false, "Active false after reset")
end

tests["epoch_14_reset_active_clears_and_increments"] = function()
    local ep = CallerEpoch.new("session_a")
    ep:observe(make_valid_state("1"))
    local r = ep:reset()
    assert(r.status == "reset" and r.changed == true and r.epoch == 2, "Reset active increments epoch")
    local s = ep:snapshot()
    assert(s.active == false, "Active false after reset")
end

tests["epoch_15_valid_observe_after_reset_binds_current"] = function()
    local ep = CallerEpoch.new("session_a")
    ep:observe(make_valid_state("1")) -- epoch 1
    ep:reset() -- epoch 2
    local r = ep:observe(make_valid_state("after_reset"))
    assert(r.status == "ready", "Status ready after reset")
    assert(r.changed == true, "Changed true")
    assert(r.epoch == 2, "Binds current epoch 2")
    assert(r.generation == "session_a:2", "Generation session_a:2")
end

tests["epoch_16_snapshot_scalar_copies"] = function()
    local ep = CallerEpoch.new("session_a")
    local s = ep:snapshot()
    s.epoch = 999
    s.active = true
    s.exhausted = true
    local s2 = ep:snapshot()
    assert(s2.epoch == 1 and s2.active == false and s2.exhausted == false, "Snapshot returned table mutations do not affect internal state")
end

tests["epoch_17_metamethods_ignored"] = function()
    local ep = CallerEpoch.new("session_a")
    local evil_state = {}
    local mt = {
        __index = function(_, k) error("Metamethod __index should not be invoked") end,
        __tostring = function(_) error("Metamethod __tostring should not be invoked") end,
    }
    setmetatable(evil_state, mt)
    rawset(evil_state, "framework", "f")
    rawset(evil_state, "controller", "c")
    rawset(evil_state, "npc", "n")
    rawset(evil_state, "cell", "cl")
    rawset(evil_state, "worldRevision", "w")
    local r = ep:observe(evil_state)
    assert(r.status == "ready", "rawget access succeeds ignoring metamethods")
end

tests["epoch_18_token_length_and_type_boundaries"] = function()
    local ep = CallerEpoch.new("session_a")
    local bad_states = {
        { framework = "", controller = "c", npc = "n", cell = "cl", worldRevision = "w" },
        { framework = string.rep("x", 97), controller = "c", npc = "n", cell = "cl", worldRevision = "w" },
        { framework = 123, controller = "c", npc = "n", cell = "cl", worldRevision = "w" },
        { framework = {}, controller = "c", npc = "n", cell = "cl", worldRevision = "w" },
    }
    for _, bs in ipairs(bad_states) do
        local r = ep:observe(bs)
        assert(r.status == "invalid", "Boundary violation token rejected")
    end
end

tests["epoch_19_overflow_permanent_exhaustion_debug"] = function()
    local ep = CallerEpoch.new("session_ovf")
    ep:observe(make_valid_state("1"))

    -- Reflection via debug library to set epoch to MAX_EPOCH (2147483647)
    local up_found = false
    local i = 1
    while true do
        local n, v = debug.getupvalue(ep.observe, i)
        if not n then break end
        if n == "epoch" then
            debug.setupvalue(ep.observe, i, 2147483647)
            up_found = true
            break
        end
        i = i + 1
    end
    assert(up_found, "debug reflection must find 'epoch' upvalue")

    -- Token change triggers epoch increment which exceeds MAX_EPOCH
    local r = ep:observe(make_valid_state("overflow"))
    assert(r.status == "exhausted", "Overflow transitions to exhausted")
    assert(r.changed == true, "Changed true on exhausted transition")
    assert(r.epoch == 2147483647, "Epoch clamped to MAX_EPOCH")
    assert(r.generation == nil, "Generation nil on exhausted")

    -- Subsequent observe remains permanently exhausted
    local r2 = ep:observe(make_valid_state("overflow2"))
    assert(r2.status == "exhausted", "Remains exhausted on observe")
    assert(r2.changed == false, "Changed false for exhausted calls")

    -- Reset cannot revive exhausted
    local r3 = ep:reset()
    assert(r3.status == "exhausted", "Remains exhausted on reset")
    assert(r3.changed == false, "Changed false on reset exhausted")
end

tests["epoch_20_generation_length_bound"] = function()
    local max_ns = string.rep("x", 32)
    local ep = CallerEpoch.new(max_ns)
    local r = ep:observe(make_valid_state("1"))
    assert(#r.generation <= 43, "Generation length must be <= 43 chars")
end

tests["epoch_21_same_caller_namespace_collision_note"] = function()
    -- Caller responsibility demonstration: two instances with same namespace
    local ep1 = CallerEpoch.new("shared_ns")
    local ep2 = CallerEpoch.new("shared_ns")
    local r1 = ep1:observe(make_valid_state("1"))
    local r2 = ep2:observe(make_valid_state("1"))
    assert(r1.generation == r2.generation, "Same namespace produces identical generations; caller must ensure instance uniqueness")
end

-- =========================================================================
-- CaptureAccounting Test Suite
-- =========================================================================

tests["accounting_01_default_construction"] = function()
    local ac = CaptureAccounting.new()
    local s = ac:snapshot()
    assert(s.captureLimit == 54, "Default captureLimit 54")
    assert(s.operationLimit == 1024, "Default operationLimit 1024")
    assert(s.captures == 0, "Captures 0")
    assert(s.operations == 0, "Operations 0")
    assert(s.remainingCaptures == 54, "Remaining captures 54")
    assert(s.remainingOperations == 1024, "Remaining operations 1024")
    assert(s.valid == true, "Valid true")
    assert(s.reason == nil, "Reason nil")
end

tests["accounting_02_custom_config_within_hard_limits"] = function()
    local ac = CaptureAccounting.new({ captureLimit = 512, operationLimit = 16384 })
    local s = ac:snapshot()
    assert(s.captureLimit == 512, "Max hard captureLimit accepted")
    assert(s.operationLimit == 16384, "Max hard operationLimit accepted")
end

tests["accounting_03_invalid_config_rejection"] = function()
    local bad_configs = {
        "not_table", 123, true,
        { captureLimit = 0 }, { captureLimit = -1 }, { captureLimit = 513 },
        { captureLimit = 1.5 }, { captureLimit = 0/0 }, { captureLimit = 1/0 },
        { operationLimit = 0 }, { operationLimit = -1 }, { operationLimit = 16385 },
        { operationLimit = 10.5 }, { operationLimit = 0/0 }, { operationLimit = 1/0 },
    }
    for _, cfg in ipairs(bad_configs) do
        local ok = pcall(CaptureAccounting.new, cfg)
        assert(not ok, "Invalid config should throw: " .. tostring(cfg))
    end
end

tests["accounting_04_begin_capture_grants_up_to_limit"] = function()
    local ac = CaptureAccounting.new({ captureLimit = 3 })
    assert(ac:beginCapture() == true, "Grant 1")
    assert(ac:beginCapture() == true, "Grant 2")
    assert(ac:beginCapture() == true, "Grant 3")
    local s = ac:snapshot()
    assert(s.captures == 3 and s.remainingCaptures == 0 and s.valid == true, "3 captures granted cleanly")
end

tests["accounting_05_begin_capture_limit_refusal_sticky"] = function()
    local ac = CaptureAccounting.new({ captureLimit = 2 })
    ac:beginCapture()
    ac:beginCapture()
    local ok = ac:beginCapture()
    assert(ok == false, "3rd capture refused")
    local s = ac:snapshot()
    assert(s.captures == 2, "Captures counter not incremented on refusal")
    assert(s.valid == false, "Ledger sticky invalid")
    assert(s.reason == "capture_budget", "Reason is capture_budget")
end

tests["accounting_06_charge_valid_groups"] = function()
    local ac = CaptureAccounting.new()
    assert(ac:charge("world") == true, "Charge world")
    assert(ac:charge("membership") == true, "Charge membership")
    assert(ac:charge("state") == true, "Charge state")
    assert(ac:charge("symbol") == true, "Charge symbol")
    local s = ac:snapshot()
    assert(s.operations == 4, "Operations 4")
    assert(s.world == 1 and s.membership == 1 and s.state == 1 and s.symbol == 1, "Group counts incremented")
end

tests["accounting_07_charge_invalid_kind_sticky"] = function()
    local ac = CaptureAccounting.new()
    local ok = ac:charge("bad_kind")
    assert(ok == false, "Charge invalid kind returns false")
    local s = ac:snapshot()
    assert(s.operations == 0, "Zero operations charged on bad kind")
    assert(s.valid == false, "Sticky invalid on bad kind")
    assert(s.reason == "invalid_kind", "Reason invalid_kind")
end

tests["accounting_08_charge_operation_limit_refusal_sticky"] = function()
    local ac = CaptureAccounting.new({ operationLimit = 2 })
    assert(ac:charge("world") == true, "Charge 1")
    assert(ac:charge("world") == true, "Charge 2")
    assert(ac:charge("world") == false, "Charge 3 refused")
    local s = ac:snapshot()
    assert(s.operations == 2, "Operations capped at limit")
    assert(s.valid == false, "Sticky invalid")
    assert(s.reason == "operation_budget", "Reason operation_budget")
end

tests["accounting_09_invalidate_cancelled_sticky"] = function()
    local ac = CaptureAccounting.new()
    ac:charge("state")
    assert(ac:invalidate() == false, "Invalidate returns false")
    local s = ac:snapshot()
    assert(s.valid == false, "Valid false")
    assert(s.reason == "cancelled", "Reason cancelled")
end

tests["accounting_10_preserve_first_reason"] = function()
    local ac = CaptureAccounting.new({ operationLimit = 1 })
    ac:charge("state")
    ac:charge("state") -- triggers operation_budget
    ac:invalidate()    -- should not overwrite with cancelled
    ac:charge("bad")   -- should not overwrite with invalid_kind
    local s = ac:snapshot()
    assert(s.reason == "operation_budget", "Preserve first invalidation reason")
end

tests["accounting_11_no_further_grants_after_invalid"] = function()
    local ac = CaptureAccounting.new()
    ac:invalidate()
    assert(ac:beginCapture() == false, "No capture grant after invalid")
    assert(ac:charge("state") == false, "No charge grant after invalid")
    local s = ac:snapshot()
    assert(s.captures == 0 and s.operations == 0, "Counters do not advance when invalid")
end

tests["accounting_12_snapshot_scalar_immutability"] = function()
    local ac = CaptureAccounting.new()
    local s = ac:snapshot()
    s.captures = 100
    s.operations = 500
    s.valid = false
    local s2 = ac:snapshot()
    assert(s2.captures == 0 and s2.operations == 0 and s2.valid == true, "Snapshot copies are independent")
end

tests["accounting_13_pass_isolation_no_refill"] = function()
    local ac = CaptureAccounting.new()
    assert(rawget(ac, "reset") == nil, "Ledger has no reset method")
    assert(rawget(ac, "refill") == nil, "Ledger has no refill method")
end

-- =========================================================================
-- Composition Suite: NativeExposureProbe + CallerEpoch + CaptureAccounting
-- =========================================================================

tests["composition_01_probe_exact_566_operations_completes"] = function()
    local ep = CallerEpoch.new("probe_session")
    local valid_st = make_valid_state("comp1")

    -- 54 captures * 10 operations (1 state + 3 world + 6 membership) = 540 operations
    -- 26 symbol reads * 1 operation (1 symbol) = 26 operations
    -- Total operations = 540 + 26 = 566 operations
    local ac = CaptureAccounting.new({ captureLimit = 54, operationLimit = 566 })

    local stable_symbols = {
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

    local api = {
        capture = function()
            if not ac:beginCapture() then return nil end
            -- Charge 10 explicit operations declared by Engine.isResident model:
            if not ac:charge("state") then return nil end
            if not ac:charge("world") then return nil end
            if not ac:charge("world") then return nil end
            if not ac:charge("world") then return nil end
            if not ac:charge("membership") then return nil end
            if not ac:charge("membership") then return nil end
            if not ac:charge("membership") then return nil end
            if not ac:charge("membership") then return nil end
            if not ac:charge("membership") then return nil end
            if not ac:charge("membership") then return nil end

            local obs = ep:observe(valid_st)
            if obs.status ~= "ready" then return nil end

            return {
                controller = valid_st.controller,
                npc = valid_st.npc,
                cell = valid_st.cell,
                generation = obs.generation,
                alive = true,
                resident = true,
                cancelled = false,
                x = 100.0,
                y = 200.0,
                z = 0.0,
                fx = 1.0,
                fy = 0.0,
            }
        end,
        readSymbol = function(key)
            if not ac:charge("symbol") then return nil end
            return stable_symbols[key]
        end,
    }

    local probe = NativeExposureProbe.new()
    local res = probe:run(api)

    assert(res.status == "completed", "Probe completed with exact 566 budget")
    assert(res.counts.captures == 54, "Probe executed 54 captures")
    assert(res.counts.symbols == 26, "Probe executed 26 symbol reads")
    assert(#res.results == 13, "13 allowlist items evaluated")

    local s = ac:snapshot()
    assert(s.captures == 54, "Ledger records 54 captures")
    assert(s.operations == 566, "Ledger records exactly 566 operations")
    assert(s.remainingCaptures == 0, "0 remaining captures")
    assert(s.remainingOperations == 0, "0 remaining operations")
    assert(s.valid == true, "Ledger remains valid")
    assert(s.state == 54, "54 state operations")
    assert(s.world == 162, "162 world operations (54 * 3)")
    assert(s.membership == 324, "324 membership operations (54 * 6)")
    assert(s.symbol == 26, "26 symbol operations")
end

tests["composition_02_probe_565_operations_budget_exhaustion"] = function()
    local ep = CallerEpoch.new("probe_session")
    local valid_st = make_valid_state("comp2")

    -- Operation limit is 565: 1 operation short of the required 566
    local ac = CaptureAccounting.new({ captureLimit = 54, operationLimit = 565 })

    local stable_symbols = {
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

    local api = {
        capture = function()
            if not ac:beginCapture() then return nil end
            if not ac:charge("state") then return nil end
            if not ac:charge("world") then return nil end
            if not ac:charge("world") then return nil end
            if not ac:charge("world") then return nil end
            if not ac:charge("membership") then return nil end
            if not ac:charge("membership") then return nil end
            if not ac:charge("membership") then return nil end
            if not ac:charge("membership") then return nil end
            if not ac:charge("membership") then return nil end
            if not ac:charge("membership") then return nil end

            local obs = ep:observe(valid_st)
            if obs.status ~= "ready" then return nil end

            return {
                controller = valid_st.controller,
                npc = valid_st.npc,
                cell = valid_st.cell,
                generation = obs.generation,
                alive = true,
                resident = true,
                cancelled = false,
                x = 100.0,
                y = 200.0,
                z = 0.0,
                fx = 1.0,
                fy = 0.0,
            }
        end,
        readSymbol = function(key)
            if not ac:charge("symbol") then return nil end
            return stable_symbols[key]
        end,
    }

    local probe = NativeExposureProbe.new()
    local res = probe:run(api)

    assert(res.status == "aborted", "Probe aborts on budget exhaustion")
    assert(#res.results == 0, "Aborted probe returns empty results")

    local s = ac:snapshot()
    assert(s.valid == false, "Ledger is sticky invalid")
    assert(s.reason == "operation_budget", "Ledger invalidation reason is operation_budget")
    assert(s.operations == 565, "Ledger stopped at exactly 565 operations")
    assert(ac:beginCapture() == false, "Sticky invalid ledger denies subsequent beginCapture")
    assert(ac:charge("state") == false, "Sticky invalid ledger denies subsequent charge")
end

tests["composition_03_probe_midpass_epoch_reset_lifecycle_drift"] = function()
    local ep = CallerEpoch.new("probe_session")
    local current_st = make_valid_state("comp3")
    local ac = CaptureAccounting.new({ captureLimit = 54, operationLimit = 1024 })

    local cap_calls = 0
    local api = {
        capture = function()
            if not ac:beginCapture() then return nil end
            ac:charge("state")
            ac:charge("world")
            cap_calls = cap_calls + 1
            if cap_calls == 20 then
                -- Reset epoch mid-pass!
                ep:reset()
                current_st = make_valid_state("comp3_after_reset")
            end
            local obs = ep:observe(current_st)
            return {
                controller = current_st.controller,
                npc = current_st.npc,
                cell = current_st.cell,
                generation = obs.generation,
                alive = true,
                resident = true,
                cancelled = false,
                x = 10.0,
                y = 10.0,
                z = 0.0,
                fx = 1.0,
                fy = 0.0,
            }
        end,
        readSymbol = function() ac:charge("symbol"); return function() end end,
    }

    local probe = NativeExposureProbe.new()
    local res = probe:run(api)
    assert(res.status == "aborted", "Probe aborts on mid-pass epoch drift")
    assert(res.reason == "lifecycle_drift", "Abort reason is lifecycle_drift due to generation mismatch")
end

tests["composition_04_probe_midpass_probe_reset_abort"] = function()
    local ep = CallerEpoch.new("probe_session")
    local st = make_valid_state("comp4")
    local ac = CaptureAccounting.new({ captureLimit = 54, operationLimit = 1024 })

    local probe = NativeExposureProbe.new()
    local cap_calls = 0
    local api = {
        capture = function()
            if not ac:beginCapture() then return nil end
            ac:charge("state")
            cap_calls = cap_calls + 1
            if cap_calls == 10 then
                probe:reset() -- Reset probe mid-pass
            end
            local obs = ep:observe(st)
            return {
                controller = st.controller,
                npc = st.npc,
                cell = st.cell,
                generation = obs.generation,
                alive = true,
                resident = true,
                cancelled = false,
                x = 10.0,
                y = 10.0,
                z = 0.0,
                fx = 1.0,
                fy = 0.0,
            }
        end,
        readSymbol = function() ac:charge("symbol"); return function() end end,
    }

    local res = probe:run(api)
    assert(res.status == "aborted", "Probe aborts on probe:reset()")
    assert(res.reason == "reset_during_probe", "Abort reason is reset_during_probe")
end

tests["composition_05_probe_capture_limit_exhaustion"] = function()
    local ep = CallerEpoch.new("probe_session")
    local st = make_valid_state("comp5")
    -- Limit set to 53: probe needs 54
    local ac = CaptureAccounting.new({ captureLimit = 53, operationLimit = 1024 })

    local api = {
        capture = function()
            if not ac:beginCapture() then return nil end
            ac:charge("state")
            local obs = ep:observe(st)
            return {
                controller = st.controller,
                npc = st.npc,
                cell = st.cell,
                generation = obs.generation,
                alive = true,
                resident = true,
                cancelled = false,
                x = 10.0,
                y = 10.0,
                z = 0.0,
                fx = 1.0,
                fy = 0.0,
            }
        end,
        readSymbol = function() ac:charge("symbol"); return function() end end,
    }

    local probe = NativeExposureProbe.new()
    local res = probe:run(api)
    assert(res.status == "aborted", "Probe aborts when ledger captures budget runs out")
    local s = ac:snapshot()
    assert(s.reason == "capture_budget", "Ledger invalidation reason is capture_budget")
end

-- =========================================================================
-- Runner Loop
-- =========================================================================


local function force_epoch(ep,n)
 assert(debug and debug.getupvalue and debug.setupvalue)
 for i=1,100 do
  local name=debug.getupvalue(ep.observe,i)
  if name=="epoch" then debug.setupvalue(ep.observe,i,n);return end
  if name==nil then break end
 end
 error("Mandatory epoch reflection failed")
end

tests["review_01_reset_at_max_exhausts"] = function()
 local ep=CallerEpoch.new("max_reset");force_epoch(ep,2147483647)
 local r=ep:reset();assert(r.status=="exhausted" and r.changed and r.generation==nil)
 assert(not ep:snapshot().active and ep:snapshot().exhausted)
 assert(ep:observe(make_valid_state()).status=="exhausted" and not ep:reset().changed)
end

tests["review_02_invalid_at_max_exhausts"] = function()
 local ep=CallerEpoch.new("max_invalid");ep:observe(make_valid_state());force_epoch(ep,2147483647)
 local r=ep:observe(nil);assert(r.status=="exhausted" and r.changed and r.generation==nil)
 assert(ep:snapshot().exhausted and not ep:snapshot().active)
 assert(ep:observe(make_valid_state()).status=="exhausted")
end

tests["review_03_max_ticket_length_transition"] = function()
 local ep=CallerEpoch.new(string.rep("a",32));force_epoch(ep,2147483646)
 local st=make_valid_state();assert(ep:observe(st).epoch==2147483646)
 st.framework="reload";local r=ep:observe(st);assert(r.epoch==2147483647 and #r.generation==43)
 assert(not ep:observe(st).changed);st.cell="new";assert(ep:observe(st).status=="exhausted")
end

tests["review_04_each_token_type_length_missing"] = function()
 assert(type(opaqueToken)=="userdata")
 for _,key in ipairs({"framework","controller","npc","cell","worldRevision"}) do
  local ep=CallerEpoch.new("roles")
  for _,bad in ipairs({{},opaqueToken,false,123,"",string.rep("x",97)}) do
   local st=make_valid_state();st[key]=bad;assert(ep:observe(st).status=="invalid")
  end
  local st=make_valid_state();st[key]=nil;assert(ep:observe(st).status=="invalid")
  st[key]=string.rep("x",96);assert(ep:observe(st).status=="ready")
 end
end

tests["review_05_private_fields_copies"] = function()
 local ep=CallerEpoch.new("private");ep.epoch=999;ep.active=true;ep.exhausted=true
 local r=ep:observe(make_valid_state());r.epoch=100;r.generation="forged"
 assert(ep:observe(make_valid_state()).generation=="private:1")
 for k,v in pairs(ep:snapshot()) do
  assert(k=="epoch" or k=="active" or k=="exhausted")
  assert(type(v)=="number" or type(v)=="boolean")
 end
end

tests["review_06_unbound_invalid_at_max_no_burn"] = function()
 local ep=CallerEpoch.new("unbound");force_epoch(ep,2147483647)
 assert(ep:observe(nil).status=="invalid")
 assert(not ep:observe(nil).changed and not ep:snapshot().exhausted)
 assert(ep:observe(make_valid_state()).status=="ready" and ep:reset().status=="exhausted")
end

tests["review_07_guarded_no_globals_engine_registration"] = function()
 local allowed={type=type,rawget=rawget,error=error,math=math}
 local env=setmetatable({}, {__index=function(_,k) assert(allowed[k],"Unexpected global "..k);return allowed[k] end,
 __newindex=function() error("Global write") end})
 local em=assert(load(epochSource,"guarded_epoch","t",env))()
 local am=assert(load(accountingSource,"guarded_accounting","t",env))()
 assert(em.new("guarded"):observe(make_valid_state()).status=="ready")
 local ac=am.new();assert(ac:beginCapture() and ac:charge("state"))
end

tests["review_08_config_raw_and_copied"] = function()
 local hits=0;local cfg=setmetatable({}, {__index=function() hits=hits+1;error("lookup") end})
 local ac=CaptureAccounting.new(cfg);cfg.captureLimit=1;cfg.operationLimit=1
 assert(ac:snapshot().captureLimit==54 and ac:snapshot().operationLimit==1024 and hits==0)
 for _,bad in ipairs({-1/0,false,"54",{}}) do
  assert(not pcall(CaptureAccounting.new,{captureLimit=bad}))
  assert(not pcall(CaptureAccounting.new,{operationLimit=bad}))
 end
end

tests["review_09_inclusive_hard_limits_then_refusal"] = function()
 local ac=CaptureAccounting.new({captureLimit=512,operationLimit=16384})
 for i=1,512 do assert(ac:beginCapture()) end
 for i=1,16384 do assert(ac:charge("membership")) end
 assert(ac:snapshot().valid and not ac:charge("membership"))
 assert(ac:snapshot().operations==16384 and ac:snapshot().reason=="operation_budget")
 assert(not ac:beginCapture() and not ac:charge("state") and ac:snapshot().captures==512)
end

tests["review_10_failed_callback_consumes_charge"] = function()
 local ac=CaptureAccounting.new({operationLimit=2});local calls=0
 local function attempted()
  if not ac:charge("state") then return false end
  calls=calls+1;return pcall(function() error("fixture query error") end)
 end
 assert(attempted()==false and attempted()==false and calls==2)
 assert(ac:snapshot().operations==2 and attempted()==false and calls==2)
 assert(ac:snapshot().reason=="operation_budget")
end

tests["review_11_probe_denial_stops_original_calls"] = function()
 local ac=CaptureAccounting.new({operationLimit=5});local calls=0
 local r=NativeExposureProbe.new():run({capture=function()
  if not ac:beginCapture() then return nil end
  for i=1,10 do
   if not ac:charge("state") then return nil end
   calls=calls+1
  end
  error("Should refuse")
 end,readSymbol=function() error("Unreachable") end})
 assert(r.status=="aborted" and #r.results==0 and r.counts.symbols==0)
 assert(calls==5 and ac:snapshot().operations==5 and not ac:snapshot().valid)
 assert(not ac:beginCapture() and not ac:charge("state") and calls==5)
end

tests["review_12_old_closed_next_pass_fresh"] = function()
 local old=CaptureAccounting.new();assert(old:charge("world"));old:invalidate()
 local fresh=CaptureAccounting.new();old.valid=true;old.operations=0
 assert(not old:charge("world") and not old:beginCapture())
 assert(fresh:beginCapture() and fresh:charge("world"))
 assert(old:snapshot().reason=="cancelled" and fresh:snapshot().valid)
end


tests["review_13_input_token_table_is_copied"] = function()
 local ep=CallerEpoch.new("copy_input");local st=make_valid_state("1")
 ep:observe(st);st.framework="mutated_after_observe"
 local r=ep:observe(make_valid_state("1"))
 assert(not r.changed and r.epoch==1)
 assert(ep:observe(st).epoch==2)
end

tests["review_14_missing_raw_field_does_not_use_metatable"] = function()
 local ep=CallerEpoch.new("raw_missing");local st=make_valid_state();st.npc=nil
 local calls=0;setmetatable(st,{__index=function() calls=calls+1;return "npc" end})
 assert(ep:observe(st).status=="invalid" and calls==0)
end

local ordered_names = {}
for name in pairs(tests) do
    ordered_names[#ordered_names + 1] = name
end
table.sort(ordered_names)

for _, name in ipairs(ordered_names) do
    run_test(name, tests[name])
end

print(string.format("RESULT %d caller checks passed", passed_count))
return true

""")
