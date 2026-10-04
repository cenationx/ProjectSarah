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
test('public observations contain no controller, adapter, or NPC handles',function()
    local c,n=fixture()
    local data=Observations.read(c,n,true)
    assert(data.controller==nil,'controller handle leaked in observation')
    assert(data.adapter==nil,'adapter handle leaked in observation')
    assert(data.npc~=n,'NPC handle leaked in observation')
    assert(type(data.npc)=='table' and data.npc.x==1 and data.npc.y==2 and data.npc.z==0)
    assert(data.player~=n,'player handle leaked in observation')
    assert(type(data.player)=='table' and data.player.x==1)
    assert(data.inventory and data.inventory.total==3)
    for _,item in ipairs(data.inventory.items) do
        assert(type(item.type)=='string' and type(item.count)=='number')
    end
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
    assert(ok and action.id==1 and action.state=='running' and action.token==1 and d.active.id==action.id)
    local statusRes=d:execute('status')
    assert(statusRes.state=='completed' and statusRes.lines[2]=='Action: #1 walk here (running)')
    local ok2,err2=d:beginAction('another action')
    assert(not ok2 and err2=='busy')
end)
test('cancellation of active action via stop command',function()
    local stoppedReason,stoppedAction=nil,nil
    local d=Commands.new(function() return {state='active'} end,function(reason,act) stoppedReason=reason; stoppedAction=act end)
    local ok,action=d:beginAction('walk here')
    assert(ok and d.active.id==action.id)
    local stopRes=d:execute('stop')
    assert(stopRes.state=='completed')
    assert(stopRes.lines[1]=='Cancelled #1 (walk here).' and stopRes.lines[2]=='Sarah stopped.')
    assert(d.active==nil and d.lastAction.state=='cancelled')
    assert(stoppedReason=='stopped by user' and stoppedAction.id==action.id)
    local statusRes=d:execute('status')
    assert(statusRes.state=='completed' and statusRes.lines[2]=='Action: idle (last: #1 cancelled)')
end)
test('stop callback exception propagates failure outcome and history',function()
    local d=Commands.new(function() return {state='active'} end,function() error('hardware stop error') end)
    local ok,action=d:beginAction('walk here')
    local stopRes=d:execute('stop')
    assert(stopRes.state=='failed')
    assert(stopRes.lines[1]=='Cancelled #1 (walk here).')
    assert(stopRes.lines[2]:find('Engine stop failed'))
    assert(d.active==nil and d.lastAction.state=='cancelled')
    local h=d:getHistory()
    assert(h[#h].state=='failed' and h[#h].summary:find('Stop failed'))
end)
test('stop callback failure return propagates failure outcome and history',function()
    local d=Commands.new(function() return {state='active'} end,function() return false,'uninterruptible animation' end)
    local ok,action=d:beginAction('walk here')
    local stopRes=d:execute('stop')
    assert(stopRes.state=='failed')
    assert(stopRes.lines[1]=='Cancelled #1 (walk here).')
    assert(stopRes.lines[2]=='Engine stop failed: uninterruptible animation.')
    assert(d.active==nil and d.lastAction.state=='cancelled')
    local h=d:getHistory()
    assert(h[#h].state=='failed' and h[#h].summary=='Stop failed: uninterruptible animation')
end)
test('idle stop callback failure propagates failure outcome and history',function()
    local d=Commands.new(function() return {state='active'} end,function() return false,'adapter offline' end)
    local stopRes=d:execute('stop')
    assert(stopRes.state=='failed' and stopRes.lines[1]=='Engine stop failed: adapter offline.')
    local h=d:getHistory()
    assert(h[#h].state=='failed' and h[#h].summary=='Stop failed: adapter offline')
end)
test('prevention of late completion on cancelled action',function()
    local d=Commands.new(function() return {state='active'} end)
    local ok,action=d:beginAction('walk here')
    assert(ok and action.id==1 and action.token==1)
    d:execute('stop')
    assert(d.active==nil)
    local completed,err=d:completeAction(1,1,true,'Reached tile')
    assert(not completed and err=='stale or cancelled')
    assert(d.lastAction.state=='cancelled')
    local h=d:getHistory()
    assert(h[1].id==1 and h[1].state=='cancelled')
end)
test('death or unload before completion without status query rejects completion',function()
    local obsState='active'
    local d=Commands.new(function() return {state=obsState} end)
    local ok,action=d:beginAction('walk here')
    assert(ok and d.active)
    obsState='dead'
    -- Direct completion without intervening status or inventory query
    local ok2,err2=d:completeAction(action.id,action.token,true,'arrived')
    assert(not ok2 and err2=='stale or cancelled')
    assert(d.active==nil and d.lastAction.reason=='dead')
    assert(d:getHistory()[1].state=='cancelled' and d:getHistory()[1].summary=='dead')

    -- Unload without intervening query
    obsState='active'
    local ok3,action2=d:beginAction('walk here')
    assert(ok3 and d.active)
    obsState='unloaded'
    local ok4,err4=d:completeAction(action2.id,action2.token,true,'arrived')
    assert(not ok4 and err4=='stale or cancelled')
    assert(d.active==nil and d.lastAction.reason=='unloaded')
    assert(d:getHistory()[2].state=='cancelled' and d:getHistory()[2].summary=='unloaded')
end)
test('controller replacement rejects stale completion and invalidates action',function()
    local currentCtrl={id='ctrl1'}
    local d=Commands.new(function() return {state='active'} end,nil,function() return currentCtrl end)
    local ok,action=d:beginAction('walk here')
    assert(ok and d.active)
    currentCtrl={id='ctrl2'}
    local ok2,err2=d:completeAction(action.id,action.token,true,'arrived')
    assert(not ok2 and err2=='stale or cancelled')
    assert(d.active==nil and d.lastAction.reason=='controller replaced')
    assert(d:getHistory()[1].state=='cancelled' and d:getHistory()[1].summary=='controller replaced')
end)
test('stale callback targeting replacement controller is rejected',function()
    local currentCtrl={id='ctrl1'}
    local d=Commands.new(function() return {state='active'} end,nil,function() return currentCtrl end)
    local ok,action=d:beginAction('walk here')
    -- Stale callback passing an old/unrelated controller object
    local ok2,err2=d:completeAction(action.id,action.token,true,'arrived',{id='old_foreign_ctrl'})
    assert(not ok2 and err2=='stale or cancelled')
    assert(d.active) -- Still running on original controller
    -- Valid completion passing matching controller
    local ok3,state3=d:completeAction(action.id,action.token,true,'arrived',currentCtrl)
    assert(ok3 and state3=='completed')
end)
test('stop callback scopes to controller identity and rejects stale controller',function()
    local currentCtrl={id='ctrl1'}
    local stoppedFor=nil
    local function stopCb(reason,act)
        if act and act.owner and act.owner~=currentCtrl then return false,'stale controller' end
        stoppedFor=act and act.owner
        return true
    end
    local d=Commands.new(function() return {state='active'} end,stopCb,function() return currentCtrl end)
    local ok,act=d:beginAction('walk here')
    assert(ok and d.active)
    local res=d:execute('stop')
    assert(res.state=='completed' and stoppedFor==currentCtrl)

    currentCtrl={id='ctrl1'}
    local ok2,act2=d:beginAction('walk here')
    currentCtrl={id='ctrl2'}
    local res2=d:execute('stop')
    assert(res2.state=='failed' and res2.lines[2]:find('stale controller'))
end)
test('action API returns shallow-copied records protecting internal state',function()
    local d=Commands.new(function() return {state='active'} end)
    local ok,action=d:beginAction('walk here',{x=10,y=20})
    action.state='tampered'; action.token=999; action.id=999
    assert(d.active.state=='running' and d.active.token==1 and d.active.id==1)
    local ok2,actionCopy=d:cancelActive('test cancel')
    actionCopy.state='tampered'
    assert(d.lastAction.state=='cancelled')
    local h=d:getHistory()
    h[1].state='tampered'
    assert(d:getHistory()[1].state=='cancelled')
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
    assert(d.active and d.active.state=='running')
end)
test('action cancellation on session reset',function()
    local d=Commands.new(function() return {state='active'} end)
    local ok,action=d:beginAction('walk here')
    assert(ok and d.active)
    d:reset()
    assert(d.active==nil and d.lastAction==nil)
    assert(not d:completeAction(action.id,action.token,true))
    assert(#d:getHistory()==0 and d.token==0)
end)
test('action cancellation on unload, death or blocked observation',function()
    local obsState='active'
    local d=Commands.new(function() return {state=obsState} end)
    local ok,action=d:beginAction('walk here')
    assert(ok and d.active)
    obsState='unloaded'
    d:execute('status')
    assert(d.active==nil and d.lastAction.state=='cancelled')
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
