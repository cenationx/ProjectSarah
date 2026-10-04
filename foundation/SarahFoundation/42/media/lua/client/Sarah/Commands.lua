-- Read-only command boundary. No engine objects are returned to callers.
local Commands={}
function Commands.new(observe)
    local self={sequence=0}
    function self:execute(input)
        self.sequence=self.sequence+1
        local result={id=self.sequence,state='rejected',lines={}}
        if type(input)~='string' or #input>128 or input:find('[%c]') then
            result.lines={'Use one command, at most 128 characters.'}; return result
        end
        local command=input:match('^%s*(.-)%s*$'):lower()
        if command~='help' and command~='status' and command~='inventory' then
            result.lines={'Unknown command. Try help.'}; return result
        end
        if command=='help' then
            result.state='completed'; result.lines={'help - list commands','status - inspect Sarah','inventory - list carried items','Read-only console. Movement commands come later.'}; return result
        end
        local ok,data=pcall(observe,command=='inventory')
        if not ok or type(data)~='table' then result.state='failed'; result.lines={'Observation failed; no action taken.'}; return result end
        result.state='completed'
        if command=='status' then
            result.lines={'Sarah: '..data.state,'Action: not tracked in this read-only slice'}
            if data.reason then result.lines[#result.lines+1]=data.reason end
            for _,name in ipairs({'player','npc'}) do
                local p=data[name]
                if p then result.lines[#result.lines+1]=string.format('%s: %.2f, %.2f, %.0f',name,p.x,p.y,p.z) end
            end
        elseif not data.inventory then
            result.lines={'Inventory unavailable: '..data.state}
        else
            result.lines={'Inventory ('..data.inventory.total..' items):'}
            for _,item in ipairs(data.inventory.items) do result.lines[#result.lines+1]=item.type..' x'..item.count end
            if data.inventory.truncated then result.lines[#result.lines+1]='Summary truncated (200 items / 20 types).' end
        end
        return result
    end
    return self
end
return Commands
