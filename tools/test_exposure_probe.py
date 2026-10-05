"""Actual-Lua exposure-policy fixtures. No native invocation or acceptance."""
from pathlib import Path
import sys
root = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(root / "tools/dependencies/python"))
from lupa import LuaRuntime
lua = LuaRuntime(unpack_returned_tuples=True)
source = (root / "tools/NativeExposureProbe.lua").read_text(encoding="utf-8")
lua.globals().probeSource = source
lua.globals().opaque1 = object()
lua.globals().opaque2 = object()
lua.globals().NativeExposureProbe = lua.execute(source)
lua.execute(r"""
local tests_passed = 0
local function test(name, fn)
    local ok, err = pcall(fn)
    if not ok then
        error("\n[FAIL] " .. name .. "\n" .. tostring(err))
    end
    print("PASS " .. name)
    tests_passed = tests_passed + 1
end

local function mk_cap(o)
    local b = {
        controller = "ctrl_probe",
        npc = "sarah_probe",
        cell = "cell_test",
        generation = "gen_probe_0",
        alive = true,
        resident = true,
        cancelled = false,
        x = 100.0,
        y = 200.0,
        z = 0.0,
        fx = 1.0,
        fy = 0.0,
    }
    if o then for k, v in pairs(o) do b[k] = v end end
    return b
end

local function mk_default_symbols()
    local fn = function() end
    local t_clear = { name = "Clear" }
    local t_open = { name = "OpenDoor" }
    local t_win = { name = "Window" }
    local t_blk = { name = "Blocked" }
    local t_cls = { name = "ClosedDoor" }
    return {
        forward_x = fn,
        forward_y = fn,
        cell_get_square = fn,
        square_get_moving_objects = fn,
        list_size = fn,
        list_get = fn,
        los_line_clear = fn,
        get_cell = fn,
        enum_clear = t_clear,
        enum_open_door = t_open,
        enum_window = t_win,
        enum_blocked = t_blk,
        enum_closed_door = t_cls,
    }
end

-- =========================================================================
-- CONSTRUCTOR, SNAPSHOT, & CONTRACT INTEGRITY
-- =========================================================================

test("NativeExposureProbe - new() has a clean snapshot", function()
    local p = NativeExposureProbe.new()
    local snap = p:snapshot()
    assert(snap.attempts == 0 and snap.completed == 0 and snap.aborted == 0)
end)

test("NativeExposureProbe - Invalid API configs rejected without throwing", function()
    local p = NativeExposureProbe.new()
    local r_nil = p:run(nil)
    assert(r_nil.status == "aborted" and r_nil.reason == "invalid_api" and #r_nil.results == 0)
    local bad = { 1234, "api", {}, { capture = function() end }, { readSymbol = function() end } }
    for _, ba in ipairs(bad) do
        local r = p:run(ba)
        assert(r.status == "aborted" and r.reason == "invalid_api" and #r.results == 0)
    end
end)

test("NativeExposureProbe - Clean run exposes all 13 keys with exact 26 reads and 54 captures", function()
    local p = NativeExposureProbe.new()
    local syms = mk_default_symbols()
    local ext = { caps = 0, syms = 0 }
    local api = {
        capture = function() ext.caps = ext.caps + 1; return mk_cap() end,
        readSymbol = function(k) ext.syms = ext.syms + 1; return syms[k] end,
    }
    local r = p:run(api)
    assert(r.status == "completed" and r.reason == "plan_completed")
    assert(r.lighting == "unknown" and r.nativeAcceptance == false)
    assert(r.enumBindings == "distinct_references")
    assert(#r.results == 13)
    assert(r.counts.symbols == 26 and ext.syms == 26, "Expected exactly 26 symbol reads, got " .. r.counts.symbols)
    assert(r.counts.captures == 54 and ext.caps == 54, "Expected exactly 54 captures, got " .. r.counts.captures)
    for _, res in ipairs(r.results) do
        assert(res.status == "exposed")
    end
end)

test("NativeExposureProbe - Hardcoded allowlist ignores caller settings or overrides", function()
    local p = NativeExposureProbe.new()
    local syms = mk_default_symbols()
    local probed_keys = {}
    local api = {
        capture = mk_cap,
        readSymbol = function(k)
            probed_keys[#probed_keys + 1] = k
            return syms[k]
        end,
        keys = { "custom_key_1", "custom_key_2" }, -- caller override attempt
        limit = 5,
    }
    local r = p:run(api)
    assert(#r.results == 13)
    assert(#probed_keys == 26)
    assert(probed_keys[1] == "forward_x" and probed_keys[2] == "forward_x")
    assert(probed_keys[25] == "enum_closed_door" and probed_keys[26] == "enum_closed_door")
end)

-- =========================================================================
-- PAIRED READ PROTOCOL & DETERMINISTIC STATUS PRIORITY
-- =========================================================================

test("Paired Read - Missing symbol when read returns nil", function()
    local p = NativeExposureProbe.new()
    local syms = mk_default_symbols()
    syms.forward_x = nil
    local api = {
        capture = mk_cap,
        readSymbol = function(k) return syms[k] end,
    }
    local r = p:run(api)
    assert(r.status == "completed")
    assert(r.results[1].key == "forward_x" and r.results[1].status == "missing" and r.results[1].valueType == "nil")
end)

test("Paired Read - Query error when read throws exception", function()
    local p = NativeExposureProbe.new()
    local syms = mk_default_symbols()
    local api = {
        capture = mk_cap,
        readSymbol = function(k)
            if k == "cell_get_square" then error("NATIVE_LOOKUP_FAULT") end
            return syms[k]
        end,
    }
    local r = p:run(api)
    assert(r.status == "completed")
    assert(r.results[3].key == "cell_get_square" and r.results[3].status == "query_error" and r.results[3].valueType == "unknown")
end)

test("Paired Read - Type mismatch when symbol returns unexpected Lua type", function()
    local p = NativeExposureProbe.new()
    local syms = mk_default_symbols()
    syms.forward_x = "not_a_function"
    syms.enum_clear = 12345 -- enum expects table or userdata
    local api = {
        capture = mk_cap,
        readSymbol = function(k) return syms[k] end,
    }
    local r = p:run(api)
    assert(r.status == "completed")
    assert(r.results[1].key == "forward_x" and r.results[1].status == "type_mismatch" and r.results[1].valueType == "string")
    assert(r.results[9].key == "enum_clear" and r.results[9].status == "type_mismatch" and r.results[9].valueType == "number")
end)

test("Paired Read - Unstable reference when pair returns two distinct references", function()
    local p = NativeExposureProbe.new()
    local syms = mk_default_symbols()
    local call_n = 0
    local api = {
        capture = mk_cap,
        readSymbol = function(k)
            if k == "list_size" then
                call_n = call_n + 1
                return function() return call_n end -- fresh closure each read
            end
            return syms[k]
        end,
    }
    local r = p:run(api)
    assert(r.status == "completed")
    assert(r.results[5].key == "list_size" and r.results[5].status == "unstable_reference" and r.results[5].valueType == "function")
end)

test("Paired Read Priority - Exception beats missing and type mismatch", function()
    local p = NativeExposureProbe.new()
    local syms = mk_default_symbols()
    local calls = 0
    local api = {
        capture = mk_cap,
        readSymbol = function(k)
            if k == "forward_x" then
                calls = calls + 1
                if calls == 1 then return nil else error("THROW_ON_SECOND") end
            end
            return syms[k]
        end,
    }
    local r = p:run(api)
    assert(r.results[1].key == "forward_x" and r.results[1].status == "query_error")
end)

test("Paired Read Priority - Missing beats type mismatch", function()
    local p = NativeExposureProbe.new()
    local syms = mk_default_symbols()
    local calls = 0
    local api = {
        capture = mk_cap,
        readSymbol = function(k)
            if k == "forward_x" then
                calls = calls + 1
                if calls == 1 then return "string_val" else return nil end
            end
            return syms[k]
        end,
    }
    local r = p:run(api)
    assert(r.results[1].key == "forward_x" and r.results[1].status == "missing")
end)

-- =========================================================================
-- ENUM BINDINGS VERIFICATION & SAFETY
-- =========================================================================

test("Enum Bindings - Duplicate enum references result in enumBindings unknown", function()
    local p = NativeExposureProbe.new()
    local syms = mk_default_symbols()
    syms.enum_open_door = syms.enum_clear -- duplicate reference!
    local api = {
        capture = mk_cap,
        readSymbol = function(k) return syms[k] end,
    }
    local r = p:run(api)
    assert(r.status == "completed")
    assert(r.enumBindings == "unknown", "Duplicates must prevent distinct_references")
end)

test("Enum Bindings - Missing enum results in enumBindings unknown", function()
    local p = NativeExposureProbe.new()
    local syms = mk_default_symbols()
    syms.enum_closed_door = nil
    local api = {
        capture = mk_cap,
        readSymbol = function(k) return syms[k] end,
    }
    local r = p:run(api)
    assert(r.status == "completed")
    assert(r.enumBindings == "unknown")
end)

test("Safety Invariant - Returned functions are NEVER invoked by Probe", function()
    local p = NativeExposureProbe.new()
    local syms = mk_default_symbols()
    local func_invoked = false
    syms.forward_x = function() func_invoked = true; error("MUST_NOT_BE_CALLED") end
    syms.los_line_clear = function() func_invoked = true; error("MUST_NOT_BE_CALLED") end
    local api = {
        capture = mk_cap,
        readSymbol = function(k) return syms[k] end,
    }
    local r = p:run(api)
    assert(r.status == "completed")
    assert(not func_invoked, "Probe must never call returned functions")
end)

test("Safety Invariant - Metamethods on returned symbols are NEVER invoked", function()
    local p = NativeExposureProbe.new()
    local syms = mk_default_symbols()
    local toxic_enum = setmetatable({}, {
        __eq = function() error("EQ_INVOKED") end,
        __index = function() error("INDEX_INVOKED") end,
        __tostring = function() error("TOSTRING_INVOKED") end,
    })
    syms.enum_clear = toxic_enum
    local api = {
        capture = mk_cap,
        readSymbol = function(k) return syms[k] end,
    }
    local r = p:run(api)
    assert(r.status == "completed")
    assert(r.results[9].key == "enum_clear" and r.results[9].status == "exposed")
end)

test("Scalar Output Contract - Results and return table contain only primitive scalars", function()
    local p = NativeExposureProbe.new()
    local syms = mk_default_symbols()
    local api = {
        capture = mk_cap,
        readSymbol = function(k) return syms[k] end,
    }
    local r = p:run(api)
    for _, res in ipairs(r.results) do
        assert(type(res.key) == "string")
        assert(type(res.status) == "string")
        assert(type(res.valueType) == "string")
        assert(res.value == nil and res.handle == nil and res.ref == nil)
    end
    assert(r.anchor == nil and r.symbols == nil)
end)

-- =========================================================================
-- LIFECYCLE, DRIFT, RESET, & STICKY INVALIDATION
-- =========================================================================

local drift_cases = {
    { "controller", "ctrl_drift" }, { "npc", "npc_drift" }, { "cell", "cell_drift" },
    { "generation", "gen_drift" }, { "x", 999.0 }, { "y", 888.0 }, { "z", 2.0 },
    { "fx", -1.0 }, { "fy", 1.0 },
}
for _, dc in ipairs(drift_cases) do
    test("Lifecycle Drift - " .. dc[1] .. " drift aborts and prevents subsequent native reads", function()
        local p = NativeExposureProbe.new()
        local syms = mk_default_symbols()
        local sym_calls = 0
        local drifted = false
        local api = {
            capture = function() return mk_cap(drifted and { [dc[1]] = dc[2] } or nil) end,
            readSymbol = function(k)
                sym_calls = sym_calls + 1
                if sym_calls == 3 then drifted = true end
                return syms[k]
            end,
        }
        local r = p:run(api)
        assert(r.status == "aborted" and r.reason == "lifecycle_drift" and #r.results == 0)
        assert(sym_calls == 3, "Sticky invalidation must halt reads immediately after drift")
    end)
end

local invalid_caps = {
    { "alive=false", { alive = false } }, { "resident=false", { resident = false } },
    { "cancelled=true", { cancelled = true } }, { "fx=0 and fy=0", { fx = 0.0, fy = 0.0 } },
    { "x=NaN", { x = 0/0 } }, { "abs(x)>1e6", { x = 1e7 } }, { "controller>96", { controller = string.rep("x", 97) } },
}
for _, ic in ipairs(invalid_caps) do
    test("Invalid Capture - " .. ic[1] .. " aborts with capture_invalid", function()
        local p = NativeExposureProbe.new()
        local r = p:run({ capture = function() return mk_cap(ic[2]) end, readSymbol = function() end })
        assert(r.status == "aborted" and r.reason == "capture_invalid" and #r.results == 0)
    end)
end

test("Reset in Callback - Initial capture reset aborts with reset_during_probe", function()
    local p = NativeExposureProbe.new()
    local r = p:run({ capture = function() p:reset(); return mk_cap() end, readSymbol = function() end })
    assert(r.status == "aborted" and r.reason == "reset_during_probe" and #r.results == 0)
end)

test("Reset in Callback - readSymbol reset aborts and halts further reads", function()
    local p = NativeExposureProbe.new()
    local syms = mk_default_symbols()
    local sym_calls = 0
    local api = {
        capture = mk_cap,
        readSymbol = function(k)
            sym_calls = sym_calls + 1
            if sym_calls == 2 then p:reset() end
            return syms[k]
        end,
    }
    local r = p:run(api)
    assert(r.status == "aborted" and r.reason == "reset_during_probe" and #r.results == 0)
    assert(sym_calls == 2, "Zero further reads permitted after reset")
end)

test("Reset in Callback - Final capture reset aborts probe", function()
    local p_dry = NativeExposureProbe.new()
    local syms = mk_default_symbols()
    local dry_caps = 0
    p_dry:run({
        capture = function() dry_caps = dry_caps + 1; return mk_cap() end,
        readSymbol = function(k) return syms[k] end,
    })
    assert(dry_caps == 54)

    local p = NativeExposureProbe.new()
    local calls = 0
    local r = p:run({
        capture = function()
            calls = calls + 1
            if calls == 54 then p:reset() end
            return mk_cap()
        end,
        readSymbol = function(k) return syms[k] end,
    })
    assert(r.status == "aborted" and r.reason == "reset_during_probe" and #r.results == 0)
end)

test("Reentrancy - Fails closed with reentrancy_rejected and zero queries", function()
    local p = NativeExposureProbe.new()
    local syms = mk_default_symbols()
    local reentrant_res = nil
    local api = {
        capture = mk_cap,
        readSymbol = function(k)
            if not reentrant_res then
                reentrant_res = p:run({ capture = mk_cap, readSymbol = function() end })
            end
            return syms[k]
        end,
    }
    local r = p:run(api)
    assert(reentrant_res.status == "reentrancy_rejected" and reentrant_res.reason == "reentrant_call")
    assert(reentrant_res.counts.symbols == 0 and reentrant_res.counts.captures == 0)
    assert(r.status == "completed", "Outer probe must finish unaffected")
end)

test("Reentrancy Lock - Released after error or abort allowing subsequent probe", function()
    local p = NativeExposureProbe.new()
    local r1 = p:run({ capture = function() error("THROW_CAP") end, readSymbol = function() end })
    assert(r1.status == "aborted")
    local syms = mk_default_symbols()
    local r2 = p:run({ capture = mk_cap, readSymbol = function(k) return syms[k] end })
    assert(r2.status == "completed", "Lock must be released after abort")
end)

test("Frozen API Callbacks - Mutating api table during initial capture has no effect", function()
    local p = NativeExposureProbe.new()
    local syms = mk_default_symbols()
    local api = {}
    api.capture = function()
        api.readSymbol = function() error("MUTATED_CALLBACK_INVOKED") end
        return mk_cap()
    end
    api.readSymbol = function(k) return syms[k] end
    local r = p:run(api)
    assert(r.status == "completed" and #r.results == 13)
    for _, row in ipairs(r.results) do assert(row.status == "exposed") end
end)

test("Private State Tampering - Public fake fields or snapshot mutations have no effect", function()
    local p = NativeExposureProbe.new()
    p._busy = true
    p._revision = 9999
    p.MAX_CAPTURES = 1
    local snap = p:snapshot()
    snap.attempts = 9999
    assert(p:snapshot().attempts == 0)
    local syms = mk_default_symbols()
    local r = p:run({ capture = mk_cap, readSymbol = function(k) return syms[k] end })
    assert(r.status == "completed" and p:snapshot().completed == 1)
end)


-- Codex review regressions. These remain fixture evidence, not native proof.
test("Guarded module environment rejects engine imports, globals and registration", function()
    local permitted = {type=type,rawget=rawget,rawequal=rawequal,pcall=pcall,error=error,ipairs=ipairs,math=math}
    local env = setmetatable({}, {
        __index = function(_, key)
            assert(permitted[key] ~= nil, "Unexpected global access: " .. key)
            return permitted[key]
        end,
        __newindex = function() error("Global registration") end,
    })
    local guarded = assert(load(probeSource, "guarded_probe", "t", env))()
    local probe = guarded.new()
    local syms = mk_default_symbols()
    local r = probe:run({capture=mk_cap,readSymbol=function(k) return syms[k] end})
    assert(r.status == "completed" and #r.results == 13)
end)

test("All 54 reset boundaries discard output and forbid further callbacks", function()
    for boundary=1,54 do
        local p=NativeExposureProbe.new()
        local syms=mk_default_symbols()
        local caps,reads=0,0
        local r=p:run({capture=function()
            caps=caps+1
            if caps==boundary then p:reset() end
            return mk_cap()
        end,readSymbol=function(k) reads=reads+1;return syms[k] end})
        assert(r.status == "aborted" and r.reason == "reset_during_probe")
        assert(#r.results == 0 and r.enumBindings == "unknown")
        assert(caps == boundary and reads == math.floor((boundary-1)/2))
        local fresh=p:run({capture=mk_cap,readSymbol=function(k) return syms[k] end})
        assert(fresh.status == "completed" and fresh.counts.symbols == 26)
    end
end)

test("All 26 cancellation boundaries halt after the detecting capture", function()
    for boundary=1,26 do
        local p=NativeExposureProbe.new()
        local syms=mk_default_symbols()
        local caps,reads=0,0
        local r=p:run({capture=function()
            caps=caps+1
            return mk_cap({cancelled=reads==boundary})
        end,readSymbol=function(k) reads=reads+1;return syms[k] end})
        assert(r.status == "aborted" and r.reason == "capture_invalid")
        assert(reads == boundary and caps == 2*boundary+1 and #r.results == 0)
    end
end)

test("Nil capture is tested explicitly with one counted attempt and zero reads", function()
    local p=NativeExposureProbe.new()
    local r=p:run({capture=function() return nil end,readSymbol=function() error("unreachable") end})
    assert(r.status == "aborted" and r.counts.captures == 1 and r.counts.symbols == 0)
end)

test("Capture and API metatable values do not supply missing raw fields", function()
    local p=NativeExposureProbe.new()
    local metaCalls=0
    local cap=mk_cap();cap.npc=nil
    setmetatable(cap,{__index=function() metaCalls=metaCalls+1;return "npc" end})
    local r=p:run({capture=function() return cap end,readSymbol=function() end})
    assert(r.status == "aborted" and metaCalls == 0)
    r=p:run(setmetatable({}, {__index=function() metaCalls=metaCalls+1;return function() end end}))
    assert(r.reason == "invalid_api" and metaCalls == 0 and r.counts.captures == 0)
end)

test("Opaque userdata is inspected only for type and exact reference", function()
    assert(type(opaque1)=="userdata" and type(opaque2)=="userdata")
    local p=NativeExposureProbe.new()
    local syms=mk_default_symbols();syms.enum_clear=opaque1;syms.enum_window=opaque2
    local r=p:run({capture=mk_cap,readSymbol=function(k) return syms[k] end})
    assert(r.enumBindings == "distinct_references" and r.results[9].valueType == "userdata")
    syms.enum_window=opaque1
    r=p:run({capture=mk_cap,readSymbol=function(k) return syms[k] end})
    assert(r.enumBindings == "unknown")
end)

test("Five hostile enum tables never invoke equality, naming or field access", function()
    local p=NativeExposureProbe.new()
    local syms=mk_default_symbols()
    local meta={__eq=function() error("equality") end,__index=function() error("field") end,
        __tostring=function() error("name") end,__call=function() error("call") end}
    for _,key in ipairs({"enum_clear","enum_open_door","enum_window","enum_blocked","enum_closed_door"}) do
        syms[key]=setmetatable({},meta)
    end
    local r=p:run({capture=mk_cap,readSymbol=function(k) return syms[k] end})
    assert(r.status == "completed" and r.enumBindings == "distinct_references")
end)

test("Failed reads still consume all fixed attempts and never leak exception objects", function()
    local p=NativeExposureProbe.new()
    local calls=0
    local err=setmetatable({}, {__tostring=function() error("error stringify") end})
    local r=p:run({capture=mk_cap,readSymbol=function() calls=calls+1;error(err) end})
    assert(r.status == "completed" and calls == 26 and r.counts.symbols == 26 and r.counts.captures == 54)
    for _,row in ipairs(r.results) do assert(row.status == "query_error" and row.valueType == "unknown") end
    assert(p:snapshot().attempts == 1 and p:snapshot().completed == 1)
end)

test("Lua weak-reference evidence shows callbacks and symbols are not retained", function()
    local p=NativeExposureProbe.new()
    local weak=setmetatable({}, {__mode="v"})
    local function once()
        local syms=mk_default_symbols()
        local cap=function() return mk_cap() end
        local read=function(k) return syms[k] end
        weak[1]=syms.enum_clear;weak[2]=cap;weak[3]=read
        return p:run({capture=cap,readSymbol=read})
    end
    local r=once();assert(r.status == "completed")
    collectgarbage("collect");collectgarbage("collect")
    assert(weak[1]==nil and weak[2]==nil and weak[3]==nil)
    -- This proves Lua fixture references only, not native Java GC behavior.
end)

test("Returned scalar copies cannot affect another run or lifetime counts", function()
    local p=NativeExposureProbe.new()
    local syms=mk_default_symbols()
    local api={capture=mk_cap,readSymbol=function(k) return syms[k] end}
    local r=p:run(api);r.results[1].key="injected";r.counts.symbols=0
    local later=p:run(api)
    assert(later.results[1].key=="forward_x" and later.counts.symbols==26)
    assert(p:snapshot().attempts==2 and p:snapshot().completed==2)
end)
print(string.format("RESULT %d probe checks passed", tests_passed))

""")
