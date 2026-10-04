local Engine = {}
local function log(message) print("[SarahFoundation] " .. tostring(message)) end
function Engine.new()
    local root = Core.getMyDocumentFolder():gsub("\\", "/"):gsub("/$", "")
    if root ~= "G:/Codex/Project Sarah/runtime/isolated" then error("experimental foundation requires isolated profile") end
    local adapter = {meta=ModData.getOrCreate("SarahFoundationV1"), log=log}
    local function file(slot)
        if slot ~= "a" and slot ~= "b" then error("invalid checkpoint slot") end
        return root .. "/Saves/" .. getWorld():getGameMode() .. "/" .. getWorld():getWorld() .. "/SarahFoundation-" .. slot .. ".bin"
    end
    function adapter.exists(slot) return fileExists(file(slot)) end
    function adapter.isDead(npc) return npc:isDead() end
    function adapter.listNPCs()
        local result, seen = {}, {}
        for _, list in ipairs({getCell():getObjectList(), getCell():getAddList()}) do
            for i=0,list:size()-1 do
                local object = list:get(i)
                if instanceof(object,"IsoPlayer") and object:getModData().SarahFoundationId == "Sarah" and not seen[object] then
                    seen[object]=true; result[#result+1]=object
                end
            end
        end
        return result
    end
    function adapter.stop(npc) ISTimedActionQueue.clear(npc); npc:getPathFindBehavior2():cancel(); npc:setPath2(nil) end
    function adapter.remove(npc) npc:removeFromWorld(); npc:removeFromSquare() end
    local function construct(square, record)
        if not square or not square:isFree(false) then error("spawn square unavailable") end
        local previous, npc = IsoPlayer.getInstance(), nil
        local ok, err = pcall(function()
            local desc=SurvivorFactory.CreateSurvivor(SurvivorFactory.SurvivorType.Neutral,true)
            desc:setForename("Sarah"); desc:setSurname("M0")
            npc=IsoPlayer.new(getCell(),desc,square:getX(),square:getY(),square:getZ())
            npc:getModData().SarahFoundationId="Sarah"
            npc:setNpc(true); npc:setSceneCulled(false)
            if record then
                npc:load(file(record.slot))
                if npc:isDead() or npc:getModData().SarahFoundationId ~= "Sarah" then error("invalid restored identity or dead checkpoint") end
            else
                npc:getModData().SarahFoundationId="Sarah"
                local inv=npc:getInventory()
                for _, type in ipairs({"Base.Tshirt_WhiteTINT", "Base.Trousers_DefaultTEXTURE_TINT", "Base.Shoes_TrainerTINT"}) do
                    local item=inv:AddItem(type)
                    if not item then error("clothing item unavailable: " .. type) end
                    npc:setWornItem(item:getBodyLocation(),item)
                end
                inv:AddItem("Base.Bandage")
            end
            npc:setNpc(true); npc:setSceneCulled(false); npc:resetModel()
        end)
        IsoPlayer.setInstance(previous)
        if not ok then
            if npc then
                local cleaned, cleanupError=pcall(adapter.remove,npc)
                if not cleaned then error("construction failed and cleanup failed: " .. tostring(cleanupError)) end
            end
            error(err)
        end
        log("ACTIVE npc=" .. tostring(npc:isNpc()) .. " worn=" .. npc:getWornItems():size() .. " localPlayerPreserved=" .. tostring(IsoPlayer.getInstance()==previous))
        return npc
    end
    function adapter.create()
        local player=getSpecificPlayer(0)
        for _, offset in ipairs({{2,0},{-2,0},{0,2},{0,-2}}) do
            local square=getCell():getGridSquare(math.floor(player:getX())+offset[1],math.floor(player:getY())+offset[2],math.floor(player:getZ()))
            if square and square:isFree(false) then return construct(square) end
        end
        error("no free nearby spawn square")
    end
    function adapter.restore(record)
        if type(record.x)~="number" or type(record.y)~="number" or type(record.z)~="number" then error("invalid saved coordinates") end
        local square=getCell():getGridSquare(math.floor(record.x),math.floor(record.y),math.floor(record.z))
        return construct(square,record)
    end
    function adapter.canRestore(record)
        if type(record.x)~="number" or type(record.y)~="number" or type(record.z)~="number" then return true end
        local square=getCell():getGridSquare(math.floor(record.x),math.floor(record.y),math.floor(record.z))
        return square ~= nil and square:isFree(false)
    end
    function adapter.snapshot(npc) return {x=npc:getX(),y=npc:getY(),z=npc:getZ()} end
    function adapter.save(npc,slot) npc:save(file(slot)) end
    return adapter
end
return Engine
