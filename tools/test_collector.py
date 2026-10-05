"""Gemini-authored actual-Lua collector fixtures with Codex review corrections.
No native integration or gameplay acceptance is implied.
"""
from pathlib import Path
import sys

root = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(root / "tools/dependencies/python"))
from lupa import LuaRuntime

lua = LuaRuntime(unpack_returned_tuples=True)
for name in ("Perception", "Knowledge"):
    lua.globals()[name] = lua.execute((root / f"foundation/SarahFoundation/42/media/lua/client/Sarah/{name}.lua").read_text(encoding="utf-8"))
lua.globals().Collector = lua.execute((root / "foundation/SarahFoundation/42/media/lua/client/Sarah/CandidateCollector.lua").read_text(encoding="utf-8"))
lua.execute(r"""
local tests_passed = 0
local function test(name, fn)
    local ok, err = pcall(fn)
    if not ok then error("\n[FAIL] " .. name .. "\n" .. tostring(err)) end
    tests_passed = tests_passed + 1
    print("PASS " .. name)
end
local function mk_cap(o)
    local b = { controller = "c1", npc = "n1", cell = "cell_0", generation = "g1", alive = true, resident = true, cancelled = false,
                x = 1000.0, y = 2000.0, z = 0.0, fx = 1.0, fy = 0.0 }
    if o then for k, v in pairs(o) do b[k] = v end end
    return b
end
test("Budgets - Nil grid 64 squares 130 captures and 64 missing_square", function()
    local c = Collector.new()
    local r = c:collect({ capture = mk_cap, getSquare = function() return nil end, listInfo = function() return 0, "t" end, readObject = function() end })
    assert(r.status == "completed" and r.incomplete == true and r.counts.squares == 64 and r.counts.captures == 130 and r.counts.missing_square == 64)
end)
test("Budgets - Empty grid stops at 63 squares 254 captures on preflight reservation", function()
    local c = Collector.new()
    local r = c:collect({ capture = mk_cap, getSquare = function() return "sq" end, listInfo = function() return 0, "t" end, readObject = function() end })
    assert(r.status == "budget_exhausted" and r.reason == "capture_limit_reached" and r.counts.squares == 63 and r.counts.captures == 254)
end)
test("Rotation Fairness - All 48 distinct IDs seen across 50 passes without hardcoded numbers", function()
    local c = Collector.new()
    local seen = {}
    local api = {
        capture = mk_cap,
        getSquare = function(x, y) return (x == 1000 and y == 2000) and "center" or nil end,
        listInfo = function(sq) return (sq == "center") and 48 or 0, "tok_dense" end,
        readObject = function(sq, i) return { id = "z_" .. i, kind = "zombie", x = 1000.0, y = 2000.0, z = 0.0 } end,
    }
    for p = 1, 50 do
        local res = c:collect(api)
        assert(res.counts.objects <= 16, "Per-list visit cap exceeded")
        for _, cand in ipairs(res.candidates) do seen[cand.id] = true end
    end
    local distinct = 0; for _ in pairs(seen) do distinct = distinct + 1 end
    assert(distinct == 48, "Expected all 48 distinct IDs seen, got " .. distinct)
end)
test("Cursor FIFO Cap - Reaches 64 in 40 passes and remains 64 after further passes", function()
    local c = Collector.new()
    local api = { capture = mk_cap, getSquare = function() return "sq" end, listInfo = function() return 20, "tok" end,
                  readObject = function(s, i) return { id = "z_" .. i, kind = "zombie", x = 1000.0, y = 2000.0, z = 0.0 } end }
    for p = 1, 40 do c:collect(api) end
    assert(c:snapshot().active_cursors == 64, "Active cursors should reach 64")
    for p = 1, 5 do c:collect(api) end
    assert(c:snapshot().active_cursors == 64, "Active cursors must remain bounded at 64")
end)
test("Partial-Read Resume - 3 populated squares advance to (last_committed + 1) % size", function()
    local c = Collector.new()
    local reads_by_coord = {}
    local api = {
        capture = mk_cap,
        getSquare = function(x, y)
            if x >= 988 and x <= 990 and y == 1988 then return x .. "," .. y end
            return nil
        end,
        listInfo = function(sq) return 20, "tok_20" end,
        readObject = function(sq, i)
            if not reads_by_coord[sq] then reads_by_coord[sq] = {} end
            table.insert(reads_by_coord[sq], i)
            return { id = "shared_" .. i, kind = "zombie", x = 1000.0, y = 2000.0, z = 0.0 }
        end,
    }
    c:collect(api)
    assert(#reads_by_coord["988,1988"] == 16 and #reads_by_coord["989,1988"] == 16)
    assert(#reads_by_coord["990,1988"] == 8, "Third list must be a real partial visit")
    for p = 2, 40 do c:collect(api) end
    for sq, indices in pairs(reads_by_coord) do
        assert(#indices >= 20, "Every populated square must receive subsequent visits")
        for i = 1, #indices do
            assert(indices[i] == (i - 1) % 20, "Resume skipped an unread item for " .. sq)
        end
    end
end)
test("Shrink Before Access - Per-visit shrink discards candidates and resets next stable visit", function()
    local c = Collector.new()
    local li_call = 0
    local api = {
        capture = mk_cap,
        getSquare = function(x, y) return (x == 1000 and y == 2000) and "sq" or nil end,
        listInfo = function() li_call = li_call + 1; return (li_call == 1) and 30 or 2, "tok" end,
        readObject = function() error("SHOULD_NOT_BE_CALLED") end,
    }
    local r = nil
    for p = 1, 5 do
        li_call = 0
        local res = c:collect(api)
        if res.counts.list_infos > 0 then r = res end
    end
    assert(r and r.counts.objects == 0 and r.counts.candidates == 0 and r.counts.list_changed > 0)
end)
test("Size Shrink Between Passes - Modulo saved index 16 % 10 = 6", function()
    local c = Collector.new()
    local sz = 30
    local first_idx = nil
    local api = {
        capture = mk_cap,
        getSquare = function(x, y) return (x == 1000 and y == 2000) and "sq" or nil end,
        listInfo = function() return sz, "tok_shrink" end,
        readObject = function(sq, i) if not first_idx then first_idx = i end; return { id = "z_" .. i, kind = "zombie", x = 1000.0, y = 2000.0, z = 0.0 } end,
    }
    for p = 1, 5 do c:collect(api) end
    sz, first_idx = 10, nil
    for p = 6, 15 do c:collect(api) end
    assert(first_idx == 6, "Expected 16 % 10 = 6 as first read index after shrink, got " .. tostring(first_idx))
end)
test("Token Replacement - Next visit resets index to 0", function()
    local c = Collector.new()
    local tok = "tok_v1"
    local first_idx = nil
    local api = {
        capture = mk_cap,
        getSquare = function(x, y) return (x == 1000 and y == 2000) and "sq" or nil end,
        listInfo = function() return 30, tok end,
        readObject = function(sq, i) if not first_idx then first_idx = i end; return { id = "z_" .. i, kind = "zombie", x = 1000.0, y = 2000.0, z = 0.0 } end,
    }
    for p = 1, 5 do c:collect(api) end
    tok, first_idx = "tok_v2", nil
    for p = 6, 15 do c:collect(api) end
    assert(first_idx == 0, "Token replacement must restart at index 0")
end)
test("Mutation Post-read - Token mutation clears square candidates", function()
    local c = Collector.new()
    local mut = false
    local api = {
        capture = mk_cap,
        getSquare = function(x, y) return (x == 1000 and y == 2000) and "sq" or nil end,
        listInfo = function() return 20, mut and "tok_mut" or "tok_init" end,
        readObject = function() mut = true; return { id = "z1", kind = "zombie", x = 1000.0, y = 2000.0, z = 0.0 } end,
    }
    local r = nil; for p = 1, 5 do local res = c:collect(api); if res.counts.objects > 0 then r = res end end
    assert(r and r.counts.candidates == 0 and r.counts.list_changed > 0)
end)
test("Candidate Cap 32 - Duplicate items in list do not fill cap prematurely and distinct reach 32", function()
    local c = Collector.new()
    local sq_n = 0
    local api = {
        capture = mk_cap,
        getSquare = function() sq_n = sq_n + 1; return (sq_n <= 4) and "sq_" .. sq_n or nil end,
        listInfo = function(sq) return sq == "sq_1" and 2 or 16, "t" end,
        readObject = function(sq, i) return { id = (sq == "sq_1") and "same_id" or (sq .. "_" .. i), kind = "zombie", x = 1000.0, y = 2000.0, z = 0.0 } end,
    }
    local res = c:collect(api)
    assert(res.counts.candidates == 32 and res.status == "budget_exhausted" and res.reason == "candidate_limit_reached")
end)
test("External Counter Tally - Exact match of callback attempts against return counts", function()
    local c = Collector.new()
    local ext = { cap = 0, sq = 0, li = 0, ro = 0 }
    local api = {
        capture = function() ext.cap = ext.cap + 1; return mk_cap() end,
        getSquare = function() ext.sq = ext.sq + 1; return "sq" end,
        listInfo = function() ext.li = ext.li + 1; return 1, "t" end,
        readObject = function() ext.ro = ext.ro + 1; return { id = "z", kind = "zombie", x = 1000.0, y = 2000.0, z = 0.0 } end,
    }
    local r = c:collect(api)
    assert(r.counts.squares == ext.sq and r.counts.captures == ext.cap and r.counts.list_infos == ext.li and r.counts.objects == ext.ro)
end)
test("Query Errors - getSquare error increments query_error", function()
    local c = Collector.new()
    local r = c:collect({ capture = mk_cap, getSquare = function() error("SQ_ERR") end, listInfo = function() end, readObject = function() end })
    assert(r.counts.query_error == 64)
end)
test("Query Errors - listInfo error increments query_error", function()
    local c = Collector.new()
    local r = c:collect({ capture = mk_cap, getSquare = function() return "sq" end, listInfo = function() error("LI_ERR") end, readObject = function() end })
    assert(r.counts.query_error == 63)
end)
test("False Square - Increments missing_square and makes zero list calls", function()
    local c = Collector.new()
    local li_called = false
    local r = c:collect({ capture = mk_cap, getSquare = function() return false end, listInfo = function() li_called = true; return 1, "t" end, readObject = function() end })
    assert(r.counts.missing_square == 64 and not li_called)
end)
local list_invalids = {
    { "NaN size", 0/0, "t" }, { "Fraction size", 2.5, "t" }, { "Negative size", -1, "t" },
    { "Huge size", 1e7, "t" }, { "Empty token", 10, "" }, { "Token > 96", 10, string.rep("x", 97) }
}
for _, li in ipairs(list_invalids) do
    test("Malformed List - " .. li[1] .. " increments invalid_list", function()
        local c = Collector.new()
        local r = c:collect({ capture = mk_cap, getSquare = function() return "sq" end, listInfo = function() return li[2], li[3] end, readObject = function() end })
        assert(r.counts.invalid_list > 0)
    end)
end
local cand_invalids = {
    { "Empty ID", { id = "", kind = "zombie", x = 1000.0, y = 2000.0, z = 0.0 } },
    { "ID > 96", { id = string.rep("a", 97), kind = "zombie", x = 1000.0, y = 2000.0, z = 0.0 } },
    { "Unsupported kind", { id = "z", kind = "alien", x = 1000.0, y = 2000.0, z = 0.0 } },
    { "NaN coord", { id = "z", kind = "zombie", x = 0/0, y = 2000.0, z = 0.0 } },
    { "Coord > 1e6", { id = "z", kind = "zombie", x = 1e7, y = 2000.0, z = 0.0 } },
    { "Floor mismatch", { id = "z", kind = "zombie", x = 1000.0, y = 2000.0, z = 1.0 } },
    { "Radius > 12.0", { id = "z", kind = "zombie", x = 1012.001, y = 2000.0, z = 0.0 } },
}
for _, ci in ipairs(cand_invalids) do
    test("Candidate Rejection - " .. ci[1] .. " is rejected", function()
        local c = Collector.new()
        local api = { capture = mk_cap, getSquare = function(x, y) return (x == 1000 and y == 2000) and "sq" or nil end,
                      listInfo = function() return 1, "t" end, readObject = function() return ci[2] end }
        local r = nil; for p = 1, 5 do r = c:collect(api) end
        assert(r and #r.candidates == 0)
    end)
end
test("Candidate Acceptance - Exact radius 12.0 boundary and negative floor accepted", function()
    local c = Collector.new()
    local api = {
        capture = function() return mk_cap({ x = -100.0, y = -100.0, z = -2.5 }) end,
        getSquare = function(x, y) return (x == -100 and y == -100) and "sq" or nil end,
        listInfo = function() return 1, "t" end,
        readObject = function() return { id = "valid_edge", kind = "zombie", x = -88.0, y = -100.0, z = -2.9 } end,
    }
    local r = nil; for p = 1, 5 do r = c:collect(api) end
    assert(r and #r.candidates == 1 and r.candidates[1].id == "valid_edge")
end)
local drift_fields = {
    { "controller", "ctrl_new" }, { "npc", "npc_new" }, { "cell", "cell_new" }, { "generation", "gen_new" },
    { "x", 1005.0 }, { "y", 2005.0 }, { "z", 1.0 }, { "fx", -1.0 }, { "fy", 1.0 }
}
for _, df in ipairs(drift_fields) do
    test("Lifecycle Drift - Valid field '" .. df[1] .. "' drift aborts with lifecycle_drift", function()
        local drift = false
        local c = Collector.new()
        local api = {
            capture = function() return mk_cap(drift and { [df[1]] = df[2] } or nil) end,
            getSquare = function() drift = true; return "sq" end,
            listInfo = function() return 0, "t" end, readObject = function() end,
        }
        local res = c:collect(api)
        assert(res.status == "aborted" and res.reason == "lifecycle_drift" and c:snapshot().offset_cursor == 1)
    end)
end
local invalid_caps = {
    { "alive=false", { alive = false } }, { "resident=false", { resident = false } }, { "cancelled=true", { cancelled = true } },
    { "fx=0 and fy=0", { fx = 0.0, fy = 0.0 } }, { "x=NaN", { x = 0/0 } }, { "abs(x)>1e6", { x = 1e7 } },
    { "controller>96", { controller = string.rep("x", 97) } }, { "empty controller", { controller = "" } },
    { "non-string controller", { controller = 12345 } },
    { "x=infinity", { x = 1/0 } }, { "x=string", { x = "1000" } },
    { "fx beyond bound", { fx = 1e7 } }, { "fy=NaN", { fy = 0/0 } }
}
for _, ic in ipairs(invalid_caps) do
    test("Invalid Capture - " .. ic[1] .. " aborts with capture_invalid", function()
        local c = Collector.new()
        local res = c:collect({ capture = function() return mk_cap(ic[2]) end, getSquare = function() end, listInfo = function() end, readObject = function() end })
        assert(res.status == "aborted" and res.reason == "capture_invalid")
    end)
end
test("Callback Reset - INITIAL capture reset aborts with reset_during_collect", function()
    local c = Collector.new()
    local res = c:collect({ capture = function() c:reset(); return mk_cap() end, getSquare = function() end, listInfo = function() end, readObject = function() end })
    assert(res.status == "aborted" and res.reason == "reset_during_collect" and c:snapshot().offset_cursor == 1)
end)
test("Callback Reset - FINAL check reset aborts and clears cursors", function()
    local c_dry = Collector.new()
    local dry_calls = 0
    c_dry:collect({ capture = function() dry_calls = dry_calls + 1; return mk_cap() end, getSquare = function() return "sq" end, listInfo = function() return 0, "t" end, readObject = function() end })
    local c = Collector.new()
    local calls = 0
    local res = c:collect({
        capture = function()
            calls = calls + 1
            if calls == dry_calls then c:reset() end
            return mk_cap()
        end,
        getSquare = function() return "sq" end, listInfo = function() return 0, "t" end, readObject = function() end,
    })
    assert(res.status == "aborted" and res.reason == "reset_during_collect" and c:snapshot().offset_cursor == 1 and c:snapshot().active_cursors == 0)
end)
test("Callback Reset - getSquare reset aborts and clears state", function()
    local c = Collector.new()
    local res = c:collect({ capture = mk_cap, getSquare = function() c:reset(); return "sq" end, listInfo = function() return 0, "t" end, readObject = function() end })
    assert(res.status == "aborted" and res.reason == "reset_during_collect" and c:snapshot().offset_cursor == 1)
end)
test("Callback Reset - listInfo reset aborts and clears state", function()
    local c = Collector.new()
    local res = c:collect({ capture = mk_cap, getSquare = function() return "sq" end, listInfo = function() c:reset(); return 1, "t" end, readObject = function() end })
    assert(res.status == "aborted" and res.reason == "reset_during_collect" and c:snapshot().offset_cursor == 1)
end)
test("Callback Reset - readObject reset aborts and clears state", function()
    local c = Collector.new()
    local res = c:collect({
        capture = mk_cap, getSquare = function() return "sq" end, listInfo = function() return 1, "t" end,
        readObject = function() c:reset(); return { id = "z", kind = "zombie", x = 1000, y = 2000, z = 0 } end
    })
    assert(res.status == "aborted" and res.reason == "reset_during_collect" and c:snapshot().offset_cursor == 1)
end)
test("Final Lifecycle Drift - Discards staged valid candidates and rolls back offset", function()
    local c_dry = Collector.new()
    local dry_calls = 0
    c_dry:collect({ capture = function() dry_calls = dry_calls + 1; return mk_cap() end, getSquare = function() return "sq" end,
                    listInfo = function() return 1, "t" end, readObject = function() return { id = "z", kind = "zombie", x = 1000, y = 2000, z = 0 } end })
    local c = Collector.new()
    local calls = 0
    local res = c:collect({
        capture = function()
            calls = calls + 1
            return mk_cap((calls == dry_calls) and { generation = "g_drift" } or nil)
        end,
        getSquare = function() return "sq" end, listInfo = function() return 1, "t" end,
        readObject = function() return { id = "z", kind = "zombie", x = 1000, y = 2000, z = 0 } end
    })
    assert(res.status == "aborted" and res.reason == "lifecycle_drift" and #res.candidates == 0 and c:snapshot().offset_cursor == 1)
end)
test("Session Change - Aborted pass preserves previous session anchor and domain", function()
    local c = Collector.new()
    c:collect({ capture = mk_cap, getSquare = function() return nil end, listInfo = function() return 0, "t" end, readObject = function() end })
    assert(c:snapshot().offset_cursor == 65)
    local call_n = 0
    local res = c:collect({
        capture = function() call_n = call_n + 1; return mk_cap({ controller = (call_n == 1) and "new_ctrl" or "drift_ctrl" }) end,
        getSquare = function() return nil end, listInfo = function() return 0, "t" end, readObject = function() end,
    })
    assert(res.status == "aborted" and c:snapshot().offset_cursor == 65)
end)
test("Capture Error Releases Lock - Subsequent pass completes cleanly", function()
    local c = Collector.new()
    local r1 = c:collect({ capture = function() error("CAP_THROW") end, getSquare = function() end, listInfo = function() end, readObject = function() end })
    assert(r1.status == "aborted" and r1.reason == "capture_invalid")
    local r2 = c:collect({ capture = mk_cap, getSquare = function() return nil end, listInfo = function() return 0, "t" end, readObject = function() end })
    assert(r2.status == "completed", "Lock must be released after capture throw")
end)
test("API Metatable Throw - Rawget access avoids invoking API metatables", function()
    local c = Collector.new()
    local api = setmetatable({
        capture = mk_cap, getSquare = function() return nil end, listInfo = function() return 0, "t" end, readObject = function() end
    }, { __index = function() error("API_METATABLE_INVOKED") end })
    local res = c:collect(api)
    assert(res.status == "completed")
end)
test("Capture & Candidate Metatable Throw - Rawget prevents metatable invocation", function()
    local c = Collector.new()
    local toxic_cap = setmetatable(mk_cap(), { __index = function() error("CAP_METATABLE_INVOKED") end })
    local toxic_cand = setmetatable({ id = "valid_id", kind = "player", x = 1000.0, y = 2000.0, z = 0.0 }, { __index = function() error("CAND_METATABLE_INVOKED") end })
    local api = {
        capture = function() return toxic_cap end,
        getSquare = function(x, y) return (x == 1000 and y == 2000) and "sq" or nil end,
        listInfo = function() return 1, "t" end, readObject = function() return toxic_cand end,
    }
    local r = nil; for p = 1, 5 do r = c:collect(api) end
    assert(r and #r.candidates == 1 and r.candidates[1].id == "valid_id")
end)
test("Result Snapshot Immutability - Mutating return table or snapshot does not alter state", function()
    local c = Collector.new()
    local api = {
        capture = mk_cap,
        getSquare = function(x, y) return (x == 1000 and y == 2000) and "sq" or nil end,
        listInfo = function() return 1, "t" end,
        readObject = function() return { id = "z1", kind = "zombie", x = 1000.0, y = 2000.0, z = 0.0 } end,
    }
    local r = nil; for p = 1, 5 do r = c:collect(api) end
    r.candidates[1].x = 999999.0
    r.counts.squares = 9999
    local snap = c:snapshot()
    snap.total_squares = 8888
    assert(c:snapshot().total_squares == 5 * 64)
end)
test("Private Field Assignment - Fake public underscore assignments have no effect", function()
    local c = Collector.new()
    c._in_collect = true
    c._offset_cursor = 999
    c._revision = 12345
    local res = c:collect({ capture = mk_cap, getSquare = function() return nil end, listInfo = function() return 0, "t" end, readObject = function() end })
    assert(res.status == "completed" and c:snapshot().offset_cursor == 65)
end)
test("Bounds Invariant Across All Operations", function()
    local c = Collector.new()
    local api = { capture = mk_cap, getSquare = function() return "sq" end, listInfo = function() return 20, "t" end,
                  readObject = function(s, i) return { id = "z_" .. i, kind = "zombie", x = 1000.0, y = 2000.0, z = 0.0 } end }
    local res = c:collect(api)
    assert(res.counts.captures <= 256, "Captures must be <= 256")
    assert(res.counts.list_infos <= 128, "ListInfos must be <= 128")
    assert(res.counts.objects <= 128, "Objects must be <= 128")
    assert(res.counts.squares <= 64, "Squares must be <= 64")
    assert(res.counts.candidates <= 32, "Candidates must be <= 32")
end)
test("Reentrancy Lock - Fails closed and releases cleanly on all exits", function()
    local c = Collector.new()
    local reentrant_res = nil
    local api = {
        capture = mk_cap,
        getSquare = function() reentrant_res = c:collect({ capture = mk_cap, getSquare = function() end, listInfo = function() end, readObject = function() end }); return nil end,
        listInfo = function() return 0, "t" end, readObject = function() end,
    }
    local res = c:collect(api)
    assert(reentrant_res.status == "reentrancy_rejected" and res.status == "completed")
    local res2 = c:collect({ capture = mk_cap, getSquare = function() return nil end, listInfo = function() return 0, "t" end, readObject = function() end })
    assert(res2.status == "completed", "Lock must be released cleanly")
end)

test("Invalid API types refuse before any calls", function()
    local c = Collector.new()
    for _, v in ipairs({false, 1, "api", {}}) do
        local r = c:collect(v)
        assert(r.status == "aborted" and r.reason == "invalid_api" and r.counts.captures == 0)
    end
    assert(c:collect().reason == "invalid_api")
end)
test("API callbacks are copied before mid-pass replacement", function()
    local c, original = Collector.new(), 0
    local api = {}
    api.capture = mk_cap
    api.getSquare = function()
        api.readObject = function() error("replacement must not run") end
        return "square"
    end
    api.listInfo = function() return 1, "list" end
    api.readObject = function()
        original = original + 1
        return {id="z",kind="zombie",x=1000,y=2000,z=0}
    end
    local r = c:collect(api)
    assert(original > 0 and #r.candidates == 1 and r.counts.invalid_snapshot == 0)
end)
test("Missing raw capture fields never invoke toxic index access", function()
    local c, invoked = Collector.new(), false
    local api = {capture=function()
        return setmetatable({}, {__index=function() invoked=true;error("index") end})
    end,getSquare=function() error("unreachable") end,listInfo=function() end,readObject=function() end}
    local r=c:collect(api)
    assert(r.status=="aborted" and r.reason=="capture_invalid" and not invoked)
end)
test("Read failure consumes one read and discards the affected square", function()
    local c, reads=Collector.new(),0
    local r=c:collect({capture=mk_cap,getSquare=function() return {} end,
        listInfo=function() return 1,"list" end,
        readObject=function() reads=reads+1;error("unavailable") end})
    assert(reads>0 and reads==r.counts.objects and r.counts.invalid_snapshot==reads and #r.candidates==0)
end)
test("Caller pipeline retains no memory with unknown lighting", function()
    local c=Collector.new()
    local object={id="z",kind="zombie",x=1002,y=2000,z=0,handle={}}
    local r=c:collect({capture=mk_cap,getSquare=function() return {} end,
        listInfo=function() return 1,"list" end,readObject=function() return object end})
    assert(#r.candidates==1 and r.candidates[1].handle==nil)
    r.candidates[1].x=1003
    assert(object.x==1002)
    local sample=Perception.new():sample({x=1000,y=2000,z=0,forward={x=1,y=0}},r.candidates,
        {coverage=function() return true end,obstruction=function() return "clear" end})
    assert(sample.results[1].visual=="unknown" and sample.results[1].position==nil)
    local memory=Knowledge.new();memory:update(sample,0)
    assert(#memory:snapshot(0)==0)
end)

print(string.format("RESULT %d collector checks passed", tests_passed))

""")
