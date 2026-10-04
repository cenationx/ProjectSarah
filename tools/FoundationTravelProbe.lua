-- Disposable SarahTravelCase only. Controlled PLAYER debug travel, never NPC teleport.
local ticks,mode,failed=0,nil,false
local function log(text) print('[SarahTravelProbe] '..text) end
local function checkPlayer(player) assert(IsoPlayer.getInstance()==player,'player instance changed') end
local function closeEnough(a,b) return math.abs(a-b)<0.25 end
Events.OnGameStart.Add(function() ticks=0; mode=nil; failed=false end)
Events.OnTick.Add(function()
    local player=getSpecificPlayer(0)
    if not player or failed then return end
    ticks=ticks+1
    local ok,err=pcall(function()
        if ticks==60 and getWorld():getWorld()=='SarahTravelCase' then
            local m=ModData.getOrCreate('SarahFoundationV1')
            if not m.TravelProbePhase then
                local s=getCell():getGridSquare(math.floor(player:getX())-2,math.floor(player:getY()),math.floor(player:getZ()))
                assert(s and s:isFree(false),'initial separation square unavailable')
                player:teleportTo(s:getX()+0.5,s:getY()+0.5,s:getZ())
                log('PREPARE playerSeparatedBeforeRestore=true')
            end
        end
        if ticks<240 then return end
        assert(getWorld():getWorld()=='SarahTravelCase','wrong disposable world')
        local c=SarahFoundation.controller
        assert(c,'controller absent'); checkPlayer(player)
        local m=c.adapter.meta
        if ticks==240 then
            if m.TravelProbePhase=='away' then
                assert(c.npc==nil and #c.adapter.listNPCs()==0,'NPC restored while away')
                assert(c.adapter.exists(m.checkpoints[1].slot),'away checkpoint absent')
                mode='return'
                log('PASS AWAY_RESTART tagged=0 playerPreserved=true checkpoint='..m.checkpoints[1].slot)
            else
                assert(m.TravelProbePhase==nil,'unexpected probe stage')
                assert(c.npc and #c.adapter.listNPCs()==1,'initial NPC absent or duplicated')
                local n=c.npc
                n:getModData().SarahTravelToken='Travel-20261004'
                m.TravelProbeAnchor={x=n:getX(),y=n:getY(),z=n:getZ()}
                m.TravelProbeWorn=n:getWornItems():size()
                m.TravelProbeInventory=n:getInventory():getItems():size()
                m.TravelProbeGod=player:isGodMod()
                local anchor=m.TravelProbeAnchor
                local origin
                for _,d in ipairs({{-2,0},{0,-2},{2,0},{0,2}}) do
                    local s=getCell():getGridSquare(math.floor(anchor.x)+d[1],math.floor(anchor.y)+d[2],math.floor(anchor.z))
                    if s and s:isFree(false) then origin={x=s:getX()+0.5,y=s:getY()+0.5,z=s:getZ()}; break end
                end
                assert(origin,'no safe return square'); m.TravelProbeOrigin=origin
                local target
                for _,d in ipairs({{36,0},{-36,0},{0,36},{0,-36}}) do
                    local s=getCell():getGridSquare(math.floor(anchor.x)+d[1],math.floor(anchor.y)+d[2],math.floor(anchor.z))
                    if s and s:isFree(false) then target=s; break end
                end
                assert(target,'no loaded departure square')
                player:setGodMod(true)
                player:teleportTo(target:getX()+0.5,target:getY()+0.5,target:getZ())
                mode='out'
                log('INITIAL tagged=1 tokenSet=true controlledPlayerTravel=true')
            end
        end
        if mode=='out' and ticks==480 then
            assert(c.npc==nil and #c.adapter.listNPCs()==0 and not c.travelBlocked,'automatic suspension failed')
            local r=m.checkpoints[1]; local a=m.TravelProbeAnchor
            assert(closeEnough(r.x,a.x) and closeEnough(r.y,a.y) and r.z==a.z,'saved location changed')
            log('PASS AUTO_SUSPEND tagged=0 savedXYZ='..r.x..','..r.y..','..r.z..' slot='..r.slot)
            player:teleportTo(math.floor(a.x)+160.5,math.floor(a.y)+0.5,a.z)
        end
        if mode=='out' and ticks==1440 then
            local a=m.TravelProbeAnchor
            assert(getCell():getGridSquare(math.floor(a.x),math.floor(a.y),math.floor(a.z))==nil,'anchor square still loaded')
            assert(c.npc==nil and #c.adapter.listNPCs()==0,'away NPC exists')
            m.TravelProbePhase='away'; mode='awaitExit'
            log('PASS REAL_SQUARE_UNLOADED tagged=0 checkpointRetained=true playerPreserved=true; EXIT_AND_RESTART')
        end
        if mode=='return' and ticks==600 then
            local p=m.TravelProbeOrigin
            player:teleportTo(p.x,p.y,p.z)
            mode='waitingReturn'; log('RETURN playerMoved=true NPCNotTeleported=true')
        end
        if mode=='waitingReturn' and ticks>=840 and ticks%120==0 and c.npc then
            local n=c.npc; local a=m.TravelProbeAnchor
            assert(#c.adapter.listNPCs()==1 and not c.travelBlocked,'return duplicate or blocked')
            assert(n:getModData().SarahTravelToken=='Travel-20261004','identity token lost')
            assert(closeEnough(n:getX(),a.x) and closeEnough(n:getY(),a.y) and n:getZ()==a.z,'NPC moved from saved location')
            assert(n:getWornItems():size()==m.TravelProbeWorn,'clothing changed')
            assert(n:getInventory():getItems():size()==m.TravelProbeInventory,'inventory changed')
            assert(c:save(),'return save failed')
            player:setGodMod(m.TravelProbeGod)
            m.TravelProbePhase='done'; mode='done'
            log('PASS RETURN_RESTORE tagged=1 tokenPreserved=true clothes='..n:getWornItems():size()..
                ' inventory='..n:getInventory():getItems():size()..' xyz='..n:getX()..','..n:getY()..','..n:getZ()..
                ' playerPreserved=true saved=true originalGodModeRestored=true')
        end
        if mode=='waitingReturn' and ticks==3600 then error('return restoration timed out') end
    end)
    if not ok then failed=true; log('FAIL '..tostring(err)) end
end)
