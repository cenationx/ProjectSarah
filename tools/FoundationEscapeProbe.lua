-- Observation only, scoped to the disposable native console case.
require 'Sarah/Console'
local last, ticks = '', 0
local function sample(label)
    if not getSpecificPlayer(0) or getWorld():getWorld()~='SarahConsoleNativeCase' then return end
    local s=SarahConsole
    local raw=GameKeyboard.isKeyDownRaw(Keyboard.KEY_ESCAPE)
    local menu=MainScreen and MainScreen.instance and MainScreen.instance.inGame
    local value='raw='..tostring(raw)..' panel='..tostring(s.panel~=nil)..' swallow='..tostring(s.swallow)..' guard='..tostring(s.guard~=nil)..' menu='..tostring(menu)
    if label~='tick' or value~=last then print('[SarahEscapeProbe] '..label..' tick='..ticks..' '..value); last=value end
end
Events.OnTick.Add(function() ticks=ticks+1; sample('tick') end)
Events.OnKeyPressed.Add(function(key) if key==Keyboard.KEY_ESCAPE then sample('release') end end)
Events.OnMainMenuEnter.Add(function() print('[SarahEscapeProbe] MAIN_MENU') end)
