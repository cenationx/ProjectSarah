require 'ISUI/ISPanel'
require 'ISUI/ISButton'
require 'ISUI/ISTextEntryBox'
require 'ISUI/ISScrollingListBox'
local Commands=require 'Sarah/Commands'
local Observations=require 'Sarah/Observations'
local binding='Sarah Console'
local registered=false
for _,bind in ipairs(keyBinding) do if bind.value==binding then registered=true end end
if not registered then
    table.insert(keyBinding,{value='[Project Sarah]'})
    table.insert(keyBinding,{value=binding,key=Keyboard.KEY_F9})
end
local old=SarahConsole
-- Vanilla opens the pause menu from OnKeyPressed (engine raises it on key release).
-- Keep the original handler so reloads never stack or lose it.
local menuOriginal=old and old.menuOriginal or ToggleEscapeMenu
if old then
    old.close()
    if old.key then Events.OnKeyPressed.Remove(old.key) end
    if old.tick then Events.OnTick.Remove(old.tick) end
    if old.guard then
        Events.OnKeyPressed.Remove(old.guard)
        if menuOriginal then Events.OnKeyPressed.Add(menuOriginal) end
    end
    Events.OnGameStart.Remove(old.reset)
    Events.OnMainMenuEnter.Remove(old.reset)
    Events.OnFillWorldObjectContextMenu.Remove(old.menu)
end
SarahConsole={}
local state=SarahConsole
state.menuOriginal=menuOriginal
state.dispatch=old and old.dispatch or nil
local function stopSarah(reason,action)
    if SarahFoundation and SarahFoundation.controller and SarahFoundation.controller.npc then
        local controller=SarahFoundation.controller
        local owner=action and (action.owner or action.controller)
        if owner and owner~=controller then
            return false,'stale controller'
        end
        local actionNpc=action and action.npc
        if actionNpc and actionNpc~=controller.npc then
            return false,'stale npc'
        end
        local ok,err=pcall(controller.adapter.stop,controller.npc)
        if not ok then return false,tostring(err) end
        if err==false then return false,'adapter stop failed' end
        return true
    end
    return true
end
local function walkSarah(target,onComplete,onFail,action)
    if not SarahFoundation or not SarahFoundation.controller or not SarahFoundation.controller.npc then
        return false,'Sarah controller or NPC unavailable'
    end
    local controller=SarahFoundation.controller
    local owner=action and (action.owner or action.controller)
    if owner and owner~=controller then
        return false,'stale controller'
    end
    local actionNpc=action and action.npc
    if actionNpc and actionNpc~=controller.npc then
        return false,'stale npc'
    end
    if not controller.adapter or not controller.adapter.walk then
        return false,'walk adapter unavailable'
    end
    local validSq=target
    if controller.adapter.validateTarget then
        local valid,sqOrErr=controller.adapter.validateTarget(controller.npc,target)
        if not valid then
            return false,sqOrErr
        end
        validSq=sqOrErr
    end
    local ok,ret=controller.adapter.walk(controller.npc,validSq,onComplete,onFail)
    if not ok then return false,tostring(ret) end
    return true,ret
end
local function getDispatch()
    if not state.dispatch then
        state.dispatch=Commands.new(function(inventory)
            return Observations.read(SarahFoundation and SarahFoundation.controller,getSpecificPlayer(0),inventory)
        end,stopSarah,function()
            -- Private identity provider contract: returns (controller, npc) references directly.
            local ctrl=SarahFoundation and SarahFoundation.controller
            return ctrl,ctrl and ctrl.npc
        end,walkSarah)
    end
    return state.dispatch
end
state.getDispatch=getDispatch
local Panel=ISPanel:derive('SarahConsolePanel')
local function allowed()
    local root=Core.getMyDocumentFolder():gsub('\\','/'):gsub('/$','')
    return root=='G:/Codex/Project Sarah/runtime/isolated' and not isClient() and not isServer() and getSpecificPlayer(0)~=nil
