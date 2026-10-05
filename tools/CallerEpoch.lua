-- tools/CallerEpoch.lua
-- Standalone inert caller lifecycle policy for Project Sarah.
-- Pure Lua 5.1 compatible. No engine imports, globals, or native bindings.

local CallerEpoch = {}

local MAX_EPOCH = 2147483647

local function is_valid_namespace(ns)
    return type(ns) == "string" and #ns >= 1 and #ns <= 32 and (ns:match("^[%w_%-]+$") ~= nil)
end

local function is_valid_token(t)
    return type(t) == "string" and #t >= 1 and #t <= 96
end

local function validate_state(state)
    if type(state) ~= "table" then return false end
    local f = rawget(state, "framework")
    local c = rawget(state, "controller")
    local n = rawget(state, "npc")
    local cl = rawget(state, "cell")
    local w = rawget(state, "worldRevision")
    if not is_valid_token(f) or not is_valid_token(c) or not is_valid_token(n) or
       not is_valid_token(cl) or not is_valid_token(w) then
        return false
    end
    return true, f, c, n, cl, w
end

function CallerEpoch.new(namespace)
    if not is_valid_namespace(namespace) then
        error("CallerEpoch.new: invalid namespace")
    end
    local ns = namespace

    local epoch = 1
    local active = false
    local exhausted = false

    local cur_f = nil
    local cur_c = nil
    local cur_n = nil
    local cur_cl = nil
    local cur_w = nil

    local inst = {}

    local function observe(self, state_arg)
        local state = state_arg
        if state == nil and type(self) == "table" and rawget(self, "observe") == nil then
            state = self
        end

        if exhausted then
            return {
                status = "exhausted",
                changed = false,
                epoch = MAX_EPOCH,
                generation = nil,
            }
        end

        local ok_state, f, c, n, cl, w = validate_state(state)

        if not ok_state then
            if active then
                active = false
                cur_f, cur_c, cur_n, cur_cl, cur_w = nil, nil, nil, nil, nil
                if epoch >= MAX_EPOCH then
                    exhausted = true
                    epoch = MAX_EPOCH
                    return {
                        status = "exhausted",
                        changed = true,
                        epoch = MAX_EPOCH,
                        generation = nil,
                    }
                else
                    epoch = epoch + 1
                    return {
                        status = "invalid",
                        changed = true,
                        epoch = epoch,
                        generation = nil,
                    }
                end
            else
                return {
                    status = "invalid",
                    changed = false,
                    epoch = epoch,
                    generation = nil,
                }
            end
        end

        if not active then
            active = true
            cur_f = f
            cur_c = c
            cur_n = n
            cur_cl = cl
            cur_w = w
            return {
                status = "ready",
                changed = true,
                epoch = epoch,
                generation = ns .. ":" .. epoch,
            }
        end

        if cur_f == f and cur_c == c and cur_n == n and cur_cl == cl and cur_w == w then
            return {
                status = "ready",
                changed = false,
                epoch = epoch,
                generation = ns .. ":" .. epoch,
            }
        end

        if epoch >= MAX_EPOCH then
            exhausted = true
            active = false
            cur_f, cur_c, cur_n, cur_cl, cur_w = nil, nil, nil, nil, nil
            epoch = MAX_EPOCH
            return {
                status = "exhausted",
                changed = true,
                epoch = MAX_EPOCH,
                generation = nil,
            }
        else
            epoch = epoch + 1
            cur_f = f
            cur_c = c
            cur_n = n
            cur_cl = cl
            cur_w = w
            return {
                status = "ready",
                changed = true,
                epoch = epoch,
                generation = ns .. ":" .. epoch,
            }
        end
    end

    local function reset(self)
        if exhausted then
            return {
                status = "exhausted",
                changed = false,
                epoch = MAX_EPOCH,
                generation = nil,
            }
        end

        active = false
        cur_f, cur_c, cur_n, cur_cl, cur_w = nil, nil, nil, nil, nil

        if epoch >= MAX_EPOCH then
            exhausted = true
            epoch = MAX_EPOCH
            return {
                status = "exhausted",
                changed = true,
                epoch = MAX_EPOCH,
                generation = nil,
            }
        else
            epoch = epoch + 1
            return {
                status = "reset",
                changed = true,
                epoch = epoch,
                generation = nil,
            }
        end
    end

    local function snapshot(self)
        return {
            epoch = epoch,
            active = active,
            exhausted = exhausted,
        }
    end

    inst.observe = observe
    inst.reset = reset
    inst.snapshot = snapshot

    return inst
end

return CallerEpoch
