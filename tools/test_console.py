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
lua.globals().Knowledge=lua.execute((source/'Knowledge.lua').read_text())
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
require=function(n) if n=='Sarah/Commands' then return Commands elseif n=='Sarah/Observations' then return {read=function()
    local dead=obsPlayer and (obsPlayer.dead==true or obsPlayer.liveness=='dead') or false
    local unknown=obsPlayer and (obsPlayer.liveness=='unknown') or false
    local alive=obsPlayer and (not dead and not unknown) or false
    return {state=obsState or 'active',npc=obsNpc,player=obsPlayer,playerDead=dead,playerAlive=alive,playerLiveness=unknown and 'unknown' or (dead and 'dead' or 'alive')}
end} end end
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
test('console panel creates all 7 shortcut buttons with valid labels and non-overlapping geometry',function()
    s.open()
    local p=s.panel
    assert(p and p.btnHelp and p.btnStatus and p.btnInventory and p.btnHistory and p.btnWalkHere and p.btnFollow and p.btnStop)
    assert(p.btnRun and p.btnClose)
    assert(p.btnHelp.title=='Help' and p.btnHelp.command=='help')
    assert(p.btnStatus.title=='Status' and p.btnStatus.command=='status')
    assert(p.btnInventory.title=='Inventory' and p.btnInventory.command=='inventory')
    assert(p.btnHistory.title=='History' and p.btnHistory.command=='history')
    assert(p.btnWalkHere.title=='Walk Here' and p.btnWalkHere.command=='walk here')
    assert(p.btnFollow.title=='Follow' and p.btnFollow.command=='follow')
    assert(p.btnStop.title=='Stop' and p.btnStop.command=='stop')
    assert(p.btnRun.title=='Run' and p.btnClose.title=='Close')

    local btns={p.btnHelp,p.btnStatus,p.btnInventory,p.btnHistory,p.btnWalkHere,p.btnFollow,p.btnStop}
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

    -- 7. Follow shortcut
    seqBefore=p.dispatch.sequence
    p.btnFollow:click()
    assert(p.dispatch.sequence==seqBefore+1)
    local foundFollowCmd,foundFollowRes=false,false
    for _,item in ipairs(p.history.items) do
        if item.text=='> follow' then foundFollowCmd=true end
        if item.text:find('#'..p.dispatch.sequence..' running') then foundFollowRes=true end
    end
    assert(foundFollowCmd and foundFollowRes)
    assert(p.dispatch.active and p.dispatch.active.command=='follow')

    -- Stop follow
    p.btnStop:click()
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
    local followScreenX = p.x + p.btnFollow.x
    assert(followScreenX==350 and followScreenX + 72 <= 500)
    local stopScreenX = p.x + p.btnStop.x
    assert(stopScreenX==428 and stopScreenX + 60 <= 500)

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
    assert(helpScreenX==12 and helpScreenX + 60 <= 500)
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
    p:onMouseDown(p.btnFollow.x + 5, p.btnFollow.y + 5)
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
test('asynchronous disengagement appends to open console panel history and notifies in-world feedback once',function()
    local lastPlayerNotified,lastMessageNotified,lastIsBadNotified
    SarahFoundation={
        controller={
            npc={x=10,y=20,z=0},
            adapter={
                walk=function(npc,sq,onComp,onFail) return true,{} end,
                stop=function() return true end,
                validateTarget=function(npc,tgt) return true,tgt end
            }
        },
        notify=function(p,msg,isBad)
            lastPlayerNotified=p
            lastMessageNotified=msg
            lastIsBadNotified=isBad
        end
    }
    obsPlayer={x=12,y=20,z=0,dead=false,alive=true}
    s.open()
    local p=s.panel
    p.dispatch:reset()

    -- Start follow
    p.btnFollow:click()
    assert(p.dispatch.active and p.dispatch.active.command=='follow')

    -- Player moves out of range (>8 tiles away: 50, 20)
    obsPlayer={x=50,y=20,z=0,dead=false,alive=true}
    local itemsBefore=#p.history.items
    s.tick()

    -- Follow is disengaged
    assert(p.dispatch.active==nil)
    assert(p.dispatch.lastAction.state=='cancelled')

    -- Notice is appended to open panel
    local foundDisengagedNotice,foundCancelledStatus=false,false
    for i=itemsBefore+1,#p.history.items do
        local text=p.history.items[i].text
        if text:find('Follow disengaged: player out of range %(>8 tiles%)%.') then
            foundDisengagedNotice=true
        end
        if text:find('cancelled') then
            foundCancelledStatus=true
        end
    end
    assert(foundDisengagedNotice and foundCancelledStatus)

    -- In-world feedback notification was delivered
    assert(lastMessageNotified=='Follow disengaged: player out of range (>8 tiles).')
    assert(lastIsBadNotified==true)

    -- Subsequent ticks do NOT append duplicate notices
    local itemsAfter=#p.history.items
    lastMessageNotified=nil
    for i=1,5 do s.tick() end
    assert(#p.history.items==itemsAfter)
    assert(lastMessageNotified==nil)

    s.close()
    s.reset()
end)
test('closed-console disengagement notifies in-world feedback and does not replay on later panel open or reopen',function()
    local lastMessageNotified,lastIsBadNotified
    SarahFoundation={
        controller={
            npc={x=10,y=20,z=0},
            adapter={
                walk=function(npc,sq,onComp,onFail) return true,{} end,
                stop=function() return true end,
                validateTarget=function(npc,tgt) return true,tgt end
            }
        },
        notify=function(p,msg,isBad)
            lastMessageNotified=msg
            lastIsBadNotified=isBad
        end
    }
    obsPlayer={x=12,y=20,z=0,dead=false,alive=true}
    s.open()
    local p=s.panel
    p.dispatch:reset()

    -- Start follow
    p.btnFollow:click()
    assert(p.dispatch.active and p.dispatch.active.command=='follow')

    -- Close console panel while follow is active
    s.close()
    assert(s.panel==nil)

    -- Player dies while console is closed
    obsPlayer={x=12,y=20,z=0,dead=true,alive=false}
    s.tick()
    assert(p.dispatch.active==nil)
    assert(p.dispatch.lastAction.reason=='player dead')

    -- In-world notification was delivered even with console closed
    assert(lastMessageNotified=='Follow disengaged: player dead.')
    assert(lastIsBadNotified==true)

    -- Open console later: must not replay notification or execute commands
    lastMessageNotified=nil
    s.open()
    local pNew=s.panel
    assert(pNew~=nil)
    -- History only contains initial greeting / commands info, no replayed notice
    local replayedNotice=false
    for _,item in ipairs(pNew.history.items) do
        if item.text:find('Follow disengaged') then replayedNotice=true end
    end
    assert(not replayedNotice)
    assert(lastMessageNotified==nil)

    -- Status button reflects disengagement accurately without extra commands
    pNew.btnStatus:click()
    local foundDisengagedStatus=false
    for _,item in ipairs(pNew.history.items) do
        if item.text:find('Follow: disengaged %(player dead%)') then
            foundDisengagedStatus=true
        end
    end
    assert(foundDisengagedStatus)

    -- Reopen does not replay or trigger commands
    s.close()
    s.open()
    assert(s.panel~=nil)
    replayedNotice=false
    for _,item in ipairs(s.panel.history.items) do
        if item.text:find('Follow disengaged') then replayedNotice=true end
    end
    assert(not replayedNotice)

    s.close()
    s.reset()
end)
test('session reset clears notice queue and prevents replay across world sessions',function()
    local lastMessageNotified
    SarahFoundation={
        controller={
            npc={x=10,y=20,z=0},
            adapter={
                walk=function(npc,sq,onComp,onFail) return true,{} end,
                stop=function() return true end,
                validateTarget=function(npc,tgt) return true,tgt end
            }
        },
        notify=function(p,msg) lastMessageNotified=msg end
    }
    obsPlayer={x=12,y=20,z=0,dead=false,alive=true}
    s.open()
    local p=s.panel
    p.dispatch:reset()

    -- Start follow
    p.btnFollow:click()
    assert(p.dispatch.active~=nil)

    -- Session reset (e.g. leaving world)
    s.reset()
    assert(s.panel==nil)
    assert(s.pos==nil)
    assert(p.dispatch.active==nil)
    assert(#p.dispatch.noticeQueue==0)

    -- Tick in new session does not fire stale notice
    lastMessageNotified=nil
    s.tick()
    assert(lastMessageNotified==nil)

    -- Reopen in new world session starts clean
    s.open()
    assert(s.panel~=nil)
    local hasNotice=false
    for _,item in ipairs(s.panel.history.items) do
        if item.text:find('Follow disengaged') or item.text:find('cancelled') then
            hasNotice=true
        end
    end
    assert(not hasNotice)

    s.close()
    s.reset()
end)
test('engine clock: getTimeSeconds fails closed when getGameTime is unavailable (no silent zero or wall-clock fallback)',function()
    s.reset()
    getGameTime = nil
    local val, err = s.getTimeSeconds()
    assert(val == nil, 'getTimeSeconds must return nil when getGameTime is nil')
    assert(err:find('engine clock unavailable'), 'error must indicate engine clock unavailable')
    assert(s.accumulatedTime == nil, 'accumulatedTime must remain nil')

    -- Throwing getGameTime
    getGameTime = function() error('native jni error') end
    local val2, err2 = s.getTimeSeconds()
    assert(val2 == nil, 'getTimeSeconds must return nil when getGameTime throws')
    assert(err2:find('engine clock unavailable'), 'error must indicate engine clock unavailable')

    -- Missing getTimeDelta
    getGameTime = function() return {} end
    local val3, err3 = s.getTimeSeconds()
    assert(val3 == nil, 'getTimeSeconds must return nil when getTimeDelta missing')
    assert(err3:find('engine clock unavailable'), 'error must indicate engine clock unavailable')

    getGameTime = nil
    s.reset()
end)
test('engine clock: state.tick accumulates bounded monotonic engine delta when getGameTime is available',function()
    s.reset()
    local mockDelta = 0.016
    local mockPaused = false
    getGameTime = function()
        return {
            getTimeDelta = function() return mockDelta end,
            isGamePaused = function() return mockPaused end,
        }
    end

    -- Before first tick, calling getTimeSeconds initializes to 0.0
    local t0, err0 = s.getTimeSeconds()
    assert(t0 == 0.0, 'getTimeSeconds initializes cleanly to 0.0 when clock available')
    assert(err0 == nil)

    -- Tick 1
    s.tick()
    local t1 = s.getTimeSeconds()
    assert(math.abs(t1 - 0.016) < 1e-6, 'first tick accumulates delta')

    -- Tick 2
    s.tick()
    local t2 = s.getTimeSeconds()
    assert(math.abs(t2 - 0.032) < 1e-6, 'second tick accumulates delta monotonically')
    assert(t2 > t1, 'must be strictly monotonic')

    -- Tick 3
    s.tick()
    local t3 = s.getTimeSeconds()
    assert(math.abs(t3 - 0.048) < 1e-6, 'third tick accumulates delta monotonically')
    assert(t3 > t2, 'must be strictly monotonic')

    getGameTime = nil
    s.reset()
end)
test('engine clock: pause stops accumulation and maintains monotonic clock without drift',function()
    s.reset()
    local mockDelta = 0.02
    local mockPaused = false
    getGameTime = function()
        return {
            getTimeDelta = function() return mockDelta end,
            isGamePaused = function() return mockPaused end,
        }
    end

    s.tick()
    local t1 = s.getTimeSeconds()
    assert(math.abs(t1 - 0.02) < 1e-6)

    -- Pause the game via isGamePaused
    mockPaused = true
    local pDelta, pReason = s.getEngineDelta()
    assert(pDelta == 0.0 and pReason == 'paused')

    s.tick()
    s.tick()
    s.tick()
    local tPaused = s.getTimeSeconds()
    assert(math.abs(tPaused - t1) < 1e-6, 'accumulated time must NOT advance while paused')

    -- Also verify SpeedControls pause detection
    mockPaused = false
    local currentSpeed = 0
    UIManager = {
        getSpeedControls = function()
            return {
                getCurrentGameSpeed = function() return currentSpeed end
            }
        end
    }
    s.tick()
    assert(math.abs(s.getTimeSeconds() - t1) < 1e-6, 'accumulated time must NOT advance when speed is 0')

    -- Unpause
    currentSpeed = 1
    s.tick()
    local tResumed = s.getTimeSeconds()
    assert(math.abs(tResumed - (t1 + 0.02)) < 1e-6, 'accumulated time advances cleanly upon resuming')
    assert(tResumed > t1, 'must remain monotonic')

    UIManager = nil
    getGameTime = nil
    s.reset()
end)
test('engine clock: pause detection fails closed on missing, throwing, or malformed APIs and recovers cleanly',function()
    s.reset()
    local mockDelta = 0.02
    local gt = {
        getTimeDelta = function() return mockDelta end
    }
    getGameTime = function() return gt end
    UIManager = nil

    -- 1. Missing pause APIs (both gt.isGamePaused and UIManager are nil)
    local dt, err = s.getEngineDelta()
    assert(dt == nil and err:find('pause state unavailable or unverified'), 'missing pause APIs must fail closed')
    local tSec, tErr = s.getTimeSeconds()
    assert(tSec == nil and tErr:find('pause state unavailable or unverified'), 'getTimeSeconds fails closed on missing pause API')

    -- 2. Throwing gt.isGamePaused with no UIManager
    gt.isGamePaused = function() error('native isGamePaused crash') end
    dt, err = s.getEngineDelta()
    assert(dt == nil and err:find('pause state unavailable or unverified'), 'throwing isGamePaused must fail closed')

    -- 3. Malformed gt.isGamePaused return values (non-boolean)
    gt.isGamePaused = function() return 'true' end -- string, not boolean
    dt, err = s.getEngineDelta()
    assert(dt == nil and err:find('pause state unavailable or unverified'), 'string return from isGamePaused must fail closed')

    gt.isGamePaused = function() return 1 end -- number, not boolean
    dt, err = s.getEngineDelta()
    assert(dt == nil and err:find('pause state unavailable or unverified'), 'number return from isGamePaused must fail closed')

    gt.isGamePaused = function() return {} end -- table, not boolean
    dt, err = s.getEngineDelta()
    assert(dt == nil and err:find('pause state unavailable or unverified'), 'table return from isGamePaused must fail closed')

    gt.isGamePaused = function() return nil end -- nil return
    dt, err = s.getEngineDelta()
    assert(dt == nil and err:find('pause state unavailable or unverified'), 'nil return from isGamePaused must fail closed')

    -- 4. Valid fallback to UIManager when gt.isGamePaused is throwing/malformed
    local curSpeed = 0
    UIManager = {
        getSpeedControls = function()
            return {
                getCurrentGameSpeed = function() return curSpeed end
            }
        end
    }
    -- With curSpeed = 0, speed controls verifies pause -> returns 0.0, 'paused'
    dt, err = s.getEngineDelta()
    assert(dt == 0.0 and err == 'paused', 'UIManager speed=0 successfully verifies paused state')

    -- With curSpeed = 1, speed controls verifies unpaused -> returns mockDelta
    curSpeed = 1
    dt, err = s.getEngineDelta()
    assert(dt == mockDelta and err == nil, 'UIManager speed=1 successfully verifies unpaused state')

    -- 5. Throwing and malformed UIManager fallback when gt.isGamePaused is unavailable
    gt.isGamePaused = function() error('crash') end
    UIManager = {
        getSpeedControls = function() error('UIManager native crash') end
    }
    dt, err = s.getEngineDelta()
    assert(dt == nil and err:find('pause state unavailable or unverified'), 'throwing UIManager must fail closed')

    UIManager = {
        getSpeedControls = function()
            return {
                getCurrentGameSpeed = function() error('getCurrentGameSpeed crash') end
            }
        end
    }
    dt, err = s.getEngineDelta()
    assert(dt == nil and err:find('pause state unavailable or unverified'), 'throwing getCurrentGameSpeed must fail closed')

    -- Malformed getCurrentGameSpeed values (string, negative, NaN)
    UIManager = {
        getSpeedControls = function()
            return {
                getCurrentGameSpeed = function() return '0' end
            }
        end
    }
    dt, err = s.getEngineDelta()
    assert(dt == nil and err:find('pause state unavailable or unverified'), 'string speed must fail closed')

    UIManager = {
        getSpeedControls = function()
            return {
                getCurrentGameSpeed = function() return -1 end
            }
        end
    }
    dt, err = s.getEngineDelta()
    assert(dt == nil and err:find('pause state unavailable or unverified'), 'negative speed must fail closed')

    UIManager = {
        getSpeedControls = function()
            return {
                getCurrentGameSpeed = function() return 0/0 end
            }
        end
    }
    dt, err = s.getEngineDelta()
    assert(dt == nil and err:find('pause state unavailable or unverified'), 'NaN speed must fail closed')

    -- 6. Knowledge memory invalidation and recovery under pause failure
    UIManager = nil
    gt.isGamePaused = function() return false end
    s.tick()
    s.tick()
    local tBefore = s.getTimeSeconds()
    assert(tBefore > 0)

    local disp = s.getDispatch()
    disp:reset()
    local k = disp:getKnowledge()
    k:update({
        status = 'sampled',
        results = {
            {id = 'p_rec', kind = 'player', geometric = 'visible', visual = 'visible', position = {x = 5, y = 5, z = 0}}
        }
    }, tBefore)
    assert(#k:snapshot(tBefore) == 1, 'Knowledge holds observation at valid time')

    -- Cause pause check to throw during tick
    gt.isGamePaused = function() error('sudden pause check failure') end
    s.tick()
    assert(s.clockDiscontinuous == true, 'clockDiscontinuous flag set when pause check throws')
    assert(#k:snapshot(0) == 0, 'Knowledge memory immediately invalidated on pause check failure')

    -- Look command fails closed while pause check is failing
    local resFail = disp:execute('look')
    assert(resFail.state == 'failed', 'look command fails closed when pause check fails')

    -- Recovery: pause check becomes valid again
    gt.isGamePaused = function() return false end
    s.tick()
    assert(s.clockDiscontinuous == false, 'clockDiscontinuous flag cleared on clean recovery')
    local tAfter = s.getTimeSeconds()
    assert(tAfter > tBefore, 'accumulated time advances monotonically after recovery')
    assert(#k:snapshot(tAfter) == 0, 'Recovery must NOT restore stale records of unknown elapsed age')

    -- New observation can be recorded after recovery
    k:update({
        status = 'sampled',
        results = {
            {id = 'p_rec2', kind = 'player', geometric = 'visible', visual = 'visible', position = {x = 6, y = 6, z = 0}}
        }
    }, tAfter)
    assert(#k:snapshot(tAfter) == 1, 'Knowledge cleanly accepts new observation after recovery')

    UIManager = nil
    getGameTime = nil
    s.reset()
end)
test('engine clock: speed scaling, simulation delta preservation without arbitrary clamp, and invalid delta rejection',function()
    s.reset()
    local mockDelta = 0.1 -- 5x speed simulation (0.02 * 5)
    getGameTime = function()
        return {
            getTimeDelta = function() return mockDelta end,
            isGamePaused = function() return false end,
        }
    end

    s.tick()
    local t1 = s.getTimeSeconds()
    assert(math.abs(t1 - 0.1) < 1e-6, 'accumulates fast-forward delta')

    -- Simulation delta at high speed (e.g. 40x speed or sleep acceleration): delta = 15.0s
    -- Must be preserved without arbitrary clamp to prevent discarding elapsed time or prolonging freshness
    mockDelta = 15.0
    local bDelta, _ = s.getEngineDelta()
    assert(bDelta == 15.0, 'single-tick simulation delta must NOT be arbitrarily clamped')
    s.tick()
    local t2 = s.getTimeSeconds()
    assert(math.abs(t2 - 15.1) < 1e-6, 'accumulated time increased by full simulation delta (15.0s)')

    -- Invalid delta: negative, NaN, infinity
    mockDelta = -1.0
    local negDelta, negErr = s.getEngineDelta()
    assert(negDelta == nil and negErr:find('invalid'), 'negative delta must be rejected')

    mockDelta = 0/0
    local nanDelta, nanErr = s.getEngineDelta()
    assert(nanDelta == nil and nanErr:find('invalid'), 'NaN delta must be rejected')

    mockDelta = 1/0
    local infDelta, infErr = s.getEngineDelta()
    assert(infDelta == nil and infErr:find('invalid'), 'infinite delta must be rejected')

    -- Tick with invalid delta fails closed and flags discontinuity
    s.tick()
    assert(math.abs(s.accumulatedTime - 15.1) < 1e-6, 'invalid delta must NOT alter accumulated time')
    local tInvalid, errInvalid = s.getTimeSeconds()
    assert(tInvalid == nil and errInvalid:find('invalid'), 'getTimeSeconds fails closed when clock is invalid')

    -- Restore valid delta: getTimeSeconds clears discontinuity flag
    mockDelta = 0.0
    assert(math.abs(s.getTimeSeconds() - 15.1) < 1e-6, 'accumulated time resumes at 15.1')

    getGameTime = nil
    s.reset()
end)
test('engine clock: clock discontinuities invalidate observation memory, and recovery does not retain records of unknown age',function()
    s.reset()
    local simDelta = 0.02
    local gtTable = {
        getTimeDelta = function() return simDelta end,
        isGamePaused = function() return false end,
    }
    getGameTime = function() return gtTable end

    local testAdapter = {
        samplePerception = function(npc)
            return {
                status = 'sampled',
                lighting = 'unknown',
                results = {
                    {id = 'p1', kind = 'player', geometric = 'visible', visual = 'unknown'}
                },
                counts = {candidates = 1, processed = 1}
            }
        end,
        resetPerception = function() end
    }
    SarahFoundation = {
        controller = {
            npc = {id = 'sarah'},
            adapter = testAdapter
        }
    }
    obsState = 'active'
    obsNpc = {x = 10, y = 20, z = 0}
    obsPlayer = {x = 12, y = 20, z = 0, dead = false, alive = true}

    local disp = s.getDispatch()
    disp:reset()
    s.accumulatedTime = 100.0

    local k = disp:getKnowledge()
    -- Record a confirmed visual observation at t=100.0
    k:update({
        status = 'sampled',
        results = {
            {id = 't1', kind = 'player', geometric = 'visible', visual = 'visible', position = {x = 10, y = 20, z = 0}}
        }
    }, 100.0)
    assert(#k:snapshot(100.0) == 1, 'Knowledge holds observation at t=100.0')

    -- Case 1: getGameTime throws error during tick (discontinuity)
    getGameTime = function() error('GameTime native crash') end
    s.tick()
    assert(s.clockDiscontinuous == true, 'clockDiscontinuous flag must be set on tick error')
    assert(#k:snapshot(100.0) == 0, 'Knowledge must be invalidated immediately on clock error during tick')

    -- Recovery from error: valid clock restored
    getGameTime = function() return gtTable end
    s.tick()
    assert(s.clockDiscontinuous == false, 'clockDiscontinuous flag cleared on recovery tick')
    assert(#k:snapshot(s.getTimeSeconds()) == 0, 'Recovery must NOT retain records whose elapsed age was unknown')

    -- Case 2: getTimeDelta returns invalid delta (negative) during tick
    k:update({
        status = 'sampled',
        results = {
            {id = 't2', kind = 'player', geometric = 'visible', visual = 'visible', position = {x = 10, y = 20, z = 0}}
        }
    }, s.getTimeSeconds())
    assert(#k:snapshot(s.getTimeSeconds()) == 1, 'Knowledge holds observation at current time')

    simDelta = -0.5
    s.tick()
    assert(s.clockDiscontinuous == true, 'clockDiscontinuous flag set on invalid delta')
    assert(#k:snapshot(s.getTimeSeconds() or 0) == 0, 'Knowledge must be invalidated immediately on invalid delta')

    -- Recovery from invalid delta
    simDelta = 0.05
    s.tick()
    assert(s.clockDiscontinuous == false)
    assert(#k:snapshot(s.getTimeSeconds()) == 0, 'Recovery from invalid delta must NOT retain records of unknown age')

    -- Case 3: look command executed while engine clock is unavailable fails and invalidates memory
    k:update({
        status = 'sampled',
        results = {
            {id = 't3', kind = 'player', geometric = 'visible', visual = 'visible', position = {x = 10, y = 20, z = 0}}
        }
    }, s.getTimeSeconds())
    assert(#k:snapshot(s.getTimeSeconds()) == 1)

    getGameTime = nil -- engine clock completely unavailable
    local resFail = disp:execute('look')
    assert(resFail.state == 'failed', 'look must fail closed when engine clock is unavailable')
    assert(#k:snapshot(100.0) == 0, 'Knowledge must be invalidated when look executes with unavailable clock')

    -- Recovery: restore clock and execute look
    getGameTime = function() return gtTable end
    simDelta = 0.02
    local resOk = disp:execute('look')
    assert(resOk.state == 'completed', 'look succeeds upon clock recovery')
    -- Snapshots from before recovery are empty (no stale records retained)
    local foundT3 = false
    for _, line in ipairs(resOk.lines) do
        if line:find('t3') then foundT3 = true end
    end
    assert(not foundT3, 'Old record t3 must NOT be retained upon clock recovery')

    SarahFoundation = nil
    getGameTime = nil
    s.reset()
end)
test('engine clock: module reload continuity on the SAME session preserves monotonicity',function()
    s.reset()
    local mockDelta = 0.025
    getGameTime = function()
        return {
            getTimeDelta = function() return mockDelta end,
            isGamePaused = function() return false end,
        }
    end

    s.tick()
    s.tick()
    local tBefore = s.getTimeSeconds()
    assert(math.abs(tBefore - 0.05) < 1e-6)

    -- Module reload: old state passed into new module instance
    local s2 = reload()
    assert(s2.accumulatedTime == s.accumulatedTime, 'accumulatedTime preserved across module reload')

    local tReload = s2.getTimeSeconds()
    assert(math.abs(tReload - 0.05) < 1e-6, 'getTimeSeconds on reloaded module returns preserved time')

    -- Tick on reloaded module continues monotonically
    s2.tick()
    local tAfter = s2.getTimeSeconds()
    assert(math.abs(tAfter - 0.075) < 1e-6, 'reloaded module advances monotonically')
    assert(tAfter > tBefore, 'must be strictly monotonic across module reload')

    s = s2
    getGameTime = nil
    s.reset()
end)
test('engine clock: session reset clears accumulated time and next session restarts cleanly from zero',function()
    s.reset()
    local mockDelta = 0.05
    getGameTime = function()
        return {
            getTimeDelta = function() return mockDelta end,
            isGamePaused = function() return false end,
        }
    end

    s.tick()
    assert(s.getTimeSeconds() > 0)

    -- Session reset (e.g. exit to main menu)
    s.reset()
    assert(s.accumulatedTime == nil, 'accumulatedTime must be nil upon session reset')

    -- Next session begins: calling getTimeSeconds initializes cleanly to 0.0
    local tNew = s.getTimeSeconds()
    assert(tNew == 0.0, 'new session starts cleanly from 0.0')

    s.tick()
    assert(math.abs(s.getTimeSeconds() - 0.05) < 1e-6, 'new session advances from zero')

    getGameTime = nil
    s.reset()
end)
test('engine clock: look command integration updates knowledge with monotonic time and prunes expired records',function()
    s.reset()
    local simTime = 100.0
    getGameTime = function()
        return {
            getTimeDelta = function() return 0.0 end,
            isGamePaused = function() return false end,
        }
    end
    s.accumulatedTime = simTime

    local testAdapter = {
        samplePerception = function(npc)
            return {
                status = 'sampled',
                lighting = 'unknown',
                results = {
                    {id = 'p1', kind = 'player', geometric = 'visible', visual = 'unknown'}
                },
                counts = {candidates = 1, processed = 1}
            }
        end,
        resetPerception = function() end
    }
    SarahFoundation = {
        controller = {
            npc = {id = 'sarah'},
            adapter = testAdapter
        }
    }
    obsState = 'active'
    obsNpc = {x = 10, y = 20, z = 0}
    obsPlayer = {x = 12, y = 20, z = 0, dead = false, alive = true}

    local disp = s.getDispatch()
    disp:reset()
    s.accumulatedTime = simTime

    -- Execute look: since lighting is unknown, visual is unknown, so confirmed = 0
    local res = disp:execute('look')
    assert(res.state == 'completed', 'look must succeed when monotonic time is available')
    local foundGeo = false
    local foundVis = false
    local foundMem = false
    for _,line in ipairs(res.lines) do
        if line:find('Geometry: 1 visible') then foundGeo = true end
        if line:find('Visual: 0 confirmed %(lighting: unknown') then foundVis = true end
        if line:find('Memory: 0 confirmed records') then foundMem = true end
    end
    assert(foundGeo and foundVis and foundMem, 'look output must format geometry, visual, and memory lines')

    -- Now simulate an explicit confirmed visual record directly in Knowledge to test time progression & expiry
    local k = disp:getKnowledge()
    k:update({
        status = 'sampled',
        results = {
            {id = 't1', kind = 'player', geometric = 'visible', visual = 'visible', position = {x = 10, y = 20, z = 0}}
        }
    }, simTime)
    assert(#k:snapshot(simTime) == 1, 'Knowledge must hold the confirmed record at simTime')

    -- Advance clock by 5 seconds: record is still fresh (< 10s age)
    simTime = 105.0
    s.accumulatedTime = simTime
    local res2 = disp:execute('look')
    local snap2 = k:snapshot(simTime)
    assert(res2.state == 'completed')
    assert(#snap2 == 1, 'record must still exist at age 5.0s')

    -- Advance clock past 10 seconds (e.g. +11s, simTime = 116.0): record expires!
    simTime = 116.0
    s.accumulatedTime = simTime
    local res3 = disp:execute('look')
    assert(res3.state == 'completed')
    local snap3 = k:snapshot(simTime)
    assert(#snap3 == 0, 'record must expire after >= 10s age')

    -- Clock reversal: simTime goes backward from 116.0 to 110.0
    -- Add a record, then trigger reversal
    k:update({
        status = 'sampled',
        results = {
            {id = 't2', kind = 'player', geometric = 'visible', visual = 'visible', position = {x = 10, y = 20, z = 0}}
        }
    }, 116.0)
    assert(#k:snapshot(116.0) == 1)

    simTime = 110.0
    s.accumulatedTime = simTime
    local resRev = disp:execute('look')
    assert(resRev.state == 'failed', 'look must fail closed on clock reversal')
    assert(resRev.lines[1]:find('non%-monotonic time'), 'error must indicate non-monotonic time')
    assert(#k:snapshot(116.0) == 0, 'Knowledge must be invalidated immediately on clock reversal')

    SarahFoundation = nil
    getGameTime = nil
    s.reset()
end)
print('RESULT '..count..' simulated console checks passed')
''')
