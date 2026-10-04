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
    for _,v in ipairs({'jump','status; unload','print(1)','status\n',string.rep('a',129)}) do
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
test('walk here starts tracked action when valid and defaults to player position',function()
    local npcPos={x=10,y=20,z=0}
    local playerPos={x=12,y=20,z=0}
    local walkTarget,walkAction=nil,nil
    local d=Commands.new(function()
        return {state='active',npc=npcPos,player=playerPos}
    end,function() return true end,function() return 'ctrl1' end,function(target,onComp,onFail,action)
        walkTarget=target; walkAction=action; return true
    end)
    local res=d:execute('walk here')
    assert(res.state=='running')
    assert(res.lines[1]=='Walking to (12, 20, 0).')
    assert(d.active and d.active.command=='walk here' and d.active.id==res.id)
    assert(walkTarget and walkTarget.x==12 and walkTarget.y==20 and walkTarget.z==0)
    assert(walkAction and walkAction.id==res.id)
    local h=d:getHistory()
    assert(h[#h].id==res.id and h[#h].state=='running')
end)
test('walk here reports already at target when NPC is already at target coordinates',function()
    local pos={x=10,y=20,z=0}
    local walked=false
    local d=Commands.new(function()
        return {state='active',npc=pos,player=pos}
    end,function() return true end,nil,function() walked=true; return true end)
    local res=d:execute('walk here')
    assert(res.state=='completed')
    assert(res.lines[1]=='Already at target (10, 20, 0).')
    assert(d.active==nil and not walked)
    local h=d:getHistory()
    assert(h[#h].state=='completed' and h[#h].summary:find('Already at'))
end)
test('walk here is rejected when another action is running (busy)',function()
    local pos={x=10,y=20,z=0}
    local d=Commands.new(function()
        return {state='active',npc=pos,player={x=12,y=20,z=0}}
    end,function() return true end,nil,function() return true end)
    local r1=d:execute('walk here')
    assert(r1.state=='running')
    local r2=d:execute('walk here')
    assert(r2.state=='rejected')
    assert(r2.lines[1]:find('Sarah is busy'))
end)
test('walk here is rejected when Sarah is dead, unloaded, or unavailable',function()
    for _,st in ipairs({'dead','unloaded','absent','deferred','unavailable'}) do
        local d=Commands.new(function()
            return {state=st,npc={x=10,y=20,z=0},player={x=12,y=20,z=0}}
        end)
        local res=d:execute('walk here')
        assert(res.state=='rejected' and res.lines[1]:find(st))
    end
end)
test('walk here is rejected on invalid coordinates or different floor',function()
    local d=Commands.new(function()
        return {state='active',npc={x=10,y=20,z=0},player={x=12,y=20,z=0}}
    end,nil,nil,function() return true end)
    local rFloor=d:execute('walk here',{x=12,y=20,z=1})
    assert(rFloor.state=='rejected' and rFloor.lines[1]=='Target is on a different floor.')
    local rNan=d:execute('walk here',{x=0/0,y=20,z=0})
    assert(rNan.state=='rejected' and rNan.lines[1]=='Invalid target coordinates.')
    local rInf=d:execute('walk here',{x=math.huge,y=20,z=0})
    assert(rInf.state=='rejected' and rInf.lines[1]=='Invalid target coordinates.')
end)
test('walk here is rejected when target is too far (> 8 tiles)',function()
    local d=Commands.new(function()
        return {state='active',npc={x=10,y=20,z=0},player={x=25,y=20,z=0}}
    end,nil,nil,function() return true end)
    local res=d:execute('walk here')
    assert(res.state=='rejected' and res.lines[1]=='Target is too far (maximum 8 tiles).')
end)
test('walk here start failure propagates failed outcome and clears active',function()
    local d=Commands.new(function()
        return {state='active',npc={x=10,y=20,z=0},player={x=12,y=20,z=0}}
    end,nil,nil,function() return false,'path engine offline' end)
    local res=d:execute('walk here')
    assert(res.state=='failed')
    assert(res.lines[1]=='Walk failed to start: path engine offline.')
    assert(d.active==nil)
    local h=d:getHistory()
    assert(h[#h].state=='failed')
end)
test('walk here arrival completes action only when NPC position matches target',function()
    local npcPos={x=10,y=20,z=0}
    local compCb=nil
    local d=Commands.new(function()
        return {state='active',npc=npcPos,player={x=12,y=20,z=0}}
    end,function() return true end,nil,function(target,onComp)
        compCb=onComp; return true
    end)
    local res=d:execute('walk here')
    assert(res.state=='running' and compCb)
    -- NPC moved to target
    npcPos.x=12.5; npcPos.y=20.2
    compCb()
    assert(d.active==nil and d.lastAction.state=='completed')
    assert(d.lastAction.reason:find('Reached target'))
    local statusRes=d:execute('status')
    assert(statusRes.lines[2]=='Action: idle (last: #'..res.id..' completed)')
end)
test('walk here arrival stopped before target fails action',function()
    local npcPos={x=10,y=20,z=0}
    local compCb=nil
    local d=Commands.new(function()
        return {state='active',npc=npcPos,player={x=12,y=20,z=0}}
    end,function() return true end,nil,function(target,onComp)
        compCb=onComp; return true
    end)
    local res=d:execute('walk here')
    assert(res.state=='running' and compCb)
    -- NPC stopped early
    npcPos.x=10.8; npcPos.y=20.1
    compCb()
    assert(d.active==nil and d.lastAction.state=='failed')
    assert(d.lastAction.reason:find('Stopped before target'))
end)
test('walk here engine path failure callback sets failed action state',function()
    local failCb=nil
    local d=Commands.new(function()
        return {state='active',npc={x=10,y=20,z=0},player={x=12,y=20,z=0}}
    end,function() return true end,nil,function(target,onComp,onFail)
        failCb=onFail; return true
    end)
    local res=d:execute('walk here')
    assert(res.state=='running' and failCb)
    failCb(nil,'path blocked')
    assert(d.active==nil and d.lastAction.state=='failed')
    assert(d.lastAction.reason=='path blocked')
end)
test('walk here is cancelled by stop command and halts engine timed action',function()
    local stopReason=nil
    local compCb=nil
    local d=Commands.new(function()
        return {state='active',npc={x=10,y=20,z=0},player={x=12,y=20,z=0}}
    end,function(reason) stopReason=reason; return true end,nil,function(target,onComp)
        compCb=onComp; return true
    end)
    local rWalk=d:execute('walk here')
    assert(rWalk.state=='running')
    local rStop=d:execute('stop')
    assert(rStop.state=='completed')
    assert(rStop.lines[1]=='Cancelled #'..rWalk.id..' (walk here).')
    assert(rStop.lines[2]=='Sarah stopped.')
    assert(stopReason=='stopped by user')
    assert(d.active==nil and d.lastAction.state=='cancelled')
    -- Late completion from cancelled engine walk is safely rejected
    compCb()
    assert(d.lastAction.state=='cancelled')
end)
test('walk here timeout after maxTicks cancels action and invokes stop',function()
    local stopReason=nil
    local d=Commands.new(function()
        return {state='active',npc={x=10,y=20,z=0},player={x=12,y=20,z=0}}
    end,function(reason) stopReason=reason; return true end,nil,function() return true end)
    local rWalk=d:execute('walk here')
    assert(rWalk.state=='running')
    for i=1,599 do assert(d:tick()==true) end
    assert(d.active~=nil)
    -- Tick 600 triggers timeout
    local valid,reason=d:tick()
    assert(not valid and reason=='timeout')
    assert(d.active==nil and d.lastAction.state=='cancelled')
    assert(stopReason=='timeout')
end)
test('walk here is invalidated by controller replacement',function()
    local currentCtrl='ctrl1'
    local d=Commands.new(function()
        return {state='active',npc={x=10,y=20,z=0},player={x=12,y=20,z=0}}
    end,function() return true end,function() return currentCtrl end,function() return true end)
    local rWalk=d:execute('walk here')
    assert(rWalk.state=='running')
    currentCtrl='ctrl2'
    local valid,reason=d:tick()
    assert(not valid and reason=='controller replaced')
    assert(d.active==nil and d.lastAction.state=='cancelled')
end)
test('requestWalk convenience method routes directly to walk here',function()
    local walkTarget=nil
    local d=Commands.new(function()
        return {state='active',npc={x=10,y=20,z=0},player={x=12,y=20,z=0}}
    end,function() return true end,nil,function(target) walkTarget=target; return true end)
    local res=d:requestWalk({x=14,y=20,z=0})
    assert(res.state=='running' and res.lines[1]=='Walking to (14, 20, 0).')
    assert(walkTarget and walkTarget.x==14)
end)
test('production controller shape preserves identity and controller replacement with same NPC cancels and isolates replacement',function()
    local sharedNpc={x=10,y=20,z=0}
    local stoppedNpc1,stoppedNpc2=nil,nil
    local adapter1={
        stop=function(n) stoppedNpc1=n; return true end,
        walk=function() return true end,
        validateTarget=function(_,tgt) return true,tgt end
    }
    local adapter2={
        stop=function(n) stoppedNpc2=n; return true end,
        walk=function() return true end,
        validateTarget=function(_,tgt) return true,tgt end
    }
    local ctrl1={npc=sharedNpc,adapter=adapter1}
    local ctrl2={npc=sharedNpc,adapter=adapter2}
    local currentCtrl=ctrl1
    local compCb=nil
    local function stopSarah(reason,action)
        if currentCtrl and currentCtrl.npc then
            local owner=action and (action.owner or action.controller)
            if owner and owner~=currentCtrl then
                return false,'stale controller'
            end
            local actionNpc=action and action.npc
            if actionNpc and actionNpc~=currentCtrl.npc then
                return false,'stale npc'
            end
            local ok,err=pcall(currentCtrl.adapter.stop,currentCtrl.npc)
            if not ok then return false,tostring(err) end
            if err==false then return false,'adapter stop failed' end
            return true
        end
        return true
    end
    local obsState='active'
    local d=Commands.new(function()
        return {state=obsState,npc=sharedNpc,player={x=12,y=20,z=0}}
    end,stopSarah,function()
        return currentCtrl,currentCtrl and currentCtrl.npc
    end,function(target,onComp)
        compCb=onComp; return true
    end)
    -- 1. Verify getIdentity preserves the exact controller reference and NPC reference
    local idCtrl,idNpc=d:getIdentity()
    assert(idCtrl==ctrl1,'getIdentity lost controller reference')
    assert(idNpc==sharedNpc,'getIdentity lost NPC reference')
    -- 2. Start walk here request
    local rWalk=d:execute('walk here')
    assert(rWalk.state=='running')
    assert(d.active and d.active.owner==ctrl1 and d.active.npc==sharedNpc)
    -- 3. Replace controller with ctrl2 (same shared NPC!)
    currentCtrl=ctrl2
    local idCtrl2,idNpc2=d:getIdentity()
    assert(idCtrl2==ctrl2,'getIdentity lost replacement controller reference')
    assert(idNpc2==sharedNpc,'getIdentity lost NPC reference on replacement')
    -- 4. Tick triggers lifecycle check which must cancel the old request
    local valid,reason=d:tick()
    assert(not valid and reason=='controller replaced')
    assert(d.active==nil and d.lastAction.state=='cancelled')
    assert(d.lastAction.reason=='controller replaced')
    -- 5. Late completion from old walk on ctrl1 must not evaluate replacement or complete
    sharedNpc.x=12; sharedNpc.y=20; sharedNpc.z=0
    compCb()
    assert(d.active==nil and d.lastAction.state=='cancelled')
    assert(not d.lastAction.reason:find('Reached target'))
    -- 6. Stop callback targeting replacement controller is refused and leaves replacement untouched
    local stopOk,stopErr=stopSarah('test_stale',{owner=ctrl1,npc=sharedNpc})
    assert(not stopOk and stopErr=='stale controller')
    assert(stoppedNpc2==nil,'replacement controller adapter.stop was erroneously called')
    -- 7. Idle stop on current controller ctrl2 operates cleanly
    local rStop=d:execute('stop')
    assert(rStop.state=='completed')
    assert(stoppedNpc2==sharedNpc,'idle stop should cleanly stop current controller')
end)
test('walk here is invalidated by NPC replacement within the same controller',function()
    local npc1={id=1}
    local npc2={id=2}
    local currentNpc=npc1
    local currentCtrl={
        npc=currentNpc,
        adapter={
            stop=function() return true end,
            walk=function() return true end
        }
    }
    local stoppedAction=nil
    local d=Commands.new(function()
        return {state='active',npc={x=10,y=20,z=0},player={x=12,y=20,z=0}}
    end,function(reason,act)
        stoppedAction=act
        return true
    end,function()
        return currentCtrl,currentCtrl and currentCtrl.npc
    end,function() return true end)
    local rWalk=d:execute('walk here')
    assert(rWalk.state=='running')
    assert(d.active and d.active.owner==currentCtrl and d.active.npc==npc1)
    currentNpc=npc2
    currentCtrl.npc=npc2
    local valid,reason=d:tick()
    assert(not valid and reason=='npc replaced')
    assert(d.active==nil and d.lastAction.state=='cancelled')
    assert(d.lastAction.reason=='npc replaced')
    assert(stoppedAction and stoppedAction.npc==npc1)
    local h=d:getHistory()
    assert(h[#h].id==rWalk.id and h[#h].state=='cancelled' and h[#h].summary=='npc replaced')
end)
test('late completion after NPC replacement does not evaluate replacement position or complete',function()
    local npc1={id=1}
    local npc2={id=2}
    local currentNpc=npc1
    local currentCtrl={
        npc=currentNpc,
        adapter={
            stop=function() return true end,
            walk=function() return true end
        }
    }
    local compCb=nil
    local obsNpc={x=10,y=20,z=0}
    local d=Commands.new(function()
        return {state='active',npc=obsNpc,player={x=12,y=20,z=0}}
    end,function() return true end,function()
        return currentCtrl,currentCtrl and currentCtrl.npc
    end,function(target,onComp)
        compCb=onComp; return true
    end)
    local rWalk=d:execute('walk here')
    assert(rWalk.state=='running' and compCb)
    currentNpc=npc2
    currentCtrl.npc=npc2
    obsNpc.x=12; obsNpc.y=20; obsNpc.z=0
    compCb()
    assert(d.active==nil)
    assert(d.lastAction.state~='completed')
    assert(not d.lastAction.reason:find('Reached target'))
end)
test('timeout and stop callback after NPC replacement leave replacement NPC untouched',function()
    local stoppedNpc=nil
    local npc1={id=1}
    local npc2={id=2}
    local currentNpc=npc1
    local currentCtrl={
        npc=npc1,
        adapter={
            stop=function(n) stoppedNpc=n; return true end
        }
    }
    local function stopSarah(reason,action)
        if currentCtrl and currentCtrl.npc then
            local actionNpc=action and action.npc
            if actionNpc and actionNpc~=currentCtrl.npc then
                return false,'stale npc'
            end
            currentCtrl.adapter.stop(currentCtrl.npc)
            return true
        end
        return true
    end
    local d=Commands.new(function()
        return {state='active',npc={x=10,y=20,z=0},player={x=12,y=20,z=0}}
    end,stopSarah,function()
        return currentCtrl,currentCtrl and currentCtrl.npc
    end,function() return true end)
    local rWalk=d:execute('walk here')
    assert(rWalk.state=='running')
    assert(d.active.npc==npc1)
    currentCtrl.npc=npc2
    currentNpc=npc2
    local rStop=d:execute('stop')
    assert(rStop.state=='failed')
    assert(rStop.lines[2]:find('stale npc'))
    assert(stoppedNpc==nil)
end)
print('RESULT '..count..' command checks passed')
''')
