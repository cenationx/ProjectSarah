"""Gemini-authored actual-Lua light source snapshot prototype fixtures.
Project Sarah Build 42.21.0. Offline verification only.
No native engine wiring or gameplay acceptance is implied.
"""
from pathlib import Path
import sys

root = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(root / "tools/dependencies/python"))
from lupa import LuaRuntime

lua = LuaRuntime(unpack_returned_tuples=True)
lua.globals().LightSourceSnapshot = lua.execute(
    (root / "foundation/SarahFoundation/42/media/lua/client/Sarah/LightSourceSnapshot.lua").read_text(encoding="utf-8")
)

lua.execute(r"""
local tests_passed = 0
local function test(name, fn)
    local ok, err = pcall(fn)
    if not ok then error("\n[FAIL] " .. name .. "\n" .. tostring(err)) end
    tests_passed = tests_passed + 1
    print("PASS " .. name)
end

local function mk_cap(o)
    local b = {
        controller = "ctrl_test_1",
        npc = "npc_sarah_1",
        cell = "cell_suburbs_0",
        generation = "gen_1",
        alive = true,
        resident = true,
        cancelled = false,
        x = 1000.0,
        y = 2000.0,
        z = 0.0,
        fx = 1.0,
        fy = 0.0,
    }
    if o then for k, v in pairs(o) do b[k] = v end end
    return b
end

local function mk_source(o)
    local s = {
        x = 1005,
        y = 2005,
        z = 0,
        r = 1.0,
        g = 0.8,
        b = 0.6,
        radius = 15,
        active = true,
        hydroPowered = false,
        id = 101,
        localToBuilding = nil,
        switches = {},
    }
    if o then for k, v in pairs(o) do s[k] = v end end
    if s.getLocalToBuilding == nil and not (o and o.omit_building_getter) then
        s.getLocalToBuilding = function() return s.localToBuilding end
    end
    if s.getSwitches == nil and not (o and o.omit_switches_getter) then
        s.getSwitches = function() return s.switches end
    end
    return s
end

local function mk_square(gen_elec, grid_elec)
    return {
        haveElectricity = function() return gen_elec end,
        hasGridPower = function() return grid_elec end,
    }
end

-- 1. API Validation
test("API - Rejects nil or non-table api", function()
    local snap = LightSourceSnapshot.new()
    local r1 = snap:snapshot(nil)
    assert(r1.status == "aborted" and r1.reason == "invalid_api" and r1.incomplete == true)
    local r2 = snap:snapshot("not_a_table")
    assert(r2.status == "aborted" and r2.reason == "invalid_api" and r2.incomplete == true)
end)

test("API - Rejects missing required functions in api", function()
    local snap = LightSourceSnapshot.new()
    local r1 = snap:snapshot({ capture = mk_cap })
    assert(r1.status == "aborted" and r1.reason == "invalid_api")
    local r2 = snap:snapshot({ capture = mk_cap, getLightSources = function() return {} end })
    assert(r2.status == "aborted" and r2.reason == "invalid_api")
end)

-- 2. Lifecycle Validation & Drift
test("Lifecycle - Aborts on invalid initial capture", function()
    local snap = LightSourceSnapshot.new()
    local api = {
        capture = function() return mk_cap({ alive = false }) end,
        getLightSources = function() return {} end,
        getSquare = function() return mk_square(true, true) end,
    }
    local r = snap:snapshot(api)
    assert(r.status == "aborted" and r.reason == "lifecycle_invalid" and r.incomplete == true)
end)

test("Lifecycle - Aborts on cancelled initial capture", function()
    local snap = LightSourceSnapshot.new()
    local api = {
        capture = function() return mk_cap({ cancelled = true }) end,
        getLightSources = function() return {} end,
        getSquare = function() return mk_square(true, true) end,
    }
    local r = snap:snapshot(api)
    assert(r.status == "aborted" and r.reason == "lifecycle_invalid")
end)

test("Lifecycle - Aborts on infinite coordinate in capture", function()
    local snap = LightSourceSnapshot.new()
    local api = {
        capture = function() return mk_cap({ x = 1/0 }) end,
        getLightSources = function() return {} end,
        getSquare = function() return mk_square(true, true) end,
    }
    local r = snap:snapshot(api)
    assert(r.status == "aborted" and r.reason == "lifecycle_invalid")
end)

test("Lifecycle - Aborts on lifecycle drift during pass", function()
    local snap = LightSourceSnapshot.new()
    local calls = 0
    local api = {
        capture = function()
            calls = calls + 1
            if calls > 1 then return mk_cap({ generation = "gen_drifted" }) end
            return mk_cap()
        end,
        getLightSources = function()
            local list = {}
            for i = 1, 10 do list[i] = mk_source({ x = 1000 + i }) end
            return list
        end,
        getSquare = function() return mk_square(true, true) end,
    }
    local r = snap:snapshot(api)
    assert(r.status == "aborted" and r.reason == "lifecycle_drift" and #r.sources == 0)
end)

test("Lifecycle - Aborts on lifecycle drift at end of pass", function()
    local snap = LightSourceSnapshot.new()
    local calls = 0
    local api = {
        capture = function()
            calls = calls + 1
            if calls == 3 then return mk_cap({ cell = "cell_new" }) end
            return mk_cap()
        end,
        getLightSources = function() return { mk_source() } end,
        getSquare = function() return mk_square(true, true) end,
    }
    local r = snap:snapshot(api)
    assert(r.status == "aborted" and r.reason == "lifecycle_drift" and #r.sources == 0)
end)

test("Lifecycle - Reentrancy is rejected cleanly", function()
    local snap = LightSourceSnapshot.new()
    local reentrant_res = nil
    local api = {
        capture = mk_cap,
        getLightSources = function()
            reentrant_res = snap:snapshot({ capture = mk_cap, getLightSources = function() return {} end, getSquare = function() return {} end })
            return {}
        end,
        getSquare = function() return mk_square(true, true) end,
    }
    local r = snap:snapshot(api)
    assert(reentrant_res ~= nil)
    assert(reentrant_res.status == "reentrancy_rejected" and reentrant_res.reason == "reentrant_call")
    assert(r.status == "completed")
end)

test("Lifecycle - Aborts if reset is called during snapshot", function()
    local snap = LightSourceSnapshot.new()
    local api = {
        capture = mk_cap,
        getLightSources = function()
            snap:reset()
            return { mk_source() }
        end,
        getSquare = function() return mk_square(true, true) end,
    }
    local r = snap:snapshot(api)
    assert(r.status == "aborted" and r.reason == "reset_during_snapshot")
end)

-- 3. Collection Types: Lua Table vs Java List & Integral Size Validation
test("Collection - Handles empty Lua table", function()
    local snap = LightSourceSnapshot.new()
    local r = snap:snapshot({
        capture = mk_cap,
        getLightSources = function() return {} end,
        getSquare = function() return mk_square(true, true) end,
    })
    assert(r.status == "completed" and r.incomplete == false and #r.sources == 0 and r.counts.collection_size == 0)
end)

test("Collection - Handles Java-style collection with size and get", function()
    local snap = LightSourceSnapshot.new()
    local raw_items = {
        mk_source({ id = 1, x = 1001, y = 2001, radius = 10 }),
        mk_source({ id = 2, x = 1002, y = 2002, radius = 20 }),
    }
    local java_coll = {
        size = function() return #raw_items end,
        get = function(self, idx) return raw_items[idx + 1] end,
    }
    local r = snap:snapshot({
        capture = mk_cap,
        getLightSources = function() return java_coll end,
        getSquare = function() return mk_square(true, true) end,
    })
    assert(r.status == "completed" and r.incomplete == true and #r.sources == 2)
    assert(r.sources[1].radius == 10 and r.sources[2].radius == 20)
    assert(r.sources[1].x == 1001 and r.sources[2].x == 1002)
end)

test("Collection - Rejects non-integral collection size", function()
    local snap = LightSourceSnapshot.new()
    local bad_coll = {
        size = function() return 2.5 end,
        get = function(self, idx) return mk_source() end,
    }
    local r = snap:snapshot({
        capture = mk_cap,
        getLightSources = function() return bad_coll end,
        getSquare = function() return mk_square(true, true) end,
    })
    assert(r.status == "aborted" and r.reason == "invalid_collection_size")
end)

-- 4. Collection Budgets & Oversized Collection Rejection
test("Budgets - Rejects oversized collection without silent truncation", function()
    local snap = LightSourceSnapshot.new({ maxCollectionSize = 10 })
    local oversized = {}
    for i = 1, 15 do oversized[i] = mk_source({ x = 1000 + i }) end
    local r = snap:snapshot({
        capture = mk_cap,
        getLightSources = function() return oversized end,
        getSquare = function() return mk_square(true, true) end,
    })
    assert(r.status == "collection_oversized" and r.reason == "collection_exceeds_budget")
    assert(r.incomplete == true and #r.sources == 0)
    assert(r.counts.collection_size == 15)
end)

test("Budgets - Hard max collection budget defaults to 128", function()
    local snap = LightSourceSnapshot.new()
    local oversized = {}
    for i = 1, 129 do oversized[i] = mk_source({ x = 1000 + i }) end
    local r = snap:snapshot({
        capture = mk_cap,
        getLightSources = function() return oversized end,
        getSquare = function() return mk_square(true, true) end,
    })
    assert(r.status == "collection_oversized" and r.reason == "collection_exceeds_budget")
    assert(#r.sources == 0)
end)

test("Budgets - Stops and marks incomplete when read budget exhausted", function()
    local snap = LightSourceSnapshot.new({ maxReads = 30 })
    local list = {}
    for i = 1, 10 do list[i] = mk_source({ x = 1000 + i }) end
    local r = snap:snapshot({
        capture = mk_cap,
        getLightSources = function() return list end,
        getSquare = function() return mk_square(true, true) end,
    })
    assert(r.status == "budget_exhausted" and r.reason == "read_limit_reached")
    assert(r.incomplete == true and r.counts.total_reads >= 30)
end)

test("Budgets - Stops and marks incomplete when square budget exhausted", function()
    local snap = LightSourceSnapshot.new({ maxSquares = 3 })
    local list = {}
    for i = 1, 10 do list[i] = mk_source({ x = 1000 + i }) end
    local r = snap:snapshot({
        capture = mk_cap,
        getLightSources = function() return list end,
        getSquare = function() return mk_square(true, true) end,
    })
    assert(r.status == "budget_exhausted" and r.reason == "square_limit_reached")
    assert(r.incomplete == true and r.counts.square_lookups == 3)
end)

test("Budgets - Stops and marks incomplete when output budget exhausted", function()
    local snap = LightSourceSnapshot.new({ maxOutputSources = 2 })
    local list = {}
    for i = 1, 10 do list[i] = mk_source({ x = 1000 + i }) end
    local r = snap:snapshot({
        capture = mk_cap,
        getLightSources = function() return list end,
        getSquare = function() return mk_square(true, true) end,
    })
    assert(r.status == "budget_exhausted" and r.reason == "output_limit_reached")
    assert(r.incomplete == true and #r.sources == 2 and r.counts.valid_sources == 2)
end)

-- 5. Collection Mutation & Same-Size Replacement/Reordering Detection
test("Mutation - Detects collection size change during iteration", function()
    local snap = LightSourceSnapshot.new()
    local list = { mk_source({ x = 1001 }), mk_source({ x = 1002 }) }
    local r = snap:snapshot({
        capture = mk_cap,
        getLightSources = function() return list end,
        getSquare = function(x, y, z)
            list[#list + 1] = mk_source({ x = 1003 })
            return mk_square(true, true)
        end,
    })
    assert(r.status == "collection_mutated")
    assert(r.incomplete == true and #r.sources == 0)
end)

test("Mutation - Detects same-size collection replacement/reordering mid-reads", function()
    local snap = LightSourceSnapshot.new()
    local s1, s2 = mk_source({ x = 1001 }), mk_source({ x = 1002 })
    local list = { s1, s2 }
    local r = snap:snapshot({
        capture = mk_cap,
        getLightSources = function() return list end,
        getSquare = function(x, y, z)
            -- Swap references without changing list size!
            list[1], list[2] = s2, s1
            return mk_square(true, true)
        end,
    })
    assert(r.status == "collection_mutated" and r.reason == "collection_changed_during_iteration")
    assert(r.incomplete == true and #r.sources == 0)
end)

test("Mutation - Detects replacement during final getter read", function()
    local snap = LightSourceSnapshot.new()
    local s1, s2 = mk_source({ x = 1001 }), mk_source({ x = 1002 })
    local list = { s1, s2 }
    local getters_called = 0
    s2.getRadius = function(self)
        getters_called = getters_called + 1
        -- Mutate list during final source's getter read!
        list[1] = mk_source({ x = 9999 })
        return 15
    end
    local r = snap:snapshot({
        capture = mk_cap,
        getLightSources = function() return list end,
        getSquare = function() return mk_square(true, true) end,
    })
    assert(r.status == "collection_mutated" and r.reason == "collection_changed_during_iteration")
    assert(#r.sources == 0)
end)

-- 6. Getter Failures vs Raw Fields
test("Getters - Getter failure does not silently succeed via raw-field fallback", function()
    local snap = LightSourceSnapshot.new()
    local bad_src = {
        getX = function() error("native JNI crash in getX") end,
        x = 1005, -- raw field present, MUST NOT BE USED
        getY = function() return 2005 end,
        getZ = function() return 0 end,
        getR = function() return 1.0 end,
        getG = function() return 1.0 end,
        getB = function() return 1.0 end,
        getRadius = function() return 10 end,
        isActive = function() return true end,
        isHydroPowered = function() return false end,
    }
    local r = snap:snapshot({
        capture = mk_cap,
        getLightSources = function() return { bad_src } end,
        getSquare = function() return mk_square(true, true) end,
    })
    assert(r.status == "completed" and r.incomplete == true)
    assert(r.counts.malformed_sources == 1 and #r.sources == 0)
end)

test("Getters - Legitimate nil getter does not fall back to raw field", function()
    local snap = LightSourceSnapshot.new()
    local raw_src = {
        getX = function() return 1005 end,
        getY = function() return 2005 end,
        getZ = function() return 0 end,
        getR = function() return 1.0 end,
        getG = function() return 1.0 end,
        getB = function() return 1.0 end,
        getRadius = function() return 10 end,
        isActive = function() return true end,
        isHydroPowered = function() return false end,
        getLocalToBuilding = function() return nil end, -- legitimately unrestricted
        localToBuilding = { id = 999 }, -- MUST NOT be used!
    }
    local r = snap:snapshot({
        capture = mk_cap,
        getLightSources = function() return { raw_src } end,
        getSquare = function() return mk_square(true, true) end,
    })
    assert(#r.sources == 1)
    assert(r.sources[1].buildingRestriction == "unrestricted")
    assert(r.sources[1].buildingId == nil)
end)

test("Getters - Raw field used only when getter is completely unavailable", function()
    local snap = LightSourceSnapshot.new()
    local mock_src = {
        x = 1005,
        y = 2005,
        z = 0,
        r = 1.0,
        g = 0.5,
        b = 0.2,
        radius = 12,
        active = true,
        hydroPowered = false,
    }
    local r = snap:snapshot({
        capture = mk_cap,
        getLightSources = function() return { mock_src } end,
        getSquare = function() return mk_square(true, true) end,
    })
    assert(#r.sources == 1 and r.sources[1].radius == 12)
end)

-- 7. Building Restrictions: Unrestricted vs Unknown vs Restricted
test("Building - Outdoor source is unrestricted with buildingId nil", function()
    local snap = LightSourceSnapshot.new()
    local r = snap:snapshot({
        capture = mk_cap,
        getLightSources = function() return { mk_source({ localToBuilding = nil }) } end,
        getSquare = function() return mk_square(true, true) end,
    })
    assert(r.sources[1].buildingRestriction == "unrestricted")
    assert(r.sources[1].buildingId == nil)
end)

test("Building - Restricted building with valid getId", function()
    local snap = LightSourceSnapshot.new()
    local b = { getId = function() return 42 end }
    local r = snap:snapshot({
        capture = mk_cap,
        getLightSources = function() return { mk_source({ localToBuilding = b }) } end,
        getSquare = function() return mk_square(true, true) end,
    })
    assert(r.sources[1].buildingRestriction == "restricted")
    assert(r.sources[1].buildingId == 42)
end)

test("Building - Throwing getLocalToBuilding yields unknown building restriction", function()
    local snap = LightSourceSnapshot.new()
    local src = mk_source({
        getLocalToBuilding = function() error("building query crashed") end,
    })
    local r = snap:snapshot({
        capture = mk_cap,
        getLightSources = function() return { src } end,
        getSquare = function() return mk_square(true, true) end,
    })
    assert(#r.sources == 1)
    assert(r.sources[1].buildingRestriction == "unknown")
    assert(r.sources[1].buildingId == nil)
end)

test("Building - Building object with throwing getId yields unknown restriction", function()
    local snap = LightSourceSnapshot.new()
    local b = { getId = function() error("getId failed") end }
    local r = snap:snapshot({
        capture = mk_cap,
        getLightSources = function() return { mk_source({ localToBuilding = b }) } end,
        getSquare = function() return mk_square(true, true) end,
    })
    assert(#r.sources == 1)
    assert(r.sources[1].buildingRestriction == "unknown")
    assert(r.sources[1].buildingId == nil)
end)

-- 8. Power Semantics: Generator vs Grid Power
test("Power - False generator power does NOT prevent checking grid power", function()
    local snap = LightSourceSnapshot.new()
    local sq = {
        haveElectricity = function() return false end, -- no generator!
        hasGridPower = function() return true end,     -- hydro grid is on!
    }
    local r = snap:snapshot({
        capture = mk_cap,
        getLightSources = function() return { mk_source({ hydroPowered = true, active = true }) } end,
        getSquare = function() return sq end,
    })
    assert(#r.sources == 1)
    assert(r.sources[1].generatorPower == false)
    assert(r.sources[1].gridPower == true)
    assert(r.sources[1].powerStatus == "powered")
end)

test("Power - Generator power present when grid power is false", function()
    local snap = LightSourceSnapshot.new()
    local sq = {
        haveElectricity = function() return true end,  -- generator is running!
        hasGridPower = function() return false end,    -- world grid is out!
    }
    local r = snap:snapshot({
        capture = mk_cap,
        getLightSources = function() return { mk_source({ hydroPowered = true, active = true }) } end,
        getSquare = function() return sq end,
    })
    assert(#r.sources == 1)
    assert(r.sources[1].generatorPower == true)
    assert(r.sources[1].gridPower == false)
    assert(r.sources[1].powerStatus == "powered")
end)

test("Power - Both generator and grid false yields unpowered", function()
    local snap = LightSourceSnapshot.new()
    local sq = {
        haveElectricity = function() return false end,
        hasGridPower = function() return false end,
    }
    local r = snap:snapshot({
        capture = mk_cap,
        getLightSources = function() return { mk_source({ hydroPowered = true, active = false }) } end,
        getSquare = function() return sq end,
    })
    assert(#r.sources == 1)
    assert(r.sources[1].generatorPower == false)
    assert(r.sources[1].gridPower == false)
    assert(r.sources[1].powerStatus == "unpowered")
end)

test("Power - Switches present keeps power status unknown", function()
    local snap = LightSourceSnapshot.new()
    local switches_list = { "sw1", "sw2" }
    local src = mk_source({
        hydroPowered = true,
        active = true,
        getSwitches = function() return switches_list end,
    })
    local sq = mk_square(true, true)
    local r = snap:snapshot({
        capture = mk_cap,
        getLightSources = function() return { src } end,
        getSquare = function() return sq end,
    })
    assert(#r.sources == 1)
    assert(r.sources[1].switchCount == 2)
    assert(r.sources[1].powerStatus == "unknown")
end)

-- 9. Freshness: Unknown Preservation vs Positive Stale Evidence
test("Freshness - hydroPowered=false preserves freshness unknown", function()
    local snap = LightSourceSnapshot.new()
    local r = snap:snapshot({
        capture = mk_cap,
        getLightSources = function() return { mk_source({ hydroPowered = false, active = true }) } end,
        getSquare = function() return mk_square(true, true) end,
    })
    assert(#r.sources == 1)
    assert(r.sources[1].freshness == "unknown")
end)

test("Freshness - Power agreement does NOT label freshness verified", function()
    local snap = LightSourceSnapshot.new()
    local r = snap:snapshot({
        capture = mk_cap,
        getLightSources = function() return { mk_source({ hydroPowered = true, active = true }) } end,
        getSquare = function() return mk_square(true, true) end,
    })
    assert(#r.sources == 1)
    assert(r.sources[1].powerStatus == "powered")
    assert(r.sources[1].freshness == "unknown")
end)

test("Freshness - Discrepancy (unpowered while active) establishes stale", function()
    local snap = LightSourceSnapshot.new()
    local sq = mk_square(false, false)
    local r = snap:snapshot({
        capture = mk_cap,
        getLightSources = function() return { mk_source({ hydroPowered = true, active = true }) } end,
        getSquare = function() return sq end,
    })
    assert(#r.sources == 1)
    assert(r.sources[1].powerStatus == "unpowered")
    assert(r.sources[1].freshness == "stale")
    assert(r.counts.stale_sources == 1)
end)

-- 10. Reentrancy Guard Exception Safety & Honest Accounting
test("Reentrancy - Unexpected exception always releases reentrancy guard", function()
    local snap = LightSourceSnapshot.new()
    local crashed = false
    local api_crash = {
        capture = mk_cap,
        getLightSources = function()
            crashed = true
            error("simulated native engine crash")
        end,
        getSquare = function() return mk_square(true, true) end,
    }
    local r1 = snap:snapshot(api_crash)
    assert(crashed == true)
    assert(r1.status == "aborted" and (r1.reason == "unexpected_error" or r1.reason == "get_sources_failed"))

    -- Crucial: Guard MUST be released; subsequent call MUST NOT be rejected as reentrant!
    local r2 = snap:snapshot({
        capture = mk_cap,
        getLightSources = function() return {} end,
        getSquare = function() return mk_square(true, true) end,
    })
    assert(r2.status == "completed")
end)

test("Accounting - Honest getter and total read counts tracked", function()
    local snap = LightSourceSnapshot.new()
    local r = snap:snapshot({
        capture = mk_cap,
        getLightSources = function() return { mk_source(), mk_source() } end,
        getSquare = function() return mk_square(true, true) end,
    })
    assert(r.status == "completed")
    assert(r.counts.source_reads == 2)
    assert(r.counts.getter_reads > 20)
    assert(r.counts.total_reads == r.counts.getter_reads + r.counts.square_lookups + r.counts.power_queries)
end)

-- 11. Reference Freedom & Separation from Sight
test("Purity - Returned snapshot contains only copied primitives, no object handles", function()
    local snap = LightSourceSnapshot.new()
    local raw_src = mk_source({
        x = 1002,
        y = 2002,
        localToBuilding = { id = 50 },
    })
    local r = snap:snapshot({
        capture = mk_cap,
        getLightSources = function() return { raw_src } end,
        getSquare = function() return mk_square(true, true) end,
    })
    assert(#r.sources == 1)
    local s = r.sources[1]
    s.x = 9999
    assert(raw_src.x == 1002)
    assert(type(s.id) == "string")
    assert(type(s.x) == "number")
    assert(type(s.buildingId) == "number")
    assert(s.visual == nil and s.targetIllumination == nil)
end)

test("Building - Extracts building ID via def object getId method", function()
    local snap = LightSourceSnapshot.new()
    local b = {
        getDef = function() return { getId = function() return 108 end } end,
    }
    local r = snap:snapshot({
        capture = mk_cap,
        getLightSources = function() return { mk_source({ localToBuilding = b }) } end,
        getSquare = function() return mk_square(true, true) end,
    })
    assert(#r.sources == 1)
    assert(r.sources[1].buildingRestriction == "restricted")
    assert(r.sources[1].buildingId == 108)
end)

test("Power - Throwing haveElectricity does not prevent checking hasGridPower", function()
    local snap = LightSourceSnapshot.new()
    local sq = {
        haveElectricity = function() error("generator query crash") end,
        hasGridPower = function() return true end,
    }
    local r = snap:snapshot({
        capture = mk_cap,
        getLightSources = function() return { mk_source({ hydroPowered = true, active = true }) } end,
        getSquare = function() return sq end,
    })
    assert(#r.sources == 1)
    assert(r.sources[1].generatorPower == nil)
    assert(r.sources[1].gridPower == true)
    assert(r.sources[1].powerStatus == "powered")
end)

test("Reentrancy - Outer exception in runner closure releases guard", function()
    local snap = LightSourceSnapshot.new()
    local faulty_api = {
        capture = mk_cap,
        getLightSources = function()
            -- Returns collection with broken metatable that errors on index
            return setmetatable({}, {
                __index = function(_, k)
                    if k == "size" then return function() return 1 end end
                    error("fatal table crash inside traversal")
                end,
            })
        end,
        getSquare = function() return mk_square(true, true) end,
    }
    local r1 = snap:snapshot(faulty_api)
    assert(r1.status == "aborted")

    -- Verify guard is released
    local r2 = snap:snapshot({
        capture = mk_cap,
        getLightSources = function() return {} end,
        getSquare = function() return mk_square(true, true) end,
    })
    assert(r2.status == "completed")
end)

-- 12. Regressions: Exact Pre-Operation Budget Enforcement & Tiny Budgets
test("Budget Regression - Tiny budgets enforce maxReads BEFORE operations and never exceed limit", function()
    for budget = 1, 15 do
        local snap = LightSourceSnapshot.new({ maxReads = budget })
        local calls = {
            getSources = 0,
            collSize = 0,
            collGet = 0,
            getters = 0,
            square = 0,
            power = 0,
        }
        local function count_call(k)
            calls[k] = calls[k] + 1
        end

        local src_item = {
            getX = function() count_call("getters") return 1005 end,
            getY = function() count_call("getters") return 2005 end,
            getZ = function() count_call("getters") return 0 end,
            getR = function() count_call("getters") return 1.0 end,
            getG = function() count_call("getters") return 0.8 end,
            getB = function() count_call("getters") return 0.6 end,
            getRadius = function() count_call("getters") return 15 end,
            isActive = function() count_call("getters") return true end,
            isHydroPowered = function() count_call("getters") return true end,
            getId = function() count_call("getters") return 101 end,
            getLocalToBuilding = function() count_call("getters") return nil end,
            getSwitches = function()
                count_call("getters")
                return {
                    size = function() count_call("getters") return 0 end,
                }
            end,
        }
        local coll = {
            size = function() count_call("collSize") return 1 end,
            get = function(self, idx) count_call("collGet") return src_item end,
        }
        local api = {
            capture = mk_cap,
            getLightSources = function() count_call("getSources") return coll end,
            getSquare = function(x, y, z)
                count_call("square")
                return {
                    haveElectricity = function() count_call("power") return true end,
                    hasGridPower = function() count_call("power") return true end,
                }
            end,
        }

        local r = snap:snapshot(api)
        local total_actual_calls = calls.getSources + calls.collSize + calls.collGet + calls.getters + calls.square + calls.power

        -- Crucial: actual native calls made must NEVER exceed budget
        assert(total_actual_calls <= budget, string.format("Actual calls %d exceeded budget %d", total_actual_calls, budget))
        -- Crucial: reported total_reads must NEVER exceed budget
        assert(r.counts.total_reads <= budget, string.format("Reported total_reads %d exceeded budget %d", r.counts.total_reads, budget))
        -- Crucial: reported total_reads must accurately match actual calls made
        assert(r.counts.total_reads == total_actual_calls, string.format("total_reads %d != actual calls %d at budget %d", r.counts.total_reads, total_actual_calls, budget))
        -- Crucial: on budget exhaustion, status is budget_exhausted and incomplete is true
        if total_actual_calls < budget then
            assert(r.status == "completed" and r.incomplete == false)
        else
            assert(r.status == "budget_exhausted" and r.reason == "read_limit_reached" and r.incomplete == true)
        end
    end
end)

test("Budget Regression - maxReads=1 stops immediately after getSources", function()
    local snap = LightSourceSnapshot.new({ maxReads = 1 })
    local sources_called = 0
    local size_called = 0
    local coll = {
        size = function() size_called = size_called + 1 return 1 end,
    }
    local r = snap:snapshot({
        capture = mk_cap,
        getLightSources = function()
            sources_called = sources_called + 1
            return coll
        end,
        getSquare = function() return mk_square(true, true) end,
    })
    assert(r.status == "budget_exhausted" and r.reason == "read_limit_reached")
    assert(r.incomplete == true)
    assert(r.counts.total_reads == 1)
    assert(r.counts.getter_reads == 1)
    assert(sources_called == 1)
    assert(size_called == 0, "size must not be called when maxReads=1!")
end)

-- 13. Regressions: Missing/Malformed Building Metadata Must Remain Unknown
test("Building Regression - Unavailable getLocalToBuilding yields unknown even with absent fields", function()
    local snap = LightSourceSnapshot.new()
    local src = mk_source({
        omit_building_getter = true,
        localToBuilding = nil,
    })
    local r = snap:snapshot({
        capture = mk_cap,
        getLightSources = function() return { src } end,
        getSquare = function() return mk_square(true, true) end,
    })
    assert(#r.sources == 1)
    assert(r.sources[1].buildingRestriction == "unknown", "missing getter must yield unknown, not unrestricted")
    assert(r.sources[1].buildingId == nil)
end)

test("Building Regression - Raw field localToBuilding does NOT establish unrestricted or restricted", function()
    local snap = LightSourceSnapshot.new()
    local src_raw_nil = mk_source({
        omit_building_getter = true,
        localToBuilding = nil,
    })
    local r1 = snap:snapshot({
        capture = mk_cap,
        getLightSources = function() return { src_raw_nil } end,
        getSquare = function() return mk_square(true, true) end,
    })
    assert(#r1.sources == 1)
    assert(r1.sources[1].buildingRestriction == "unknown")

    local src_raw_table = mk_source({
        omit_building_getter = true,
        localToBuilding = { id = 42 },
    })
    local r2 = snap:snapshot({
        capture = mk_cap,
        getLightSources = function() return { src_raw_table } end,
        getSquare = function() return mk_square(true, true) end,
    })
    assert(#r2.sources == 1)
    assert(r2.sources[1].buildingRestriction == "unknown")
end)

test("Building Regression - Malformed building object without valid integer ID yields unknown", function()
    local snap = LightSourceSnapshot.new()
    local b_bad = { getId = function() return "not_an_int" end }
    local src = mk_source({ localToBuilding = b_bad })
    local r = snap:snapshot({
        capture = mk_cap,
        getLightSources = function() return { src } end,
        getSquare = function() return mk_square(true, true) end,
    })
    assert(#r.sources == 1)
    assert(r.sources[1].buildingRestriction == "unknown")
    assert(r.sources[1].buildingId == nil)
end)

-- 14. Regressions: Missing/Malformed Switch Metadata Must Remain Unknown
test("Switch Regression - Unavailable getSwitches keeps switchCount unknown and powerStatus unknown", function()
    local snap = LightSourceSnapshot.new()
    local src = mk_source({
        omit_switches_getter = true,
        hydroPowered = true,
        active = true,
    })
    local sq = mk_square(true, true)
    local r = snap:snapshot({
        capture = mk_cap,
        getLightSources = function() return { src } end,
        getSquare = function() return sq end,
    })
    assert(#r.sources == 1)
    assert(r.sources[1].switchCount == nil, "missing switch getter must yield nil switchCount, not 0")
    assert(r.sources[1].powerStatus == "unknown", "unknown switches must preserve powerStatus unknown")
    assert(r.incomplete == true)
    assert(r.counts.unverified_power == 1)
end)

test("Switch Regression - Malformed switch collection size keeps switchCount unknown", function()
    local snap = LightSourceSnapshot.new()
    local bad_switches = {
        size = function() return 3.14 end,
    }
    local src = mk_source({
        hydroPowered = true,
        active = true,
        switches = bad_switches,
    })
    local sq = mk_square(true, true)
    local r = snap:snapshot({
        capture = mk_cap,
        getLightSources = function() return { src } end,
        getSquare = function() return sq end,
    })
    assert(#r.sources == 1)
    assert(r.sources[1].switchCount == nil)
    assert(r.sources[1].powerStatus == "unknown")
end)

test("Switch Regression - Validated empty switch collection allows powered status", function()
    local snap = LightSourceSnapshot.new()
    local src = mk_source({
        hydroPowered = true,
        active = true,
        switches = {},
    })
    local sq = mk_square(true, true)
    local r = snap:snapshot({
        capture = mk_cap,
        getLightSources = function() return { src } end,
        getSquare = function() return sq end,
    })
    assert(#r.sources == 1)
    assert(r.sources[1].switchCount == 0)
    assert(r.sources[1].powerStatus == "powered")
end)

test("Switch Regression - Switch-size query is charged against maxReads", function()
    local snap = LightSourceSnapshot.new({ maxReads = 12 })
    local size_checked = false
    local sw = {
        size = function()
            size_checked = true
            return 0
        end
    }
    local src = mk_source({
        hydroPowered = false,
        switches = sw,
    })
    local r = snap:snapshot({
        capture = mk_cap,
        getLightSources = function() return { src } end,
        getSquare = function() return mk_square(true, true) end,
    })
    assert(r.status == "budget_exhausted" and r.reason == "read_limit_reached")
    assert(r.counts.total_reads == 12)
end)

-- 15. Regressions: Member-Lookup Exceptions vs Truly Unavailable Getters
test("Lookup Exception - Throwing __index on getter does NOT fall back to raw field", function()
    local snap = LightSourceSnapshot.new()
    local mt = {
        __index = function(t, k)
            if k == "getX" then
                error("simulated JNI exception during getX member lookup")
            end
            return rawget(t, k)
        end
    }
    local src = setmetatable(mk_source({ x = 1005 }), mt)
    local r = snap:snapshot({
        capture = mk_cap,
        getLightSources = function() return { src } end,
        getSquare = function() return mk_square(true, true) end,
    })
    assert(r.status == "completed")
    assert(r.counts.malformed_sources == 1, "throwing lookup must reject source as malformed, not fall back to field")
    assert(#r.sources == 0)
end)

test("Lookup Exception - Non-function non-nil getter property does NOT fall back to field", function()
    local snap = LightSourceSnapshot.new()
    local src = mk_source({
        getX = "not_a_callable_function",
        x = 1005,
    })
    local r = snap:snapshot({
        capture = mk_cap,
        getLightSources = function() return { src } end,
        getSquare = function() return mk_square(true, true) end,
    })
    assert(r.status == "completed")
    assert(r.counts.malformed_sources == 1)
    assert(#r.sources == 0)
end)

test("Lookup Exception - Throwing __index on building getter yields unknown restriction", function()
    local snap = LightSourceSnapshot.new()
    local mt = {
        __index = function(t, k)
            if k == "getLocalToBuilding" then
                error("JNI member lookup error on getLocalToBuilding")
            end
            return rawget(t, k)
        end
    }
    local src = setmetatable(mk_source({ omit_building_getter = true }), mt)
    local r = snap:snapshot({
        capture = mk_cap,
        getLightSources = function() return { src } end,
        getSquare = function() return mk_square(true, true) end,
    })
    assert(#r.sources == 1)
    assert(r.sources[1].buildingRestriction == "unknown")
end)

test("Lookup Exception - Throwing __index on switches getter yields unknown switches", function()
    local snap = LightSourceSnapshot.new()
    local mt = {
        __index = function(t, k)
            if k == "getSwitches" then
                error("JNI member lookup error on getSwitches")
            end
            return rawget(t, k)
        end
    }
    local src = setmetatable(mk_source({ omit_switches_getter = true, hydroPowered = true, active = true }), mt)
    local sq = mk_square(true, true)
    local r = snap:snapshot({
        capture = mk_cap,
        getLightSources = function() return { src } end,
        getSquare = function() return sq end,
    })
    assert(#r.sources == 1)
    assert(r.sources[1].switchCount == nil)
    assert(r.sources[1].powerStatus == "unknown")
end)

print(string.format("RESULT %d light snapshot checks passed", tests_passed))
""")
