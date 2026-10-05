"""Actual-Lua identity and obstruction fixtures; no native engine acceptance.
Gemini base source/fixtures with Codex review corrections and regressions.
"""
from pathlib import Path
import sys
root = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(root / "tools/dependencies/python"))
from lupa import LuaRuntime
lua = LuaRuntime(unpack_returned_tuples=True)
for name in ("SessionIdentity", "ObstructionNormalizer", "Perception", "Knowledge"):
    lua.globals()[name] = lua.execute((root / f"foundation/SarahFoundation/42/media/lua/client/Sarah/{name}.lua").read_text(encoding="utf-8"))
lua.globals().opaqueFixtures = lua.table_from({
    name: object() for name in ("Clear", "ClearThroughOpenDoor", "ClearThroughWindow", "Blocked", "ClearThroughClosedDoor")
})
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

local function get_valid_bindings()
    return {
        Clear = { _tag = "Clear" },
        ClearThroughOpenDoor = { _tag = "OpenDoor" },
        ClearThroughWindow = { _tag = "Window" },
        Blocked = { _tag = "Blocked" },
        ClearThroughClosedDoor = { _tag = "ClosedDoor" },
    }
end

local function set_upval(fn, target_name, val)
    if not debug or not debug.getupvalue or not debug.setupvalue then return false end
    local i = 1
    while true do
        local n = debug.getupvalue(fn, i)
        if not n then break end
        if n == target_name then
            debug.setupvalue(fn, i, val)
            return true
        end
        i = i + 1
    end
    return false
end

-- =========================================================================
-- SESSION IDENTITY TESTS
-- =========================================================================

test("SessionIdentity - Valid instantiation and initial snapshot", function()
    local id_mgr = SessionIdentity.new("session_alpha")
    local s = id_mgr:snapshot()
    assert(s.epoch == 1 and s.issued == 0 and s.retained == 0 and s.exhausted == false)
end)

test("SessionIdentity - Invalid namespace configs error on construct", function()
    local invalids = { "", "with space", "punctuation!", "toolong_" .. string.rep("x", 26), 1234, {}, false }
    for _, inv in ipairs(invalids) do
        local ok = pcall(function() SessionIdentity.new(inv) end)
        assert(not ok, "Expected error for namespace: " .. tostring(inv))
    end
end)

test("SessionIdentity - Resolve valid new tokens for player and zombie", function()
    local id_mgr = SessionIdentity.new("s1")
    local r1 = id_mgr:resolve("tok_p", "player")
    local r2 = id_mgr:resolve("tok_z", "zombie")
    assert(r1.id == "s1:1:1" and r1.kind == "player" and r1.reason == "new")
    assert(r2.id == "s1:1:2" and r2.kind == "zombie" and r2.reason == "new")
    assert(id_mgr:snapshot().retained == 2)
end)

test("SessionIdentity - Invalid token inputs return invalid_token with no state change", function()
    local id_mgr = SessionIdentity.new("s1")
    local invalids = { "", string.rep("a", 97), 123, {}, false }
    for _, inv in ipairs(invalids) do
        local r = id_mgr:resolve(inv, "player")
        assert(r.reason == "invalid_token" and r.id == nil)
    end
    assert(id_mgr:snapshot().issued == 0 and id_mgr:snapshot().retained == 0)
end)
test("SessionIdentity - Invalid kind inputs return invalid_kind with no state change", function()
    local id_mgr = SessionIdentity.new("s1")
    local invalids = { "npc", "vehicle", "Player", "ZOMBIE", 1, {} }
    for _, inv in ipairs(invalids) do
        local r = id_mgr:resolve("tok1", inv)
        assert(r.reason == "invalid_kind" and r.id == nil)
    end
    assert(id_mgr:snapshot().issued == 0 and id_mgr:snapshot().retained == 0)
end)

test("SessionIdentity - Existing token lookup returns copied existing record", function()
    local id_mgr = SessionIdentity.new("s1")
    local r_new = id_mgr:resolve("t1", "zombie")
    local r_exist = id_mgr:resolve("t1", "zombie")
    assert(r_exist.id == r_new.id and r_exist.kind == "zombie" and r_exist.reason == "existing")
    assert(id_mgr:snapshot().issued == 1 and id_mgr:snapshot().retained == 1)
    r_exist.id = "tampered"
    local r_check = id_mgr:resolve("t1", "zombie")
    assert(r_check.id == r_new.id, "Lookup copy must be independent of internal storage")
end)

