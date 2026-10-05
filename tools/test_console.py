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
Events={OnKeyPressed=event(),OnTick=event(),OnGameStart=event(),OnMainMenuEnter=event(),OnFillWorldObjectContextMenu=event(),OnResolutionChange=event()}
local Base={}
function Base:derive() local c={}; c.__index=c; return setmetatable(c,{__index=self}) end
function Base:new(x,y,w,h) return setmetatable({x=x,y=y,width=w,height=h,items={},visible=true}, {__index=self}) end
for _,name in ipairs({'initialise','instantiate','setWantKeyEvents','addChild','addToUIManager','removeFromUIManager','setMaxTextLength','prerender','drawText','setFont'}) do Base[name]=function() end end
function Base:setVisible(v) self.visible=v end
function Base:getIsVisible() return self.visible~=false end
function Base:setX(x) self.x=x end
function Base:setY(y) self.y=y end
function Base:setHeight(h) self.height=h end
function Base:bringToTop() self.top=true end
function Base:addItem(text) self.items[#self.items+1]={text=text} end
function Base:setYScroll(v) self.scroll=v end
function Base:setFont() self.itemheight=24 end
function Base:focus() self.focused=true; focused=self end
function Base:unfocus() self.focused=false; if focused==self then focused=nil end end
function Base:isFocused() return self.focused end
function Base:getText() return self.text or '' end
function Base:setText(v) self.text=v end
ISPanel=Base; ISScrollingListBox=Base
ISButton=Base:derive()
function ISButton:new(x,y,w,h,title,target,onclick)
    local o=Base.new(self,x,y,w,h)
    o.title=title; o.target=target; o.onclick=onclick
    return o
end
function ISButton:click()
    if self.onclick then return self.onclick(self.target,self) end
end
ISTextEntryBox=Base:derive()
function ISTextEntryBox:new(text,x,y,w,h) local o=Base.new(self,x,y,w,h); o.text=text; return o end
UIFont={Small=1,Medium=2}
Keyboard={KEY_F9=67,KEY_F8=66,KEY_ESCAPE=1}
keyBinding={{value='Forward',key=17}}
local keys={['Sarah Console']=67,Forward=17}; local alts={}
local raw={}; local eaten={}
GameKeyboard={isKeyDownRaw=function(k) return raw[k] or false end,isKeyDown=function(k) return not focused and (raw[k] or false) end,eatKeyPress=function(k) eaten[k]=true end}
local screenW=nil; local screenH=nil
local core={getKey=function(_,n) return keys[n] or 0 end,getAltKey=function(_,n) return alts[n] or 0 end,isKey=function(_,n,k) return keys[n]==k or alts[n]==k end,getScreenWidth=function() return screenW or 1280 end,getScreenHeight=function() return screenH or 720 end}
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
    for _,name in ipairs({'OnTick','OnGameStart','OnMainMenuEnter','OnFillWorldObjectContextMenu','OnResolutionChange'}) do assert(#Events[name].callbacks==1) end
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
    local idCtrl,idNpc=dispatch:getIdentity()
    assert(idCtrl==SarahFoundation.controller and idNpc==npc1)
    local res=dispatch:execute('walk here')
    assert(res.state=='running')
    assert(dispatch.active and dispatch.active.owner==SarahFoundation.controller and dispatch.active.npc==npc1)
    -- Replace NPC within controller
    SarahFoundation.controller.npc=npc2
    -- Execute stop command via dispatch
    local stopRes=dispatch:execute('stop')
    assert(stopRes.state=='failed')
    assert(stopRes.lines[2]:find('stale npc'))
    assert(stoppedNpc==nil)
    dispatch:reset()
end)
test('console dispatch rejects controller replacement with same NPC and leaves replacement untouched',function()
    local sharedNpc={x=10,y=20,z=0}
    local stopped1,stopped2=nil,nil
    local ctrl1={
        npc=sharedNpc,
        adapter={
            walk=function(npc,sq,onComp,onFail) return true,{} end,
            stop=function(n) stopped1=n; return true end,
            validateTarget=function(npc,tgt) return true,tgt end
        }
    }
    local ctrl2={
        npc=sharedNpc,
        adapter={
            walk=function(npc,sq,onComp,onFail) return true,{} end,
            stop=function(n) stopped2=n; return true end,
            validateTarget=function(npc,tgt) return true,tgt end
        }
    }
    SarahFoundation={controller=ctrl1}
    local dispatch=s.getDispatch()
    dispatch:reset()
    local idCtrl,idNpc=dispatch:getIdentity()
    assert(idCtrl==ctrl1 and idNpc==sharedNpc)
    local res=dispatch:execute('walk here')
    assert(res.state=='running')
    assert(dispatch.active and dispatch.active.owner==ctrl1 and dispatch.active.npc==sharedNpc)
    -- Replace controller with ctrl2 (same NPC)
    SarahFoundation.controller=ctrl2
    local idCtrl2,idNpc2=dispatch:getIdentity()
    assert(idCtrl2==ctrl2 and idNpc2==sharedNpc)
    local valid,reason=dispatch:tick()
    assert(not valid and reason=='controller replaced')
    assert(dispatch.active==nil and dispatch.lastAction.state=='cancelled')
    assert(dispatch.lastAction.reason=='controller replaced')
    -- Stop callback targeting replacement controller is refused and leaves replacement untouched
    local stopRes=dispatch:invokeStop('test_stale',{owner=ctrl1,npc=sharedNpc})
    assert(stopRes==false)
    assert(stopped2==nil)
    dispatch:reset()
end)
test('console panel creates all 6 shortcut buttons with valid labels and non-overlapping geometry',function()
    s.open()
    local p=s.panel
    assert(p and p.btnHelp and p.btnStatus and p.btnInventory and p.btnHistory and p.btnWalkHere and p.btnStop)
    assert(p.btnRun and p.btnClose)
    assert(p.btnHelp.title=='Help' and p.btnHelp.command=='help')
    assert(p.btnStatus.title=='Status' and p.btnStatus.command=='status')
    assert(p.btnInventory.title=='Inventory' and p.btnInventory.command=='inventory')
    assert(p.btnHistory.title=='History' and p.btnHistory.command=='history')
    assert(p.btnWalkHere.title=='Walk Here' and p.btnWalkHere.command=='walk here')
    assert(p.btnStop.title=='Stop' and p.btnStop.command=='stop')
    assert(p.btnRun.title=='Run' and p.btnClose.title=='Close')

    local btns={p.btnHelp,p.btnStatus,p.btnInventory,p.btnHistory,p.btnWalkHere,p.btnStop}
    for i,b in ipairs(btns) do
        assert(b.width>0 and b.height>0)
        assert(b.x>=12 and (b.x+b.width)<=p.width-12)
        assert(b.y>=0 and (b.y+b.height)<=p.height)
        if i>1 then
            local prev=btns[i-1]
            assert(prev.x+prev.width<=b.x,'Buttons must not overlap horizontally: '..prev.title..' and '..b.title)
        end
        assert(p.history.y+p.history.height<=b.y,'Shortcut buttons must not overlap history output')
        assert(b.y+b.height<=p.entry.y,'Shortcut buttons must not overlap text entry')
    end
    assert(p.btnClose.y+p.btnClose.height<=p.history.y,'Close button must not overlap history output')
    assert(p.entry.x+p.entry.width<=p.btnRun.x,'Text entry must not overlap Run button')
    s.close()
end)
test('each shortcut button invokes its command once through normal output path and refocused entry',function()
    SarahFoundation={
        controller={
            npc={x=10,y=20,z=0},
            adapter={
                walk=function(npc,sq,onComp,onFail) return true,{} end,
                stop=function() return true end,
                validateTarget=function(npc,tgt) return true,tgt end
            }
        }
    }
    obsPlayer={x=12,y=20,z=0}
    s.open()
    local p=s.panel
    p.dispatch:reset()

    -- 1. Help shortcut
    local seqBefore=p.dispatch.sequence
    p.btnHelp:click()
    assert(p.dispatch.sequence==seqBefore+1)
    local foundHelpCmd,foundHelpRes=false,false
    for _,item in ipairs(p.history.items) do
        if item.text=='> help' then foundHelpCmd=true end
        if item.text:find('#'..p.dispatch.sequence..' completed') then foundHelpRes=true end
    end
    assert(foundHelpCmd and foundHelpRes)
    assert(p.entry:getText()=='' and p.entry:isFocused())

    -- 2. Status shortcut
    seqBefore=p.dispatch.sequence
    p.btnStatus:click()
    assert(p.dispatch.sequence==seqBefore+1)
    local foundStatusCmd,foundStatusRes=false,false
    for _,item in ipairs(p.history.items) do
        if item.text=='> status' then foundStatusCmd=true end
        if item.text:find('#'..p.dispatch.sequence..' completed') then foundStatusRes=true end
    end
    assert(foundStatusCmd and foundStatusRes)

    -- 3. Inventory shortcut
    seqBefore=p.dispatch.sequence
    p.btnInventory:click()
    assert(p.dispatch.sequence==seqBefore+1)
    local foundInvCmd,foundInvRes=false,false
    for _,item in ipairs(p.history.items) do
        if item.text=='> inventory' then foundInvCmd=true end
        if item.text:find('#'..p.dispatch.sequence..' completed') then foundInvRes=true end
    end
    assert(foundInvCmd and foundInvRes)

    -- 4. History shortcut
    seqBefore=p.dispatch.sequence
    p.btnHistory:click()
    assert(p.dispatch.sequence==seqBefore+1)
    local foundHistCmd,foundHistRes=false,false
    for _,item in ipairs(p.history.items) do
        if item.text=='> history' then foundHistCmd=true end
        if item.text:find('#'..p.dispatch.sequence..' completed') then foundHistRes=true end
    end
    assert(foundHistCmd and foundHistRes)

    -- 5. Walk here shortcut
    seqBefore=p.dispatch.sequence
    p.btnWalkHere:click()
    assert(p.dispatch.sequence==seqBefore+1)
    local foundWalkCmd,foundWalkRes=false,false
    for _,item in ipairs(p.history.items) do
        if item.text=='> walk here' then foundWalkCmd=true end
        if item.text:find('#'..p.dispatch.sequence..' running') then foundWalkRes=true end
    end
    assert(foundWalkCmd and foundWalkRes)
    assert(p.dispatch.active and p.dispatch.active.command=='walk here')

    -- 6. Stop shortcut
    seqBefore=p.dispatch.sequence
    local walkActId=p.dispatch.active.id
    p.btnStop:click()
    assert(p.dispatch.sequence==seqBefore+1)
    local foundStopCmd,foundStopRes=false,false
    for _,item in ipairs(p.history.items) do
        if item.text=='> stop' then foundStopCmd=true end
        if item.text:find('Cancelled #'..walkActId) and item.text:find('%(walk here%)') then foundStopRes=true end
    end
    assert(foundStopCmd and foundStopRes)
    assert(p.dispatch.active==nil)

    s.close()
    p.dispatch:reset()
end)
test('stop shortcut button remains accessible and halts active walk mid-stride',function()
    SarahFoundation={
        controller={
            npc={x=10,y=20,z=0},
            adapter={
                walk=function(npc,sq,onComp,onFail) return true,{} end,
                stop=function() return true end,
                validateTarget=function(npc,tgt) return true,tgt end
            }
        }
    }
    obsPlayer={x=12,y=20,z=0}
    s.open()
    local p=s.panel
    p.dispatch:reset()

    p.btnWalkHere:click()
    local walkId=p.dispatch.active and p.dispatch.active.id
    assert(walkId and p.dispatch.active.state=='running')

    -- Click Stop while walk is actively running
    p.btnStop:click()
    assert(p.dispatch.active==nil)
    local h=p.dispatch:getHistory()
    assert(h[#h-1].id==walkId and h[#h-1].state=='cancelled' and h[#h-1].summary=='stopped by user')
    assert(h[#h].command=='stop' and h[#h].state=='completed')

    local foundCancelled=false
    for _,item in ipairs(p.history.items) do
        if item.text:find('Cancelled #'..walkId) and item.text:find('%(walk here%)') then foundCancelled=true end
    end
    assert(foundCancelled)

    s.close()
    p.dispatch:reset()
end)
test('rejected walk shortcut feedback displays rejection reason and request id',function()
    s.open()
    local p=s.panel
    p.dispatch:reset()

    -- 1. Player too far away (> 8 tiles)
    obsPlayer={x=50,y=50,z=0}
    p.btnWalkHere:click()
    assert(p.dispatch.active==nil)
    local rejId=p.dispatch.sequence
    local foundTooFar,foundRejId=false,false
    for _,item in ipairs(p.history.items) do
        if item.text:find('Target is too far %(maximum 8 tiles%)') then foundTooFar=true end
        if item.text=='#'..rejId..' rejected' then foundRejId=true end
    end
    assert(foundTooFar and foundRejId)

    -- 2. Sarah busy refusal
    obsPlayer={x=12,y=20,z=0}
    SarahFoundation={
        controller={
            npc={x=10,y=20,z=0},
            adapter={
                walk=function(npc,sq,onComp,onFail) return true,{} end,
                stop=function() return true end,
                validateTarget=function(npc,tgt) return true,tgt end
            }
        }
    }
    p.btnWalkHere:click()
    assert(p.dispatch.active and p.dispatch.active.command=='walk here')
    local activeId=p.dispatch.active.id

    -- Click Walk Here again while already running
    p.btnWalkHere:click()
    local busyId=p.dispatch.sequence
    local foundBusy,foundBusyId=false,false
    for _,item in ipairs(p.history.items) do
        if item.text:find('Sarah is busy %('..'#'..activeId) then foundBusy=true end
        if item.text=='#'..busyId..' rejected' then foundBusyId=true end
    end
    assert(foundBusy and foundBusyId)

    s.close()
    p.dispatch:reset()
end)
test('reopening, redrawing, or layout changes do not execute commands or advance sequence',function()
    s.open()
    local p=s.panel
    p.dispatch:reset()
    local initialSeq=p.dispatch.sequence
    local initialItemCount=#p.history.items

    -- Redraws
    p:prerender()
    p:prerender()
    assert(p.dispatch.sequence==initialSeq)
    assert(#p.history.items==initialItemCount)

    -- Close and reopen
    s.close()
    assert(s.panel==nil)
    s.open()
    p=s.panel
    assert(p.dispatch.sequence==initialSeq)
    p:prerender()
    assert(p.dispatch.sequence==initialSeq)

    s.close()
end)
test('translation helper uses getText when available and falls back gracefully',function()
    -- When getText returns a translated string
    getText=function(k)
        if k=='UI_SarahConsole_Help' then return 'Aide' end
        if k=='UI_SarahConsole_Status' then return 'Statut' end
        return k
    end
    local sTr=reload()
    sTr.open()
    local p=sTr.panel
    assert(p.btnHelp.title=='Aide')
    assert(p.btnStatus.title=='Statut')
    -- Missing translation key returns k, tr() falls back to English string
    assert(p.btnInventory.title=='Inventory')
    assert(p.btnHistory.title=='History')
    assert(p.btnWalkHere.title=='Walk Here')
    assert(p.btnStop.title=='Stop')
    sTr.close()
    getText=nil
    s=reload()
end)
test('typed command entry and session reset remain fully operational alongside shortcuts',function()
    s.open()
    local p=s.panel
    p.dispatch:reset()

    -- Typed command via Enter/submit
    p.entry:setText('status')
    p:submit()
    local foundTypedStatus=false
    for _,item in ipairs(p.history.items) do
        if item.text=='> status' then foundTypedStatus=true end
    end
    assert(foundTypedStatus)
    assert(p.entry:getText()=='')

    -- Typed command via Run button
    p.entry:setText('help')
    p.btnRun:click()
    local foundRunHelp=false
    for _,item in ipairs(p.history.items) do
        if item.text=='> help' then foundRunHelp=true end
    end
    assert(foundRunHelp)

    -- Session reset
    s.reset()
    assert(s.panel==nil and s.dispatch.active==nil and #s.dispatch:getHistory()==0)
    s.open()
    assert(s.panel and s.panel.dispatch.sequence==0)
    s.close()
    s.reset()
end)
test('title bar mouse dragging moves panel and updates coordinates and state.pos',function()
    s.open()
    local p=s.panel
    -- Default centered position on 1280x720: (1280-560)/2 = 360, (720-370)/2 = 175
    assert(p.x==360 and p.y==175)
    assert(s.pos and s.pos.x==360 and s.pos.y==175)
    assert(not p.moving)

    -- Mouse down in title bar (y < 40 and x < 480)
    p:onMouseDown(100, 20)
    assert(p.moving==true and p.top==true)
    p.top=nil

    -- Move mouse: dx = 50, dy = 30
    p:onMouseMove(50, 30)
    assert(p.x==410 and p.y==205)
    assert(s.pos.x==410 and s.pos.y==205)
    assert(p.top==true)
    p.top=nil

    -- Move mouse outside during drag: dx = 20, dy = -15
    p:onMouseMoveOutside(20, -15)
    assert(p.x==430 and p.y==190)
    assert(s.pos.x==430 and s.pos.y==190)
    assert(p.top==true)

    -- Mouse up outside ends drag
    p:onMouseUpOutside(430, 190)
    assert(p.moving==false)
    assert(s.pos.x==430 and s.pos.y==190)

    -- Further mouse move when not moving does not alter position
    p:onMouseMove(100, 100)
    assert(p.x==430 and p.y==190)

    s.close()
    s.reset()
end)
test('dragging bounds clamped on standard screen and keeps entire panel onscreen',function()
    s.open()
    local p=s.panel
    assert(p.x==360 and p.y==175)

    -- Start drag
    p:onMouseDown(50, 15)
    assert(p.moving==true)

    -- Drag far beyond top-left screen edge
    p:onMouseMove(-2000, -2000)
    assert(p.x==0 and p.y==0)
    assert(s.pos.x==0 and s.pos.y==0)

    -- Drag far beyond bottom-right screen edge
    -- maxX = 1280 - 560 = 720; maxY = 720 - 370 = 350
    p:onMouseMove(5000, 5000)
    assert(p.x==720 and p.y==350)
    assert(s.pos.x==720 and s.pos.y==350)

    -- Release
    p:onMouseUp(100, 20)
    assert(p.moving==false)
    assert(p.x==720 and p.y==350)

    s.close()
    s.reset()
end)
test('small-screen layout adapts height and keeps title bar, drag handle, Close, and controls reachable',function()
    -- Small screen: 500x300 (smaller than default 560x370)
    screenW=500; screenH=300
    s.open()
    local p=s.panel
    assert(p~=nil)

    -- 1. Height adaptation and layout geometry
    assert(p.height==300)
    assert(p.history.height==176) -- 300 - 124
    assert(p.btnHelp.y==226)      -- 300 - 74
    assert(p.entry.y==260)        -- 300 - 40
    assert(p.btnRun.y==260)
    assert(p.btnClose.y==10)
    assert(p.y==0)                -- Strictly non-negative; title bar is at [0, 40]
    assert(p.x<=0 and p.x>=-60)   -- Horizontal centering/clamp: [500-560, 0] = [-60, 0]

    -- 2. Vertical drag cannot move title bar offscreen (y stays strictly non-negative)
    p:onMouseDown(50, 15)
    assert(p.moving==true)

    p:onMouseMove(0, -200)
    assert(p.y==0)                -- Cannot drag up into negative space
    assert(s.pos.y==0)

    p:onMouseMove(0, 200)
    assert(p.y==0)                -- Cannot drag down beyond screen height
    assert(s.pos.y==0)

    -- 3. Horizontal sliding makes all controls accessible
    -- Slide left to x = -60: right controls (Close, Run, Stop) are on screen
    p:onMouseMove(-200, 0)
    assert(p.x==-60 and p.y==0)
    -- Verify right-side controls are fully within screen bounds [0, 500]
    local closeScreenX = p.x + p.btnClose.x
    assert(closeScreenX==420 and closeScreenX + 68 <= 500)
    local runScreenX = p.x + p.btnRun.x
    assert(runScreenX==424 and runScreenX + 64 <= 500)
    local stopScreenX = p.x + p.btnStop.x
    assert(stopScreenX==416 and stopScreenX + 72 <= 500)

    -- Release mouse at x = -60
    p:onMouseUp(50, 15)
    assert(p.moving==false)
    assert(s.pos.x==-60 and s.pos.y==0)

    -- 4. Drag restart works after release from the accessible title bar
    -- Title bar is visible from screen 0 to 420; grab at screen x=100 (relative x = 160)
    p:onMouseDown(160, 15)
    assert(p.moving==true)
    -- Slide back right to x = 0: left controls (Help, Status, text entry) are on screen
    p:onMouseMove(200, 0)
    assert(p.x==0 and p.y==0)
    local helpScreenX = p.x + p.btnHelp.x
    assert(helpScreenX==12 and helpScreenX + 72 <= 500)
    local entryScreenX = p.x + p.entry.x
    assert(entryScreenX==12 and entryScreenX + 464 <= 500)
    p:onMouseUp(50, 15)
    assert(p.moving==false)

    -- 5. Command execution works on small screen
    p.btnHelp:click()
    local foundHelp=false
    for _,item in ipairs(p.history.items) do
        if item.text:find('help') then foundHelp=true end
    end
    assert(foundHelp)

    -- 6. Close and reopen retains accessible position and adapted height
    p.btnClose:click()
    assert(s.panel==nil)
    assert(s.pos.y==0)

    s.open()
    p=s.panel
    assert(p~=nil and p.height==300 and p.y==0 and p.x==0)
    assert(p.btnClose.y==10 and p.btnClose.x==480)

    s.close()
    s.reset()
    screenW=nil; screenH=nil
end)
test('clicking controls does not start drag, modify coordinates, or duplicate commands',function()
    s.open()
    local p=s.panel
    p.dispatch:reset()
    local origX,origY=p.x,p.y

    -- 1. Clicking on Close button (x = 480..548, y = 10..34)
    p:onMouseDown(p.btnClose.x + 5, p.btnClose.y + 5)
    assert((not p.moving) and p.x==origX and p.y==origY)

    -- 2. Clicking in History listbox (y >= 40)
    p:onMouseDown(200, 100)
    assert((not p.moving) and p.x==origX and p.y==origY)

    -- 3. Clicking on shortcut buttons (y >= 40)
    p:onMouseDown(p.btnHelp.x + 5, p.btnHelp.y + 5)
    assert((not p.moving) and p.x==origX and p.y==origY)
    p:onMouseDown(p.btnStatus.x + 5, p.btnStatus.y + 5)
    assert((not p.moving) and p.x==origX and p.y==origY)
    p:onMouseDown(p.btnInventory.x + 5, p.btnInventory.y + 5)
    assert((not p.moving) and p.x==origX and p.y==origY)
    p:onMouseDown(p.btnHistory.x + 5, p.btnHistory.y + 5)
    assert((not p.moving) and p.x==origX and p.y==origY)
    p:onMouseDown(p.btnWalkHere.x + 5, p.btnWalkHere.y + 5)
    assert((not p.moving) and p.x==origX and p.y==origY)
    p:onMouseDown(p.btnStop.x + 5, p.btnStop.y + 5)
    assert((not p.moving) and p.x==origX and p.y==origY)

    -- 4. Clicking on Entry box and Run button (y >= 40)
    p:onMouseDown(p.entry.x + 10, p.entry.y + 10)
    assert((not p.moving) and p.x==origX and p.y==origY)
    p:onMouseDown(p.btnRun.x + 5, p.btnRun.y + 5)
    assert((not p.moving) and p.x==origX and p.y==origY)

    -- 5. Clicking outside bottom of panel
    p:onMouseDown(100, 400)
    assert((not p.moving) and p.x==origX and p.y==origY)

    -- 6. Triggering buttons executes command exactly once without drag
    local seqBefore=p.dispatch.sequence
    p.btnHelp:click()
    assert(p.dispatch.sequence==seqBefore+1)
    assert((not p.moving) and p.x==origX and p.y==origY)

    p.btnStatus:click()
    assert(p.dispatch.sequence==seqBefore+2)
    assert((not p.moving) and p.x==origX and p.y==origY)

    s.close()
    s.reset()
end)
test('position is preserved across close and reopen within same world session',function()
    s.open()
    local p=s.panel
    p:onMouseDown(50, 15)
    p:onMouseMove(-160, 75)
    p:onMouseUp(50, 15)
    -- Initial was (360, 175) -> -160, +75 => (200, 250)
    assert(p.x==200 and p.y==250)
    assert(s.pos.x==200 and s.pos.y==250)

    -- Close via close()
    s.close()
    assert(s.panel==nil)
    assert(s.pos.x==200 and s.pos.y==250)

    -- Reopen in same session
    s.open()
    p=s.panel
    assert(p and p.x==200 and p.y==250)
    assert(s.pos.x==200 and s.pos.y==250)

    -- Close via btnClose click
    p.btnClose:click()
    assert(s.panel==nil)
    assert(s.pos.x==200 and s.pos.y==250)

    -- Reopen again
    s.open()
    assert(s.panel.x==200 and s.panel.y==250)

    s.close()
    s.reset()
end)
test('session reset clears position and re-centers console on next open',function()
    s.open()
    local p=s.panel
    p:onMouseDown(50, 15)
    p:onMouseMove(100, 100)
    p:onMouseUp(50, 15)
    assert(p.x==460 and p.y==275)
    assert(s.pos.x==460 and s.pos.y==275)

    -- Session reset (e.g. OnMainMenuEnter or OnGameStart)
    s.reset()
    assert(s.panel==nil)
    assert(s.pos==nil)

    -- Reopen in new session
    s.open()
    assert(s.panel and s.panel.x==360 and s.panel.y==175)
    assert(s.pos.x==360 and s.pos.y==175)

    s.close()
    s.reset()
end)
test('OnResolutionChange immediately re-clamps open panel, adapts height, and updates closed position',function()
    s.open()
    local p=s.panel
    -- Move to bottom-right of 1280x720: (720, 350)
    p:onMouseDown(50, 15)
    p:onMouseMove(500, 500)
    p:onMouseUp(50, 15)
    assert(p.x==720 and p.y==350)
    assert(p.height==370 and p.history.height==246)

    -- Shrink resolution to 1024x768 while open
    screenW=1024; screenH=768
    -- Fire OnResolutionChange
    for _,cb in ipairs(Events.OnResolutionChange.callbacks) do cb(1280, 720, 1024, 768) end
    -- Clamped to max X = 1024 - 560 = 464; Y = 350 (<= 768 - 370 = 398)
    assert(s.panel.x==464 and s.panel.y==350)
    assert(s.panel.height==370 and s.panel.history.height==246)
    assert(s.pos.x==464 and s.pos.y==350)

    -- Shrink resolution further while open to small screen 500x300
    screenW=500; screenH=300
    for _,cb in ipairs(Events.OnResolutionChange.callbacks) do cb(1024, 768, 500, 300) end
    -- Adapted height: 300, history: 176, toolbar: 226, entry: 260
    assert(s.panel.height==300)
    assert(s.panel.history.height==176)
    assert(s.panel.btnHelp.y==226)
    assert(s.panel.entry.y==260)
    -- Clamped position: X clamped to 0 (since 464 > 0 and maxX = 0), Y clamped to 0 (minY = 0, maxY = 0)
    assert(s.panel.x==0 and s.panel.y==0)
    assert(s.pos.x==0 and s.pos.y==0)

    -- Expand resolution back to 1280x720 while open
    screenW=1280; screenH=720
    for _,cb in ipairs(Events.OnResolutionChange.callbacks) do cb(500, 300, 1280, 720) end
    assert(s.panel.height==370)
    assert(s.panel.history.height==246)
    assert(s.panel.btnHelp.y==296)
    assert(s.panel.entry.y==330)
    assert(s.panel.x==0 and s.panel.y==0)

    -- Close panel
    s.close()

    -- Shrink resolution while closed to 500x300
    screenW=500; screenH=300
    for _,cb in ipairs(Events.OnResolutionChange.callbacks) do cb(1280, 720, 500, 300) end
    -- Clamped pos to maxX = 0, maxY = 0
    assert(s.pos.x==0 and s.pos.y==0)

    -- Reopen after resolution change on small screen
    s.open()
    assert(s.panel.height==300 and s.panel.history.height==176)
    assert(s.panel.x==0 and s.panel.y==0)

    s.close()
    s.reset()
    screenW=nil; screenH=nil
end)
print('RESULT '..count..' simulated console checks passed')
''')