end
function state.conflict(key)
    if not key or key==0 then return 'Console key is unbound; use the context menu or key settings.' end
    if key==Keyboard.KEY_F8 then return 'F8 is used by the map editor; choose another key.' end
    if key>=10000 then return 'Choose a keyboard key for Sarah Console.' end
    for _,bind in ipairs(keyBinding) do
        if bind.key and bind.value~=binding then
            local current=getCore():getKey(bind.value)
            if current==key or getCore():getAltKey(bind.value)==key then return 'Key conflict with '..bind.value..'; rebind Sarah Console in Options.' end
        end
    end
end
function state.close()
    if state.panel then
        state.panel.entry:unfocus(); state.panel:setVisible(false); state.panel:removeFromUIManager()
        state.panel=nil
    end
end
local function tr(key,fallback)
    if getText then
        local val=getText(key)
        if val and val~=key then return val end
    end
    return fallback
end
function Panel:onShortcutHelp() self:executeCommand('help') end
function Panel:onShortcutStatus() self:executeCommand('status') end
function Panel:onShortcutInventory() self:executeCommand('inventory') end
function Panel:onShortcutHistory() self:executeCommand('history') end
function Panel:onShortcutWalkHere() self:executeCommand('walk here') end
function Panel:onShortcutStop() self:executeCommand('stop') end
function Panel:initialise()
    ISPanel.initialise(self)
    self:setWantKeyEvents(true)
    self.history=ISScrollingListBox:new(12,42,self.width-24,self.height-124)
    self.history:initialise(); self.history:instantiate(); self:addChild(self.history)
    self.history:setFont(UIFont.Small,4)

    local btnY=self.height-74
    local btnH=26
    local buttons={
        {key='btnHelp',cmd='help',label=tr('UI_SarahConsole_Help','Help'),x=12,w=72,fn=Panel.onShortcutHelp},
        {key='btnStatus',cmd='status',label=tr('UI_SarahConsole_Status','Status'),x=90,w=80,fn=Panel.onShortcutStatus},
        {key='btnInventory',cmd='inventory',label=tr('UI_SarahConsole_Inventory','Inventory'),x=176,w=96,fn=Panel.onShortcutInventory},
        {key='btnHistory',cmd='history',label=tr('UI_SarahConsole_History','History'),x=279,w=82,fn=Panel.onShortcutHistory},
        {key='btnWalkHere',cmd='walk here',label=tr('UI_SarahConsole_WalkHere','Walk Here'),x=368,w=102,fn=Panel.onShortcutWalkHere},
        {key='btnStop',cmd='stop',label=tr('UI_SarahConsole_Stop','Stop'),x=476,w=72,fn=Panel.onShortcutStop},
    }
    for _,b in ipairs(buttons) do
        local btn=ISButton:new(b.x,btnY,b.w,btnH,b.label,self,b.fn)
        btn.command=b.cmd
        btn:initialise()
        self:addChild(btn)
        self[b.key]=btn
    end

    local inputY=self.height-40
    local inputH=26
    self.entry=ISTextEntryBox:new('',12,inputY,self.width-96,inputH)
    self.entry:initialise(); self.entry:instantiate(); self.entry:setMaxTextLength(128); self:addChild(self.entry)
    self.entry.onCommandEntered=function() self:submit() end

    local run=ISButton:new(self.width-76,inputY,64,inputH,tr('UI_SarahConsole_Run','Run'),self,Panel.submit)
    run:initialise(); self:addChild(run)
    self.btnRun=run

    local close=ISButton:new(self.width-80,10,68,24,tr('UI_SarahConsole_Close','Close'),nil,state.close)
    close:initialise(); self:addChild(close)
    self.btnClose=close

    self.dispatch=getDispatch()
    self:append('Commands: help, status, inventory, walk here, stop, history. Enter submits.')
    local conflict=state.conflict(getCore():getKey(binding))
    self:append(conflict or 'Toggle: '..getKeyName(getCore():getKey(binding))..' (Options > Key bindings)')