test("SessionIdentity - Kind conflict returns kind_conflict without state change", function()
    local id_mgr = SessionIdentity.new("s1")
    id_mgr:resolve("t1", "zombie")
    local r_conflict = id_mgr:resolve("t1", "player")
    assert(r_conflict.reason == "kind_conflict" and r_conflict.id == nil)
    assert(id_mgr:snapshot().issued == 1 and id_mgr:snapshot().retained == 1)
    local r_verify = id_mgr:resolve("t1", "zombie")
    assert(r_verify.reason == "existing" and r_verify.kind == "zombie")
end)

test("SessionIdentity - 64 FIFO cap evicts oldest token and bounds retained count", function()
    local id_mgr = SessionIdentity.new("s1")
    for i = 1, 64 do
        id_mgr:resolve("token_" .. i, "zombie")
    end
    assert(id_mgr:snapshot().retained == 64 and id_mgr:snapshot().issued == 64)
    local r65 = id_mgr:resolve("token_65", "zombie")
    assert(r65.id == "s1:1:65" and r65.reason == "new")
    assert(id_mgr:snapshot().retained == 64, "Retained count must stay capped at 64")
end)

test("SessionIdentity - No FIFO renewal on lookup ensures strictly oldest eviction", function()
    local id_mgr = SessionIdentity.new("s1")
    id_mgr:resolve("first_token", "player")
    for i = 2, 64 do
        id_mgr:resolve("token_" .. i, "zombie")
    end
    for _ = 1, 5 do
        local r = id_mgr:resolve("first_token", "player")
        assert(r.reason == "existing")
    end
    id_mgr:resolve("token_65", "zombie")
    local r_first = id_mgr:resolve("first_token", "player")
    assert(r_first.reason == "new" and r_first.id == "s1:1:66", "Oldest must be evicted despite prior lookups")
end)

test("SessionIdentity - Evicted token seen again gets new ID and never reuses old ID", function()
    local id_mgr = SessionIdentity.new("s1")
    local first_res = id_mgr:resolve("recycled_token", "player")
    assert(first_res.id == "s1:1:1")
    for i = 2, 65 do
        id_mgr:resolve("filler_" .. i, "zombie")
    end
    local second_res = id_mgr:resolve("recycled_token", "player")
    assert(second_res.reason == "new")
    assert(second_res.id == "s1:1:66", "Re-resolved token must get a strictly fresh sequence ID")
    assert(second_res.id ~= first_res.id)
end)

test("SessionIdentity - Reset clears map, increments epoch, and resets sequence", function()
    local id_mgr = SessionIdentity.new("s1")
    id_mgr:resolve("tok_a", "player")
    id_mgr:resolve("tok_b", "zombie")
    id_mgr:reset()
    local snap = id_mgr:snapshot()
    assert(snap.epoch == 2 and snap.issued == 0 and snap.retained == 0 and snap.exhausted == false)
    local r_new = id_mgr:resolve("tok_a", "player")
    assert(r_new.id == "s1:2:1" and r_new.reason == "new")
end)

test("SessionIdentity - Multiple resets advance epoch monotonically", function()
    local id_mgr = SessionIdentity.new("s_multi")
    for ep = 1, 5 do
        assert(id_mgr:snapshot().epoch == ep)
        id_mgr:resolve("t", "zombie")
        id_mgr:reset()
    end
    assert(id_mgr:snapshot().epoch == 6)
end)

test("SessionIdentity - Instances with distinct namespaces are strictly independent", function()
    local id1 = SessionIdentity.new("ns_one")
    local id2 = SessionIdentity.new("ns_two")
    local r1 = id1:resolve("common_tok", "player")
    local r2 = id2:resolve("common_tok", "player")
    assert(r1.id == "ns_one:1:1" and r2.id == "ns_two:1:1")
    assert(r1.id ~= r2.id)
end)

test("SessionIdentity - Private counter tampering via instance fields has no effect", function()
    local id_mgr = SessionIdentity.new("s1")
    id_mgr._epoch = 999
    id_mgr._sequence = 9999
    id_mgr._exhausted = true
    local r = id_mgr:resolve("t1", "player")
    assert(r.id == "s1:1:1" and r.reason == "new")
    local s = id_mgr:snapshot()
    assert(s.epoch == 1 and s.issued == 1 and s.exhausted == false)
end)

