-- Command parser, validation, dispatch and action boundary.
-- No mutable engine handles are exposed to callers.
local Commands={}
function Commands.new(observe,stopCallback,identityProvider,walkCallback)
    local self={
        sequence=0,
        session=1,
        active=nil,
        token=0,
        history={},
        maxHistory=30,
        lastAction=nil,
        observe=observe or function() return {state='unavailable'} end,
        stopCallback=stopCallback,
        identityProvider=identityProvider,
        walkCallback=walkCallback
    }
    function self:getIdentity()
        if type(self.identityProvider)=='function' then
            local ok,id=pcall(self.identityProvider)
            if ok then return id end
            return nil
        end
        return self.identityProvider
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
    function self:invokeWalk(target,onComplete,onFail,action)
        if not self.walkCallback then return false,'walk callback unavailable' end
        local ok,ret,err=pcall(self.walkCallback,target,onComplete,onFail,action)
        if not ok then
            local clean=tostring(ret):match(':%d+: (.*)') or tostring(ret)
            return false,clean:sub(1,60)
        end
        if ret==false then
            local clean=tostring(err or 'walk failed')
            return false,clean:sub(1,60)
        end
        return true,ret
    end
    function self:cancelActive(reason)
        if not self.active then return false,'nothing active' end
        local action=self.active
        self.active=nil
        action.state='cancelled'
        action.summary=reason or 'cancelled'
        self.lastAction={id=action.id,command=action.command,state='cancelled',reason=action.summary}
        self:updateHistory(action.id,'cancelled',action.summary)
        local stopOk,stopErr=self:invokeStop(reason or 'cancelled',{
            id=action.id,
            command=action.command,
            state=action.state,
            owner=action.owner,
            controller=action.owner,
            session=action.session
        })
        return true,{id=action.id,command=action.command,state=action.state,summary=action.summary},stopOk,stopErr
    end
    function self:checkLifecycle()
        if not self.active then return true end
        local ok,data=pcall(self.observe,false)
        if not ok or type(data)~='table' then
            local errReason='observation error'
            self:cancelActive(errReason)
            return false,errReason
        end
        if data.state~='active' then
            self:cancelActive(data.state)
            return false,data.state
        end
        local currentOwner=self:getIdentity()
        if self.active.owner and currentOwner and self.active.owner~=currentOwner then
            self:cancelActive('controller replaced')
            return false,'controller replaced'
        end
        return true,data
    end
    function self:tick()
        local valid,reason=self:checkLifecycle()
        if not valid then return false,reason end
        if self.active and self.active.command=='walk here' then
            local act=self.active
            act.ticks=(act.ticks or 0)+1
            local maxTicks=act.maxTicks or 600
            if act.ticks>=maxTicks then
                self:cancelActive('timeout')
                return false,'timeout'
            end
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
        local owner=self:getIdentity()
        local action={
            id=self.sequence,
            session=self.session,
            command=name,
            state='running',
            token=self.token,
            owner=owner,
            controller=owner,
            maxTicks=detailsCopy.maxTicks or 600,
            ticks=0,
            details=detailsCopy
        }
        self.active=action
        addHistory({id=action.id,command=action.command,state='running',summary='Started '..name})
        return true,{id=action.id,command=action.command,state=action.state,token=action.token}
    end
    function self:completeAction(id,token,success,message,owner)
        if not self.active or self.active.id~=id or self.active.token~=token then
            return false,'stale or cancelled'
        end
        if owner and self.active.owner and owner~=self.active.owner then
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
        return true,action.state
    end
    function self:reset()
        if self.active then self:cancelActive('session reset') end
        self.active=nil
        self.lastAction=nil
        self.token=0
        self.session=self.session+1
        self.history={}
    end
    function self:requestWalk(target)
        return self:execute('walk here',target)
    end
    function self:execute(input,target)
        self.sequence=self.sequence+1
        local result={id=self.sequence,state='rejected',lines={}}
        if type(input)~='string' or #input>128 or input:find('[%c]') then
            result.lines={'Use one command, at most 128 characters.'}
            addHistory({id=result.id,command=tostring(input):sub(1,32),state=result.state,summary=result.lines[1]})
            return result
        end
        local command=input:match('^%s*(.-)%s*$'):lower():gsub('%s+',' ')
        if command~='help' and command~='status' and command~='inventory' and command~='stop' and command~='history' and command~='walk here' then
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
                'stop - cancel active action or request',
                'history - list recent command outcomes',
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
            if not data.npc then
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
            if type(tx)~='number' or type(ty)~='number' or type(tz)~='number' or
               tx~=tx or ty~=ty or tz~=tz or
               tx==math.huge or tx==-math.huge or
               ty==math.huge or ty==-math.huge or
               tz==math.huge or tz==-math.huge then
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
            local owner=self:getIdentity()
            local resolvedTarget={x=tx,y=ty,z=tz}
            local action={
                id=result.id,
                session=self.session,
                command='walk here',
                state='running',
                token=self.token,
                owner=owner,
                controller=owner,
                maxTicks=600,
                ticks=0,
                details={targetX=tx,targetY=ty,targetZ=tz}
            }
            self.active=action
            local actId=action.id
            local actToken=action.token
            local function onComplete()
                local obsOk,obsData=pcall(self.observe,false)
                if not obsOk or type(obsData)~='table' or obsData.state~='active' or not obsData.npc then
                    self:completeAction(actId,actToken,false,'Sarah unavailable on arrival')
                    return
                end
                local nx,ny,nz=math.floor(obsData.npc.x),math.floor(obsData.npc.y),math.floor(obsData.npc.z)
                if nx==tx and ny==ty and nz==tz then
                    self:completeAction(actId,actToken,true,string.format('Reached target (%d, %d, %d).',tx,ty,tz))
                else
                    self:completeAction(actId,actToken,false,string.format('Stopped before target at (%d, %d, %d).',nx,ny,nz))
                end
            end
            local function onFail(actionObj,reason)
                self:completeAction(actId,actToken,false,reason or 'Walk failed')
            end
            local walkOk,walkErr=self:invokeWalk(resolvedTarget,onComplete,onFail,action)
            if not walkOk then
                self.active=nil
                result.state='failed'
                result.lines={'Walk failed to start: '..tostring(walkErr)..'.'}
                addHistory({id=result.id,command=command,state='failed',summary='Start failed: '..tostring(walkErr)})
                return result
            end
            result.state='running'
            result.lines={string.format('Walking to (%d, %d, %d).',tx,ty,tz)}
            addHistory({id=result.id,command=command,state='running',summary=string.format('Walking to (%d, %d, %d)',tx,ty,tz)})
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
            if self.active then
                local cancelledId=self.active.id
                local cancelledCmd=self.active.command
                local ok,actionCopy,stopOk,stopErr=self:cancelActive('stopped by user')
                if not stopOk then
                    result.state='failed'
                    result.lines={'Cancelled #'..cancelledId..' ('..cancelledCmd..').','Engine stop failed: '..stopErr..'.'}
                    addHistory({id=result.id,command=command,state='failed',summary='Stop failed: '..stopErr})
                    return result
                end
                result.state='completed'
                result.lines={'Cancelled #'..cancelledId..' ('..cancelledCmd..').','Sarah stopped.'}
                addHistory({id=result.id,command=command,state='completed',summary='Cancelled #'..cancelledId})
                return result
            end
            local ok,data=pcall(self.observe,false)
            if not ok or type(data)~='table' then
                local stopOk,stopErr=self:invokeStop('stop_no_active')
                if not stopOk then
                    result.state='failed'
                    result.lines={'Engine stop failed: '..stopErr..'.'}
                    addHistory({id=result.id,command=command,state='failed',summary='Stop failed: '..stopErr})
                    return result
                end
                result.state='completed'
                result.lines={'Sarah stopped; nothing active.'}
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
                result.state='failed'
                result.lines={'Engine stop failed: '..stopErr..'.'}
                addHistory({id=result.id,command=command,state='failed',summary='Stop failed: '..stopErr})
                return result
            end
            result.state='completed'
            result.lines={'Sarah stopped; nothing active.'}
            addHistory({id=result.id,command=command,state='completed',summary='Nothing active'})
            return result
        end
        local ok,data=pcall(self.observe,command=='inventory')
        if not ok or type(data)~='table' then
            result.state='failed'; result.lines={'Observation failed; no action taken.'}
            addHistory({id=result.id,command=command,state='failed',summary=result.lines[1]})
            return result
        end
        if self.active then
            if data.state~='active' then
                self:cancelActive(data.state)
            else
                local currentOwner=self:getIdentity()
                if self.active.owner and currentOwner and self.active.owner~=currentOwner then
                    self:cancelActive('controller replaced')
                end
            end
        end
        result.state='completed'
        if command=='status' then
            result.lines={'Sarah: '..data.state}
            if self.active then
                result.lines[#result.lines+1]='Action: #'..self.active.id..' '..self.active.command..' (running)'
            elseif self.lastAction then
                result.lines[#result.lines+1]='Action: idle (last: #'..self.lastAction.id..' '..self.lastAction.state..')'
            else
                result.lines[#result.lines+1]='Action: idle'
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
