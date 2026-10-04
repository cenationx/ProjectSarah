local Observations={}
local function position(npc) return {x=npc:getX(),y=npc:getY(),z=npc:getZ()} end
function Observations.read(controller,player,includeInventory)
    local data={state='unavailable'}
    if player then data.player=position(player) end
    if not controller then data.reason='Foundation is not ready.'; return data end
    local a,npc=controller.adapter,controller.npc
    if a.meta.dead or (npc and a.isDead(npc)) then data.state='dead'; return data end
    if controller.travelBlocked or a.verificationNPC then data.state='blocked'; data.reason='Recovery or cleanup is blocked; preserve the case and investigate.'; return data end
    if controller.busy then data.state='busy'; return data end
    local listed=a.listNPCs()
    if #listed>1 or (#listed==1 and listed[1]~=npc) then data.state='blocked'; data.reason='Sarah registration is inconsistent; no action taken.'; return data end
    if not npc then
        data.state=controller.manualUnloaded and 'unloaded' or (a.meta.checkpoints and 'deferred' or 'absent')
        return data
    end
    if a.isIncomplete(npc) or not a.isResident(npc) then data.state='blocked'; data.reason='NPC is incomplete or no longer resident.'; return data end
    data.state='active'; data.npc=position(npc)
    if includeInventory then
        local items=npc:getInventory():getItems()
        local counts,types={},{}
        local total=items:size()
        for i=0,math.min(total,200)-1 do
            local name=tostring(items:get(i):getFullType()):sub(1,96)
            if not counts[name] then counts[name]=0; types[#types+1]=name end
            counts[name]=counts[name]+1
        end
        table.sort(types)
        local summary={total=total,items={},truncated=total>200 or #types>20}
        for i=1,math.min(#types,20) do summary.items[i]={type=types[i],count=counts[types[i]]} end
        data.inventory=summary
    end
    return data
end
return Observations