test("SessionIdentity - Snapshot copy immutability", function()
    local id_mgr = SessionIdentity.new("s1")
    local s1 = id_mgr:snapshot()
    s1.epoch = 999
    s1.issued = 888
    s1.retained = 777
    s1.exhausted = true
    local s2 = id_mgr:snapshot()
    assert(s2.epoch == 1 and s2.issued == 0 and s2.retained == 0 and s2.exhausted == false)
end)

test("SessionIdentity - Scalar handle-free output", function()
    local id_mgr = SessionIdentity.new("s_scalar")
    local res = id_mgr:resolve("sample_tok", "zombie")
    for k, v in pairs(res) do
        assert(type(k) == "string" and type(v) == "string", "Output must contain only primitive strings")
    end
end)

test("SessionIdentity - Sequence overflow at 2^31-1 fails closed to exhausted", function()
    local id_mgr = SessionIdentity.new("s_overflow")
    local hooked = set_upval(id_mgr.resolve, "sequence", 2147483646)
    assert(hooked, "Offline debug hook must be available; cannot count a skipped overflow test")
    if hooked then
        local r_max = id_mgr:resolve("tok_max", "player")
        assert(r_max.id == "s_overflow:1:2147483647" and r_max.reason == "new")
        local r_over = id_mgr:resolve("tok_overflow", "player")
        assert(r_over.reason == "exhausted" and r_over.id == nil)
        local snap = id_mgr:snapshot()
        assert(snap.exhausted == true and snap.retained == 0)
        local r_after = id_mgr:resolve("any_tok", "player")
        assert(r_after.reason == "exhausted")
        id_mgr:reset()
        assert(id_mgr:snapshot().exhausted == true, "Reset cannot revive exhausted instance")
    else
        print("SKIP: debug.setupvalue unavailable in this runtime")
    end
end)

test("SessionIdentity - Epoch overflow at 2^31-1 fails closed to exhausted", function()
    local id_mgr = SessionIdentity.new("s_epoch_overflow")
    local hooked = set_upval(id_mgr.resolve, "epoch", 2147483647)
    assert(hooked, "Offline debug hook must be available; cannot count a skipped overflow test")
    if hooked then
        id_mgr:reset()
        local snap = id_mgr:snapshot()
        assert(snap.exhausted == true and snap.epoch == 2147483647)
        local r = id_mgr:resolve("t", "zombie")
        assert(r.reason == "exhausted")
    else
        print("SKIP: debug.setupvalue unavailable in this runtime")
    end
end)

-- =========================================================================
-- OBSTRUCTION NORMALIZER TESTS
-- =========================================================================

test("ObstructionNormalizer - Valid bindings construction and snapshot", function()
    local b = get_valid_bindings()
    local norm = ObstructionNormalizer.new(b)
    local s = norm:snapshot()
    assert(s.valid == true and s.bound == 5)
end)

test("ObstructionNormalizer - Invalid bindings rejection on non-table or missing keys", function()
    local bad_bindings = {
        123,
        "string_bindings",
        {},
        { Clear = {} },
        { Clear = {}, ClearThroughOpenDoor = {}, ClearThroughWindow = {}, Blocked = {} },
    }
    for _, bb in ipairs(bad_bindings) do
        local norm = ObstructionNormalizer.new(bb)
        assert(norm:snapshot().valid == false and norm:snapshot().bound == 0)
        local r = norm:normalize({}, true)
        assert(r.status == "unknown" and r.reason == "invalid_bindings")
    end
end)
test("ObstructionNormalizer - Scalar and non-reference values reject configuration", function()
    local scalar_cases = { "Clear", 1, false, function() end }
    for _, sc in ipairs(scalar_cases) do
        local b = get_valid_bindings()
        b.Clear = sc
        local norm = ObstructionNormalizer.new(b)
        assert(norm:snapshot().valid == false)
        local r = norm:normalize({}, true)
        assert(r.status == "unknown" and r.reason == "invalid_bindings")
    end
end)

