"""Read-only command tests execute actual Lua against hostile/mutable fixtures."""
from pathlib import Path
import sys
root=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(root/'tools/dependencies/python'))
from lupa import LuaRuntime
lua=LuaRuntime(unpack_returned_tuples=True)
for name in ('Commands','Observations','Knowledge'):
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
    assert(#d:getHistory()==0 and d.token==action.token and d.sequence==0 and d.session==2)
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
test('walk here synchronous failure during start updates history and returns failed outcome',function()
    local obs={state='active',player={x=12,y=20,z=0},npc={x=10,y=20,z=0}}
    local d=Commands.new(function() return obs end,nil,nil,function(target,onComp,onFail,action)
        onFail(action,'path blocked')
        return true
    end)
    local res=d:execute('walk here')
    assert(res.state=='failed')
    assert(res.lines[1]=='path blocked')
    assert(d.active==nil)
    assert(d.lastAction and d.lastAction.state=='failed')
    local h=d:getHistory()
    assert(h[#h].id==res.id and h[#h].state=='failed')
    local statusRes=d:execute('status')
    assert(statusRes.lines[2]=='Action: idle (last: #'..res.id..' failed)')
end)
test('walk here synchronous completion during start updates history and returns completed outcome',function()
    local obs={state='active',player={x=12,y=20,z=0},npc={x=10,y=20,z=0}}
    local d=Commands.new(function() return obs end,nil,nil,function(target,onComp,onFail,action)
        obs.npc={x=12,y=20,z=0}
        onComp()
        return true
    end)
    local res=d:execute('walk here')
    assert(res.state=='completed')
    assert(res.lines[1]:find('Reached target'))
    assert(d.active==nil)
    assert(d.lastAction and d.lastAction.state=='completed')
    local h=d:getHistory()
    assert(h[#h].id==res.id and h[#h].state=='completed')
    local statusRes=d:execute('status')
    assert(statusRes.lines[2]=='Action: idle (last: #'..res.id..' completed)')
end)
test('session reset resets sequence counter and controller unavailable invalidates active action',function()
    local currentCtrl={npc={id=1}}
    local d=Commands.new(function()
        return {state='active',npc={x=10,y=20,z=0},player={x=12,y=20,z=0}}
    end,nil,function()
        return currentCtrl,currentCtrl and currentCtrl.npc
    end,function() return true end)
    local r1=d:execute('help')
    assert(r1.id==1)
    d:reset()
    assert(d.sequence==0)
    local r2=d:execute('help')
    assert(r2.id==1)
    local rWalk=d:execute('walk here')
    assert(rWalk.state=='running' and d.active)
    currentCtrl=nil
    local valid,reason=d:tick()
    assert(not valid and reason=='controller unavailable')
    assert(d.active==nil and d.lastAction.state=='cancelled')
    assert(not d:completeAction(rWalk.id,d.token,true))
end)
test('old failure callback after session reset with same controller and reused visible request ID is rejected',function()
    local sharedNpc={x=10,y=20,z=0}
    local ctrl={npc=sharedNpc}
    local capturedComplete1,capturedFail1=nil,nil
    local capturedComplete2,capturedFail2=nil,nil
    local walkCallCount=0
    local d=Commands.new(function()
        return {state='active',npc={x=sharedNpc.x,y=sharedNpc.y,z=sharedNpc.z},player={x=12,y=20,z=0}}
    end,nil,function()
        return ctrl,ctrl.npc
    end,function(target,onComplete,onFail,action)
        walkCallCount=walkCallCount+1
        if walkCallCount==1 then
            capturedComplete1=onComplete
            capturedFail1=onFail
        else
            capturedComplete2=onComplete
            capturedFail2=onFail
        end
        return true
    end)
    local r1=d:execute('walk here')
    assert(r1.id==1 and r1.state=='running')
    assert(capturedFail1~=nil)
    local token1=d.active.token
    assert(token1==1)

    d:reset()
    assert(d.sequence==0 and d.active==nil and #d:getHistory()==0)
    assert(d.token==1)

    local r2=d:execute('walk here')
    assert(r2.id==1 and r2.state=='running')
    assert(d.active and d.active.id==1 and d.active.state=='running')
    assert(d.active.token==2)
    assert(d.active.session==2)
    local h=d:getHistory()
    assert(#h==1 and h[1].id==1 and h[1].state=='running')

    local staleOk1,staleErr1=d:completeAction(1,token1,false,'old error',ctrl,sharedNpc,1)
    assert(not staleOk1 and staleErr1=='stale or cancelled')
    local staleOk2,staleErr2=d:completeAction(1,d.active.token,false,'old error',ctrl,sharedNpc,1)
    assert(not staleOk2 and staleErr2=='stale or cancelled')
    assert(d.active and d.active.state=='running')

    capturedFail1(nil,'old path failure')

    assert(d.active and d.active.id==1 and d.active.state=='running')
    h=d:getHistory()
    assert(#h==1 and h[1].id==1 and h[1].state=='running')

    assert(capturedFail2~=nil)
    capturedFail2(nil,'actual path failure')
    assert(d.active==nil)
    assert(d.lastAction.id==1 and d.lastAction.state=='failed' and d.lastAction.reason=='actual path failure')
    h=d:getHistory()
    assert(#h==1 and h[1].id==1 and h[1].state=='failed' and h[1].summary:find('actual path failure'))
end)
test('old completion callback after session reset with same controller and reused visible request ID is rejected',function()
    local sharedNpc={x=10,y=20,z=0}
    local ctrl={npc=sharedNpc}
    local capturedComplete1,capturedFail1=nil,nil
    local capturedComplete2,capturedFail2=nil,nil
    local walkCallCount=0
    local d=Commands.new(function()
        return {state='active',npc={x=sharedNpc.x,y=sharedNpc.y,z=sharedNpc.z},player={x=12,y=20,z=0}}
    end,nil,function()
        return ctrl,ctrl.npc
    end,function(target,onComplete,onFail,action)
        walkCallCount=walkCallCount+1
        if walkCallCount==1 then
            capturedComplete1=onComplete
            capturedFail1=onFail
        else
            capturedComplete2=onComplete
            capturedFail2=onFail
        end
        return true
    end)
    local r1=d:execute('walk here')
    assert(r1.id==1 and r1.state=='running')
    assert(capturedComplete1~=nil)
    local token1=d.active.token

    d:reset()
    assert(d.sequence==0 and d.active==nil and #d:getHistory()==0)

    local r2=d:execute('walk here')
    assert(r2.id==1 and r2.state=='running')
    assert(d.active and d.active.id==1 and d.active.state=='running')
    assert(d.active.token~=token1)
    assert(d.active.session==2)
    local h=d:getHistory()
    assert(#h==1 and h[1].id==1 and h[1].state=='running')

    capturedComplete1()

    assert(d.active and d.active.id==1 and d.active.state=='running')
    h=d:getHistory()
    assert(#h==1 and h[1].id==1 and h[1].state=='running')

    sharedNpc.x=12
    sharedNpc.y=20
    sharedNpc.z=0

    assert(capturedComplete2~=nil)
    capturedComplete2()
    assert(d.active==nil)
    assert(d.lastAction.id==1 and d.lastAction.state=='completed' and d.lastAction.reason:find('Reached target'))
    h=d:getHistory()
    assert(#h==1 and h[1].id==1 and h[1].state=='completed' and h[1].summary:find('Reached target'))
end)
test('look and perceive commands recognized and documented in help',function()
    local d=Commands.new(function() return {state='active'} end)
    local h=d:execute('help')
    assert(h.state=='completed')
    local foundHelp=false
    for _,l in ipairs(h.lines) do
        if l:find('look %-') then foundHelp=true end
    end
    assert(foundHelp,'help must document look command')
    local r1=d:execute('look')
    assert(r1.lines[1]~='Unknown command. Try help.','look must not be unknown')
    local r2=d:execute('perceive')
    assert(r2.lines[1]~='Unknown command. Try help.','perceive must not be unknown')
end)
test('look during active follow is strictly read-only and leaves follow unchanged',function()
    local sharedNpc={x=10,y=20,z=0}
    local ctrl={npc=sharedNpc}
    local d=Commands.new(function()
        return {state='active',npc={x=sharedNpc.x,y=sharedNpc.y,z=sharedNpc.z},player={x=12,y=20,z=0},playerLiveness='alive'}
    end,nil,function()
        return ctrl,ctrl.npc
    end,function(target,onComplete,onFail,action)
        return true
    end,function(target) return true end,
    function()
        return {
            status='sampled',
            lighting='unknown',
            results={},
            counts={candidates=0,processed=0}
        }
    end,nil,function() return 100.0 end)
    local fRes=d:execute('follow')
    assert(fRes.state=='running')
    assert(d.active and d.active.command=='follow')
    local actId=d.active.id
    local actToken=d.active.token
    local actGen=d.active.stepGen
    local curTarget=d.active.currentTarget

    local lRes=d:execute('look')
    assert(lRes.state=='completed')
    assert(lRes.lines[1]:find('Perception: sampled'))

    assert(d.active~=nil,'active follow must remain active')
    assert(d.active.id==actId,'active action ID must not change')
    assert(d.active.token==actToken,'action token must not change')
    assert(d.active.stepGen==actGen,'step generation must not advance')
    assert(d.active.command=='follow','command must remain follow')
    assert(d.active.currentTarget==curTarget,'target must remain unchanged')
    assert(#d.noticeQueue==0,'no notices consumed or generated')
end)
test('look when Sarah is dead or unloaded is rejected and resets knowledge memory',function()
    local k=Knowledge.new()
    k:update({
        results={
            {id='p1',kind='player',geometric='visible',visual='visible',position={x=10,y=20,z=0}}
        }
    },0)
    assert(#k:snapshot(0)==1)

    local stateObs='dead'
    local d=Commands.new(function()
        return {state=stateObs}
    end,nil,nil,nil,nil,function() return {status='sampled',lighting='unknown',results={}} end,k)

    local rDead=d:execute('look')
    assert(rDead.state=='rejected')
    assert(rDead.lines[1]=='Sarah is dead; cannot perceive.')
    assert(#k:snapshot(0)==0,'Knowledge must be reset when Sarah is dead')

    k:update({
        results={
            {id='p1',kind='player',geometric='visible',visual='visible',position={x=10,y=20,z=0}}
        }
    },0)
    assert(#k:snapshot(0)==1)

    stateObs='unloaded'
    local rUnload=d:execute('look')
    assert(rUnload.state=='rejected')
    assert(rUnload.lines[1]=='Sarah is unloaded; cannot perceive.')
    assert(#k:snapshot(0)==0,'Knowledge must be reset when Sarah is unloaded')
end)
test('look fails safely when sampler is missing or throws error',function()
    local dNoSampler=Commands.new(function() return {state='active'} end)
    local r1=dNoSampler:execute('look')
    assert(r1.state=='failed')
    assert(r1.lines[1]=='Perception sampler unavailable.')

    local dErr=Commands.new(function() return {state='active'} end,nil,nil,nil,nil,function()
        error('native sampler crash')
    end)
    local r2=dErr:execute('look')
    assert(r2.state=='failed')
    assert(r2.lines[1]:find('Perception sampling failed'))
end)
test('look reports reentrancy rejection and sampler abort cleanly',function()
    local dReentrant=Commands.new(function() return {state='active'} end,nil,nil,nil,nil,function()
        return {status='reentrancy_rejected',reason='reentrant_call',lighting='unknown',results={}}
    end)
    local r1=dReentrant:execute('look')
    assert(r1.state=='failed')
    assert(r1.lines[1]=='Perception rejected: sampler is reentrant.')

    local dAbort=Commands.new(function() return {state='active'} end,nil,nil,nil,nil,function()
        return {status='aborted',reason='capture_limit_reached',lighting='unknown',results={}}
    end)
    local r2=dAbort:execute('look')
    assert(r2.state=='failed')
    assert(r2.lines[1]=='Perception aborted: capture_limit_reached.')
end)
test('look reports geometry and visual status separately and unknown lighting never implies sight',function()
    local sampleData={
        status='sampled',
        lighting='unknown',
        results={
            {id='z1',kind='zombie',geometric='visible',visual='unknown',reason='lighting_unknown'},
            {id='z2',kind='zombie',geometric='blocked',visual='blocked',reason='opaque_wall'},
            {id='p1',kind='player',geometric='unknown',visual='unknown',reason='coverage_unknown'},
        },
        counts={candidates=3,processed=3}
    }
    local d=Commands.new(function() return {state='active'} end,nil,nil,nil,nil,function()
        return sampleData
    end,nil,function() return 100.0 end)
    local res=d:execute('look')
    assert(res.state=='completed')
    assert(res.lines[1]=='Perception: sampled (candidates: 3, processed: 3)')
    assert(res.lines[2]=='Geometry: 1 visible, 1 blocked, 1 unknown')
    assert(res.lines[3]=='Visual: 0 confirmed (lighting: unknown; unknown lighting never implies sight)')
    assert(res.lines[4]=='Memory: 0 confirmed records')
end)
test('look reports bounded memory snapshot with last-seen age in seconds',function()
    local k=Knowledge.new()
    k:update({
        results={
            {id='p1',kind='player',geometric='visible',visual='visible',position={x=12,y=20,z=0}}
        }
    },100.0)

    local currentTime=104.5
    local d=Commands.new(function() return {state='active'} end,nil,nil,nil,nil,function()
        return {status='sampled',lighting='unknown',results={},counts={candidates=0,processed=0}}
    end,k,function() return currentTime end)

    local res=d:execute('look')
    assert(res.state=='completed')
    local foundMemory=false
    for _,l in ipairs(res.lines) do
        if l:find('%[p1%] player at %(12%.0, 20%.0, 0%), age 4%.5s') then
            foundMemory=true
        end
    end
    assert(foundMemory,'Memory snapshot line with age 4.5s must be present in output')
end)
test('lifecycle resets clear knowledge memory on reset and controller or NPC replacement',function()
    local k=Knowledge.new()
    k:update({
        results={
            {id='p1',kind='player',geometric='visible',visual='visible',position={x=10,y=20,z=0}}
        }
    },10.0)
    assert(#k:snapshot(10.0)==1)

    local ctrl={id='ctrl1'}
    local npcObj={id='npc1'}
    local d=Commands.new(function() return {state='active'} end,nil,function()
        return ctrl,npcObj
    end,nil,nil,function()
        return {status='sampled',lighting='unknown',results={}}
    end,k,function() return 10.0 end)

    -- Commands:reset clears knowledge
    d:reset()
    assert(#k:snapshot(10.0)==0,'d:reset() must reset knowledge')

    -- Re-seed knowledge
    k:update({
        results={
            {id='p1',kind='player',geometric='visible',visual='visible',position={x=10,y=20,z=0}}
        }
    },10.0)
    assert(#k:snapshot(10.0)==1)

    -- Replacing controller identity triggers knowledge reset on next execute
    ctrl={id='ctrl2'}
    local res=d:execute('look')
    assert(res.state=='completed')
    assert(#k:snapshot(10.0)==0,'Controller replacement must reset knowledge')
end)
test('look rejects non-active states (blocked, busy, unavailable) without cancelling active movement',function()
    local sharedState='blocked'
    local d=Commands.new(function()
        return {state=sharedState}
    end,nil,nil,nil,nil,function()
        return {status='sampled',lighting='unknown',results={}}
    end,nil,function() return 100.0 end)

    local rBlocked=d:execute('look')
    assert(rBlocked.state=='rejected')
    assert(rBlocked.lines[1]=='Sarah is blocked; cannot perceive.')

    sharedState='busy'
    local rBusy=d:execute('look')
    assert(rBusy.state=='rejected')
    assert(rBusy.lines[1]=='Sarah is busy; cannot perceive.')

    sharedState='unavailable'
    local rUnavail=d:execute('look')
    assert(rUnavail.state=='rejected')
    assert(rUnavail.lines[1]=='Sarah is unavailable; cannot perceive.')

    -- Ensure checkLifecycle is NOT called by look even if active follow exists
    local checkCalled=false
    local sharedNpc={x=10,y=20,z=0}
    local ctrl={npc=sharedNpc}
    local dActive=Commands.new(function()
        return {state='active',npc=sharedNpc,player={x=12,y=20,z=0},playerLiveness='alive'}
    end,nil,function() return ctrl,ctrl.npc end,function() return true end,function() return true end,
    function() return {status='sampled',lighting='unknown',results={}} end,nil,function() return 100.0 end)

    local fRes=dActive:execute('follow')
    assert(fRes.state=='running')
    assert(dActive.active~=nil)

    -- Override checkLifecycle to track if look invokes it
    local origCheck=dActive.checkLifecycle
    dActive.checkLifecycle=function(self)
        checkCalled=true
        return origCheck(self)
    end

    local lRes=dActive:execute('look')
    assert(lRes.state=='completed')
    assert(checkCalled==false,'look command must never invoke movement-cancelling checkLifecycle')
    assert(dActive.active~=nil,'active follow must remain active after look')
end)
test('missing, throwing, or non-monotonic time fails look closed and never updates knowledge',function()
    local k=Knowledge.new()
    local sampleData={
        status='sampled',
        lighting='unknown',
        results={
            {id='p1',kind='player',geometric='visible',visual='visible',position={x=10,y=20,z=0}}
        }
    }

    -- 1. Missing time provider
    local dNoTime=Commands.new(function() return {state='active'} end,nil,nil,nil,nil,function()
        return sampleData
    end,k,nil)

    local r1=dNoTime:execute('look')
    assert(r1.state=='failed')
    assert(r1.lines[1]:find('time source unavailable %(missing time provider%)'))
    assert(#k:snapshot(0)==0,'Knowledge must NOT be updated when time provider is missing')

    -- 2. Throwing time provider
    local dThrowTime=Commands.new(function() return {state='active'} end,nil,nil,nil,nil,function()
        return sampleData
    end,k,function() error('clock hardware failure') end)

    local r2=dThrowTime:execute('look')
    assert(r2.state=='failed')
    assert(r2.lines[1]:find('time source unavailable %(time provider error'))
    assert(#k:snapshot(0)==0,'Knowledge must NOT be updated when time provider throws')

    -- 3. Non-monotonic time provider
    local clockVal=100.0
    local dMono=Commands.new(function() return {state='active'} end,nil,nil,nil,nil,function()
        return sampleData
    end,k,function() return clockVal end)

    local r3=dMono:execute('look')
    assert(r3.state=='completed')
    assert(#k:snapshot(100.0)==1,'Knowledge updated at t=100.0')

    -- Clock goes backward from 100.0 to 95.0
    clockVal=95.0
    local r4=dMono:execute('look')
    assert(r4.state=='failed')
    assert(r4.lines[1]:find('time source unavailable %(non%-monotonic time'))
    local snap=k:snapshot(100.0)
    assert(#snap==0,'Knowledge must be invalidated on clock reversal rather than retaining old records indefinitely')
end)
test('clock discontinuity in Commands: missing, throwing, or invalid time invalidates knowledge, and recovery does not retain records of unknown elapsed age',function()
    local k=Knowledge.new()
    local clockMode='valid'
    local clockVal=100.0
    local function mockTime()
        if clockMode=='valid' then return clockVal
        elseif clockMode=='error' then error('hardware timer failure')
        elseif clockMode=='nil' then return nil
        elseif clockMode=='nan' then return 0/0
        elseif clockMode=='neg' then return -10.0
        elseif clockMode=='inf' then return 1/0
        end
        return nil
    end

    local sampleCount=0
    local d=Commands.new(function() return {state='active'} end,nil,nil,nil,nil,function()
        sampleCount=sampleCount+1
        return {
            status='sampled',
            lighting='unknown',
            results={
                {id='p'..sampleCount,kind='player',geometric='visible',visual='visible',position={x=10,y=20,z=0}}
            }
        }
    end,k,mockTime)

    -- Step 1: Initial look at t=100.0 succeeds
    local r1=d:execute('look')
    assert(r1.state=='completed')
    assert(#k:snapshot(100.0)==1,'Knowledge holds record p1 at t=100.0')

    -- Step 2: Clock throws error during command execution
    clockMode='error'
    local r2=d:execute('look')
    assert(r2.state=='failed')
    assert(r2.lines[1]:find('time source unavailable %(time provider error'))
    assert(#k:snapshot(100.0)==0,'Knowledge must be invalidated immediately when clock throws')

    -- Step 3: Clock recovers with valid time (e.g. t=115.0)
    clockMode='valid'
    clockVal=115.0
    local r3=d:execute('look')
    assert(r3.state=='completed')
    -- Verify old record p1 is NOT in memory; only newly sampled p3 is present
    local snap3=k:snapshot(115.0)
    assert(#snap3==1,'Only fresh observation present after recovery')
    assert(snap3[1].id=='p3','Stale record p1 must NOT be retained after clock recovery')

    -- Step 4: Clock returns nil during tick
    clockMode='nil'
    d:tick()
    assert(#k:snapshot(115.0)==0,'Knowledge invalidated on nil clock during tick')

    -- Step 5: Clock recovers after nil during tick
    clockMode='valid'
    clockVal=125.0
    d:tick()
    local snap5=k:snapshot(125.0)
    assert(#snap5==0,'Knowledge remains clean upon tick recovery until new perception is sampled')

    -- Step 6: Clock returns NaN (invalid number)
    k:update({
        status='sampled',
        results={{id='p_temp',kind='player',geometric='visible',visual='visible',position={x=10,y=20,z=0}}}
    },125.0)
    assert(#k:snapshot(125.0)==1)

    clockMode='nan'
    local r6=d:execute('look')
    assert(r6.state=='failed')
    assert(r6.lines[1]:find('time source unavailable %(invalid time value%)'))
    assert(#k:snapshot(125.0)==0,'Knowledge invalidated on NaN clock')

    -- Step 7: Recovery after NaN
    clockMode='valid'
    clockVal=135.0
    local r7=d:execute('look')
    assert(r7.state=='completed')
    local snap7=k:snapshot(135.0)
    assert(#snap7==1 and snap7[1].id~='p_temp','Stale temp record not retained after NaN recovery')
end)
test('idle lifecycle check: tick invalidates knowledge and perception on death, unload, and controller replacement without movement command',function()
    local resetPerceptionCount=0
    local mockAdapter={
        resetPerception=function()
            resetPerceptionCount=resetPerceptionCount+1
        end
    }
    local ctrl1={adapter=mockAdapter,npc={id='npc1'}}
    local currentCtrl=ctrl1
    local currentNpc=ctrl1.npc
    local obsState='active'
    local k=Knowledge.new()
    local stopped=false
    local stopCallback=function() stopped=true; return true end

    local d=Commands.new(
        function() return {state=obsState,npc={x=10,y=20,z=0}} end,
        stopCallback,
        function() return currentCtrl,currentNpc end,
        nil,nil,nil,k,function() return 100.0 end,
        function() resetPerceptionCount=resetPerceptionCount+1 end
    )

    -- Initial tick while idle: initializes without invalidating
    assert(d:tick()==true)
    assert(resetPerceptionCount==0)
    assert(d.active==nil)
    assert(stopped==false)

    -- Populate knowledge memory
    k:update({status='sampled',lighting='unknown',results={{id='z1',kind='zombie',geometric='visible',visual='visible',position={x=12,y=20,z=0}}}},100.0)
    assert(#k:snapshot(100.0)==1)

    -- 1. Controller replacement while idle
    local resetPerceptionCount2=0
    local mockAdapter2={
        resetPerception=function()
            resetPerceptionCount2=resetPerceptionCount2+1
        end
    }
    currentCtrl={adapter=mockAdapter2,npc={id='npc1'}}
    assert(d:tick()==true,'tick returns true on controller replacement while idle')
    assert(d.active==nil,'no movement command active')
    assert(stopped==false,'no movement cancelled')
    assert(#k:snapshot(100.0)==0,'knowledge invalidated on controller replacement while idle')
    assert(resetPerceptionCount>0 or resetPerceptionCount2>0,'perception reset on controller replacement while idle')

    -- Populate knowledge again
    k:update({status='sampled',lighting='unknown',results={{id='z2',kind='zombie',geometric='visible',visual='visible',position={x=12,y=20,z=0}}}},101.0)
    assert(#k:snapshot(101.0)==1)

    -- 2. Sarah death while idle
    obsState='dead'
    local tickRes,tickReason=d:tick()
    assert(tickRes==false and tickReason=='dead','tick returns false, dead on death')
    assert(d.active==nil,'no movement command active')
    assert(stopped==false,'no movement cancelled')
    assert(#k:snapshot(101.0)==0,'knowledge invalidated on death while idle')

    -- Populate knowledge again
    obsState='active'
    d:tick()
    k:update({status='sampled',lighting='unknown',results={{id='z3',kind='zombie',geometric='visible',visual='visible',position={x=12,y=20,z=0}}}},102.0)
    assert(#k:snapshot(102.0)==1)

    -- 3. Sarah unload while idle
    obsState='unloaded'
    local tickResU,tickReasonU=d:tick()
    assert(tickResU==false and tickReasonU=='unloaded','tick returns false, unloaded on unload')
    assert(d.active==nil,'no movement command active')
    assert(stopped==false,'no movement cancelled')
    assert(#k:snapshot(102.0)==0,'knowledge invalidated on unload while idle')
end)
test('Console and Commands reset wiring resets adapter sampler, identity, and knowledge while idle',function()
    local resetPerceptionCount=0
    local mockAdapter={
        resetPerception=function()
            resetPerceptionCount=resetPerceptionCount+1
        end
    }
    local ctrl={adapter=mockAdapter,npc={id='npc1'}}
    local k=Knowledge.new()
    k:update({
        results={
            {id='z1',kind='zombie',geometric='visible',visual='visible',position={x=10,y=20,z=0}}
        }
    },50.0)
    assert(#k:snapshot(50.0)==1)

    local d=Commands.new(function() return {state='active'} end,nil,function()
        return ctrl,ctrl.npc
    end,nil,nil,function()
        return {status='sampled',lighting='unknown',results={}}
    end,k,function() return 50.0 end,function()
        mockAdapter.resetPerception()
    end)

    -- d:reset() while IDLE
    assert(d.active==nil,'Sarah is idle')
    d:reset()
    assert(#k:snapshot(50.0)==0,'d:reset() must reset knowledge memory while idle')
    assert(resetPerceptionCount>0,'d:reset() must invoke resetPerception on adapter while idle')

    -- Re-seed knowledge
    k:update({
        results={
            {id='z1',kind='zombie',geometric='visible',visual='visible',position={x=10,y=20,z=0}}
        }
    },50.0)
    assert(#k:snapshot(50.0)==1)
    resetPerceptionCount=0

    -- Controller replacement while IDLE
    ctrl={adapter=mockAdapter,npc={id='npc2'}}
    local sRes=d:execute('status')
    assert(sRes.state=='completed')
    assert(#k:snapshot(50.0)==0,'Controller replacement must reset knowledge memory while idle')
    assert(resetPerceptionCount>0,'Controller replacement must invoke resetPerception on adapter while idle')

    -- Dead observation while IDLE
    k:update({
        results={
            {id='z1',kind='zombie',geometric='visible',visual='visible',position={x=10,y=20,z=0}}
        }
    },50.0)
    assert(#k:snapshot(50.0)==1)
    resetPerceptionCount=0

    local deadObs=false
    local dDead=Commands.new(function()
        return {state=deadObs and 'dead' or 'active'}
    end,nil,function() return ctrl,ctrl.npc end,nil,nil,nil,k,function() return 50.0 end,function()
        mockAdapter.resetPerception()
    end)

    deadObs=true
    local sDead=dDead:execute('status')
    assert(sDead.state=='completed')
    assert(#k:snapshot(50.0)==0,'Dead state observation while idle must reset knowledge')
    assert(resetPerceptionCount>0,'Dead state observation while idle must reset perception')
end)
print('RESULT '..count..' command checks passed')
''')
