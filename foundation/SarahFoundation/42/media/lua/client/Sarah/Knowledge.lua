-- Session-local confirmed observations only; no engine references or persistence.
local Knowledge={}
local function finite(n)
    return type(n)=="number" and n==n and n~=math.huge and n~=-math.huge
end
local function copy(r)
    return {id=r.id,kind=r.kind,position={x=r.position.x,y=r.position.y,z=r.position.z},observedAt=r.observedAt}
end
function Knowledge.new()
    local records,sequence,lastTime={},0,nil
    local self={}
    function self:reset()
        records={}; sequence=0; lastTime=nil
    end
    function self:advance(now)
        assert(finite(now) and now>=0,"time must be nonnegative seconds")
        if lastTime and now<lastTime then self:reset() end
        lastTime=now
        for id,r in pairs(records) do
            if now-r.observedAt>=10 then records[id]=nil end
        end
    end
    function self:update(sample,now)
        self:advance(now)
        assert(type(sample)=="table" and type(sample.results)=="table","invalid sample")
        for i=1,math.min(#sample.results,32) do
            local r=sample.results[i]
            local p=type(r)=="table" and r.position
            if type(r)=="table" and r.visual=="visible" and r.geometric=="visible"
                and type(r.id)=="string" and #r.id>0 and #r.id<=96
                and (r.kind=="player" or r.kind=="zombie") and type(p)=="table"
                and finite(p.x) and finite(p.y) and finite(p.z) then
                sequence=sequence+1
                records[r.id]={id=r.id,kind=r.kind,position={x=p.x,y=p.y,z=p.z},observedAt=now,sequence=sequence}
            end
        end
        local count=0
        for _ in pairs(records) do count=count+1 end
        while count>32 do
            local oldest
            for _,r in pairs(records) do
                if not oldest or r.observedAt<oldest.observedAt or
                    (r.observedAt==oldest.observedAt and r.sequence<oldest.sequence) then oldest=r end
            end
            records[oldest.id]=nil; count=count-1
        end
    end
    function self:snapshot(now)
        self:advance(now)
        local out={}
        for _,r in pairs(records) do out[#out+1]=copy(r) end
        table.sort(out,function(a,b) return a.id<b.id end)
        return out
    end
    return self
end
return Knowledge