test("ObstructionNormalizer - Duplicate references reject configuration via rawequal", function()
    local b = get_valid_bindings()
    local shared_ref = { _tag = "duplicate" }
    b.Clear = shared_ref
    b.Blocked = shared_ref
    local norm = ObstructionNormalizer.new(b)
    assert(norm:snapshot().valid == false and norm:snapshot().bound == 0)
    local r = norm:normalize(shared_ref, true)
    assert(r.status == "unknown" and r.reason == "invalid_bindings")
end)

test("ObstructionNormalizer - Normalize Clear returns clear/clear", function()
    local b = get_valid_bindings()
    local norm = ObstructionNormalizer.new(b)
    local r = norm:normalize(b.Clear, true)
    assert(r.status == "clear" and r.reason == "clear")
end)

test("ObstructionNormalizer - Normalize ClearThroughOpenDoor returns clear/open_door", function()
    local b = get_valid_bindings()
    local norm = ObstructionNormalizer.new(b)
    local r = norm:normalize(b.ClearThroughOpenDoor, true)
    assert(r.status == "clear" and r.reason == "open_door")
end)

test("ObstructionNormalizer - Normalize ClearThroughWindow returns clear/window", function()
    local b = get_valid_bindings()
    local norm = ObstructionNormalizer.new(b)
    local r = norm:normalize(b.ClearThroughWindow, true)
    assert(r.status == "clear" and r.reason == "window")
end)

test("ObstructionNormalizer - Normalize Blocked returns blocked/blocked", function()
    local b = get_valid_bindings()
    local norm = ObstructionNormalizer.new(b)
    local r = norm:normalize(b.Blocked, true)
    assert(r.status == "blocked" and r.reason == "blocked")
end)

test("ObstructionNormalizer - Normalize ClearThroughClosedDoor returns unknown/closed_door", function()
    local b = get_valid_bindings()
    local norm = ObstructionNormalizer.new(b)
    local r = norm:normalize(b.ClearThroughClosedDoor, true)
    assert(r.status == "unknown" and r.reason == "closed_door")
end)

test("ObstructionNormalizer - Coverage false or non-boolean returns coverage_unknown", function()
    local b = get_valid_bindings()
    local norm = ObstructionNormalizer.new(b)
    local non_trues = { false, 1, 0, "true", {}, function() end }
    for _, cv in ipairs(non_trues) do
        local r = norm:normalize(b.Clear, cv)
        assert(r.status == "unknown" and r.reason == "coverage_unknown")
        local r_blk = norm:normalize(b.Blocked, cv)
        assert(r_blk.status == "unknown" and r_blk.reason == "coverage_unknown")
    end
end)

test("ObstructionNormalizer - Unexpected results return unknown_result", function()
    local b = get_valid_bindings()
    local norm = ObstructionNormalizer.new(b)
    local unexpecteds = { "Clear", "Blocked", 0, 1, 99, {}, { _tag = "Clear" } }
    for _, unk in ipairs(unexpecteds) do
        local r = norm:normalize(unk, true)
        assert(r.status == "unknown" and r.reason == "unknown_result")
    end
end)

test("ObstructionNormalizer - Cloned table with identical fields fails rawequal", function()
    local b = get_valid_bindings()
    local norm = ObstructionNormalizer.new(b)
    local clone = { _tag = b.Clear._tag }
    local r = norm:normalize(clone, true)
    assert(r.status == "unknown" and r.reason == "unknown_result", "Table clones must not match rawequal")
end)

test("ObstructionNormalizer - Forged table with metamethods does not invoke metamethods", function()
    local b = get_valid_bindings()
    local norm = ObstructionNormalizer.new(b)
    local forged = setmetatable({}, {
        __eq = function() return true end,
        __index = function() error("FORGED_INDEX_INVOKED") end,
        __tostring = function() error("FORGED_TOSTRING_INVOKED") end,
    })
    local r = norm:normalize(forged, true)
    assert(r.status == "unknown" and r.reason == "unknown_result")
end)

test("ObstructionNormalizer - Bindings table metamethods not invoked during construction", function()
    local toxic_bindings = setmetatable(get_valid_bindings(), {
        __index = function() error("BINDINGS_INDEX_INVOKED") end,
    })
    local norm = ObstructionNormalizer.new(toxic_bindings)
    assert(norm:snapshot().valid == true and norm:snapshot().bound == 5)
end)

