"""Actual Lua policy and memory tests; no native gameplay claim."""
from pathlib import Path
import sys
root = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(root / "tools/dependencies/python"))
from lupa import LuaRuntime
lua = LuaRuntime(unpack_returned_tuples=True)
for name in ("Perception", "Knowledge"):
    lua.globals()[name] = lua.execute((root / f"foundation/SarahFoundation/42/media/lua/client/Sarah/{name}.lua").read_text())
lua.execute(r"""
local count=0
local function test(name,fn) fn(); count=count+1; print('PASS '..name) end
local observer={x=0,y=0,z=0,forward={x=1,y=0}}
local function candidate(x,y,id) return {id=id or 'z1',kind='zombie',x=x or 2,y=y or 0,z=0} end
local function queries() return {coverage=function() return true end,obstruction=function() return 'clear' end,lighting=function() return 'detectable' end} end
local policy=Perception.new()
local function result(c,q,o) return policy:sample(o or observer,{c or candidate()},q or queries()).results[1] end
local function status(c,g,v,q,o) local r=result(c,q,o); assert(r.geometric==g and r.visual==v,r.reason) end
for _,name in ipairs({'move','attack','getInventory','clearQueue','getSpecificPlayer'}) do _G[name]=function() error('physical/global access: '..name) end end
test('front confirmed',function() status(nil,'visible','visible') end)
test('behind blocked',function() status(candidate(-2),'blocked','blocked') end)
test('cone boundary inclusive',function() status(candidate(2,2),'visible','visible') end)
test('outside cone',function() status(candidate(2,2.01),'blocked','blocked') end)
test('range boundary inclusive',function() status(candidate(12),'visible','visible') end)
test('beyond range',function() status(candidate(12.01),'blocked','blocked') end)
test('different floor',function() local c=candidate();c.z=1;status(c,'blocked','blocked') end)
test('opaque obstruction',function() local q=queries();q.obstruction=function() return 'blocked' end;status(nil,'blocked','blocked',q) end)
for _,enum in ipairs({'ClearThroughWindow','ClearThroughOpenDoor','ClearThroughClosedDoor','Clear','unexpected'}) do
 test('raw enum stays unknown '..enum,function() local q=queries();q.obstruction=function() return enum end;status(nil,'unknown','unknown',q) end)
end
test('explicit normalized window/door clear',function() status(nil,'visible','visible',queries()) end)
for _,coverage in ipairs({'endpoint','intermediate'}) do
 test('missing '..coverage,function() local q=queries();q.coverage=function() return false end;status(nil,'unknown','unknown',q) end)
end
test('failed query',function() local q=queries();q.obstruction=function() error('failure') end;status(nil,'unknown','unknown',q) end)
test('missing queries',function() status(nil,'unknown','unknown',{}) end)
test('invalid coordinates',function() local c=candidate();c.x=0/0;status(c,'unknown','unknown') end)
test('invalid forward',function() status(nil,'unknown','unknown',nil,{x=0,y=0,z=0,forward={x=0,y=0}}) end)
test('nonfinite forward',function() status(nil,'unknown','unknown',nil,{x=0,y=0,z=0,forward={x=math.huge,y=0}}) end)
test('coincident is unknown',function() status(candidate(0,0),'unknown','unknown') end)
test('unknown lighting geometric only',function() local q=queries();q.lighting=nil;status(nil,'visible','unknown',q) end)
test('darkness blocks visual only',function() local q=queries();q.lighting=function() return 'undetectable' end;status(nil,'visible','blocked',q) end)
test('player supported',function() local c=candidate();c.kind='player';status(c,'visible','visible') end)
test('unsupported kind',function() local c=candidate();c.kind='container';status(c,'unknown','unknown') end)
test('duplicate identity refused',function() local s=policy:sample(observer,{candidate(),candidate(3)},queries());assert(s.results[2].visual=='unknown') end)
test('truncation 32 candidates',function() local cs={};for i=1,40 do cs[i]=candidate(2,0,tostring(i)) end;local s=policy:sample(observer,cs,queries());assert(s.processed==32 and s.truncated and #s.results==32) end)
test('player rendering irrelevant',function() local c=candidate();c.playerVisible=false;status(c,'visible','visible');c.playerVisible=true;status(c,'visible','visible') end)
test('configurable cone/range',function() local p=Perception.new({range=3,coneDegrees=180});assert(p:sample(observer,{candidate(0,2)},queries()).results[1].visual=='visible') end)
test('invalid configuration rejected',function() assert(not pcall(Perception.new,{range=-1}));assert(not pcall(Perception.new,{coneDegrees=400})) end)
local function sample(c,q) return policy:sample(observer,{c or candidate()},q or queries()) end
test('unknown lighting never remembered',function() local k=Knowledge.new();local q=queries();q.lighting=nil;k:update(sample(nil,q),0);assert(#k:snapshot(0)==0) end)
test('confirmed observation copied',function() local k=Knowledge.new();local s=sample();k:update(s,1);s.results[1].position.x=99;local r=k:snapshot(1);assert(r[1].position.x==2 and r[1].observedAt==1);r[1].position.x=55;assert(k:snapshot(1)[1].position.x==2) end)
test('hidden movement cannot refresh memory',function() local k=Knowledge.new();k:update(sample(),0);local q=queries();q.obstruction=function() return 'blocked' end;k:update(sample(candidate(5),q),5);assert(k:snapshot(5)[1].position.x==2 and k:snapshot(5)[1].observedAt==0) end)
test('reappearance corrects memory',function() local k=Knowledge.new();k:update(sample(),0);k:update(sample(candidate(5)),2);assert(k:snapshot(2)[1].position.x==5) end)
test('exact expiry',function() local k=Knowledge.new();k:update(sample(),0);assert(#k:snapshot(9.99)==1);assert(#k:snapshot(10)==0) end)
test('oldest evicted and cap retained',function() local k=Knowledge.new();for i=1,33 do k:update(sample(candidate(2,0,string.format('%02d',i))),i/100) end;local r=k:snapshot(1);assert(#r==32 and r[1].id=='02') end)
test('equal-time deterministic eviction',function() local k=Knowledge.new();for i=1,33 do k:update(sample(candidate(2,0,string.format('%02d',i))),0) end;assert(k:snapshot(0)[1].id=='02') end)
test('refresh preserves recently seen entry',function() local k=Knowledge.new();for i=1,32 do k:update(sample(candidate(2,0,tostring(i))),0) end;k:update(sample(candidate(2,0,'1')),1);k:update(sample(candidate(2,0,'33')),2);local found=false;for _,r in ipairs(k:snapshot(2)) do if r.id=='1' then found=true end;assert(r.id~='2') end;assert(found) end)
for _,event in ipairs({'session','replacement','unload','death'}) do test('reset on '..event,function() local k=Knowledge.new();k:update(sample(),0);k:reset();assert(#k:snapshot(0)==0) end) end
test('backward clock clears stale session',function() local k=Knowledge.new();k:update(sample(),5);assert(#k:snapshot(1)==0) end)
test('invalid time rejected',function() local k=Knowledge.new();assert(not pcall(k.snapshot,k,-1));assert(not pcall(k.snapshot,k,0/0)) end)
test('omitted candidates not remembered',function() local cs={};for i=1,33 do cs[i]=candidate(2,0,tostring(i)) end;local k=Knowledge.new();k:update(policy:sample(observer,cs,queries()),0);for _,r in ipairs(k:snapshot(0)) do assert(r.id~='33') end end)
print('RESULT '..count..' perception checks passed')
""")
