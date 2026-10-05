-- Inert offline loaded-square coverage policy. No native calls or retained squares.
local Coverage = {}
local CHECK = {} -- private closure key; budgets live in each explicit sample context
local DEFAULT_CANDIDATE, DEFAULT_SAMPLE = 1024, 4096
local MAX_CANDIDATE, MAX_SAMPLE, MAX_COORD = 2048, 8192, 1000000
Coverage.DEFAULT_CANDIDATE_BUDGET = DEFAULT_CANDIDATE
Coverage.DEFAULT_SAMPLE_BUDGET = DEFAULT_SAMPLE
Coverage.HARD_MAX_CANDIDATE_BUDGET = MAX_CANDIDATE
Coverage.HARD_MAX_SAMPLE_BUDGET = MAX_SAMPLE
Coverage.HARD_MAX_COORD = MAX_COORD
Coverage.MAX_RANGE = 64
local function finite(n)
    return type(n)=="number" and n==n and n~=math.huge and n~=-math.huge
end
local function result(reason, reads, area)
    return {status=reason=="ok" and "covered" or "unknown", reason=reason,
        covered=reason=="ok", reads=reads or 0, area=area}
end
local function option(options,key,default,maximum,integer)
    local value=rawget(options,key)
    if value==nil then value=default end
    assert(finite(value) and value>0 and value<=maximum
        and (not integer or value==math.floor(value)), "invalid "..key)
    return value
end
local function position(p)
    if type(p)~="table" then return nil end
    local x,y,z=rawget(p,"x"),rawget(p,"y"),rawget(p,"z")
    if not finite(x) or not finite(y) or not finite(z)
        or math.abs(x)>MAX_COORD or math.abs(y)>MAX_COORD or math.abs(z)>MAX_COORD then return nil end
    return x,y,z
end
function Coverage.newContext(options)
    if options==nil then options={} end
    assert(type(options)=="table", "options must be a table")
    local sampleBudget=option(options,"sampleBudget",DEFAULT_SAMPLE,MAX_SAMPLE,true)
    local candidateBudget=option(options,"candidateBudget",DEFAULT_CANDIDATE,MAX_CANDIDATE,true)
    local range=option(options,"range",12,64,false)
    local remaining,total,success,failed=sampleBudget,0,0,0
    local checking=false
    local function check(observer,candidate,getSquare)
        if checking then return result("reentrant_check") end
        if type(getSquare)~="function" then return result("missing_getter") end
        if type(observer)~="table" then return result("invalid_observer") end
        if type(candidate)~="table" then return result("invalid_candidate") end
        local ox,oy,oz=position(observer)
        local cx,cy,cz=position(candidate)
        if ox==nil or cx==nil then return result("invalid_coordinates") end
        local z=math.floor(oz)
        if z~=math.floor(cz) then return result("different_floor") end
        local dx,dy=cx-ox,cy-oy
        if dx*dx+dy*dy>range*range then return result("out_of_range") end
        local fox,foy,fcx,fcy=math.floor(ox),math.floor(oy),math.floor(cx),math.floor(cy)
        local minX,maxX=math.min(fox,fcx)-1,math.max(fox,fcx)+1
        local minY,maxY=math.min(foy,fcy)-1,math.max(foy,fcy)+1
        local area=(maxX-minX+1)*(maxY-minY+1)
        if area>candidateBudget then return result("candidate_budget_exceeded",0,area) end
        if area>remaining then return result("sample_budget_exceeded",0,area) end
        local reads=0
        checking=true
        for x=minX,maxX do
            for y=minY,maxY do
                -- Exactly one lookup per unique coordinate in THIS candidate rectangle.
                -- Later candidates requery; no positive/negative cache survives a call.
                remaining=remaining-1; total=total+1; reads=reads+1
                local ok,square=pcall(getSquare,x,y,z)
                if not ok or square==nil or square==false then
                    failed=failed+1; checking=false
                    return result(ok and "missing_square" or "query_error",reads,area)
                end
                success=success+1
            end
        end
        checking=false
        return result("ok",reads,area)
    end
    local context={}
    context[CHECK]=check
    function context:check(observer,candidate,getSquare)
        return check(observer,candidate,getSquare)
    end
    function context:snapshot()
        return {sampleBudget=sampleBudget,candidateBudget=candidateBudget,range=range,
            sampleRemaining=remaining,totalReads=total,successfulReads=success,failedReads=failed}
    end
    return context
end
function Coverage.check(observer,candidate,getSquare,context,options)
    if options~=nil then return result("invalid_options") end
    local check=type(context)=="table" and rawget(context,CHECK)
    if type(check)~="function" then return result("invalid_context") end
    return check(observer,candidate,getSquare)
end
return Coverage
