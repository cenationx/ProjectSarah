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
test('stop with no active request reports stopped and calls engine stop safely',function()
    local stoppedReason=nil
    local d=Commands.new(function() return {state='active'} end,function(reason) stoppedReason=reason end)
    local res=d:execute('stop')
    assert(res.state=='completed' and res.lines[1]=='Sarah stopped; nothing active.' and stoppedReason=='stop_no_active')
    stoppedReason=nil
    local res2=d:execute('stop')
    assert(res2.state=='completed' and res2.lines[1]=='Sarah stopped; nothing active.' and stoppedReason=='stop_no_active')
end)
test('stop when Sarah is dead or unloaded reports cleanly without errors',function()
    local d=Commands.new(function() return {state='dead'} end)
    local res=d:execute('stop')
    assert(res.state=='completed' and res.lines[1]=='Sarah is dead; nothing active to stop.')
    local d2=Commands.new(function() return {state='unloaded'} end)
    local res2=d2:execute('stop')
    assert(res2.state=='completed' and res2.lines[1]=='Sarah is unloaded; nothing active to stop.')
end)
test('active action registration and status reflection',function()
    local d=Commands.new(function() return {state='active'} end)
    local ok,action=d:beginAction('walk here',{x=10,y=20})
    assert(ok and action.id==1 and action.state=='running' and action.token==1 and d.active==action)
    local statusRes=d:execute('status')
    assert(statusRes.state=='completed' and statusRes.lines[2]=='Action: #1 walk here (running)')
    local ok2,err2=d:beginAction('another action')
    assert(not ok2 and err2=='busy')
end)
test('cancellation of active action via stop command',function()
    local stoppedReason,stoppedAction=nil,nil
    local d=Commands.new(function() return {state='active'} end,function(reason,act) stoppedReason=reason; stoppedAction=act end)
    local ok,action=d:beginAction('walk here')
    assert(ok and d.active==action)
    local stopRes=d:execute('stop')
    assert(stopRes.state=='completed')
    assert(stopRes.lines[1]=='Cancelled #1 (walk here).' and stopRes.lines[2]=='Sarah stopped.')
    assert(d.active==nil and action.state=='cancelled')
    assert(stoppedReason=='stopped by user' and stoppedAction==action)
    local statusRes=d:execute('status')
    assert(statusRes.state=='completed' and statusRes.lines[2]=='Action: idle (last: #1 cancelled)')
end)
test('prevention of late completion on cancelled action',function()
    local d=Commands.new(function() return {state='active'} end)
    local ok,action=d:beginAction('walk here')
    assert(ok and action.id==1 and action.token==1)
    d:execute('stop')
    assert(d.active==nil)
    local completed,err=d:completeAction(1,1,true,'Reached tile')
    assert(not completed and err=='stale or cancelled')
    assert(action.state=='cancelled')
    local h=d:getHistory()
    assert(h[1].id==1 and h[1].state=='cancelled')
end)
test('successful completion of active action',function()
    local d=Commands.new(function() return {state='active'} end)
    local ok,action=d:beginAction('walk here')
    assert(ok and action.id==1 and action.token==1)
    local completed,state=d:completeAction(1,1,true,'Target reached')
    assert(completed and state=='completed' and d.active==nil)
    local h=d:getHistory()
    assert(h[1].id==1 and h[1].state=='completed' and h[1].summary=='Target reached')
    local statusRes=d:execute('status')
    assert(statusRes.lines[2]=='Action: idle (last: #1 completed)')
end)
test('stale completion with mismatched token or wrong ID is rejected',function()
    local d=Commands.new(function() return {state='active'} end)
    local ok,action=d:beginAction('walk here')
    assert(ok and action.id==1 and action.token==1)
    assert(not d:completeAction(999,1,true))
    assert(not d:completeAction(1,999,true))
    assert(d.active==action and action.state=='running')
end)
test('action cancellation on session reset',function()
    local d=Commands.new(function() return {state='active'} end)
    local ok,action=d:beginAction('walk here')
    assert(ok and d.active==action)
    d:reset()
    assert(d.active==nil and action.state=='cancelled')
    assert(not d:completeAction(action.id,action.token,true))
    assert(#d:getHistory()==0 and d.token==0)
end)
test('action cancellation on unload, death or blocked observation',function()
    local obsState='active'
    local d=Commands.new(function() return {state=obsState} end)
    local ok,action=d:beginAction('walk here')
    assert(ok and d.active==action)
    obsState='unloaded'
    d:execute('status')
    assert(d.active==nil and action.state=='cancelled')
end)
test('bounded request/result history retention and query',function()
    local d=Commands.new(function() return {state='active'} end)
    for i=1,40 do d:execute('help') end
    local h=d:getHistory()
    assert(#h==30 and h[1].id==11 and h[30].id==40)
    h[1].state='tampered'
    assert(d:getHistory()[1].state=='completed')
    local histRes=d:execute('history')
    assert(histRes.state=='completed' and histRes.lines[1]:find('Recent commands'))
    assert(#histRes.lines>=10)
end)
print('RESULT '..count..' command checks passed')
''')