end
function Panel:append(line)
    -- Rows are clipped to a compact fixed width; no unbounded history.
    self.history:addItem(tostring(line):sub(1,90),{})
    while #self.history.items>60 do table.remove(self.history.items,1) end
    self.history:setYScroll(-math.max(0,#self.history.items*self.history.itemheight-self.history.height+8))
end
function Panel:executeCommand(commandText)
    if not allowed() then state.close(); return end
    local input=commandText or self.entry:getText()
    local result=self.dispatch:execute(input)
    self:append('> '..input)
    for _,line in ipairs(result.lines) do self:append(line) end
    self:append('#'..result.id..' '..result.state)
    self.entry:setText(''); self.entry:focus()
    return result
end
function Panel:submit()
    return self:executeCommand(self.entry:getText())
end
function Panel:prerender()
    ISPanel.prerender(self)
    self:drawText('Sarah Console',12,14,0.9,0.95,1,1,UIFont.Medium)
end
function Panel:isKeyConsumed(key) return self.entry:isFocused() or key==getCore():getKey(binding) end
function state.open()
    if not allowed() then return end
    if state.panel then state.panel.entry:focus(); return end
    local w,h=560,370
    local panel=Panel:new(math.max(0,(getCore():getScreenWidth()-w)/2),math.max(0,(getCore():getScreenHeight()-h)/2),w,h)
    panel.backgroundColor={r=0.05,g=0.07,b=0.10,a=0.97}
    panel:initialise(); panel:addToUIManager(); state.panel=panel; panel.entry:focus()
end
-- GameKeyboard suppresses UI key callbacks while native text entry has focus.
-- Observe raw key edges on the game thread so the toggle also closes the entry.
-- Eat the release to avoid opening the pause menu after closing with Escape.
state.tick=function()
    if not allowed() then state.close(); return end
    if state.dispatch then state.dispatch:tick() end
    local key=getCore():getKey(binding)
    local alt=getCore():getAltKey(binding)
    local pressed=0
    for _,candidate in ipairs({key,alt}) do
        if candidate>0 and candidate<10000 and GameKeyboard.isKeyDownRaw(candidate) and getCore():isKey(binding,candidate) then pressed=candidate; break end
    end
    local escape=GameKeyboard.isKeyDownRaw(Keyboard.KEY_ESCAPE) or false
    local escapeEdge=state.panel and escape and not state.escapeHeld
    local edge=pressed~=0 and not state.held
    state.held=pressed~=0; state.escapeHeld=escape
    -- Expire an unused swallow shortly after Escape is released (engine raises
    -- the release event on the same or next frame) so a later real Escape works.
    if state.swallow then
        if escape then state.swallowUp=0 else state.swallowUp=(state.swallowUp or 0)+1 end
        if state.swallowUp>=5 then state.swallow=false end
    end
    if escapeEdge then
        GameKeyboard.eatKeyPress(Keyboard.KEY_ESCAPE)
        state.swallow=true; state.swallowUp=0
        state.close()
    elseif edge and not state.conflict(pressed) then
        if state.panel then GameKeyboard.eatKeyPress(pressed); state.close()
        elseif GameKeyboard.isKeyDown(pressed) then GameKeyboard.eatKeyPress(pressed); state.open() end
    end
end
-- Belt and braces for the pause menu: the Escape that closed the console must not
-- also reach the vanilla ToggleEscapeMenu handler, whatever order the engine used.
state.guard=function(key)
    if state.swallow and key==Keyboard.KEY_ESCAPE then state.swallow=false; return end
    if state.menuOriginal then return state.menuOriginal(key) end
end
state.reset=function()
    state.close(); state.held=false; state.escapeHeld=false; state.swallow=false
    if state.dispatch then state.dispatch:reset() end
end
state.menu=function(playerIndex,context,objects,test)
    if not test and playerIndex==0 and allowed() then context:addOption('Sarah: console',nil,state.open) end
end
Events.OnTick.Add(state.tick)
if state.menuOriginal then
    Events.OnKeyPressed.Remove(state.menuOriginal)
    Events.OnKeyPressed.Add(state.guard)
else
    state.guard=nil -- vanilla handler not found: keep previous behavior, never guess
end
Events.OnGameStart.Add(state.reset)
Events.OnMainMenuEnter.Add(state.reset)
Events.OnFillWorldObjectContextMenu.Add(state.menu)
return state
