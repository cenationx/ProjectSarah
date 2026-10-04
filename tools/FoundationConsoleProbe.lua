-- Observe only the named disposable console case; no commands or keys injected.
require 'Sarah/Console'
Events.OnFillWorldObjectContextMenu.Add(function(playerIndex,context,objects,test)
    if test or playerIndex~=0 or getWorld():getWorld()~='SarahConsoleCase' then return end
    context:addOption('Console test: inventory',nil,function()
        local p=getSpecificPlayer(0); local x,y=p:getX(),p:getY()
        local c=SarahFoundation.controller; local npc=c.npc
        SarahConsole.open()
        SarahConsole.panel.entry:setText('inventory'); SarahConsole.panel:submit()
        print('[SarahConsoleProbe] HARNESS inventory rows='..#SarahConsole.panel.history.items..
            ' sameNPC='..tostring(c.npc==npc)..' samePlayer='..tostring(IsoPlayer.getInstance()==p)..
            ' still='..tostring(p:getX()==x and p:getY()==y))
    end)
end)
local ticks=0
Events.OnTick.Add(function()
    if not getSpecificPlayer(0) then return end
    ticks=ticks+1
    if ticks%600~=240 then return end
    if getWorld():getWorld()~='SarahConsoleCase' then print('[SarahConsoleProbe] FAIL wrong world'); return end
    local p=getSpecificPlayer(0)
    local c=SarahFoundation.controller
    print('[SarahConsoleProbe] SAMPLE key='..getCore():getKey('Sarah Console')..' panel='..tostring(SarahConsole.panel~=nil)..
        ' focused='..tostring(SarahConsole.panel and SarahConsole.panel.entry:isFocused() or false)..
        ' tagged='..tostring(c and #c.adapter.listNPCs())..' playerPreserved='..tostring(IsoPlayer.getInstance()==p)..
        ' x='..p:getX()..' y='..p:getY())
end)
