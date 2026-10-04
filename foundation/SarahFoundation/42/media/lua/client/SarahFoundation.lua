require "TimedActions/ISTimedActionQueue"
require "TimedActions/WalkToTimedAction"
local Lifecycle=require "Sarah/Lifecycle"
local Engine=require "Sarah/Engine"
-- Remove prior callbacks on Lua reload so a second controller cannot be registered.
if SarahFoundation then
    Events.OnTick.Remove(SarahFoundation.tick)
    Events.OnFillWorldObjectContextMenu.Remove(SarahFoundation.menu)
    Events.OnSave.Remove(SarahFoundation.save)
    Events.OnPlayerDeath.Remove(SarahFoundation.death)
    if SarahFoundation.render then Events.RenderOpaqueObjectsInWorld.Remove(SarahFoundation.render) end
    if SarahFoundation.reset then
        Events.OnGameStart.Remove(SarahFoundation.reset)
        Events.OnMainMenuEnter.Remove(SarahFoundation.reset)
    end
end
-- Preserve a controller during script reload so failed-cleanup references survive.
SarahFoundation={ticks=0,controller=SarahFoundation and SarahFoundation.controller or nil}
local state=SarahFoundation
state.reset=function()
    state.controller=nil; state.ticks=0; state.disabled=nil; state.renderDisabled=nil
    print("[SarahFoundation] SESSION_RESET")
end
state.tick=function()
    if isClient() or isServer() or not getSpecificPlayer(0) then return end
    if state.disabled then return end
    state.ticks=state.ticks+1
    if state.ticks%120~=0 then return end
    if not state.controller then
        local ok, adapter=pcall(Engine.new)
        if not ok then state.disabled=true; print("[SarahFoundation] DISABLED " .. tostring(adapter)); return end
        state.controller=Lifecycle.new(adapter)
    end
    state.controller:observeDeath()
    if not state.controller.npc and state.ticks==120 then state.controller:ensure() end
end
state.save=function() if state.controller then state.controller:save() end end
state.render=function(playerIndex)
    if state.renderDisabled or not state.controller or not state.controller.npc then return end
    local ok,err=pcall(state.controller.adapter.render,state.controller.npc,playerIndex)
    if not ok then
        state.renderDisabled=true
        print("[SarahFoundation] RENDER_DISABLED " .. tostring(err))
    end
end
state.death=function(player)
    if state.controller and state.controller.npc==player then state.controller.adapter.meta.dead=true end
end
state.menu=function(playerIndex,context,objects,test)
    if test or isClient() or isServer() or playerIndex~=0 or not state.controller then return end
    local controller=state.controller
    context:addOption("Sarah: spawn or restore",nil,function() controller:ensure() end)
    if controller.npc then
        context:addOption("Sarah: save and unload",nil,function() controller:unload() end)
        context:addOption("Sarah: walk here",nil,function()
            ISTimedActionQueue.add(ISWalkToTimedAction:new(controller.npc,getSpecificPlayer(0):getSquare()))
        end)
    end
end
Events.OnTick.Add(state.tick)
Events.OnSave.Add(state.save)
Events.RenderOpaqueObjectsInWorld.Add(state.render)
Events.OnPlayerDeath.Add(state.death)
Events.OnFillWorldObjectContextMenu.Add(state.menu)
Events.OnGameStart.Add(state.reset)
Events.OnMainMenuEnter.Add(state.reset)
print("[SarahFoundation] LOADED; no external AI layer")
