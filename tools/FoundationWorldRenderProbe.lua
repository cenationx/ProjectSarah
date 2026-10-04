-- Temporary diagnosis; experimentalDraw must remain false with production hook.
local experimentalDraw=false
local ticks,renderCalls=0,0
local function describe(label,character)
    local square=character:getCurrentSquare()
    print('[SarahWorldRenderProbe] '..label..
        ' xyz='..character:getX()..','..character:getY()..','..character:getZ()..
        ' square='..tostring(square~=nil)..
        ' squareRegistered='..tostring(square and square:getMovingObjects():contains(character))..
        ' objectRegistered='..tostring(getCell():getObjectList():contains(character))..
        ' activeModel='..tostring(character:hasActiveModel())..
        ' modelManager='..tostring(character:isAddedToModelManager())..
        ' doRender='..tostring(character:getDoRender())..
        ' spriteInvisible='..tostring(character:isSpriteInvisible())..
        ' alpha='..character:getAlpha(0)..
        ' targetAlpha='..character:getTargetAlpha(0)..
        ' culled='..tostring(character:isSceneCulled())..
        ' squareCanSee='..tostring(square and square:isCanSee(0)))
end
Events.OnGameStart.Add(function() ticks=0; renderCalls=0 end)
Events.OnTick.Add(function()
    local player=getSpecificPlayer(0)
    if not player then return end
    local controller=SarahFoundation and SarahFoundation.controller
    if not experimentalDraw and controller and not controller.adapter.worldProbeWrapped then
        local adapter=controller.adapter
        local original=adapter.render
        adapter.render=function(npc,index)
            local drawn=original(npc,index)
            if drawn then renderCalls=renderCalls+1 end
            return drawn
        end
        adapter.worldProbeWrapped=true
    end
    ticks=ticks+1
    if ticks~=240 and ticks~=600 and ticks~=1800 then return end
    local ok,err=pcall(function()
        local c=SarahFoundation.controller
        assert(c and c.npc,'Sarah absent')
        assert(#c.adapter.listNPCs()==1,'duplicate Sarah')
        print('[SarahWorldRenderProbe] SAMPLE ticks='..ticks..
            ' world='..getWorld():getWorld()..
            ' playerPreserved='..tostring(IsoPlayer.getInstance()==player)..
            ' renderCalls='..renderCalls)
        describe('PLAYER',player); describe('SARAH',c.npc)
    end)
    if not ok then print('[SarahWorldRenderProbe] FAIL '..tostring(err)) end
end)
-- Experimental candidate only: inspect baseline before enabling at tick 600.
Events.RenderOpaqueObjectsInWorld.Add(function(playerIndex)
    if not experimentalDraw then return end
    if ticks<600 or playerIndex~=0 or not PerformanceSettings.fboRenderChunk then return end
    local c=SarahFoundation and SarahFoundation.controller
    local npc=c and c.npc
    if not npc or npc:isDead() or not npc:isOnScreen() then return end
    local square=npc:getCurrentSquare()
    if not square or not square:isCanSee(playerIndex) then return end
    local light=square:getLightInfo(playerIndex)
    if not light then return end
    npc:renderShadow(npc:getX(),npc:getY(),npc:getZ())
    npc:render(npc:getX(),npc:getY(),npc:getZ(),light,true,false,nil)
    renderCalls=renderCalls+1
end)
