"""Actual console module with simulated native UI, key edges and session events."""
from pathlib import Path
import sys
root=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(root/'tools/dependencies/python'))
from lupa import LuaRuntime
lua=LuaRuntime(unpack_returned_tuples=True)
source=root/'foundation/SarahFoundation/42/media/lua/client/Sarah'
lua.globals().ConsoleSource=(source/'Console.lua').read_text()
lua.globals().Commands=lua.execute((source/'Commands.lua').read_text())
lua.execute(r'''
local count=0
local function test(name,fn) fn(); count=count+1; print('PASS '..name) end
local function event()
    local e={callbacks={}}
    e.Add=function(fn) e.callbacks[#e.callbacks+1]=fn end
    e.Remove=function(fn) for i=#e.callbacks,1,-1 do if e.callbacks[i]==fn then table.remove(e.callbacks,i) end end end
    return e
end
Events={OnKeyPressed=event(),OnTick=event(),OnGameStart=event(),OnMainMenuEnter=event(),OnFillWorldObjectContextMenu=event()}
local Base={}
function Base:derive() local c={}; c.__index=c; return setmetatable(c,{__index=self}) end
function Base:new(x,y,w,h) return setmetatable({x=x,y=y,width=w,height=h,items={}}, {__index=self}) end
for _,name in ipairs({'initialise','instantiate','setWantKeyEvents','addChild','addToUIManager','removeFromUIManager','setVisible','setMaxTextLength','prerender','drawText','setFont'}) do Base[name]=function() end end
function Base:addItem(text) self.items[#self.items+1]={text=text} end
function Base:setYScroll(v) self.scroll=v end
function Base:setFont() self.itemheight=24 end
function Base:focus() self.focused=true; focused=self end
function Base:unfocus() self.focused=false; if focused==self then focused=nil end end
function Base:isFocused() return self.focused end
function Base:getText() return self.text or '' end
function Base:setText(v) self.text=v end
ISPanel=Base; ISScrollingListBox=Base; ISButton=Base
ISTextEntryBox=Base:derive()
function ISTextEntryBox:new(text,x,y,w,h) local o=Base.new(self,x,y,w,h); o.text=text; return o end
UIFont={Small=1,Medium=2}
Keyboard={KEY_F9=67,KEY_F8=66,KEY_ESCAPE=1}
keyBinding={{value='Forward',key=17}}
local keys={['Sarah Console']=67,Forward=17}; local alts={}
local raw={}; local eaten={}
GameKeyboard={isKeyDownRaw=function(k) return raw[k] or false end,isKeyDown=function(k) return not focused and (raw[k] or false) end,eatKeyPress=function(k) eaten[k]=true end}
local core={getKey=function(_,n) return keys[n] or 0 end,getAltKey=function(_,n) return alts[n] or 0 end,isKey=function(_,n,k) return keys[n]==k or alts[n]==k end,getScreenWidth=function() return 1280 end,getScreenHeight=function() return 720 end}
getCore=function() return core end
local root='G:/Codex/Project Sarah/runtime/isolated'; local client=false
Core={getMyDocumentFolder=function() return root end}
isClient=function() return client end; isServer=function() return false end
getSpecificPlayer=function() return {} end; getKeyName=function() return 'F9' end
local obsState='active'
local obsNpc={x=10,y=20,z=0}
local obsPlayer={x=12,y=20,z=0}
require=function(n) if n=='Sarah/Commands' then return Commands elseif n=='Sarah/Observations' then return {read=function() return {state=obsState or 'active',npc=obsNpc,player=obsPlayer} end} end end
local function reload() return assert(load(ConsoleSource))() end
local s=reload()
local function release() raw={}; s.tick() end
test('key edge opens once; holding does not toggle repeatedly',function()
    raw[67]=true; s.tick(); local p=s.panel; assert(p and p.entry:isFocused())
    for i=1,20 do s.tick(); assert(s.panel==p) end
    release(); raw[67]=true; s.tick(); assert(not s.panel and eaten[67]); release()
end)
test('Escape closes focused input and eats its game release',function()
    s.open(); local p=s.panel; raw[1]=true; s.tick(); assert(not s.panel and not p.entry:isFocused() and eaten[1]); release()
end)
test('primary and runtime alternate conflicts refuse keyboard opening',function()
    keys.Forward=67; raw[67]=true; s.tick(); assert(not s.panel and s.conflict(67)); release()
    keys.Forward=17; alts.Forward=67; raw[67]=true; s.tick(); assert(not s.panel and s.conflict(67)); release(); alts.Forward=0
end)
test('rebound primary and alternate keys follow current runtime values',function()
    keys['Sarah Console']=65; raw[65]=true; s.tick(); assert(s.panel); release(); s.close()
    alts['Sarah Console']=64; raw[64]=true; s.tick(); assert(s.panel); release(); s.close()
    keys['Sarah Console']=67; alts['Sarah Console']=0
end)
test('unbound, F8 and mouse binding are refused with menu fallback',function()
    assert(s.conflict(0) and s.conflict(66) and s.conflict(10001))
    keys['Sarah Console']=0; s.open(); assert(s.panel); s.close(); keys['Sarah Console']=67
end)
test('other text entry never opens the console; exact profile and multiplayer gates',function()
    focused={}; raw[67]=true; s.tick(); assert(not s.panel); focused=nil; release()
    root='C:/Users/test/Zomboid'; s.open(); assert(not s.panel)
    root='G:/Codex/Project Sarah/runtime/isolated'; client=true; s.open(); assert(not s.panel); client=false
end)
test('history stays bounded and reset unfocuses/removes the panel',function()
    s.open(); for i=1,100 do s.panel:append(string.rep('x',200)) end
    assert(#s.panel.history.items==60 and #s.panel.history.items[60].text==90)
    local p=s.panel; s.reset(); assert(not s.panel and not p.entry:isFocused())
end)
test('module reload closes old UI and retains one callback per event',function()
    s.open(); local p=s.panel; s=reload(); assert(not p.entry:isFocused() and not s.panel)
    for _,name in ipairs({'OnTick','OnGameStart','OnMainMenuEnter','OnFillWorldObjectContextMenu'}) do assert(#Events[name].callbacks==1) end
    assert(#Events.OnKeyPressed.callbacks==0)
end)
local function fire(key) for _,cb in ipairs({table.unpack(Events.OnKeyPressed.callbacks)}) do cb(key) end end
test('Escape-closing the console cannot open the pause menu; later Escape still can',function()
    menuOpened=0; ToggleEscapeMenu=function(k) if k==1 then menuOpened=menuOpened+1 end end
    Events.OnKeyPressed.Add(ToggleEscapeMenu); s=reload()
    assert(#Events.OnKeyPressed.callbacks==1 and Events.OnKeyPressed.callbacks[1]==s.guard)
    s.open(); raw[1]=true; s.tick(); assert(not s.panel and s.swallow)
    raw={}; fire(1); s.tick(); assert(menuOpened==0 and not s.swallow)   -- release swallowed once
    fire(1); assert(menuOpened==1)                                       -- next real Escape works
end)
test('unused swallow expires after Escape is up; other keys and idle Escape pass through',function()
    s.open(); raw[1]=true; s.tick(); assert(s.swallow)
    for i=1,10 do s.tick() end raw={}                                    -- held, then released
    for i=1,5 do s.tick() end assert(not s.swallow)
    menuOpened=0; fire(1); assert(menuOpened==1)
    s.swallow=true; fire(67); assert(s.swallow); s.reset(); assert(not s.swallow)
end)
test('reload restores vanilla handler without stacking guards; missing handler is safe',function()
    local original=s.menuOriginal; s=reload()
    assert(#Events.OnKeyPressed.callbacks==1 and Events.OnKeyPressed.callbacks[1]==s.guard and s.menuOriginal==original)
    s=reload(); assert(#Events.OnKeyPressed.callbacks==1)
    menuOpened=0; fire(1); assert(menuOpened==1)
    Events.OnKeyPressed.Remove(s.guard); Events.OnKeyPressed.Add(original)
    local keep=SarahConsole; SarahConsole=nil; ToggleEscapeMenu=nil; s=reload()
    assert(s.guard==nil and s.menuOriginal==nil and #Events.OnKeyPressed.callbacks==1)
    ToggleEscapeMenu=original; SarahConsole=nil; s=reload()
end)
test('stop command executed from console panel reports stopped and appends outcome',function()
    s.open()
    s.panel.entry:setText('stop')
    s.panel:submit()
    local foundCmd,foundResult=false,false
    for _,item in ipairs(s.panel.history.items) do
        if item.text=='> stop' then foundCmd=true end
        if item.text=='Sarah stopped; nothing active.' then foundResult=true end
    end
    assert(foundCmd and foundResult)
    s.close()
end)
test('history command executed from console panel displays formatted recent requests',function()
    s.open()
    s.panel.entry:setText('history')
    s.panel:submit()
    local found=false
    for _,item in ipairs(s.panel.history.items) do
        if item.text:find('Recent commands') then found=true end
    end
    assert(found)
    s.close()
end)
test('session reset clears console dispatch and resets action tracking',function()
    s.open()
    local ok,action=s.panel.dispatch:beginAction('walk here')
    assert(ok and s.panel.dispatch.active)
    s.reset()
    assert(not s.panel and s.dispatch.active==nil and #s.dispatch:getHistory()==0)
end)
test('lifecycle monitoring invalidates active action while console is closed',function()
    s.open()
    local ok,action=s.panel.dispatch:beginAction('walk here')
    assert(ok and s.panel.dispatch.active)
    s.close()
    assert(not s.panel)
    obsState='dead'
    s.tick()
    assert(s.dispatch.active==nil)
    local h=s.dispatch:getHistory()
    assert(h[#h].state=='cancelled' and h[#h].summary=='dead')
    obsState='active'
end)
test('walk here command executed from console panel reports running and appends outcome',function()
    SarahFoundation={
        controller={
            npc={},
            adapter={
                walk=function(npc,sq,onComp,onFail) return true,{} end,
                stop=function() return true end,
                validateTarget=function(npc,tgt) return true,tgt end
            }
        }
    }
    s.open()
    s.panel.entry:setText('walk here')
    s.panel:submit()
    local foundCmd,foundResult=false,false
    for _,item in ipairs(s.panel.history.items) do
        if item.text=='> walk here' then foundCmd=true end
        if item.text:find('Walking to %(12, 20, 0%)') then foundResult=true end
    end
    assert(foundCmd and foundResult)
    s.close()
end)
test('state.getDispatch export is available and context menu walk here routes through it',function()
    assert(s.getDispatch and type(s.getDispatch)=='function')
    local dispatch=s.getDispatch()
    assert(dispatch)
    -- Reset dispatch to clear earlier walk
    dispatch:reset()
    local res=dispatch:execute('walk here')
    assert(res.state=='running')
    assert(dispatch.active and dispatch.active.command=='walk here')
    dispatch:reset()
end)
test('console dispatch stop callback rejects stale NPC and leaves replacement NPC untouched',function()
    local stoppedNpc=nil
    local npc1={id=1}
    local npc2={id=2}
    SarahFoundation={
        controller={
            npc=npc1,
            adapter={
                walk=function(npc,sq,onComp,onFail) return true,{} end,
                stop=function(n) stoppedNpc=n; return true end,
                validateTarget=function(npc,tgt) return true,tgt end
            }
        }
    }
    local dispatch=s.getDispatch()
    dispatch:reset()
    local res=dispatch:execute('walk here')
    assert(res.state=='running')
    assert(dispatch.active and dispatch.active.npc==npc1)
    -- Replace NPC within controller
    SarahFoundation.controller.npc=npc2
    -- Execute stop command via dispatch
    local stopRes=dispatch:execute('stop')
    assert(stopRes.state=='failed')
    assert(stopRes.lines[2]:find('stale npc'))
    assert(stoppedNpc==nil)
    dispatch:reset()
end)
print('RESULT '..count..' simulated console checks passed')
''')
