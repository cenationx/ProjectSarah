"""Actual Lua sampler composition fixtures; no native gameplay acceptance."""
from pathlib import Path
import sys
root = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(root / "tools/dependencies/python"))
from lupa import LuaRuntime
lua = LuaRuntime(unpack_returned_tuples=True)
for name in ("CandidateCollector", "Coverage", "Perception", "ObstructionNormalizer", "Knowledge", "DiagnosticSampler"):
    lua.globals()[name] = lua.execute((root / f"foundation/SarahFoundation/42/media/lua/client/Sarah/{name}.lua").read_text(encoding="utf-8"))
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

local function get_modules()
    return {
        CandidateCollector = CandidateCollector,
        Coverage = Coverage,
        Perception = Perception,
        ObstructionNormalizer = ObstructionNormalizer,
    }
end

local function mk_cap(o)
    local b = {
        controller = "ctrl_1",
        npc = "npc_1",
        cell = "cell_1",
        generation = "gen_1",
        alive = true,
        resident = true,
        cancelled = false,
        x = 0.0,
        y = 0.0,
        z = 0.0,
        fx = 1.0,
        fy = 0.0,
    }
    if o then for k, v in pairs(o) do b[k] = v end end
    return b
end

local function mk_bindings()
    return {
        Clear = { _tag = "Clear" },
        ClearThroughOpenDoor = { _tag = "OpenDoor" },
        ClearThroughWindow = { _tag = "Window" },
        Blocked = { _tag = "Blocked" },
        ClearThroughClosedDoor = { _tag = "ClosedDoor" },
    }
end

local function mk_single_target_api(opts)
    opts = opts or {}
    local first_sq = true
    return {
        capture = mk_cap,
        getSquare = function(x, y, z)
            if first_sq then
                first_sq = false
                return "sq_populated"
            end
            return "sq_floor"
        end,
        listInfo = function(sq)
            if sq == "sq_populated" then return 1, "tok" end
            return 0, "tok"
        end,
        readObject = function(sq, i)
            return { id = opts.id or "target_1", kind = opts.kind or "zombie", x = 5.0, y = 0.0, z = 0.0 }
        end,
        obstruction = opts.obstruction,
        bindings = opts.bindings,
    }
end

-- =========================================================================
-- CONSTRUCTOR & CONTRACT TESTS
-- =========================================================================

test("DiagnosticSampler - Valid instantiation and initial snapshot", function()
    local s = DiagnosticSampler.new(get_modules())
    local snap = s:snapshot()
    assert(snap.total_samples == 0 and snap.total_aborted == 0 and snap.collector_cursors == 0)
end)

test("DiagnosticSampler - Invalid constructor module configs error", function()
    local ok_nil = pcall(function() DiagnosticSampler.new(nil) end)
    assert(not ok_nil, "Expected constructor error for nil modules")
    local bad = { {}, { CandidateCollector = {} }, { CandidateCollector = CandidateCollector } }
    for _, m in ipairs(bad) do
        local ok = pcall(function() DiagnosticSampler.new(m) end)
        assert(not ok, "Expected constructor error for bad module config")
    end
end)

