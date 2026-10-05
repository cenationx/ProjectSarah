local Observations={}
local function position(npc)
    if not npc then return nil end
    local okX,x=pcall(npc.getX,npc)
    local okY,y=pcall(npc.getY,npc)
    local okZ,z=pcall(npc.getZ,npc)
    if okX and okY and okZ and type(x)=='number' and type(y)=='number' and type(z)=='number' then
        return {x=x,y=y,z=z}
    end
    if type(npc.x)=='number' and type(npc.y)=='number' and type(npc.z)=='number' then
        return {x=npc.x,y=npc.y,z=npc.z}
    end
    return nil
end
local function isCharacterDead(char)
    if not char then return true end
    if type(char.isDead)=='function' then
        local ok,dead=pcall(char.isDead,char)
        if ok and type(dead)=='boolean' then return dead end
    end
    if char.dead~=nil then
        return char.dead==true
    end
    return false
end
function Observations.read(controller,player,includeInventory)
    local data={state='unavailable'}
    if player then
        local pPos=position(player)
        if pPos then
            local dead=isCharacterDead(player)
            pPos.dead=dead
            pPos.isDead=dead
            pPos.alive=not dead
            data.player=pPos
            data.playerDead=dead
            data.playerAlive=not dead
        end
    end
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