test("ObstructionNormalizer - Invalidate clears references and normalizer becomes invalid", function()
    local b = get_valid_bindings()
    local norm = ObstructionNormalizer.new(b)
    assert(norm:snapshot().valid == true)
    norm:invalidate()
    local s = norm:snapshot()
    assert(s.valid == false and s.bound == 0)
    local r = norm:normalize(b.Clear, true)
    assert(r.status == "unknown" and r.reason == "invalid_bindings")
end)

test("ObstructionNormalizer - Invalidate is idempotent and cannot be revived", function()
    local b = get_valid_bindings()
    local norm = ObstructionNormalizer.new(b)
    norm:invalidate()
    norm:invalidate()
    assert(norm:snapshot().valid == false and norm:snapshot().bound == 0)
    local r = norm:normalize(b.Clear, true)
    assert(r.status == "unknown" and r.reason == "invalid_bindings")
end)

test("ObstructionNormalizer - Snapshot copy immutability", function()
    local b = get_valid_bindings()
    local norm = ObstructionNormalizer.new(b)
    local s = norm:snapshot()
    s.valid = false
    s.bound = 0
    assert(norm:snapshot().valid == true and norm:snapshot().bound == 5)
end)

test("ObstructionNormalizer - Scalar handle-free return output", function()
    local b = get_valid_bindings()
    local norm = ObstructionNormalizer.new(b)
    local r = norm:normalize(b.Clear, true)
    assert(type(r.status) == "string" and type(r.reason) == "string")
    assert(r.Clear == nil and r.raw == nil and r.ref == nil)
end)

-- =========================================================================
-- INTEGRATION & PIPELINE ISOLATION TESTS
-- =========================================================================

