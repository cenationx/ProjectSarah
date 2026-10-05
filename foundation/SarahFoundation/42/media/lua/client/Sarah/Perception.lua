-- Offline policy only. Query callbacks must be read-only and Sarah-relative.
local Perception = {}
local function finite(n)
    return type(n)=="number" and n==n and n~=math.huge and n~=-math.huge
end
local function position(p)
    return type(p)=="table" and finite(p.x) and finite(p.y) and finite(p.z)
end
local function identity(c)
    return type(c)=="table" and type(c.id)=="string" and #c.id>0 and #c.id<=96
        and (c.kind=="player" or c.kind=="zombie")
end
function Perception.new(options)
    options=options or {}
    local range=options.range or 12
    local cone=options.coneDegrees or 90
    assert(finite(range) and range>0 and range<=64, "invalid range")
    assert(finite(cone) and cone>0 and cone<=360, "invalid cone")
    local limit=math.cos(math.rad(cone/2))
    local self={}
    function self:sample(observer,candidates,queries)
        assert(type(candidates)=="table", "candidates must be a dense array")
        queries=queries or {}
        local count=math.min(#candidates,32)
        local out={results={},processed=count,truncated=#candidates>32}
        local facing=type(observer)=="table" and observer.forward
        local valid=position(observer) and type(facing)=="table" and finite(facing.x) and finite(facing.y)
        local magnitude=valid and math.sqrt(facing.x*facing.x+facing.y*facing.y) or 0
        valid=valid and finite(magnitude) and magnitude>0
        local seen={}
        for i=1,count do
            local c=candidates[i]
            local r={geometric="unknown",visual="unknown",reason="invalid_snapshot"}
            if identity(c) then r.id=c.id; r.kind=c.kind end
            local function block(reason) r.geometric="blocked"; r.visual="blocked"; r.reason=reason end
            local function query(name)
                if type(queries[name])~="function" then return nil end
                local ok,value=pcall(queries[name],observer,c)
                if ok then return value end
            end
            if not valid then r.reason="invalid_observer"
            elseif not identity(c) or not position(c) then r.reason="invalid_candidate"
            elseif seen[c.id] then r.reason="duplicate_identity"
            else
                seen[c.id]=true
                local dx,dy=c.x-observer.x,c.y-observer.y
                local distance=math.sqrt(dx*dx+dy*dy)
                if not finite(distance) then r.reason="invalid_distance"
                elseif math.floor(c.z)~=math.floor(observer.z) then block("different_floor")
                elseif distance>range then block("out_of_range")
                elseif distance==0 then r.reason="coincident_position"
                elseif (dx/distance)*(facing.x/magnitude)+(dy/distance)*(facing.y/magnitude)<limit-1e-12 then block("outside_cone")
                elseif query("coverage")~=true then r.reason="coverage_unknown"
                else
                    -- Adapter normalizes native results to clear / blocked / unknown.
                    -- Native window/door enum names are deliberately not accepted here.
                    local obstruction=query("obstruction")
                    if obstruction=="blocked" then block("obstructed")
                    elseif obstruction~="clear" then r.reason="obstruction_unknown"
                    else
                        r.geometric="visible"
                        local light=query("lighting")
                        if light=="detectable" then
                            r.visual="visible"; r.reason="confirmed"
                            r.position={x=c.x,y=c.y,z=c.z}
                        elseif light=="undetectable" then r.visual="blocked"; r.reason="lighting_blocked"
                        else r.reason="lighting_unknown" end
                    end
                end
            end
            out.results[i]=r
        end
        return out
    end
    return self
end
return Perception
