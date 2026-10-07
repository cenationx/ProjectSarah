-- Command parser, validation, dispatch and action boundary.
-- No mutable engine handles are exposed to callers.
local Commands={}
local function loadModule(name)
    local mod = rawget(_G, name)
    if not mod and type(require) == "function" then
        local ok, m = pcall(require, "Sarah/" .. name)
        if ok and m then return m end
        local ok2, m2 = pcall(require, name)
        if ok2 and m2 then return m2 end
    end
    return mod
end
local Knowledge = loadModule("Knowledge")
local function isValidNumber(n)
    return type(n)=='number' and n==n and n~=math.huge and n~=-math.huge
end
local function isValidCoord(x,y,z)
    return isValidNumber(x) and isValidNumber(y) and isValidNumber(z)
end
local function isPlayerDead(data)
    if not data then return false end
    if data.playerLiveness=='dead' then return true end
    if data.playerDead~=nil then return data.playerDead==true end
    if data.player then
        if data.player.liveness=='dead' then return true end
        if data.player.dead~=nil then return data.player.dead==true end
        if data.player.isDead~=nil then return data.player.isDead==true end
        if data.player.alive~=nil then return data.player.alive==false end
    end
    return false
end
local function isPlayerAlive(data)
    if not data then return false end
    if data.playerLiveness~=nil then
        return data.playerLiveness=='alive'
    end
    if data.playerDead~=nil then
        if data.playerDead==true then return false end
        if data.playerAlive~=nil then return data.playerAlive==true end
    end
    if data.player then
        if data.player.liveness~=nil then
            return data.player.liveness=='alive'
        end
        if data.player.alive~=nil then return data.player.alive==true end
        if data.player.dead~=nil then return data.player.dead==false end
        if data.player.isDead~=nil then return data.player.isDead==false end
    end
    return false
