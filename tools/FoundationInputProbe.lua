-- Read-only diagnostic: capture sampled raw transitions for all native key codes.
local down,ticks,budget={},0,400
local function active()
    return getSpecificPlayer(0) and getWorld():getWorld()=='SarahConsoleNativeCase'
end
Events.OnTick.Add(function()
    if not active() then return end
    ticks=ticks+1
    if ticks==1 then print('[SarahInputProbe] READY scan=1..255') end
    for key=1,255 do
        local now=GameKeyboard.isKeyDownRaw(key) or false
        if now~=(down[key] or false) then
            down[key]=now
            if budget>0 then
                budget=budget-1
                print('[SarahInputProbe] RAW tick='..ticks..' code='..key..' name='..tostring(getKeyName(key))..' down='..tostring(now))
            end
        end
    end
end)
Events.OnKeyPressed.Add(function(key)
    if active() and budget>0 then
        budget=budget-1
        print('[SarahInputProbe] RELEASE tick='..ticks..' code='..key..' name='..tostring(getKeyName(key)))
    end
end)