test("DiagnosticSampler - Invalid API configs abort without throwing", function()
    local s = DiagnosticSampler.new(get_modules())
    local r_nil = s:sample(nil)
    assert(r_nil.status == "aborted" and r_nil.reason == "invalid_api" and #r_nil.results == 0)
    local bad_apis = { 1234, "api", {}, { capture = function() end } }
    for _, ba in ipairs(bad_apis) do
        local r = s:sample(ba)
        assert(r.status == "aborted" and r.reason == "invalid_api" and #r.results == 0)
    end
end)

test("DiagnosticSampler - Malformed obstruction type returns invalid_api", function()
    local s = DiagnosticSampler.new(get_modules())
    local api_num = mk_single_target_api({ obstruction = 1234 })
    local r1 = s:sample(api_num)
    assert(r1.status == "aborted" and r1.reason == "invalid_api")
    local api_str = mk_single_target_api({ obstruction = "not_a_func" })
    local r2 = s:sample(api_str)
    assert(r2.status == "aborted" and r2.reason == "invalid_api")
end)

-- =========================================================================
-- NORMALIZER EXACT ENUMS & LIGHTING ISOLATION
-- =========================================================================

test("Obstruction - Clear exact enum yields geometric visible and visual unknown", function()
    local s = DiagnosticSampler.new(get_modules())
    local b = mk_bindings()
    local api = mk_single_target_api({
        obstruction = function() return b.Clear end,
        bindings = b,
    })
    local r = s:sample(api)
    assert(r.status == "sampled" and r.lighting == "unknown")
    assert(#r.results == 1, "Expected 1 candidate result, got " .. #r.results)
    local res = r.results[1]
    assert(res.id == "target_1" and res.geometric == "visible" and res.visual == "unknown" and res.reason == "lighting_unknown")
end)

test("Obstruction - OpenDoor exact enum yields geometric visible", function()
    local s = DiagnosticSampler.new(get_modules())
    local b = mk_bindings()
    local api = mk_single_target_api({
        obstruction = function() return b.ClearThroughOpenDoor end,
        bindings = b,
    })
    local r = s:sample(api)
    assert(#r.results == 1 and r.results[1].geometric == "visible" and r.results[1].visual == "unknown")
end)

test("Obstruction - Window exact enum yields geometric visible", function()
    local s = DiagnosticSampler.new(get_modules())
    local b = mk_bindings()
    local api = mk_single_target_api({
        obstruction = function() return b.ClearThroughWindow end,
        bindings = b,
    })
    local r = s:sample(api)
    assert(#r.results == 1 and r.results[1].geometric == "visible" and r.results[1].visual == "unknown")
end)

test("Obstruction - Blocked exact enum yields geometric blocked and visual blocked", function()
    local s = DiagnosticSampler.new(get_modules())
    local b = mk_bindings()
    local api = mk_single_target_api({
        obstruction = function() return b.Blocked end,
        bindings = b,
    })
    local r = s:sample(api)
    assert(#r.results == 1)
    assert(r.results[1].geometric == "blocked" and r.results[1].visual == "blocked" and r.results[1].reason == "obstructed")
end)

test("Obstruction - ClosedDoor exact enum yields geometric unknown", function()
    local s = DiagnosticSampler.new(get_modules())
    local b = mk_bindings()
    local api = mk_single_target_api({
        obstruction = function() return b.ClearThroughClosedDoor end,
        bindings = b,
    })
    local r = s:sample(api)
    assert(#r.results == 1 and r.results[1].geometric == "unknown" and r.results[1].reason == "obstruction_unknown")
end)

test("Obstruction - Unexpected enum string or number yields geometric unknown", function()
    local s = DiagnosticSampler.new(get_modules())
    local b = mk_bindings()
    local unexpecteds = { { _tag = "unbound" }, "Clear", 1234 }
    for _, unk in ipairs(unexpecteds) do
        local api = mk_single_target_api({
            obstruction = function() return unk end,
            bindings = b,
        })
        local r = s:sample(api)
        assert(#r.results == 1 and r.results[1].geometric == "unknown" and r.results[1].reason == "obstruction_unknown")
    end
end)

test("Obstruction - Invalid bindings table yields ZERO obstruction calls and geometric unknown", function()
    local s = DiagnosticSampler.new(get_modules())
    local obs_calls = 0
    local api = mk_single_target_api({
        obstruction = function() obs_calls = obs_calls + 1; return "Clear" end,
        bindings = { Clear = "scalar_value" }, -- invalid bindings
    })
    local r = s:sample(api)
    assert(#r.results == 1 and r.results[1].geometric == "unknown" and r.results[1].reason == "obstruction_unknown")
    assert(obs_calls == 0, "Obstruction callback must NOT be invoked when bindings are invalid")
end)

test("Lighting - Malicious api.lighting is NEVER called and visual remains unknown", function()
    local s = DiagnosticSampler.new(get_modules())
    local b = mk_bindings()
    local lighting_called = false
    local api = mk_single_target_api({
        obstruction = function() return b.Clear end,
        bindings = b,
    })
    api.lighting = function() lighting_called = true; return "detectable" end
    local r = s:sample(api)
    assert(not lighting_called, "api.lighting must NEVER be queried")
    assert(r.results[1].visual == "unknown" and r.results[1].reason == "lighting_unknown")
    assert(r.results[1].position == nil, "Position must never be published without confirmed visual detection")
end)

test("Knowledge Isolation - Positive geometric visible target produces ZERO records in Knowledge", function()
    local s = DiagnosticSampler.new(get_modules())
    local b = mk_bindings()
    local api = mk_single_target_api({
        obstruction = function() return b.Clear end,
        bindings = b,
    })
    local r = s:sample(api)
    assert(#r.results == 1 and r.results[1].geometric == "visible", "Must have positive visible candidate before testing Knowledge")
    local kn = Knowledge.new()
    kn:update(r, 0)
    assert(#kn:snapshot(0) == 0, "Actual Knowledge must reject unknown lighting")
end)

-- =========================================================================
-- COVERAGE INTEGRATION & SHARED 4096 BUDGET
-- =========================================================================

test("Coverage Gate - Missing coverage tile yields coverage_unknown and ZERO obstruction calls", function()
    local s = DiagnosticSampler.new(get_modules())
    local b = mk_bindings()
    local obs_calls = 0
    local first_sq = true
    local api = {
        capture = mk_cap,
        getSquare = function(x, y, z)
            if first_sq then
                first_sq = false
                return "sq_first"
            end
            if x == 2 and y == 0 then return nil end -- ray hole in coverage
            return "sq_floor"
        end,
        listInfo = function(sq)
            if sq == "sq_first" then return 1, "tok" end
            return 0, "tok"
        end,
        readObject = function() return { id = "t", kind = "zombie", x = 5.0, y = 0.0, z = 0.0 } end,
        obstruction = function() obs_calls = obs_calls + 1; return b.Clear end,
        bindings = b,
    }
    local r = s:sample(api)
    assert(#r.results == 1 and r.results[1].geometric == "unknown" and r.results[1].reason == "coverage_unknown")
    assert(obs_calls == 0, "Obstruction must not be called when coverage fails")
end)

test("Coverage Gate - Missing side halo square prevents geometric clearance", function()
    local s = DiagnosticSampler.new(get_modules())
    local b = mk_bindings()
    local first_sq = true
    local api = {
        capture = mk_cap,
        getSquare = function(x, y, z)
            if first_sq then
                first_sq = false
                return "sq_first"
            end
            if x == 5 and y == 1 then return nil end -- halo hole (+1 y)
            return "sq_floor"
        end,
        listInfo = function(sq)
            if sq == "sq_first" then return 1, "tok" end
            return 0, "tok"
        end,
        readObject = function() return { id = "t", kind = "zombie", x = 5.0, y = 0.0, z = 0.0 } end,
        obstruction = function() return b.Clear end,
        bindings = b,
    }
    local r = s:sample(api)
    assert(#r.results == 1 and r.results[1].geometric == "unknown" and r.results[1].reason == "coverage_unknown")
end)

test("Shared 4096 Coverage Budget - 32 candidates at (9.47, 9.47) observer (.99, .99) yields exact 4032 reads", function()
    local s = DiagnosticSampler.new(get_modules())
    local b = mk_bindings()
    local sq_calls = 0
    local api = {
        capture = function() return mk_cap({ x = 0.99, y = 0.99, fx = 1.0, fy = 1.0 }) end,
        getSquare = function(x, y, z)
            sq_calls = sq_calls + 1
            if sq_calls <= 2 then return "sq_pop_" .. sq_calls end
            return "sq_floor"
        end,
        listInfo = function(sq)
            if sq == "sq_pop_1" or sq == "sq_pop_2" then return 16, "tok" end
            return 0, "tok"
        end,
        readObject = function(sq, i)
            local idx = (sq == "sq_pop_1") and i or (i + 16)
            return { id = "c_" .. idx, kind = "zombie", x = 9.47, y = 9.47, z = 0.0 }
        end,
        obstruction = function() return b.Clear end,
        bindings = b,
    }
    local r = s:sample(api)
    assert(r.status == "sampled")
    assert(r.counts.candidates == 32, "Expected 32 candidates, got " .. r.counts.candidates)
    assert(r.counts.coverageReads == 4032, "Expected exactly 28 * 144 = 4032 reads, got " .. r.counts.coverageReads)
    for i = 1, 28 do
        assert(r.results[i].geometric == "visible", "Candidate " .. i .. " should be visible")
    end
    for i = 29, 32 do
        assert(r.results[i].geometric == "unknown" and r.results[i].reason == "coverage_unknown", "Candidate " .. i .. " should fail on coverage budget")
    end
end)

-- =========================================================================
-- ATTEMPTS, COUNTERS, & SCALAR ISOLATION
-- =========================================================================

test("Counter Tally - Exact external counts for squares, enumeration, coverage, objects, listInfos, captures, obstructions", function()
    local s = DiagnosticSampler.new(get_modules())
    local b = mk_bindings()
    local ext = { cap = 0, sq = 0, li = 0, ro = 0, obs = 0 }
    local first_sq = true
    local api = {
        capture = function() ext.cap = ext.cap + 1; return mk_cap() end,
        getSquare = function(x, y, z)
            ext.sq = ext.sq + 1
            if first_sq then first_sq = false; return "sq_first" end
            return "sq_floor"
        end,
        listInfo = function(sq) ext.li = ext.li + 1; return (sq == "sq_first") and 1 or 0, "tok" end,
        readObject = function() ext.ro = ext.ro + 1; return { id = "t", kind = "zombie", x = 5.0, y = 0.0, z = 0.0 } end,
        obstruction = function() ext.obs = ext.obs + 1; return b.Clear end,
        bindings = b,
    }
    local r = s:sample(api)
    assert(r.counts.captures == ext.cap)
    assert(r.counts.squares == ext.sq)
    assert(r.counts.listInfos == ext.li)
    assert(r.counts.objects == ext.ro)
    assert(r.counts.obstructions == ext.obs)
end)

test("Exception Absorption - getSquare throws during enumeration and coverage are safely caught", function()
    local s = DiagnosticSampler.new(get_modules())
    local b = mk_bindings()
    local first_sq = true
    local api = {
        capture = mk_cap,
        getSquare = function(x, y, z)
            if first_sq then first_sq = false; return "sq_first" end
            if x == 2 and y == 0 then error("THROW_SQ") end
            return "sq_floor"
        end,
        listInfo = function(sq) return (sq == "sq_first") and 1 or 0, "tok" end,
        readObject = function() return { id = "t", kind = "zombie", x = 5.0, y = 0.0, z = 0.0 } end,
        obstruction = function() return b.Clear end,
        bindings = b,
    }
    local r = s:sample(api)
    assert(r.status == "sampled")
    assert(r.results[1].geometric == "unknown")
end)

test("Exception Absorption - obstruction throw yields geometric unknown", function()
    local s = DiagnosticSampler.new(get_modules())
    local b = mk_bindings()
    local api = mk_single_target_api({
        obstruction = function() error("THROW_OBS") end,
        bindings = b,
    })
    local r = s:sample(api)
    assert(r.status == "sampled" and r.results[1].geometric == "unknown")
end)

test("Scalar Output - Results contain only primitive strings, no positions, handles, or locators", function()
    local s = DiagnosticSampler.new(get_modules())
    local b = mk_bindings()
    local api = mk_single_target_api({
        obstruction = function() return b.Clear end,
        bindings = b,
    })
    local r = s:sample(api)
    assert(#r.results == 1)
    local res = r.results[1]
    assert(res.position == nil and res.distance == nil and res.bearing == nil)
    assert(type(res.id) == "string" and type(res.kind) == "string")
    assert(type(res.geometric) == "string" and type(res.visual) == "string")
    assert(r.candidates == nil and r.anchor == nil and r.bindings == nil)
end)

test("Geometry Immutability - Mutating observer or candidate inside obstruction callback has no effect", function()
    local s = DiagnosticSampler.new(get_modules())
    local b = mk_bindings()
    local api = mk_single_target_api({
        obstruction = function(obs, cand)
            obs.x = 9999.0
            cand.x = -8888.0
            return b.Clear
        end,
        bindings = b,
    })
    local r = s:sample(api)
    assert(r.results[1].geometric == "visible")
end)

test("Binding Mutation - Mutating api.bindings during capture callback cannot inject fake enums", function()
    local s = DiagnosticSampler.new(get_modules())
    local b = mk_bindings()
    local api = mk_single_target_api({
        obstruction = function() return b.Clear end,
        bindings = b,
    })
    local orig_cap = api.capture
    api.capture = function()
        b.Clear = { _tag = "forged_enum" } -- mutate original bindings table
        return orig_cap()
    end
    local r = s:sample(api)
    -- Forged return differs from the reference frozen before capture.
    assert(r.status == "sampled" and r.results[1].geometric == "unknown")
end)

test("Collector Rotation - Cursors advance across multiple samples without modifying private state", function()
    local s = DiagnosticSampler.new(get_modules())
    local api = {
        capture = mk_cap,
        getSquare = function() return "sq" end,
        listInfo = function() return 0, "tok" end,
        readObject = function() end,
    }
    s:sample(api)
    assert(s:snapshot().total_enumeration_squares == 63)
    s:sample(api)
    assert(s:snapshot().total_enumeration_squares == 126)
end)

-- =========================================================================
-- LIFECYCLE, DRIFT, RESET, & STICKY INVALIDATION
-- =========================================================================

local drift_fields = {
    { "controller", "ctrl_new" }, { "npc", "npc_new" }, { "cell", "cell_new" }, { "generation", "gen_new" },
    { "x", 1005.0 }, { "y", 2005.0 }, { "z", 1.0 }, { "fx", -1.0 }, { "fy", 1.0 }
}
for _, df in ipairs(drift_fields) do
    test("Lifecycle Drift - Field '" .. df[1] .. "' drift aborts pass and clears results", function()
        local s = DiagnosticSampler.new(get_modules())
        local drift = false
        local api = {
            capture = function() return mk_cap(drift and { [df[1]] = df[2] } or nil) end,
            getSquare = function() drift = true; return "sq" end,
            listInfo = function() return 0, "tok" end,
            readObject = function() end,
        }
        local r = s:sample(api)
        assert(r.status == "aborted" and r.reason == "lifecycle_drift" and #r.results == 0)
    end)
end

local invalid_caps = {
    { "alive=false", { alive = false } }, { "resident=false", { resident = false } }, { "cancelled=true", { cancelled = true } },
    { "fx=0 and fy=0", { fx = 0.0, fy = 0.0 } }, { "x=NaN", { x = 0/0 } }, { "abs(x)>1e6", { x = 1e7 } },
    { "controller>96", { controller = string.rep("x", 97) } }, { "empty controller", { controller = "" } },
}
for _, ic in ipairs(invalid_caps) do
    test("Invalid Capture - " .. ic[1] .. " aborts with capture_invalid", function()
        local s = DiagnosticSampler.new(get_modules())
        local r = s:sample({ capture = function() return mk_cap(ic[2]) end, getSquare = function() end, listInfo = function() end, readObject = function() end })
        assert(r.status == "aborted" and r.reason == "capture_invalid" and #r.results == 0)
    end)
end

test("Sticky Invalidation - After drift, zero further native queries are made", function()
    local s = DiagnosticSampler.new(get_modules())
    local queries_after_drift = 0
    local drifted = false
    local api = {
        capture = function()
            if drifted then queries_after_drift = queries_after_drift + 1 end
            return mk_cap(drifted and { generation = "g_drift" } or nil)
        end,
        getSquare = function()
            drifted = true
            return "sq"
        end,
        listInfo = function() return 0, "t" end,
        readObject = function() end,
    }
    local r = s:sample(api)
    assert(r.status == "aborted" and r.reason == "lifecycle_drift")
    assert(queries_after_drift <= 1, "Zero further queries permitted after invalidation")
end)

test("Reset in Callback - Initial capture reset aborts and stays reset", function()
    local s = DiagnosticSampler.new(get_modules())
    local r = s:sample({ capture = function() s:reset(); return mk_cap() end, getSquare = function() end, listInfo = function() end, readObject = function() end })
    assert(r.status == "aborted" and r.reason == "reset_during_collect" and #r.results == 0)
end)

test("Reset in Callback - Enumeration getSquare reset aborts and stays reset", function()
    local s = DiagnosticSampler.new(get_modules())
    local r = s:sample({
        capture = mk_cap,
        getSquare = function() s:reset(); return "sq" end,
        listInfo = function() return 0, "t" end,
        readObject = function() end,
    })
    assert(r.status == "aborted" and r.reason == "reset_during_collect" and #r.results == 0)
end)

test("Reset in Callback - Enumeration getSquare after listInfo reset aborts", function()
    local s = DiagnosticSampler.new(get_modules())
    local b = mk_bindings()
    local in_cov = false
    local first_sq = true
    local api = {
        capture = mk_cap,
        getSquare = function(x, y, z)
            if in_cov then s:reset(); return "sq" end
            if first_sq then first_sq = false; return "sq_pop" end
            return "sq_floor"
        end,
        listInfo = function(sq) in_cov = true; return (sq == "sq_pop") and 1 or 0, "t" end,
        readObject = function() return { id = "t", kind = "zombie", x = 5.0, y = 0.0, z = 0.0 } end,
        obstruction = function() return b.Clear end,
        bindings = b,
    }
    local r = s:sample(api)
    assert(r.status == "aborted" and r.reason == "reset_during_collect" and #r.results == 0)
end)

test("Reset in Callback - Obstruction query reset aborts and stays reset", function()
    local s = DiagnosticSampler.new(get_modules())
    local b = mk_bindings()
    local api = mk_single_target_api({
        obstruction = function() s:reset(); return b.Clear end,
        bindings = b,
    })
    local r = s:sample(api)
    assert(r.status == "aborted" and r.reason == "reset_during_collect" and #r.results == 0)
end)

test("Final Capture Drift - Discards results and resets collector", function()
    local s_dry = DiagnosticSampler.new(get_modules())
    local b = mk_bindings()
    local dry_calls = 0
    local api_dry = mk_single_target_api({
        obstruction = function() return b.Clear end,
        bindings = b,
    })
    local orig_cap = api_dry.capture
    api_dry.capture = function() dry_calls = dry_calls + 1; return orig_cap() end
    s_dry:sample(api_dry)

    local s = DiagnosticSampler.new(get_modules())
    local calls = 0
    local api = mk_single_target_api({
        obstruction = function() return b.Clear end,
        bindings = b,
    })
    api.capture = function()
        calls = calls + 1
        return mk_cap((calls == dry_calls) and { cell = "cell_drift" } or nil)
    end
    local r = s:sample(api)
    assert(r.status == "aborted" and r.reason == "lifecycle_drift" and #r.results == 0)
end)

test("Reentrancy - Fails closed with reentrancy_rejected and makes ZERO queries", function()
    local s = DiagnosticSampler.new(get_modules())
    local reentrant_res = nil
    local api = {
        capture = mk_cap,
        getSquare = function()
            reentrant_res = s:sample({ capture = mk_cap, getSquare = function() end, listInfo = function() end, readObject = function() end })
            return nil
        end,
        listInfo = function() return 0, "t" end,
        readObject = function() end,
    }
    local r = s:sample(api)
    assert(reentrant_res.status == "reentrancy_rejected" and reentrant_res.reason == "reentrant_call")
    assert(reentrant_res.counts.captures == 0 and reentrant_res.counts.squares == 0)
    assert(r.status == "sampled")
end)

test("Reentrancy Lock - Released after error or abort, allowing subsequent sample to succeed", function()
    local s = DiagnosticSampler.new(get_modules())
    local r1 = s:sample({ capture = function() error("CAP_ERR") end, getSquare = function() end, listInfo = function() end, readObject = function() end })
    assert(r1.status == "aborted")
    local r2 = s:sample({ capture = mk_cap, getSquare = function() return nil end, listInfo = function() return 0, "t" end, readObject = function() end })
    assert(r2.status == "sampled", "Lock must be cleanly released")
end)

test("Hard Bounds - Squares cap 4160 and captures cap 512 strictly enforced", function()
    local s = DiagnosticSampler.new(get_modules())
    local api = {
        capture = mk_cap,
        getSquare = function() return "sq" end,
        listInfo = function() return 0, "t" end,
        readObject = function() end,
    }
    local r = s:sample(api)
    assert(r.counts.squares <= 4160, "Squares must be <= 4160")
    assert(r.counts.captures <= 512, "Captures must be <= 512")
end)

test("Private Field Tampering - Fake underscore assignments do not affect snapshot or caps", function()
    local s = DiagnosticSampler.new(get_modules())
    s._busy = true
    s._revision = 9999
    local snap = s:snapshot()
    snap.total_samples = 9999
    assert(s:snapshot().total_samples == 0)
    local r = s:sample({ capture = mk_cap, getSquare = function() return nil end, listInfo = function() return 0, "t" end, readObject = function() end })
    assert(r.status == "sampled" and s:snapshot().total_samples == 1)
end)


-- Codex review regressions: exercise actual stages and failure cleanup.
for _, stage in ipairs({"listInfo", "readObject"}) do
    test("Reset in " .. stage .. " prevents later queries", function()
        local sampler = DiagnosticSampler.new(get_modules())
        local api = mk_single_target_api()
        local old = api[stage]
        local calls = 0
        api[stage] = function(...)
            calls = calls + 1
            sampler:reset()
            return old(...)
        end
        local r = sampler:sample(api)
        assert(calls == 1 and r.status == "aborted" and #r.results == 0)
        assert(sampler:snapshot().collector_cursors == 0)
    end)
end

test("Coverage reset happens after successful enumeration and stops square reads", function()
    local sampler = DiagnosticSampler.new(get_modules())
    local modules = get_modules()
    local in_coverage = false
    modules.Coverage = {newContext = function(config)
        local ctx = Coverage.newContext(config)
        return {check = function(self, ...)
            in_coverage = true
            return ctx:check(...)
        end}
    end}
    sampler = DiagnosticSampler.new(modules)
    local api = mk_single_target_api()
    local old = api.getSquare
    local coverage_calls = 0
    api.getSquare = function(...)
        if in_coverage then coverage_calls = coverage_calls + 1; sampler:reset() end
        return old(...)
    end
    local r = sampler:sample(api)
    assert(coverage_calls == 1 and r.counts.coverageReads == 1)
    assert(r.counts.objects == 1 and r.status == "aborted" and #r.results == 0)
    assert(sampler:snapshot().collector_cursors == 0)
end)

test("Unexpected coverage factory failure clears committed cursors and releases lock", function()
    local modules = get_modules()
    local fail = true
    modules.Coverage = {newContext = function(config)
        if fail then error("factory failure") end
        return Coverage.newContext(config)
    end}
    local sampler = DiagnosticSampler.new(modules)
    local r = sampler:sample(mk_single_target_api())
    assert(r.status == "aborted" and r.reason == "internal_error")
    assert(sampler:snapshot().collector_cursors == 0)
    fail = false
    assert(sampler:sample(mk_single_target_api()).status == "sampled")
end)

test("Cleanup failure aborts with empty output and releases lock", function()
    local modules = get_modules()
    local fail = true
    modules.ObstructionNormalizer = {new = function(bindings)
        local n = ObstructionNormalizer.new(bindings)
        return {snapshot = function() return n:snapshot() end,
            normalize = function(self, ...) return n:normalize(...) end,
            invalidate = function() n:invalidate(); if fail then error("cleanup") end end}
    end}
    local sampler = DiagnosticSampler.new(modules)
    local r = sampler:sample(mk_single_target_api())
    assert(r.status == "aborted" and r.reason == "cleanup_error" and #r.results == 0)
    assert(sampler:snapshot().collector_cursors == 0)
    assert(sampler:snapshot().total_samples == 0 and sampler:snapshot().total_aborted == 1)
    fail = false
    assert(sampler:sample(mk_single_target_api()).status == "sampled")
end)

test("Geometry rejected candidates cause zero coverage and obstruction calls", function()
    local sampler = DiagnosticSampler.new(get_modules())
    local api = mk_single_target_api()
    api.readObject = function() return {id="behind",kind="zombie",x=-5,y=0,z=0} end
    local r = sampler:sample(api)
    assert(r.status == "sampled" and #r.results == 1)
    assert(r.counts.coverageReads == 0 and r.counts.obstructions == 0)
end)

test("API function replacements in first capture do not replace frozen callbacks", function()
    local sampler = DiagnosticSampler.new(get_modules())
    local api = mk_single_target_api()
    local old = api.capture
    local swaps = 0
    api.capture = function()
        swaps = swaps + 1
        api.getSquare = function() error("replacement queried") end
        api.capture = function() error("replacement capture queried") end
        return old()
    end
    local r = sampler:sample(api)
    assert(r.status == "sampled" and swaps == r.counts.captures and r.counts.objects == 1)
end)
print(string.format("RESULT %d sampler checks passed", tests_passed))

""")
