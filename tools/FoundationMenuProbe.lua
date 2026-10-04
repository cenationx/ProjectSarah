-- Temporary UI test entrypoint; all quitting/loading uses the game's real UI.
require 'ISUI/ISButton'
local button
Events.OnGameStart.Add(function()
    if button then button:removeFromUIManager() end
    button=ISButton:new(20,getCore():getScreenHeight()-65,210,30,
        'Test: open game menu',nil,function()
            print('[SarahMenuProbe] OPEN world='..getWorld():getWorld())
            ToggleEscapeMenu(getCore():getKey(KeybindId.MAIN_MENU))
        end)
    button:initialise(); button:addToUIManager()
end)
Events.OnMainMenuEnter.Add(function()
    if button then button:removeFromUIManager(); button=nil end
    print('[SarahMenuProbe] MAIN_MENU controllerNil='..tostring(not SarahFoundation or SarahFoundation.controller==nil))
end)
