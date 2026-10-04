"""Read-only command tests execute actual Lua against hostile/mutable fixtures."""
from pathlib import Path
import sys
root=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(root/'tools/dependencies/python'))
from lupa import LuaRuntime
lua=LuaRuntime(unpack_returned_tuples=True)
for name in ('Commands','Observations'):
    lua.globals()[name]=lua.execute((root/f'foundation/SarahFoundation/42/media/lua/client/Sarah/{name}.lua').read_text())
lua.execute(r'''
local count=0
local function test(name,fn) fn(); count=count+1; print('PASS '..name) end
local function fixture()
    local n={getX=function() return 1 end,getY=function() return 2 end,getZ=function() return 0 end}
    local items={size=function() return 3 end,get=function(_,i) return {getFullType=function() return i<2 and 'Base.Bandage' or 'Base.Tshirt' end} end}
    n.getInventory=function() return {getItems=function() return items end} end
    local a={meta={},listNPCs=function() return {n} end,isDead=function() return false end,isResident=function() return true end,isIncomplete=function() return false end}
    local c={npc=n,adapter=a}
    for _,key in ipairs({'ensure','save','unload','maintain','transaction'}) do c[key]=function() error('mutation forbidden') end end
    return c,n,items
end
test('unknown/injection/control/oversized commands never observe',function()
    local d=Commands.new(function() error('must not observe') end)
    for _,v in ipairs({'walk here','status; unload','print(1)','status\n',string.rep('a',129)}) do
        assert(d:execute(v).state=='rejected')
    end
end)
test('help works without a controller or observation',function()
    assert(Commands.new(function() error('no') end):execute(' HELP ').state=='completed')
end)
test('request IDs advance even on rejected input',function()
    local d=Commands.new(function() return {state='active'} end)
    assert(d:execute('help').id==1 and d:execute('bad').id==2 and d:execute('status').id==3)
end)
test('active status is read-only and contains copied positions',function()
    local c,n=fixture(); local data=Observations.read(c,n,false)
    assert(data.state=='active' and data.npc.x==1 and data.player.x==1)
    data.npc.x=90; assert(n:getX()==1 and c.npc==n)
    assert(Commands.new(function() return Observations.read(c,n,false) end):execute('status').state=='completed')
end)
test('inventory aggregates items without returning mutable handles',function()
    local c,n=fixture(); local data=Observations.read(c,n,true)
    assert(data.inventory.total==3 and #data.inventory.items==2 and data.inventory.items[1].count==2)
    assert(data.inventory.items[1].type=='Base.Bandage')
end)
test('inventory scan and output stay bounded',function()
    local c,n,items=fixture(); local reads=0
    items.size=function() return 1000 end
    items.get=function(_,i) reads=reads+1; return {getFullType=function() return 'Base.Item'..i end} end
    local data=Observations.read(c,n,true)
    assert(reads==200 and #data.inventory.items==20 and data.inventory.truncated)
end)
test('absent/unloaded/deferred do not restore or create',function()
    local c=fixture(); c.npc=nil; c.adapter.listNPCs=function() return {} end
    assert(Observations.read(c,nil,true).state=='absent')
    c.adapter.meta.checkpoints={{slot='a'}}; assert(Observations.read(c,nil,true).state=='deferred')
    c.manualUnloaded=true; assert(Observations.read(c,nil,true).state=='unloaded')
end)
test('dead state never exposes a living inventory',function()
    local c=fixture(); c.adapter.meta.dead=true
    local data=Observations.read(c,nil,true); assert(data.state=='dead' and not data.inventory)
end)
test('blocked cleanup and duplicate states do not expose inventory',function()
    local c,n=fixture(); c.adapter.verificationNPC={}
    assert(Observations.read(c,nil,true).state=='blocked')
    c.adapter.verificationNPC=nil; c.adapter.listNPCs=function() return {n,n} end
    assert(Observations.read(c,nil,true).state=='blocked')
    c.adapter.listNPCs=function() return {{}} end
    assert(Observations.read(c,nil,true).state=='blocked')
end)
test('nonresident or incomplete NPC is blocked',function()
    local c=fixture(); c.adapter.isResident=function() return false end
    assert(Observations.read(c,nil,true).state=='blocked')
    c.adapter.isResident=function() return true end; c.adapter.isIncomplete=function() return true end
    assert(Observations.read(c,nil,true).state=='blocked')
end)
test('busy and missing-controller observations remain harmless',function()
    local c=fixture(); c.busy=true
    assert(Observations.read(c,nil,true).state=='busy' and Observations.read(nil,nil,true).state=='unavailable')
end)
test('observation errors return failure without evaluating input',function()
    local d=Commands.new(function() error('native observation fault') end)
    local result=d:execute('inventory'); assert(result.state=='failed' and result.lines[1]=='Observation failed; no action taken.')
end)
print('RESULT '..count..' read-only command checks passed')
''')
