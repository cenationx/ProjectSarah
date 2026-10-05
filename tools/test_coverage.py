"""Actual Lua coverage policy and memory tests; no native gameplay claim."""
from pathlib import Path
import sys

root = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(root / "tools/dependencies/python"))
from lupa import LuaRuntime

lua = LuaRuntime(unpack_returned_tuples=True)
for name in ("Perception", "Knowledge", "Coverage"):
    lua.globals()[name] = lua.execute((root / f"foundation/SarahFoundation/42/media/lua/client/Sarah/{name}.lua").read_text())

lua.execute(r"""
local count = 0
local function test(name, fn)
    fn()
    count = count + 1
    print('PASS ' .. name)
end

local function makeGrid(minX, maxX, minY, maxY, z, val)
    local g = {}
    for x = minX, maxX do
        for y = minY, maxY do
            g[x .. ',' .. y .. ',' .. z] = (val ~= nil) and val or { id = 'square_' .. x .. '_' .. y }
        end
    end
    return g
end

local function makeGetter(grid, counter)
    return function(x, y, z)
        if counter then counter[1] = counter[1] + 1 end
        local k = x .. ',' .. y .. ',' .. z
        return grid[k]
    end
end

-- 1. Basic covered ray: (0,0,0) to (2,0,0), halo [-1,3]x[-1,1] = 5x3 = 15 tiles
test('basic covered ray', function()
    local g = makeGrid(-1, 3, -1, 1, 0)
    local c = {1}
    c[1] = 0
    local ctx = Coverage.newContext()
    local r = Coverage.check({x=0,y=0,z=0}, {x=2,y=0,z=0}, makeGetter(g, c), ctx)
    assert(r.status == 'covered' and r.reason == 'ok')
    assert(r.reads == 15 and c[1] == 15)
    assert(r.covered == true)
end)

-- 2. Reverse direction equivalence: (2,0,0) to (0,0,0) produces identical area and coverage
test('reverse direction equivalence', function()
    local g = makeGrid(-1, 3, -1, 1, 0)
    local ctx = Coverage.newContext()
    local r = Coverage.check({x=2,y=0,z=0}, {x=0,y=0,z=0}, makeGetter(g), ctx)
    assert(r.status == 'covered' and r.area == 15)
end)

-- 3. Horizontal axis ray: (0,0) to (5,0), halo [-1,6]x[-1,1] = 8x3 = 24 tiles
test('horizontal axis ray', function()
    local g = makeGrid(-1, 6, -1, 1, 0)
    local ctx = Coverage.newContext()
    local r = Coverage.check({x=0,y=0,z=0}, {x=5,y=0,z=0}, makeGetter(g), ctx)
    assert(r.status == 'covered' and r.area == 24)
end)

-- 4. Vertical axis ray: (0,0) to (0,5), halo [-1,1]x[-1,6] = 3x8 = 24 tiles
test('vertical axis ray', function()
    local g = makeGrid(-1, 1, -1, 6, 0)
    local ctx = Coverage.newContext()
    local r = Coverage.check({x=0,y=0,z=0}, {x=0,y=5,z=0}, makeGetter(g), ctx)
    assert(r.status == 'covered' and r.area == 24)
end)

-- 5. Diagonal tie ray: (0,0) to (3,3), halo [-1,4]x[-1,4] = 6x6 = 36 tiles
test('diagonal tie ray', function()
    local g = makeGrid(-1, 4, -1, 4, 0)
    local ctx = Coverage.newContext()
    local r = Coverage.check({x=0,y=0,z=0}, {x=3,y=3,z=0}, makeGetter(g), ctx)
    assert(r.status == 'covered' and r.area == 36)
end)

-- 6. Steep ray: (0,0) to (1,4), halo [-1,2]x[-1,5] = 4x7 = 28 tiles
test('steep ray', function()
    local g = makeGrid(-1, 2, -1, 5, 0)
    local ctx = Coverage.newContext()
    local r = Coverage.check({x=0,y=0,z=0}, {x=1,y=4,z=0}, makeGetter(g), ctx)
    assert(r.status == 'covered' and r.area == 28)
end)

-- 7. Shallow ray: (0,0) to (4,1), halo [-1,5]x[-1,2] = 7x4 = 28 tiles
test('shallow ray', function()
    local g = makeGrid(-1, 5, -1, 2, 0)
    local ctx = Coverage.newContext()
    local r = Coverage.check({x=0,y=0,z=0}, {x=4,y=1,z=0}, makeGetter(g), ctx)
    assert(r.status == 'covered' and r.area == 28)
end)

-- 8. Halo boundary missing minX
test('missing halo minX returns unknown', function()
    local g = makeGrid(-1, 3, -1, 1, 0)
    g['-1,0,0'] = nil
    local ctx = Coverage.newContext()
    local r = Coverage.check({x=0,y=0,z=0}, {x=2,y=0,z=0}, makeGetter(g), ctx)
    assert(r.status == 'unknown' and r.reason == 'missing_square')
end)

-- 9. Halo boundary missing maxX
test('missing halo maxX returns unknown', function()
    local g = makeGrid(-1, 3, -1, 1, 0)
    g['3,0,0'] = nil
    local ctx = Coverage.newContext()
    local r = Coverage.check({x=0,y=0,z=0}, {x=2,y=0,z=0}, makeGetter(g), ctx)
    assert(r.status == 'unknown' and r.reason == 'missing_square')
end)

-- 10. Halo boundary missing minY
test('missing halo minY returns unknown', function()
    local g = makeGrid(-1, 3, -1, 1, 0)
    g['1,-1,0'] = nil
    local ctx = Coverage.newContext()
    local r = Coverage.check({x=0,y=0,z=0}, {x=2,y=0,z=0}, makeGetter(g), ctx)
    assert(r.status == 'unknown' and r.reason == 'missing_square')
end)

-- 11. Halo boundary missing maxY
test('missing halo maxY returns unknown', function()
    local g = makeGrid(-1, 3, -1, 1, 0)
    g['1,1,0'] = nil
    local ctx = Coverage.newContext()
    local r = Coverage.check({x=0,y=0,z=0}, {x=2,y=0,z=0}, makeGetter(g), ctx)
    assert(r.status == 'unknown' and r.reason == 'missing_square')
end)

-- 12. Missing diagonal halo corner stays unknown
test('missing diagonal halo corner stays unknown', function()
    local g = makeGrid(-1, 3, -1, 1, 0)
    g['-1,-1,0'] = nil
    local ctx = Coverage.newContext()
    local r = Coverage.check({x=0,y=0,z=0}, {x=2,y=0,z=0}, makeGetter(g), ctx)
    assert(r.status == 'unknown' and r.reason == 'missing_square')
end)

-- 13. Missing observer endpoint square
test('missing observer endpoint square returns unknown', function()
    local g = makeGrid(-1, 3, -1, 1, 0)
    g['0,0,0'] = nil
    local ctx = Coverage.newContext()
    local r = Coverage.check({x=0,y=0,z=0}, {x=2,y=0,z=0}, makeGetter(g), ctx)
    assert(r.status == 'unknown' and r.reason == 'missing_square')
end)

-- 14. Missing candidate endpoint square
test('missing candidate endpoint square returns unknown', function()
    local g = makeGrid(-1, 3, -1, 1, 0)
    g['2,0,0'] = nil
    local ctx = Coverage.newContext()
    local r = Coverage.check({x=0,y=0,z=0}, {x=2,y=0,z=0}, makeGetter(g), ctx)
    assert(r.status == 'unknown' and r.reason == 'missing_square')
end)

-- 15. Missing interior square
test('missing interior square returns unknown', function()
    local g = makeGrid(-1, 3, -1, 1, 0)
    g['1,0,0'] = nil
    local ctx = Coverage.newContext()
    local r = Coverage.check({x=0,y=0,z=0}, {x=2,y=0,z=0}, makeGetter(g), ctx)
    assert(r.status == 'unknown' and r.reason == 'missing_square')
end)

-- 16. Negative fraction observer coordinates
test('negative fraction observer floored explicitly', function()
    -- ox = -0.5 -> -1, oy = -0.5 -> -1. cx = 1, cy = 0. bounds: [-2, 2] x [-2, 1] = 5x4 = 20
    local g = makeGrid(-2, 2, -2, 1, 0)
    local ctx = Coverage.newContext()
    local r = Coverage.check({x=-0.5,y=-0.5,z=0}, {x=1,y=0,z=0}, makeGetter(g), ctx)
    assert(r.status == 'covered' and r.area == 20)
end)

-- 17. Negative fraction candidate coordinates
test('negative fraction candidate floored explicitly', function()
    -- ox = 0, oy = 0. cx = -2.1 -> -3, cy = -1.9 -> -2. bounds: [-4, 1] x [-3, 1] = 6x5 = 30
    local g = makeGrid(-4, 1, -3, 1, 0)
    local ctx = Coverage.newContext()
    local r = Coverage.check({x=0,y=0,z=0}, {x=-2.1,y=-1.9,z=0}, makeGetter(g), ctx)
    assert(r.status == 'covered' and r.area == 30)
end)

-- 18. Exact negative integer boundaries
test('exact negative integer boundaries', function()
    -- ox = -1.0, oy = -2.0, cx = -3.0, cy = -2.0. bounds: [-4, 0] x [-3, -1] = 5x3 = 15
    local g = makeGrid(-4, 0, -3, -1, 0)
    local ctx = Coverage.newContext()
    local r = Coverage.check({x=-1.0,y=-2.0,z=0}, {x=-3.0,y=-2.0,z=0}, makeGetter(g), ctx)
    assert(r.status == 'covered' and r.area == 15)
end)

-- 19. Zero-length policy covered when 3x3 halo loaded
test('zero-length policy covered when 3x3 halo loaded', function()
    local g = makeGrid(1, 3, 2, 4, 0)
    local ctx = Coverage.newContext()
    local r = Coverage.check({x=2,y=3,z=0}, {x=2,y=3,z=0}, makeGetter(g), ctx)
    assert(r.status == 'covered' and r.area == 9 and r.reads == 9)
end)

-- 20. Zero-length policy unknown when halo square missing
test('zero-length policy unknown when halo square missing', function()
    local g = makeGrid(1, 3, 2, 4, 0)
    g['1,2,0'] = nil
    local ctx = Coverage.newContext()
    local r = Coverage.check({x=2,y=3,z=0}, {x=2,y=3,z=0}, makeGetter(g), ctx)
    assert(r.status == 'unknown' and r.reason == 'missing_square')
end)

-- 21. Different floor rejected without getter invocation
test('different floor rejected without getter invocation', function()
    local c = {1}; c[1] = 0
    local ctx = Coverage.newContext()
    local r = Coverage.check({x=0,y=0,z=0}, {x=2,y=0,z=1}, makeGetter({}, c), ctx)
    assert(r.status == 'unknown' and r.reason == 'different_floor')
    assert(c[1] == 0 and r.reads == 0)
end)

-- 22. Different floor via fractional z rejected
test('different floor via fractional z rejected', function()
    local ctx = Coverage.newContext()
    local r = Coverage.check({x=0,y=0,z=0.9}, {x=2,y=0,z=1.1}, makeGetter({}), ctx)
    assert(r.status == 'unknown' and r.reason == 'different_floor')
end)

-- 23. Range boundary exact 12 inclusive
test('range boundary exact 12 inclusive', function()
    local g = makeGrid(-1, 13, -1, 1, 0)
    local ctx = Coverage.newContext({range=12})
    local r = Coverage.check({x=0,y=0,z=0}, {x=12,y=0,z=0}, makeGetter(g), ctx)
    assert(r.status == 'covered')
end)

-- 24. Range boundary 12.01 rejected before querying
test('range boundary 12.01 rejected before querying', function()
    local c = {1}; c[1] = 0
    local ctx = Coverage.newContext({range=12})
    local r = Coverage.check({x=0,y=0,z=0}, {x=12.01,y=0,z=0}, makeGetter({}, c), ctx)
    assert(r.status == 'unknown' and r.reason == 'out_of_range')
    assert(c[1] == 0 and r.reads == 0)
end)

-- 25. Configured range above hard max is rejected
test('configured range above hard max rejected', function()
    assert(not pcall(Coverage.newContext,{range=100}))
end)

-- 26. Beyond max range 64 rejected
test('beyond max range 64 rejected', function()
    local ctx = Coverage.newContext()
    local r = Coverage.check({x=0,y=0,z=0}, {x=64.1,y=0,z=0}, makeGetter({}), ctx)
    assert(r.status == 'unknown' and r.reason == 'out_of_range')
end)

-- 27. Invalid NaN coordinates observer
test('invalid NaN coordinates observer', function()
    local ctx = Coverage.newContext()
    local r = Coverage.check({x=0/0,y=0,z=0}, {x=2,y=0,z=0}, makeGetter({}), ctx)
    assert(r.status == 'unknown' and r.reason == 'invalid_coordinates')
end)

-- 28. Invalid NaN coordinates candidate
test('invalid NaN coordinates candidate', function()
    local ctx = Coverage.newContext()
    local r = Coverage.check({x=0,y=0,z=0}, {x=2,y=0/0,z=0}, makeGetter({}), ctx)
    assert(r.status == 'unknown' and r.reason == 'invalid_coordinates')
end)

-- 29. Infinite coordinates observer
test('infinite coordinates observer', function()
    local ctx = Coverage.newContext()
    local r = Coverage.check({x=math.huge,y=0,z=0}, {x=2,y=0,z=0}, makeGetter({}), ctx)
    assert(r.status == 'unknown' and r.reason == 'invalid_coordinates')
end)

-- 30. Infinite coordinates candidate
test('infinite coordinates candidate', function()
    local ctx = Coverage.newContext()
    local r = Coverage.check({x=0,y=0,z=0}, {x=2,y=-math.huge,z=0}, makeGetter({}), ctx)
    assert(r.status == 'unknown' and r.reason == 'invalid_coordinates')
end)

-- 31. Extreme coordinate bound exceeded
test('extreme coordinate bound exceeded', function()
    local ctx = Coverage.newContext()
    local r = Coverage.check({x=1000001,y=0,z=0}, {x=1000002,y=0,z=0}, makeGetter({}), ctx)
    assert(r.status == 'unknown' and r.reason == 'invalid_coordinates')
end)

-- 32. Invalid observer non-table
test('invalid observer non-table', function()
    local ctx = Coverage.newContext()
    local r = Coverage.check('bad', {x=2,y=0,z=0}, makeGetter({}), ctx)
    assert(r.status == 'unknown' and r.reason == 'invalid_observer')
end)

-- 33. Invalid candidate non-table
test('invalid candidate non-table', function()
    local ctx = Coverage.newContext()
    local r = Coverage.check({x=0,y=0,z=0}, 123, makeGetter({}), ctx)
    assert(r.status == 'unknown' and r.reason == 'invalid_candidate')
end)

-- 34. Missing getter non-function
test('missing getter non-function', function()
    local ctx = Coverage.newContext()
    local r = Coverage.check({x=0,y=0,z=0}, {x=2,y=0,z=0}, nil, ctx)
    assert(r.status == 'unknown' and r.reason == 'missing_getter')
end)

-- 35. Getter throws exception handled via pcall and recorded
test('getter throws exception handled safely', function()
    local ctx = Coverage.newContext()
    local fn = function() error('native jni fault') end
    local r = Coverage.check({x=0,y=0,z=0}, {x=2,y=0,z=0}, fn, ctx)
    assert(r.status == 'unknown' and r.reason == 'query_error')
    assert(r.reads == 1 and ctx:snapshot().failedReads == 1)
end)

-- 36. Getter returns false handled as missing
test('getter returns false handled as missing', function()
    local ctx = Coverage.newContext()
    local fn = function() return false end
    local r = Coverage.check({x=0,y=0,z=0}, {x=2,y=0,z=0}, fn, ctx)
    assert(r.status == 'unknown' and r.reason == 'missing_square')
    assert(r.reads == 1 and ctx:snapshot().failedReads == 1)
end)

-- 37. Getter returns nil handled as missing
test('getter returns nil handled as missing', function()
    local ctx = Coverage.newContext()
    local fn = function() return nil end
    local r = Coverage.check({x=0,y=0,z=0}, {x=2,y=0,z=0}, fn, ctx)
    assert(r.status == 'unknown' and r.reason == 'missing_square')
    assert(r.reads == 1 and ctx:snapshot().failedReads == 1)
end)

-- 38. Getter returns opaque truthy fixture without leaking handle
test('opaque fixture accepted and handles never leaked', function()
    local g = makeGrid(-1, 3, -1, 1, 0, { nativeHandle = 0xdeadbeef })
    local ctx = Coverage.newContext()
    local r = Coverage.check({x=0,y=0,z=0}, {x=2,y=0,z=0}, makeGetter(g), ctx)
    assert(r.status == 'covered')
    assert(r.nativeHandle == nil)
    assert(ctx:snapshot().successfulReads == 15 and r.square == nil)
end)

-- 39. Exact candidate budget matches area
test('exact candidate budget matches area', function()
    local g = makeGrid(1, 3, 2, 4, 0) -- 3x3 = 9
    local ctx = Coverage.newContext({candidateBudget=9})
    local r = Coverage.check({x=2,y=3,z=0}, {x=2,y=3,z=0}, makeGetter(g), ctx)
    assert(r.status == 'covered' and r.area == 9)
end)

-- 40. Insufficient candidate budget refuses before query
test('insufficient candidate budget refuses before query', function()
    local c = {1}; c[1] = 0
    local ctx = Coverage.newContext({candidateBudget=8})
    local r = Coverage.check({x=2,y=3,z=0}, {x=2,y=3,z=0}, makeGetter({}, c), ctx)
    assert(r.status == 'unknown' and r.reason == 'candidate_budget_exceeded')
    assert(c[1] == 0 and r.reads == 0)
end)

-- 41. Exact sample budget matches queries
test('exact sample budget matches queries', function()
    local g = makeGrid(1, 3, 2, 4, 0) -- 9 tiles
    local ctx = Coverage.newContext({sampleBudget=9})
    local r = Coverage.check({x=2,y=3,z=0}, {x=2,y=3,z=0}, makeGetter(g), ctx)
    assert(r.status == 'covered' and ctx:snapshot().sampleRemaining == 0)
end)

-- 42. Insufficient sample budget refuses before query
test('insufficient sample budget refuses before query', function()
    local c = {1}; c[1] = 0
    local ctx = Coverage.newContext({sampleBudget=8})
    local r = Coverage.check({x=2,y=3,z=0}, {x=2,y=3,z=0}, makeGetter({}, c), ctx)
    assert(r.status == 'unknown' and r.reason == 'sample_budget_exceeded')
    assert(c[1] == 0 and r.reads == 0)
end)

-- 43. Shared sample exhaustion across candidates refuses 2nd candidate
test('shared sample exhaustion across candidates', function()
    -- candidate 1 needs 9 queries; sampleBudget is 15. Candidate 1 leaves 6 remaining.
    -- candidate 2 needs 9 disjoint queries; 9 > 6 -> candidate 2 refused before queries.
    local g1 = makeGrid(1, 3, 1, 3, 0) -- (2,2) to (2,2) = 9 tiles
    local g2 = makeGrid(11, 13, 11, 13, 0) -- (12,12) to (12,12) = 9 tiles
    for k, v in pairs(g2) do g1[k] = v end
    local c = {1}; c[1] = 0
    local ctx = Coverage.newContext({sampleBudget=15})
    local r1 = Coverage.check({x=2,y=2,z=0}, {x=2,y=2,z=0}, makeGetter(g1, c), ctx)
    assert(r1.status == 'covered' and r1.reads == 9 and c[1] == 9)
    assert(ctx:snapshot().sampleRemaining == 6)
    local r2 = Coverage.check({x=12,y=12,z=0}, {x=12,y=12,z=0}, makeGetter(g1, c), ctx)
    assert(r2.status == 'unknown' and r2.reason == 'sample_budget_exceeded')
    assert(r2.reads == 0 and c[1] == 9)
end)

-- 44. Overlapping candidates must still consume fresh-query budget
test('overlapping candidates never bypass exhausted budget', function()
    local ctx=Coverage.newContext({sampleBudget=12})
    local calls=0
    local get=function() calls=calls+1;return true end
    assert(Coverage.check({x=0,y=0,z=0},{x=1,y=0,z=0},get,ctx).covered)
    local r=Coverage.check({x=0,y=0,z=0},{x=0,y=0,z=0},get,ctx)
    assert(r.reason=='sample_budget_exceeded' and r.reads==0 and calls==12)
end)

-- 45. Fresh context re-queries squares (no stale cache)
test('fresh context re-queries squares without stale cache', function()
    local g = makeGrid(1, 3, 1, 3, 0)
    local c = {1}; c[1] = 0
    local ctx1 = Coverage.newContext()
    Coverage.check({x=2,y=2,z=0}, {x=2,y=2,z=0}, makeGetter(g, c), ctx1)
    assert(c[1] == 9)
    local ctx2 = Coverage.newContext()
    Coverage.check({x=2,y=2,z=0}, {x=2,y=2,z=0}, makeGetter(g, c), ctx2)
    assert(c[1] == 18)
end)

-- 46. Missing data can recover without a stale negative cache
test('missing square can become loaded in same context without stale cache', function()
    local ctx=Coverage.newContext()
    local o={x=2,y=2,z=0}
    local first=Coverage.check(o,o,function() return nil end,ctx)
    assert(first.reason=='missing_square' and first.reads==1)
    local second=Coverage.check(o,o,function() return true end,ctx)
    assert(second.covered and second.reads==9 and ctx:snapshot().totalReads==10)
end)

-- 47. No context silently renewed in check
test('no context silently created or renewed', function()
    local r = Coverage.check({x=0,y=0,z=0}, {x=2,y=0,z=0}, function() return true end, nil)
    assert(r.status == 'unknown' and r.reason == 'invalid_context')
end)

-- 48. Malformed context rejected fail closed
test('malformed context rejected fail closed', function()
    local r = Coverage.check({x=0,y=0,z=0}, {x=2,y=0,z=0}, function() return true end, {sampleRemaining='huge'})
    assert(r.status == 'unknown' and r.reason == 'invalid_context')
end)

-- 49. newContext rejects invalid sampleBudget
test('newContext rejects invalid sampleBudget', function()
    assert(not pcall(Coverage.newContext, {sampleBudget=-5}))
    assert(not pcall(Coverage.newContext, {sampleBudget=0/0}))
end)

-- 50. newContext rejects invalid candidateBudget
test('newContext rejects invalid candidateBudget', function()
    assert(not pcall(Coverage.newContext, {candidateBudget=0}))
    assert(not pcall(Coverage.newContext, {candidateBudget=math.huge}))
end)

-- 51. Oversized budgets fail closed
test('newContext rejects budgets above hard ceilings', function()
    assert(not pcall(Coverage.newContext,{sampleBudget=8193}))
    assert(not pcall(Coverage.newContext,{candidateBudget=2049}))
end)

-- 52. Input snapshots not mutated by check
test('input snapshots not mutated by check', function()
    local o = {x=1.5, y=2.5, z=0}
    local c = {x=3.5, y=2.5, z=0, id='z1', kind='zombie'}
    local ctx = Coverage.newContext()
    Coverage.check(o, c, function() return true end, ctx)
    assert(o.x == 1.5 and o.y == 2.5 and o.z == 0)
    assert(c.x == 3.5 and c.y == 2.5 and c.z == 0 and c.id == 'z1')
    assert(o.status == nil and c.status == nil)
end)

-- 53. Perception adapter injection returning true ONLY for confirmed coverage
test('perception adapter injection confirmed coverage visible', function()
    local p = Perception.new()
    local obs = {x=0, y=0, z=0, forward={x=1, y=0}}
    local cand = {id='z1', kind='zombie', x=2, y=0, z=0}
    local g = makeGrid(-1, 3, -1, 1, 0)
    local ctx = Coverage.newContext()
    local queries = {
        coverage = function(o, c)
            local r = Coverage.check(o, c, makeGetter(g), ctx)
            return r.status == 'covered'
        end,
        obstruction = function() return 'clear' end,
        lighting = function() return 'detectable' end,
    }
    local res = p:sample(obs, {cand}, queries).results[1]
    assert(res.geometric == 'visible' and res.visual == 'visible' and res.reason == 'confirmed')
end)

-- 54. Perception adapter unknown coverage blocks perception
test('perception adapter unknown coverage blocks perception', function()
    local p = Perception.new()
    local obs = {x=0, y=0, z=0, forward={x=1, y=0}}
    local cand = {id='z1', kind='zombie', x=2, y=0, z=0}
    local ctx = Coverage.newContext()
    local queries = {
        coverage = function(o, c)
            local r = Coverage.check(o, c, function() return nil end, ctx)
            return r.status == 'covered'
        end,
        obstruction = function() return 'clear' end,
        lighting = function() return 'detectable' end,
    }
    local res = p:sample(obs, {cand}, queries).results[1]
    assert(res.geometric == 'unknown' and res.visual == 'unknown' and res.reason == 'coverage_unknown')
end)

-- 55. Perception adapter unknown lighting leaves visual unknown and Knowledge gets no record
test('perception unknown lighting leaves visual unknown and Knowledge gets no record', function()
    local p = Perception.new()
    local k = Knowledge.new()
    local obs = {x=0, y=0, z=0, forward={x=1, y=0}}
    local cand = {id='z1', kind='zombie', x=2, y=0, z=0}
    local g = makeGrid(-1, 3, -1, 1, 0)
    local ctx = Coverage.newContext()
    local queries = {
        coverage = function(o, c)
            local r = Coverage.check(o, c, makeGetter(g), ctx)
            return r.status == 'covered'
        end,
        obstruction = function() return 'clear' end,
        lighting = nil, -- unknown lighting
    }
    local sample = p:sample(obs, {cand}, queries)
    local res = sample.results[1]
    assert(res.geometric == 'visible' and res.visual == 'unknown' and res.reason == 'lighting_unknown')
    k:update(sample, 0)
    assert(#k:snapshot(0) == 0)
end)


test('covered square becoming missing is rechecked within sample',function()
    local ctx=Coverage.newContext()
    local o={x=0,y=0,z=0}
    assert(ctx:check(o,o,function() return true end).covered)
    local r=ctx:check(o,o,function(x,y) if x==0 and y==0 then return nil end;return true end)
    assert(not r.covered and r.reason=='missing_square' and r.reads==5)
end)
test('getter change cannot reuse previous coverage',function()
    local ctx=Coverage.newContext()
    local o={x=0,y=0,z=0}
    assert(ctx:check(o,o,function() return true end).covered)
    assert(ctx:check(o,o,function() error('new query fails') end).reason=='query_error')
end)
test('budget public fields and copied snapshots cannot renew sample',function()
    local ctx=Coverage.newContext({sampleBudget=9})
    local o={x=0,y=0,z=0}
    assert(ctx:check(o,o,function() return true end).covered)
    ctx.sampleRemaining=100000;ctx.sampleBudget=100000;ctx.candidateBudget=100000
    local snapshot=ctx:snapshot();snapshot.sampleRemaining=100000
    assert(ctx:check(o,o,function() error('must not call') end).reason=='sample_budget_exceeded')
    assert(ctx:snapshot().sampleRemaining==0 and ctx:snapshot().totalReads==9)
end)
test('malformed context cannot forge remaining budget',function()
    local r=Coverage.check({x=0,y=0,z=0},{x=0,y=0,z=0},function() error('no call') end,
        {sampleRemaining=math.huge,queriedSquares={},candidateBudget=math.huge})
    assert(r.reason=='invalid_context')
end)
test('reentrant query does not consume or reset budget',function()
    local ctx=Coverage.newContext({sampleBudget=9})
    local o={x=0,y=0,z=0}
    local calls=0
    local r=ctx:check(o,o,function()
        calls=calls+1
        assert(ctx:check(o,o,function() error('nested') end).reason=='reentrant_check')
        return true
    end)
    assert(r.covered and calls==9 and ctx:snapshot().totalReads==9)
end)
test('invalid options rejected rather than expanding limits',function()
    for _,v in ipairs({false,1,'options'}) do assert(not pcall(Coverage.newContext,v)) end
    for _,v in ipairs({-1,0,0.5,math.huge,-math.huge,'10',false}) do
        assert(not pcall(Coverage.newContext,{sampleBudget=v}))
        assert(not pcall(Coverage.newContext,{candidateBudget=v}))
    end
    assert(not pcall(Coverage.newContext,{range=0/0}))
    local ctx=Coverage.newContext({range=1})
    assert(Coverage.check({x=0,y=0,z=0},{x=2,y=0,z=0},function() return true end,ctx,{range=64}).reason=='invalid_options')
end)
test('missing any rectangle square never grants coverage across ray directions',function()
    for _,delta in ipairs({{3,3},{1,4},{4,1},{-3,2},{0,-3}}) do
        for _,reverse in ipairs({false,true}) do
            local o={x=-0.25,y=0.75,z=0};local c={x=o.x+delta[1],y=o.y+delta[2],z=0}
            if reverse then o,c=c,o end
            local minX,maxX=math.min(math.floor(o.x),math.floor(c.x))-1,math.max(math.floor(o.x),math.floor(c.x))+1
            local minY,maxY=math.min(math.floor(o.y),math.floor(c.y))-1,math.max(math.floor(o.y),math.floor(c.y))+1
            for missingX=minX,maxX do for missingY=minY,maxY do
                local calls=0;local seen={}
                local r=Coverage.newContext():check(o,c,function(x,y,z)
                    calls=calls+1;local key=x..','..y..','..z
                    assert(not seen[key]);seen[key]=true
                    assert(z==0 and x>=minX and x<=maxX and y>=minY and y<=maxY)
                    if x==missingX and y==missingY then return nil end
                    return true
                end)
                assert(not r.covered and r.reason=='missing_square' and calls==r.reads)
            end end
        end
    end
end)
test('candidate budget rejection leaves sample budget intact',function()
    local ctx=Coverage.newContext({candidateBudget=9,sampleBudget=18})
    local o={x=0,y=0,z=0}
    assert(ctx:check(o,{x=2,y=0,z=0},function() error('no call') end).reason=='candidate_budget_exceeded')
    assert(ctx:snapshot().totalReads==0 and ctx:snapshot().sampleRemaining==18)
    assert(ctx:check(o,o,function() return true end).covered)
    assert(ctx:check(o,o,function() return true end).covered)
end)
test('32-candidate caller cap bounds shared sample work',function()
    local ctx=Coverage.newContext({sampleBudget=90})
    local policy=Perception.new();local candidates={}
    for i=1,40 do candidates[i]={id=tostring(i),kind='zombie',x=2,y=0,z=0} end
    local calls=0
    local sample=policy:sample({x=0,y=0,z=0,forward={x=1,y=0}},candidates,{
        coverage=function(o,c) return ctx:check(o,c,function() calls=calls+1;return true end).covered end,
        obstruction=function() return 'clear' end,
        lighting=function() return 'unknown' end})
    assert(sample.processed==32 and sample.truncated and calls==90)
    assert(ctx:snapshot().totalReads==90 and ctx:snapshot().sampleRemaining==0)
    for _,r in ipairs(sample.results) do assert(r.visual=='unknown') end
end)

print('RESULT ' .. count .. ' coverage checks passed')
""")