end
function Commands.new(observe,stopCallback,identityProvider,walkCallback,validateCallback,perceiveCallback,knowledge,timeProvider,resetPerceptionCallback)
    local function resolveKnowledge(k)
        if k then return k end
        local modK = Knowledge or loadModule("Knowledge")
        if modK and type(modK.new) == "function" then
            local ok, inst = pcall(modK.new)
            if ok and inst then return inst end
        end
        return nil
    end

    local initialKnowledge = resolveKnowledge(knowledge)

    local self={
        sequence=0,
        session=1,
        active=nil,
        token=0,
        history={},
        maxHistory=30,
        lastAction=nil,
        stopFailed=nil,
        noticeQueue={},
        observe=observe or function() return {state='unavailable'} end,
        stopCallback=stopCallback,
        identityProvider=identityProvider,
        walkCallback=walkCallback,
        validateCallback=validateCallback,
        perceiveCallback=perceiveCallback,
        knowledge=initialKnowledge,
        timeProvider=timeProvider,
        resetPerceptionCallback=resetPerceptionCallback,
        lastNow=nil,
        lastOwner=nil,
        lastNpc=nil
    }
    function self:getKnowledge()
        if not self.knowledge then
            self.knowledge = resolveKnowledge(nil)
        end
        return self.knowledge
    end
    function self:getNow()
        if type(self.timeProvider) ~= 'function' then
            self:resetKnowledge()
            self.lastNow = nil
            return nil, 'missing time provider'
        end
        local ok, t = pcall(self.timeProvider)
        if not ok then
            self:resetKnowledge()
            self.lastNow = nil
            return nil, 'time provider error: ' .. tostring(t)
        end
        if t == nil then
            self:resetKnowledge()
            self.lastNow = nil
            return nil, 'time source unavailable'
        end
        if type(t) ~= 'number' or t ~= t or t < 0 or t == math.huge then
            self:resetKnowledge()
            self.lastNow = nil
            return nil, 'invalid time value'
        end
        if self.lastNow and t < self.lastNow then
            self:resetKnowledge()
            local prev = self.lastNow
            self.lastNow = nil
            return nil, 'non-monotonic time: ' .. tostring(t) .. ' < ' .. tostring(prev)
        end
        self.lastNow = t
        return t
    end
    function self:resetKnowledge()
        if self.knowledge and self.knowledge.reset then
            pcall(self.knowledge.reset, self.knowledge)
        end
    end
    function self:resetPerception()
        if type(self.resetPerceptionCallback) == 'function' then
            pcall(self.resetPerceptionCallback)
        end
        local ctrl, _ = self:getIdentity()
        if ctrl and ctrl.adapter and type(ctrl.adapter.resetPerception) == 'function' then
            pcall(ctrl.adapter.resetPerception)
        end
    end
    -- Unambiguous private identity contract:
    -- identityProvider function returns (controller, npc) references directly.
    -- Preserves exact controller and NPC identities without wrapper ambiguity
    -- and without exposing mutable engine handles through public observations.
    function self:getIdentity()
        if type(self.identityProvider)=='function' then
            local ok,ctrl,npc=pcall(self.identityProvider)
            if ok then return ctrl,npc end
            return nil,nil
        end
        return self.identityProvider,nil
    end
    local function addHistory(record)
        self.history[#self.history+1]=record
        while #self.history>self.maxHistory do table.remove(self.history,1) end
    end
    function self:updateHistory(id,newState,newSummary)
        for i=#self.history,1,-1 do
            if self.history[i].id==id then
                self.history[i].state=newState
                if newSummary then self.history[i].summary=newSummary end
                break
            end
        end
    end
    function self:getHistory()
        local copy={}
        for i,h in ipairs(self.history) do
            copy[i]={id=h.id,command=h.command,state=h.state,summary=h.summary}
        end
        return copy
    end
    function self:consumeNotices()
        local list=self.noticeQueue or {}
        self.noticeQueue={}
        return list
    end
    function self:invokeStop(reason,action)
        if not self.stopCallback then return true end
        local ok,ret,err=pcall(self.stopCallback,reason or 'cancelled',action)
        if not ok then
            local clean=tostring(ret):match(':%d+: (.*)') or tostring(ret)
            return false,clean:sub(1,60)
        end
        if ret==false then
            local clean=tostring(err or 'stop failed')
            return false,clean:sub(1,60)
        end
        return true
    end
    function self:invokeValidate(target)
        if self.validateCallback then
            local ok,ret,err=pcall(self.validateCallback,target)
            if not ok then return false,tostring(ret) end
            return ret,err
        end
        local ctrl,npc=self:getIdentity()
        if ctrl and ctrl.adapter and ctrl.adapter.validateTarget and npc then
            local ok,ret,err=pcall(ctrl.adapter.validateTarget,npc,target)
            if not ok then return false,tostring(ret) end
            return ret,err
        end
        if type(target)=='table' and type(target.x)=='number' and type(target.y)=='number' and type(target.z)=='number' then
            return true
        end
        return false,'invalid target'
    end
    function self:invokeWalk(target,onComplete,onFail,action)
        if not self.walkCallback then return false,'walk callback unavailable' end
        local ok,ret,extra=pcall(self.walkCallback,target,onComplete,onFail,action)
        if not ok then
            local clean=tostring(ret):match(':%d+: (.*)') or tostring(ret)
            return false,clean:sub(1,60)
        end
        if ret==false then
            local clean=tostring(extra or 'walk failed')
            return false,clean:sub(1,60)
        end
        local actionObj=(type(ret)=='table' and ret) or (type(extra)=='table' and extra) or (ret~=false and ret)
        return true,actionObj
    end
    function self:cancelActive(reason,isUserStop)
        if not self.active then return false,'nothing active' end
        local action=self.active
        if action.retireStep then
            action.retireStep()
            action.retireStep=nil
        end
        action.stepGen=(action.stepGen or 0)+1
        self.active=nil
        action.state='cancelled'
        action.summary=reason or 'cancelled'
        self.lastAction={id=action.id,command=action.command,state='cancelled',reason=action.summary}
        self:updateHistory(action.id,'cancelled',action.summary)

        if reason == 'session reset' or reason == 'controller replaced' or reason == 'npc replaced'
           or reason == 'controller unavailable' or reason == 'npc unavailable'
           or reason == 'dead' or reason == 'unloaded' or reason == 'absent' then
            self:resetKnowledge()
            self:resetPerception()
        end

        local stopOk,stopErr
        if action.stopFailed then
            stopOk=false
            stopErr=action.stopFailed
        else
            stopOk,stopErr=self:invokeStop(reason or 'cancelled',{
                id=action.id,
                command=action.command,
                state=action.state,
                owner=action.owner,
                controller=action.owner,
                npc=action.npc,
                session=action.session
            })
        end
        if not stopOk then
            self.stopFailed=stopErr or 'stop failed'
            action.stopFailed=self.stopFailed
            self.lastAction.stopFailed=self.stopFailed
        else
            self.stopFailed=nil
        end

        local isUser=(isUserStop==true) or (reason=='stopped by user') or (reason=='session reset')
        if not isUser then
            local noticeMsg
            local stopWarn=not stopOk and (' Warning: engine stop failed ('..tostring(self.stopFailed)..'); movement blocked pending recovery.') or ''
            if action.command=='follow' then
                noticeMsg='Follow disengaged: '..action.summary..'.'..stopWarn
            else
                noticeMsg='Action #'..action.id..' cancelled: '..action.summary..'.'..stopWarn
            end
            self.noticeQueue[#self.noticeQueue+1]={
                id=action.id,
                command=action.command,
                state=action.state,
                reason=action.summary,
                message=noticeMsg,
                isBad=true,
                stopFailed=not stopOk and self.stopFailed or nil
            }
        end

        return true,{id=action.id,command=action.command,state=action.state,summary=action.summary},stopOk,stopErr
    end
    function self:checkLifecycle()
        local ok,data=pcall(self.observe,false)
        if not ok or type(data)~='table' then
            local errReason='observation error'
            if self.active then
                self:cancelActive(errReason)
            end
            return false,errReason
        end
        if data.state~='active' then
            if data.state == 'dead' or data.state == 'unloaded' or data.state == 'absent' then
                self:resetKnowledge()
                self:resetPerception()
            end
            if self.active then
                self:cancelActive(data.state)
            end
            return false,data.state
        end
        local currentOwner,currentNpc=self:getIdentity()
        if (self.lastOwner and currentOwner and self.lastOwner~=currentOwner) or
           (self.lastNpc and currentNpc and self.lastNpc~=currentNpc) or
           (self.lastOwner and currentOwner==nil) or
           (self.lastNpc and currentNpc==nil) then
            if self.lastOwner and self.lastOwner.adapter and type(self.lastOwner.adapter.resetPerception) == 'function' then
                pcall(self.lastOwner.adapter.resetPerception)
            end
            self:resetKnowledge()
            self:resetPerception()
        end
        self.lastOwner=currentOwner
        self.lastNpc=currentNpc
        if self.active then
            if self.active.owner and currentOwner and self.active.owner~=currentOwner then
                self:cancelActive('controller replaced')
                return false,'controller replaced'
            end
            if self.active.owner and currentOwner==nil then
                self:cancelActive('controller unavailable')
                return false,'controller unavailable'
            end
            if self.active.npc and currentNpc and self.active.npc~=currentNpc then
                self:cancelActive('npc replaced')
                return false,'npc replaced'
            end
            if self.active.npc and currentNpc==nil then
                self:cancelActive('npc unavailable')
                return false,'npc unavailable'
            end
            if self.active.command=='follow' then
                if not data.player or not isValidCoord(data.player.x,data.player.y,data.player.z) then
                    self:cancelActive('player unavailable')
                    return false,'player unavailable'
                end
                if isPlayerDead(data) then
                    self:cancelActive('player dead')
                    return false,'player dead'
                end
                if not isPlayerAlive(data) then
                    self:cancelActive('player liveness unknown')
                    return false,'player liveness unknown'
                end
            end
        end
        return true,data
    end
    function self:findFollowTarget(nx,ny,nz,px,py,pz)
        local ipx=math.floor(px)
        local ipy=math.floor(py)
        local offsets={
            {1,0},{-1,0},{0,1},{0,-1},
            {1,1},{-1,1},{1,-1},{-1,-1}
        }
        local candidates={}
        for i,off in ipairs(offsets) do
            candidates[i]={x=ipx+off[1],y=ipy+off[2],z=pz}
        end
        local snx=(math.floor(nx)==nx) and (nx+0.5) or nx
        local sny=(math.floor(ny)==ny) and (ny+0.5) or ny
        table.sort(candidates,function(a,b)
            local da=(a.x+0.5-snx)^2+(a.y+0.5-sny)^2
            local db=(b.x+0.5-snx)^2+(b.y+0.5-sny)^2
            if da~=db then return da<db end
            if a.x~=b.x then return a.x<b.x end
            return a.y<b.y
        end)

        for _,cand in ipairs(candidates) do
            local valid,err=self:invokeValidate(cand)
            if valid then
                return cand
            end
        end
        return nil
    end
    function self:dispatchFollowStep(data,nx,ny,nz,px,py,pz,precomputedTarget)
        local act=self.active
        if not act or act.command~='follow' then return false,'no active follow' end
        if not isValidCoord(nx,ny,nz) or not isValidCoord(px,py,pz) then
            self:cancelActive('invalid coordinates')
            return false,'invalid coordinates'
        end

        local chosenTarget=precomputedTarget or self:findFollowTarget(nx,ny,nz,px,py,pz)

        if not chosenTarget then
            self:cancelActive('no valid target near player')
            return false,'no valid target near player'
        end

        act.stepGen=(act.stepGen or 0)+1
        local curStepGen=act.stepGen
        act.stepState='walking'
        act.pace=(data and data.playerRunning) and 'run' or 'walk'
        act.stepTicks=0
        act.currentTarget=chosenTarget
        act.lastTarget=chosenTarget
        act.targetPlayer={x=px,y=py,z=pz}
        act.summary=string.format('Following player to (%d, %d, %d)',chosenTarget.x,chosenTarget.y,chosenTarget.z)
        self:updateHistory(act.id,'running',act.summary)

        local actId=act.id
        local actToken=act.token
        local actSession=act.session
        local stepRetired=false

        act.retireStep=function()
            stepRetired=true
        end

        local function checkStepCallback()
            if stepRetired then
                return false,'retired'
            end
            if not self.active or self.active.id~=actId or self.active.token~=actToken then
                stepRetired=true
                return false,'stale'
            end
            if actSession and self.active.session and actSession~=self.active.session then
                stepRetired=true
                return false,'stale'
            end
            if self.active.stepGen~=curStepGen or self.active.stepState~='walking' then
                stepRetired=true
                return false,'stale step'
            end
            local currentOwner,currentNpc=self:getIdentity()
            if self.active.owner and currentOwner and self.active.owner~=currentOwner then
                stepRetired=true
                self:cancelActive('controller replaced')
                return false,'controller replaced'
            end
            if self.active.owner and currentOwner==nil then
                stepRetired=true
                self:cancelActive('controller unavailable')
                return false,'controller unavailable'
            end
            if self.active.npc and currentNpc and self.active.npc~=currentNpc then
                stepRetired=true
                self:cancelActive('npc replaced')
                return false,'npc replaced'
            end
            if self.active.npc and currentNpc==nil then
                stepRetired=true
                self:cancelActive('npc unavailable')
                return false,'npc unavailable'
            end
            local valid,reason=self:checkLifecycle()
            if not valid then
                stepRetired=true
                return false,reason
            end
            return true
        end

        local function onStepComplete()
            local ok,reason=checkStepCallback()
            if not ok then return end
            stepRetired=true
            if self.active then
                self.active.retireStep=nil
                self.active.stepGen=self.active.stepGen+1
                self.active.stepState='idle'
                self.active.stepTicks=0
                self.active.stallTicks=0
                self.active.pace='walk'
                local obsOk,obsData=pcall(self.observe,false)
                if obsOk and type(obsData)=='table' and obsData.npc and isValidCoord(obsData.npc.x,obsData.npc.y,obsData.npc.z) then
                    self.active.lastProgressX=obsData.npc.x
                    self.active.lastProgressY=obsData.npc.y
                end
                self.active.currentTarget=nil
                self.active.cooldown=0
                self.active.summary='Following player (in range)'
                self:updateHistory(self.active.id,'running',self.active.summary)
            end
        end

        local function onStepFail(actionObj,reason)
            local ok,failReason=checkStepCallback()
            if not ok then return end
            stepRetired=true
            if self.active then
                self.active.retireStep=nil
                self.active.stepGen=self.active.stepGen+1
            end
            self:cancelActive(reason or 'path failed')
        end

        local walkOk,actOrErr=self:invokeWalk(chosenTarget,onStepComplete,onStepFail,act)
        if not walkOk then
            stepRetired=true
            if self.active and self.active == act and self.active.id == actId and self.active.token == actToken and self.active.stepGen == curStepGen then
                act.stepAction=nil
                self.active.retireStep=nil
                self.active.stepGen=self.active.stepGen+1
                self:cancelActive(actOrErr or 'walk failed to start')
            end
            return false,actOrErr
        end
        if not stepRetired and self.active and self.active == act and self.active.id == actId and self.active.token == actToken and self.active.stepGen == curStepGen and self.active.stepState == 'walking' then
            act.stepAction = (type(actOrErr) == 'table') and actOrErr or nil
        end
        return true
    end
    function self:tickFollow()
        local act=self.active
        if not act or act.command~='follow' then return true end

        local ok,data=pcall(self.observe,false)
        if not ok or type(data)~='table' then
            self:cancelActive('observation error')
            return false,'observation error'
        end
        if data.state~='active' then
            self:cancelActive(data.state)
            return false,data.state
        end
        if not data.npc or not isValidCoord(data.npc.x,data.npc.y,data.npc.z) then
            self:cancelActive('Sarah position unavailable')
            return false,'Sarah position unavailable'
        end
        if not data.player or not isValidCoord(data.player.x,data.player.y,data.player.z) then
            self:cancelActive('player unavailable')
            return false,'player unavailable'
        end
        if isPlayerDead(data) then
            self:cancelActive('player dead')
            return false,'player dead'
        end
        if not isPlayerAlive(data) then
            self:cancelActive('player liveness unknown')
            return false,'player liveness unknown'
        end

        local nx,ny,nz=data.npc.x,data.npc.y,math.floor(data.npc.z)
        local px,py,pz=data.player.x,data.player.y,math.floor(data.player.z)

        if nz~=pz then
            self:cancelActive('player changed floor')
            return false,'player changed floor'
        end

        local dx=px-nx
        local dy=py-ny
        local distSq=dx*dx+dy*dy
        if distSq>64 then
            self:cancelActive('player out of range (>8 tiles)')
            return false,'player out of range (>8 tiles)'
        end

        if act.stepState=='walking' then
            act.stepTicks=(act.stepTicks or 0)+1
            local maxStepTicks=act.maxStepTicks or 600
            if act.stepTicks>=maxStepTicks then
                self:cancelActive('timeout')
                return false,'timeout'
            end

            local desiredPace=(data and data.playerRunning) and 'run' or 'walk'
            if act.pace~=desiredPace then
                act.pace=desiredPace
                if act.stepAction and act.stepAction.setPace then
                    act.stepAction:setPace(desiredPace)
                end
            end

            local minRetargetTicks=act.minRetargetTicks or 6

            if distSq<=4.0 then
                act.stallTicks=0
                act.lastProgressX=nx
                act.lastProgressY=ny
                act.pace='walk'
                if act.stepTicks>=minRetargetTicks then
                    if act.retireStep then
                        act.retireStep()
                        act.retireStep=nil
                    end
                    act.stepGen=(act.stepGen or 0)+1
                    local stopOk,stopErr=self:invokeStop('in range',{
                        id=act.id,
                        command=act.command,
                        state=act.state,
                        owner=act.owner,
                        controller=act.owner,
                        npc=act.npc,
                        session=act.session
                    })
                    if not stopOk then
                        self.stopFailed=stopErr or 'stop failed'
                        act.stopFailed=self.stopFailed
                        self:cancelActive(stopErr or 'stop failed')
                        return false,stopErr
                    end
                    act.stepState='idle'
                    act.stepTicks=0
                    act.currentTarget=nil
                    act.cooldown=0
                    act.summary='Following player (in range)'
                    self:updateHistory(act.id,'running',act.summary)
                end
                return true
            end

            local lpx=act.lastProgressX or nx
            local lpy=act.lastProgressY or ny
            local movedSq=(nx-lpx)*(nx-lpx)+(ny-lpy)*(ny-lpy)
            if movedSq>=0.25 then
                act.lastProgressX=nx
                act.lastProgressY=ny
                act.stallTicks=0
            else
                act.stallTicks=(act.stallTicks or 0)+1
                local maxStallTicks=act.maxStallTicks or maxStepTicks or 600
                if act.stallTicks>=maxStallTicks then
                    self:cancelActive('timeout')
                    return false,'timeout'
                end
            end

            if act.stepTicks>=minRetargetTicks then
                local pdx=px-(act.targetPlayer and act.targetPlayer.x or px)
                local pdy=py-(act.targetPlayer and act.targetPlayer.y or py)
                local playerShiftSq=pdx*pdx+pdy*pdy
                local tdx=act.currentTarget and ((act.currentTarget.x+0.5)-px) or 0
                local tdy=act.currentTarget and ((act.currentTarget.y+0.5)-py) or 0
                local targetDistSq=tdx*tdx+tdy*tdy

                if playerShiftSq>=4.0 or targetDistSq>4.0 then
                    local newTarget=self:findFollowTarget(nx,ny,nz,px,py,pz)
                    if newTarget then
                        local isSameTarget=act.currentTarget and (newTarget.x==act.currentTarget.x and newTarget.y==act.currentTarget.y and newTarget.z==act.currentTarget.z)
                        if not isSameTarget then
                            if act.retireStep then
                                act.retireStep()
                                act.retireStep=nil
                            end
                            act.stepGen=(act.stepGen or 0)+1

                            local stopOk,stopErr=self:invokeStop('retarget',{
                                id=act.id,
                                command=act.command,
                                state=act.state,
                                owner=act.owner,
                                controller=act.owner,
                                npc=act.npc,
                                session=act.session
                            })
                            if not stopOk then
                                self.stopFailed=stopErr or 'stop failed'
                                act.stopFailed=self.stopFailed
                                self:cancelActive(stopErr or 'stop failed')
                                return false,stopErr
                            end

                            act.stepState='idle'
                            act.stepTicks=0
                            act.currentTarget=nil
                            return self:dispatchFollowStep(data,nx,ny,nz,px,py,pz,newTarget)
                        else
                            act.targetPlayer={x=px,y=py,z=pz}
                        end
                    end
                end
            end

            return true
        end

        if distSq<=4.0 then
            act.stallTicks=0
            act.lastProgressX=nx
            act.lastProgressY=ny
            act.summary='Following player (in range)'
            self:updateHistory(act.id,'running',act.summary)
            return true
        end

        if (act.cooldown or 0)>0 then
            act.cooldown=act.cooldown-1
            return true
        end

        return self:dispatchFollowStep(data,nx,ny,nz,px,py,pz)
    end
    function self:tick()
        local valid,reason=self:checkLifecycle()
        if not valid then return false,reason end
        if self.timeProvider then
            self:getNow()
        end
        if self.active and self.active.command=='walk here' then
            local act=self.active
            act.ticks=(act.ticks or 0)+1
            local maxTicks=act.maxTicks or 600
            if act.ticks>=maxTicks then
                self:cancelActive('timeout')
                return false,'timeout'
            end
        elseif self.active and self.active.command=='follow' then
            return self:tickFollow()
        end
        return true
    end
    function self:beginAction(name,details)
        if self.active then return false,'busy' end
        local ok,data=pcall(self.observe,false)
        if not ok or type(data)~='table' or data.state~='active' then
            return false,(type(data)=='table' and data.state) or 'unavailable'
        end
        self.sequence=self.sequence+1
        self.token=self.token+1
        local detailsCopy={}
        if type(details)=='table' then
            for k,v in pairs(details) do detailsCopy[k]=v end
        end
        local owner,npcOwner=self:getIdentity()
        local action={
            id=self.sequence,
            session=self.session,
            command=name,
            state='running',
            token=self.token,
            owner=owner,
            controller=owner,
            npc=npcOwner,
            maxTicks=detailsCopy.maxTicks or 600,
            ticks=0,
            details=detailsCopy
        }
        self.active=action
        addHistory({id=action.id,command=action.command,state='running',summary='Started '..name})
        return true,{id=action.id,command=action.command,state=action.state,token=action.token,session=action.session}
    end
    function self:completeAction(id,token,success,message,owner,npc,session)
        if not self.active or self.active.id~=id or self.active.token~=token then
            return false,'stale or cancelled'
        end
        if session and self.active.session and session~=self.active.session then
            return false,'stale or cancelled'
        end
        if owner and self.active.owner and owner~=self.active.owner then
            return false,'stale or cancelled'
        end
        if npc and self.active.npc and npc~=self.active.npc then
            return false,'stale or cancelled'
        end
        local currentOwner,currentNpc=self:getIdentity()
        if self.active.owner and currentOwner and self.active.owner~=currentOwner then
            self:cancelActive('controller replaced')
            return false,'stale or cancelled'
        end
        if self.active.owner and currentOwner==nil then
            self:cancelActive('controller unavailable')
            return false,'stale or cancelled'
        end
        if self.active.npc and currentNpc and self.active.npc~=currentNpc then
            self:cancelActive('npc replaced')
            return false,'stale or cancelled'
        end
        if self.active.npc and currentNpc==nil then
            self:cancelActive('npc unavailable')
            return false,'stale or cancelled'
        end
        local valid,reason=self:checkLifecycle()
        if not valid then
            return false,'stale or cancelled'
        end
        local action=self.active
        self.active=nil
        action.state=success and 'completed' or 'failed'
        action.summary=message or (success and 'Completed' or 'Failed')
        self.lastAction={id=action.id,command=action.command,state=action.state,reason=action.summary}
        self:updateHistory(id,action.state,action.summary)
        if not success then
            local isUser=(message=='stopped by user') or (message=='session reset')
            if not isUser then
                local noticeMsg
                if action.command=='follow' then
                    noticeMsg='Follow disengaged: '..action.summary..'.'
                else
                    noticeMsg='Action #'..action.id..' failed: '..action.summary..'.'
                end
                self.noticeQueue[#self.noticeQueue+1]={
                    id=action.id,
                    command=action.command,
                    state=action.state,
                    reason=action.summary,
                    message=noticeMsg,
                    isBad=true
                }
            end
        end
        return true,action.state
    end
    function self:reset()
        if self.active then self:cancelActive('session reset',true) end
        self:resetKnowledge()
        self:resetPerception()
        self.active=nil
        self.lastAction=nil
        self.stopFailed=nil
        self.sequence=0
        self.session=self.session+1
        self.history={}
        self.noticeQueue={}
        self.lastNow=nil
        self.lastOwner,self.lastNpc=self:getIdentity()
    end
    function self:requestWalk(target)
        return self:execute('walk here',target)
    end
    function self:requestFollow()
        return self:execute('follow')
    end
    function self:execute(input,target)
        self.sequence=self.sequence+1
        local result={id=self.sequence,state='rejected',lines={}}
        if type(input)~='string' or #input>128 or input:find('[%c]') then
            result.lines={'Use one command, at most 128 characters.'}
            addHistory({id=result.id,command=tostring(input):sub(1,32),state=result.state,summary=result.lines[1]})
            return result
        end
        local curOwner,curNpc=self:getIdentity()
        if (self.lastOwner and curOwner and self.lastOwner~=curOwner) or
           (self.lastNpc and curNpc and self.lastNpc~=curNpc) then
            self:resetKnowledge()
            self:resetPerception()
        end
        self.lastOwner=curOwner
        self.lastNpc=curNpc
        local command=input:match('^%s*(.-)%s*$'):lower():gsub('%s+',' ')
        if command~='help' and command~='status' and command~='inventory' and command~='stop' and command~='history' and command~='walk here' and command~='follow' and command~='look' and command~='perceive' then
            result.lines={'Unknown command. Try help.'}
            addHistory({id=result.id,command=command,state=result.state,summary=result.lines[1]})
            return result
        end
        if command=='help' then
            result.state='completed'
            result.lines={
                'help - list commands',
                'status - inspect Sarah and current action',
                'inventory - list carried items',
                'walk here - walk to player square (max 8 tiles, same floor)',
                'follow - follow player (max 8 tiles, same floor)',
                'stop - cancel active action or request',
                'history - list recent command outcomes',
                'look - sample diagnostic perception around Sarah',
                'Manual console slice C. Movement commands validated.'
            }
            addHistory({id=result.id,command=command,state=result.state,summary='Help displayed'})
            return result
        end
        if command=='walk here' then
            if self.active then
                result.state='rejected'
                result.lines={'Sarah is busy (#'..self.active.id..' '..self.active.command..' is running).'}
                addHistory({id=result.id,command=command,state='rejected',summary='Busy (#'..self.active.id..')'})
                return result
            end
            if self.stopFailed then
                result.state='rejected'
                result.lines={'Prior engine stop failed ('..self.stopFailed..'); movement blocked until stop recovers.'}
                addHistory({id=result.id,command=command,state='rejected',summary='Stop recovery required'})
                return result
            end
            local ok,data=pcall(self.observe,false)
            if not ok or type(data)~='table' then
                result.state='failed'
                result.lines={'Observation failed; no action taken.'}
                addHistory({id=result.id,command=command,state='failed',summary='Observation failed'})
                return result
            end
            if data.state~='active' then
                result.state='rejected'
                result.lines={'Sarah is '..data.state..'; cannot walk.'}
                addHistory({id=result.id,command=command,state='rejected',summary='Sarah '..data.state})
                return result
            end
            if not data.npc or not isValidCoord(data.npc.x,data.npc.y,data.npc.z) then
                result.state='rejected'
                result.lines={'Sarah position unavailable.'}
                addHistory({id=result.id,command=command,state='rejected',summary='NPC position missing'})
                return result
            end
            local tx,ty,tz
            if target then
                if type(target)=='table' then
                    if target.getX and type(target.getX)=='function' then
                        tx,ty,tz=target:getX(),target:getY(),target:getZ()
                    else
                        tx,ty,tz=target.x,target.y,target.z
                    end
                end
            elseif data.player then
                tx,ty,tz=data.player.x,data.player.y,data.player.z
            else
                result.state='rejected'
                result.lines={'Player position unavailable.'}
                addHistory({id=result.id,command=command,state='rejected',summary='Player position missing'})
                return result
            end
            if not isValidCoord(tx,ty,tz) then
                result.state='rejected'
                result.lines={'Invalid target coordinates.'}
                addHistory({id=result.id,command=command,state='rejected',summary='Invalid target coordinates'})
                return result
            end
            tx=math.floor(tx)
            ty=math.floor(ty)
            tz=math.floor(tz)
            local sx,sy,sz=data.npc.x,data.npc.y,math.floor(data.npc.z)
            if sz~=tz then
                result.state='rejected'
                result.lines={'Target is on a different floor.'}
                addHistory({id=result.id,command=command,state='rejected',summary='Different floor'})
                return result
            end
            local dx=(tx+0.5)-sx
            local dy=(ty+0.5)-sy
            if (dx*dx+dy*dy)>64 then
                result.state='rejected'
                result.lines={'Target is too far (maximum 8 tiles).'}
                addHistory({id=result.id,command=command,state='rejected',summary='Too far (>8 tiles)'})
                return result
            end
            if math.floor(sx)==tx and math.floor(sy)==ty then
                result.state='completed'
                result.lines={string.format('Already at target (%d, %d, %d).',tx,ty,tz)}
                addHistory({id=result.id,command=command,state='completed',summary=string.format('Already at (%d, %d, %d)',tx,ty,tz)})
                return result
            end
            self.token=self.token+1
            local owner,npcOwner=self:getIdentity()
            local resolvedTarget={x=tx,y=ty,z=tz}
            local action={
                id=result.id,
                session=self.session,
                command='walk here',
                state='running',
                token=self.token,
                owner=owner,
                controller=owner,
                npc=npcOwner,
                maxTicks=600,
                ticks=0,
                pace='walk',
                details={targetX=tx,targetY=ty,targetZ=tz}
            }
            self.active=action
            addHistory({id=action.id,command=command,state='running',summary=string.format('Walking to (%d, %d, %d)',tx,ty,tz)})
            local actId=action.id
            local actToken=action.token
            local actSession=action.session
            local function onComplete()
                if not self.active or self.active.id~=actId or self.active.token~=actToken or (actSession and self.active.session and actSession~=self.active.session) then
                    self:completeAction(actId,actToken,false,'stale or cancelled',action.owner,action.npc,actSession)
                    return
                end
                local currentOwner,currentNpc=self:getIdentity()
                if action.owner and currentOwner and action.owner~=currentOwner then
                    self:completeAction(actId,actToken,false,'stale controller',action.owner,action.npc,actSession)
                    return
                end
                if action.npc and currentNpc and action.npc~=currentNpc then
                    self:completeAction(actId,actToken,false,'stale npc',action.owner,action.npc,actSession)
                    return
                end
                local obsOk,obsData=pcall(self.observe,false)
                if not obsOk or type(obsData)~='table' or obsData.state~='active' or not obsData.npc then
                    self:completeAction(actId,actToken,false,'Sarah unavailable on arrival',action.owner,action.npc,actSession)
                    return
                end
                local nx,ny,nz=math.floor(obsData.npc.x),math.floor(obsData.npc.y),math.floor(obsData.npc.z)
                if nx==tx and ny==ty and nz==tz then
                    self:completeAction(actId,actToken,true,string.format('Reached target (%d, %d, %d).',tx,ty,tz),action.owner,action.npc,actSession)
                else
                    self:completeAction(actId,actToken,false,string.format('Stopped before target at (%d, %d, %d).',nx,ny,nz),action.owner,action.npc,actSession)
                end
            end
            local function onFail(actionObj,reason)
                if not self.active or self.active.id~=actId or self.active.token~=actToken or (actSession and self.active.session and actSession~=self.active.session) then
                    self:completeAction(actId,actToken,false,'stale or cancelled',action.owner,action.npc,actSession)
                    return
                end
                self:completeAction(actId,actToken,false,reason or 'Walk failed',action.owner,action.npc,actSession)
            end
            local walkOk,walkErr=self:invokeWalk(resolvedTarget,onComplete,onFail,action)
            if not walkOk then
                self.active=nil
                self:updateHistory(action.id,'failed','Start failed: '..tostring(walkErr))
                result.state='failed'
                result.lines={'Walk failed to start: '..tostring(walkErr)..'.'}
                return result
            end
            if not self.active then
                result.state=action.state
                result.lines={action.summary or ('Walk '..action.state)}
                return result
            end
            result.state='running'
            result.lines={string.format('Walking to (%d, %d, %d).',tx,ty,tz)}
            return result
        end
        if command=='follow' then
            if self.active then
                result.state='rejected'
                result.lines={'Sarah is busy (#'..self.active.id..' '..self.active.command..' is running).'}
                addHistory({id=result.id,command=command,state='rejected',summary='Busy (#'..self.active.id..')'})
                return result
            end
            if self.stopFailed then
                result.state='rejected'
                result.lines={'Prior engine stop failed ('..self.stopFailed..'); movement blocked until stop recovers.'}
                addHistory({id=result.id,command=command,state='rejected',summary='Stop recovery required'})
                return result
            end
            local ok,data=pcall(self.observe,false)
            if not ok or type(data)~='table' then
                result.state='failed'
                result.lines={'Observation failed; no action taken.'}
                addHistory({id=result.id,command=command,state='failed',summary='Observation failed'})
                return result
            end
            if data.state~='active' then
                result.state='rejected'
                result.lines={'Sarah is '..data.state..'; cannot follow.'}
                addHistory({id=result.id,command=command,state='rejected',summary='Sarah '..data.state})
                return result
            end
            if not data.npc or not isValidCoord(data.npc.x,data.npc.y,data.npc.z) then
                result.state='rejected'
                result.lines={'Sarah position unavailable.'}
                addHistory({id=result.id,command=command,state='rejected',summary='NPC position missing'})
                return result
            end
            if not data.player or not isValidCoord(data.player.x,data.player.y,data.player.z) then
                result.state='rejected'
                result.lines={'Player position unavailable.'}
                addHistory({id=result.id,command=command,state='rejected',summary='Player position missing'})
                return result
            end
            if isPlayerDead(data) then
                result.state='rejected'
                result.lines={'Player is dead; cannot follow.'}
                addHistory({id=result.id,command=command,state='rejected',summary='Player dead'})
                return result
            end
            if not isPlayerAlive(data) then
                result.state='rejected'
                result.lines={'Player liveness query failed; cannot follow.'}
                addHistory({id=result.id,command=command,state='rejected',summary='Player liveness unknown'})
                return result
            end
            local nx,ny,nz=data.npc.x,data.npc.y,math.floor(data.npc.z)
            local px,py,pz=data.player.x,data.player.y,math.floor(data.player.z)
            if nz~=pz then
                result.state='rejected'
                result.lines={'Player is on a different floor.'}
                addHistory({id=result.id,command=command,state='rejected',summary='Different floor'})
                return result
            end
            local dx=px-nx
            local dy=py-ny
            local distSq=dx*dx+dy*dy
            if distSq>64 then
                result.state='rejected'
                result.lines={'Player is too far (maximum 8 tiles).'}
                addHistory({id=result.id,command=command,state='rejected',summary='Too far (>8 tiles)'})
                return result
            end
            self.token=self.token+1
            local owner,npcOwner=self:getIdentity()
            local action={
                id=result.id,
                session=self.session,
                command='follow',
                state='running',
                token=self.token,
                owner=owner,
                controller=owner,
                npc=npcOwner,
                stepGen=0,
                stepState='idle',
                stepTicks=0,
                stallTicks=0,
                lastProgressX=nx,
                lastProgressY=ny,
                maxStepTicks=600,
                maxStallTicks=600,
                minRetargetTicks=6,
                cooldown=0,
                summary=(distSq<=4.0) and 'Following player (in range)' or 'Following player'
            }
            self.active=action
            addHistory({id=action.id,command=command,state='running',summary=action.summary})

            if distSq<=4.0 then
                result.state='running'
                result.lines={'Following player (already within 2 tiles).'}
                return result
            end

            local stepOk,stepErr=self:dispatchFollowStep(data,nx,ny,nz,px,py,pz)
            if not stepOk then
                result.state='failed'
                result.lines={stepErr or 'No valid target near player to start follow.'}
                return result
            end
            if not self.active then
                result.state='failed'
                result.lines={action.reason or 'Follow step failed immediately.'}
                return result
            end
            result.state='running'
            local targetDesc
            if action.currentTarget then
                targetDesc=string.format('walking to (%d, %d, %d)',action.currentTarget.x,action.currentTarget.y,action.currentTarget.z)
            elseif action.lastTarget then
                targetDesc=string.format('reached (%d, %d, %d)',action.lastTarget.x,action.lastTarget.y,action.lastTarget.z)
            else
                targetDesc='following'
            end
            result.lines={'Following player; '..targetDesc..'.'}
            return result
        end
        if command=='history' then
            result.state='completed'
            if #self.history==0 then
                result.lines={'No command history.'}
            else
                result.lines={'Recent commands ('..#self.history..'):'}
                local start=math.max(1,#self.history-9)
                for i=start,#self.history do
                    local h=self.history[i]
                    local line=string.format('#%d %s: %s',h.id,h.command,h.state)
                    if h.summary and h.summary~='' then line=line..' ('..h.summary..')' end
                    result.lines[#result.lines+1]=line:sub(1,90)
                end
            end
            addHistory({id=result.id,command=command,state=result.state,summary='History displayed'})
            return result
        end
        if command=='stop' then
            local priorStopFailed=self.stopFailed
            if self.active then
                local cancelledId=self.active.id
                local cancelledCmd=self.active.command
                local ok,actionCopy,stopOk,stopErr=self:cancelActive('stopped by user',true)
                if not stopOk then
                    self.stopFailed=stopErr or 'stop failed'
                    result.state='failed'
                    result.lines={'Cancelled #'..cancelledId..' ('..cancelledCmd..').','Engine stop failed: '..stopErr..'.'}
                    addHistory({id=result.id,command=command,state='failed',summary='Stop failed: '..stopErr})
                    return result
                end
                self.stopFailed=nil
                result.state='completed'
                local lines={'Cancelled #'..cancelledId..' ('..cancelledCmd..').'}
                if priorStopFailed then
                    lines[#lines+1]='Prior engine stop failure cleared; movement recovered.'
                end
                lines[#lines+1]='Sarah stopped.'
                result.lines=lines
                addHistory({id=result.id,command=command,state='completed',summary='Cancelled #'..cancelledId})
                return result
            end
            local ok,data=pcall(self.observe,false)
            if not ok or type(data)~='table' then
                local stopOk,stopErr=self:invokeStop('stop_no_active')
                if not stopOk then
                    self.stopFailed=stopErr or 'stop failed'
                    result.state='failed'
                    result.lines={'Engine stop failed: '..stopErr..'.'}
                    addHistory({id=result.id,command=command,state='failed',summary='Stop failed: '..stopErr})
                    return result
                end
                self.stopFailed=nil
                result.state='completed'
                local lines={}
                if priorStopFailed then
                    lines[#lines+1]='Prior engine stop failure cleared; movement recovered.'
                end
                lines[#lines+1]='Sarah stopped; nothing active.'
                result.lines=lines
                addHistory({id=result.id,command=command,state='completed',summary='Nothing active'})
                return result
            end
            if data.state=='dead' then
                result.state='completed'
                result.lines={'Sarah is dead; nothing active to stop.'}
                addHistory({id=result.id,command=command,state='completed',summary='Sarah dead'})
                return result
            end
            if data.state=='unloaded' or data.state=='absent' or data.state=='deferred' then
                result.state='completed'
                result.lines={'Sarah is '..data.state..'; nothing active to stop.'}
                addHistory({id=result.id,command=command,state='completed',summary='Sarah '..data.state})
                return result
            end
            local stopOk,stopErr=self:invokeStop('stop_no_active')
            if not stopOk then
                self.stopFailed=stopErr or 'stop failed'
                result.state='failed'
                result.lines={'Engine stop failed: '..stopErr..'.'}
                addHistory({id=result.id,command=command,state='failed',summary='Stop failed: '..stopErr})
                return result
            end
            self.stopFailed=nil
            result.state='completed'
            local lines={}
            if priorStopFailed then
                lines[#lines+1]='Prior engine stop failure cleared; movement recovered.'
            end
            lines[#lines+1]='Sarah stopped; nothing active.'
            result.lines=lines
            addHistory({id=result.id,command=command,state='completed',summary='Nothing active'})
            return result
        end
        if command=='look' or command=='perceive' then
            local ok,data=pcall(self.observe,false)
            if not ok or type(data)~='table' then
                result.state='failed'
                result.lines={'Observation failed; no action taken.'}
                addHistory({id=result.id,command=command,state='failed',summary='Observation failed'})
                return result
            end
            if data.state~='active' then
                if data.state=='dead' or data.state=='unloaded' or data.state=='absent' then
                    self:resetKnowledge()
                    self:resetPerception()
                end
                result.state='rejected'
                result.lines={'Sarah is '..tostring(data.state or 'unavailable')..'; cannot perceive.'}
                addHistory({id=result.id,command=command,state='rejected',summary='Sarah '..tostring(data.state or 'unavailable')})
                return result
            end
            if not self.perceiveCallback then
                result.state='failed'
                result.lines={'Perception sampler unavailable.'}
                addHistory({id=result.id,command=command,state='failed',summary='Sampler unavailable'})
                return result
            end

            local sampOk,sampleRes,sampErr=pcall(self.perceiveCallback)
            if not sampOk then
                result.state='failed'
                result.lines={'Perception sampling failed: '..tostring(sampleRes)..'.'}
                addHistory({id=result.id,command=command,state='failed',summary='Sampling error'})
                return result
            end
            if not sampleRes then
                result.state='failed'
                result.lines={'Perception sampling failed: '..tostring(sampErr or 'sampler returned nil')..'.'}
                addHistory({id=result.id,command=command,state='failed',summary='Sampling failed'})
                return result
            end
            if sampleRes.status=='reentrancy_rejected' then
                result.state='failed'
                result.lines={'Perception rejected: sampler is reentrant.'}
                addHistory({id=result.id,command=command,state='failed',summary='Reentrancy rejected'})
                return result
            end
            if sampleRes.status=='aborted' then
                result.state='failed'
                local abReason=sampleRes.reason or 'aborted'
                result.lines={'Perception aborted: '..tostring(abReason)..'.'}
                addHistory({id=result.id,command=command,state='failed',summary='Aborted: '..tostring(abReason)})
                return result
            end

            local now,timeErr=self:getNow()
            if not now then
                result.state='failed'
                result.lines={'Perception failed: time source unavailable ('..tostring(timeErr or 'unspecified')..').'}
                addHistory({id=result.id,command=command,state='failed',summary='Time unavailable: '..tostring(timeErr or 'unspecified')})
                return result
            end

            local k=self:getKnowledge()
            if k and k.update then
                pcall(k.update,k,sampleRes,now)
            end

            local rawResults=sampleRes.results or {}
            local geomVisible=0
            local geomBlocked=0
            local geomUnknown=0
            local visConfirmed=0

            for _,r in ipairs(rawResults) do
                if r.geometric=='visible' then geomVisible=geomVisible+1
                elseif r.geometric=='blocked' then geomBlocked=geomBlocked+1
                else geomUnknown=geomUnknown+1 end

                if r.visual=='visible' then visConfirmed=visConfirmed+1 end
            end

            local lines={}
            local numCands=sampleRes.counts and sampleRes.counts.candidates or #rawResults
            local numProc=sampleRes.counts and sampleRes.counts.processed or #rawResults
            lines[#lines+1]=string.format('Perception: %s (candidates: %d, processed: %d)',
                tostring(sampleRes.status or 'sampled'),numCands,numProc)
            lines[#lines+1]=string.format('Geometry: %d visible, %d blocked, %d unknown',
                geomVisible,geomBlocked,geomUnknown)
            lines[#lines+1]=string.format('Visual: %d confirmed (lighting: %s; unknown lighting never implies sight)',
                visConfirmed,tostring(sampleRes.lighting or 'unknown'))

            if k and k.snapshot then
                local snapOk,snap=pcall(k.snapshot,k,now)
                if snapOk and type(snap)=='table' then
                    if #snap==0 then
                        lines[#lines+1]='Memory: 0 confirmed records'
                    else
                        lines[#lines+1]=string.format('Memory (%d records):',#snap)
                        for i=1,math.min(#snap,10) do
                            local rec=snap[i]
                            local age=math.max(0,math.floor((now-(rec.observedAt or now))*10)/10)
                            local px=rec.position and rec.position.x or 0
                            local py=rec.position and rec.position.y or 0
                            local pz=rec.position and rec.position.z or 0
                            lines[#lines+1]=string.format('  [%s] %s at (%.1f, %.1f, %.0f), age %.1fs',
                                tostring(rec.id),tostring(rec.kind),px,py,pz,age)
                        end
                        if #snap>10 then
                            lines[#lines+1]=string.format('  ... and %d more records',#snap-10)
                        end
                    end
                end
            end

            result.state='completed'
            result.lines=lines
            addHistory({
                id=result.id,
                command=command,
                state='completed',
                summary=string.format('Sampled %d candidates (%d geom visible, %d vis confirmed)',numCands,geomVisible,visConfirmed)
            })
            return result
        end
        local ok,data=pcall(self.observe,command=='inventory')
        if not ok or type(data)~='table' then
            result.state='failed'; result.lines={'Observation failed; no action taken.'}
            addHistory({id=result.id,command=command,state='failed',summary=result.lines[1]})
            return result
        end
        if self.active then
            self:checkLifecycle()
        elseif data.state=='dead' or data.state=='unloaded' or data.state=='absent' then
            self:resetKnowledge()
            self:resetPerception()
        end
        result.state='completed'
        if command=='status' then
            result.lines={'Sarah: '..data.state}
            if self.active then
                result.lines[#result.lines+1]='Action: #'..self.active.id..' '..self.active.command..' (running)'
                if self.active.command=='follow' then
                    if self.active.stepState=='walking' then
                        if self.active.currentTarget then
                            result.lines[#result.lines+1]=string.format('Follow: following while walking to (%d, %d, %d)',self.active.currentTarget.x,self.active.currentTarget.y,self.active.currentTarget.z)
                        else
                            result.lines[#result.lines+1]='Follow: following while walking'
                        end
                    else
                        local inDeadzone=false
                        if data.npc and isValidCoord(data.npc.x,data.npc.y,data.npc.z) and
                           data.player and isValidCoord(data.player.x,data.player.y,data.player.z) then
                            local nz=math.floor(data.npc.z)
                            local pz=math.floor(data.player.z)
                            if nz==pz then
                                local dx=data.player.x-data.npc.x
                                local dy=data.player.y-data.npc.y
                                if dx*dx+dy*dy<=4.0 then
                                    inDeadzone=true
                                end
                            end
                        end
                        if inDeadzone then
                            result.lines[#result.lines+1]='Follow: follow engaged but waiting within range'
                        else
                            result.lines[#result.lines+1]='Follow: follow engaged but waiting before next walk'
                        end
                    end
                end
            elseif self.lastAction then
                result.lines[#result.lines+1]='Action: idle (last: #'..self.lastAction.id..' '..self.lastAction.state..')'
                if self.lastAction.command=='follow' and self.lastAction.state=='cancelled' then
                    result.lines[#result.lines+1]='Follow: disengaged ('..(self.lastAction.reason or 'disengaged')..')'
                end
            else
                result.lines[#result.lines+1]='Action: idle'
            end
            if self.stopFailed then
                result.lines[#result.lines+1]='Warning: engine stop failed ('..tostring(self.stopFailed)..'); movement blocked pending recovery.'
            end
            if data.reason then result.lines[#result.lines+1]=data.reason end
            for _,name in ipairs({'player','npc'}) do
                local p=data[name]
                if p then result.lines[#result.lines+1]=string.format('%s: %.2f, %.2f, %.0f',name,p.x,p.y,p.z) end
            end
            addHistory({id=result.id,command=command,state=result.state,summary='Sarah '..data.state})
        elseif not data.inventory then
            result.lines={'Inventory unavailable: '..data.state}
            addHistory({id=result.id,command=command,state=result.state,summary='Inventory unavailable'})
        else
            result.lines={'Inventory ('..data.inventory.total..' items):'}
            for _,item in ipairs(data.inventory.items) do result.lines[#result.lines+1]=item.type..' x'..item.count end
            if data.inventory.truncated then result.lines[#result.lines+1]='Summary truncated (200 items / 20 types).' end
            addHistory({id=result.id,command=command,state=result.state,summary=data.inventory.total..' items'})
        end
        return result
    end
    return self
end
return Commands