test("Pipeline Boundary - Clear geometry with unknown lighting never records knowledge", function()
    local b = get_valid_bindings()
    local norm = ObstructionNormalizer.new(b)
    local id_mgr = SessionIdentity.new("pipe_test")
    local norm_res = norm:normalize(b.Clear, true)
    assert(norm_res.status == "clear")
    local ent_id = id_mgr:resolve("zombie_token_1", "zombie")
    assert(ent_id.reason == "new")
    local candidate = {id=ent_id.id,kind=ent_id.kind,x=2,y=0,z=0}
    local sample = Perception.new():sample({x=0,y=0,z=0,forward={x=1,y=0}}, {candidate}, {
        coverage=function() return true end,
        obstruction=function() return norm:normalize(b.Clear,true).status end
    })
    assert(sample.results[1].geometric=="visible" and sample.results[1].visual=="unknown")
    assert(sample.results[1].position==nil)
    local memory=Knowledge.new();memory:update(sample,0)
    assert(#memory:snapshot(0)==0, "Unknown lighting cannot enter actual Knowledge")
end)

test("Pipeline Boundary - Opaque fixture references do not escape into output records", function()
    local native_userdata_mock = { __native_ptr = "0xDEADBEEF" }
    local b = {
        Clear = native_userdata_mock,
        ClearThroughOpenDoor = { _tag = "OpenDoor" },
        ClearThroughWindow = { _tag = "Window" },
        Blocked = { _tag = "Blocked" },
        ClearThroughClosedDoor = { _tag = "ClosedDoor" },
    }
    local norm = ObstructionNormalizer.new(b)
    local r = norm:normalize(native_userdata_mock, true)
    assert(r.status == "clear" and r.reason == "clear")
    assert(r.__native_ptr == nil and rawget(r, "__native_ptr") == nil)
end)


-- Codex review regressions: nil holes must not silently skip real cases.
test("Explicit nil identity arguments refuse without allocating", function()
    assert(not pcall(SessionIdentity.new,nil))
    local registry=SessionIdentity.new("nil_args")
    assert(registry:resolve(nil,"player").reason=="invalid_token")
    assert(registry:resolve("t",nil).reason=="invalid_kind")
    assert(registry:snapshot().issued==0 and registry:snapshot().retained==0)
end)
test("Explicit nil bindings and missing enum refuse", function()
    local invalid=ObstructionNormalizer.new(nil)
    assert(invalid:snapshot().bound==0 and invalid:normalize(nil,true).reason=="invalid_bindings")
    local b=get_valid_bindings();local old=b.Clear;b.Clear=nil
    assert(ObstructionNormalizer.new(b):normalize(old,true).reason=="invalid_bindings")
end)
test("Explicit nil result and coverage cannot grant obstruction", function()
    local b=get_valid_bindings();local normal=ObstructionNormalizer.new(b)
    assert(normal:normalize(nil,true).reason=="unknown_result")
    assert(normal:normalize(b.Clear,nil).reason=="coverage_unknown")
    assert(normal:normalize(b.Blocked,nil).reason=="coverage_unknown")
end)
test("Bindings are copied before caller replaces all fields", function()
    local b=get_valid_bindings();local old=b.Clear;local normal=ObstructionNormalizer.new(b)
    for k in pairs(b) do b[k]={} end
    assert(normal:normalize(old,true).status=="clear")
    assert(normal:normalize(b.Clear,true).reason=="unknown_result")
    normal:invalidate();assert(normal:normalize(old,true).reason=="invalid_bindings")
end)
test("Shared toxic equality metamethod never runs", function()
    local calls=0
    local meta={__eq=function() calls=calls+1;error("equality callback") end,
        __index=function() error("index callback") end,__tostring=function() error("string callback") end}
    local b=get_valid_bindings()
    for _,ref in pairs(b) do setmetatable(ref,meta) end
    local normal=ObstructionNormalizer.new(b)
    assert(normal:snapshot().valid)
    assert(normal:normalize(setmetatable({},meta),true).reason=="unknown_result")
    assert(normal:normalize(b.Clear,true).status=="clear" and calls==0)
end)
test("Missing binding with throwing index fails closed", function()
    local b=get_valid_bindings();b.Blocked=nil
    setmetatable(b,{__index=function() error("must use rawget") end})
    assert(not ObstructionNormalizer.new(b):snapshot().valid)
end)
test("Maximum counters produce bounded IDs before fail-closed exhaustion", function()
    local registry=SessionIdentity.new(string.rep("n",32))
    assert(set_upval(registry.resolve,"epoch",2147483647))
    assert(set_upval(registry.resolve,"sequence",2147483646))
    local r=registry:resolve(string.rep("t",96),"player")
    assert(r.reason=="new" and #r.id==54 and #r.id<=96)
    assert(registry:resolve("overflow","player").reason=="exhausted")
    registry:reset();assert(registry:snapshot().exhausted and registry:snapshot().retained==0)
end)
test("Repeated eviction and reset never reuse IDs within a unique namespace", function()
    local registry=SessionIdentity.new("bounded_stress");local seen={}
    for pass=1,3 do
        for i=1,150 do
            local r=registry:resolve("t"..i,"zombie")
            assert(r.reason=="new" and not seen[r.id]);seen[r.id]=true
            assert(registry:snapshot().retained<=64)
        end
        registry:reset()
    end
end)
test("Unknown obstruction cannot reach confirmed perception or memory", function()
    local b=get_valid_bindings();local normal=ObstructionNormalizer.new(b)
    for _,raw in ipairs({b.ClearThroughClosedDoor,{},"Clear",1}) do
        local sample=Perception.new():sample({x=0,y=0,z=0,forward={x=1,y=0}},
            {{id="z",kind="zombie",x=2,y=0,z=0}},
            {coverage=function() return true end,obstruction=function() return normal:normalize(raw,true).status end,
             lighting=function() return "detectable" end})
        assert(sample.results[1].visual=="unknown" and sample.results[1].position==nil)
        local memory=Knowledge.new();memory:update(sample,0);assert(#memory:snapshot(0)==0)
    end
end)


test("Userdata references normalize without Java or string conversion", function()
    assert(type(opaqueFixtures.Clear)=="userdata")
    local normal=ObstructionNormalizer.new(opaqueFixtures)
    assert(normal:snapshot().bound==5)
    assert(normal:normalize(opaqueFixtures.Clear,true).status=="clear")
    assert(normal:normalize(opaqueFixtures.Blocked,true).status=="blocked")
    assert(normal:normalize(opaqueFixtures.ClearThroughClosedDoor,true).status=="unknown")
    normal:invalidate();assert(normal:snapshot().bound==0)
end)
test("Userdata token never becomes a guessed session identity", function()
    local registry=SessionIdentity.new("opaque_input")
    assert(registry:resolve(opaqueFixtures.Clear,"player").reason=="invalid_token")
    assert(registry:snapshot().retained==0 and registry:snapshot().issued==0)
end)

print(string.format("RESULT %d adapter boundary checks passed", tests_passed))

""")
