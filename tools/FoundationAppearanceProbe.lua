-- Temporary read-only model viewer for the actual foundation NPC.
-- Deploy only in a backed-up disposable world; not a production UI feature.
require 'ISUI/ISPanel'
require 'ISUI/ISUI3DModel'
local ticks, panel = 0, nil
Events.OnGameStart.Add(function() ticks=0 end)
Events.OnTick.Add(function()
    local player=getSpecificPlayer(0)
    if not player then return end
    ticks=ticks+1
    if ticks~=240 then return end
    local ok,err=pcall(function()
        local controller=SarahFoundation and SarahFoundation.controller
        assert(controller and controller.npc,'Sarah absent')
        local npc=controller.npc
        assert(not npc:isDead() and npc:isNpc(),'invalid NPC')
        assert(#controller.adapter.listNPCs()==1,'duplicate Sarah')
        assert(IsoPlayer.getInstance()==player,'local player replaced')
        print('[SarahAppearanceProbe] NPC world='..getWorld():getWorld()..
            ' name='..npc:getDescriptor():getForename()..
            ' worn='..npc:getWornItems():size()..
            ' xyz='..npc:getX()..','..npc:getY()..','..npc:getZ()..
            ' playerXYZ='..player:getX()..','..player:getY()..','..player:getZ())
        local worn=npc:getWornItems()
        for i=0,worn:size()-1 do
            local item=worn:get(i):getItem()
            print('[SarahAppearanceProbe] WORN '..item:getFullType())
        end
        panel=ISPanel:new(30,100,370,570)
        panel.backgroundColor={r=0.18,g=0.18,b=0.18,a=1}
        panel:initialise(); panel:addToUIManager()
        panel.render=function(self)
            self:drawText('Actual Sarah NPC - appearance probe',12,12,1,1,1,1,UIFont.Small)
            self:drawText('Drag model to inspect another angle',12,35,1,1,1,1,UIFont.Small)
        end
        local model=ISUI3DModel:new(10,65,350,485)
        panel:addChild(model)
        model:setCharacter(npc)
        model:setState('idle'); model:setDirection(IsoDirections.S)
        model:setIsometric(false)
        assert(model:getCharacter()==npc,'viewer did not bind actual NPC')
        print('[SarahAppearanceProbe] VIEWER actualNPC=true playerPreserved=true')
    end)
    if not ok then print('[SarahAppearanceProbe] FAIL '..tostring(err)) end
end)
Events.OnMainMenuEnter.Add(function()
    if panel then panel:removeFromUIManager(); panel=nil end
end)
