-- Inert offline diagnostic-only light source snapshot prototype.
-- Project Sarah Build 42.21.0. No native engine wiring or callbacks.
local LightSourceSnapshot = {}

local DEFAULT_MAX_COLLECTION = 128
local HARD_MAX_COLLECTION = 256

local DEFAULT_MAX_READS = 1024
local HARD_MAX_READS = 4096

local DEFAULT_MAX_SQUARES = 128
local HARD_MAX_SQUARES = 256

local DEFAULT_MAX_CAPTURES = 32
local HARD_MAX_CAPTURES = 64

local DEFAULT_MAX_OUTPUT = 64
local HARD_MAX_OUTPUT = 128

local MAX_COORD = 1000000
local MIN_Z = -32
local MAX_Z = 31
local MAX_RADIUS = 64
local MAX_COLOR = 10.0

LightSourceSnapshot.DEFAULT_MAX_COLLECTION = DEFAULT_MAX_COLLECTION
LightSourceSnapshot.HARD_MAX_COLLECTION = HARD_MAX_COLLECTION
LightSourceSnapshot.DEFAULT_MAX_READS = DEFAULT_MAX_READS
LightSourceSnapshot.HARD_MAX_READS = HARD_MAX_READS
LightSourceSnapshot.DEFAULT_MAX_SQUARES = DEFAULT_MAX_SQUARES
LightSourceSnapshot.HARD_MAX_SQUARES = HARD_MAX_SQUARES
LightSourceSnapshot.DEFAULT_MAX_CAPTURES = DEFAULT_MAX_CAPTURES
LightSourceSnapshot.HARD_MAX_CAPTURES = HARD_MAX_CAPTURES
LightSourceSnapshot.DEFAULT_MAX_OUTPUT = DEFAULT_MAX_OUTPUT
LightSourceSnapshot.HARD_MAX_OUTPUT = HARD_MAX_OUTPUT

local function is_finite(n)
    return type(n) == "number" and n == n and n ~= 1/0 and n ~= -1/0
end

local function is_int(n)
    return is_finite(n) and math.floor(n) == n
end

local function is_str96(s)
    return type(s) == "string" and #s > 0 and #s <= 96
end

local function val_cap(c)
    if type(c) ~= "table" then return false end
    local fx, fy = rawget(c, "fx"), rawget(c, "fy")
    local x, y, z = rawget(c, "x"), rawget(c, "y"), rawget(c, "z")
    return is_str96(rawget(c, "controller")) and is_str96(rawget(c, "npc")) and
           is_str96(rawget(c, "cell")) and is_str96(rawget(c, "generation")) and
           rawget(c, "alive") == true and rawget(c, "resident") == true and rawget(c, "cancelled") == false and
           is_finite(x) and math.abs(x) <= MAX_COORD and
           is_finite(y) and math.abs(y) <= MAX_COORD and
           is_finite(z) and math.abs(z) <= MAX_COORD and
           is_finite(fx) and math.abs(fx) <= MAX_COORD and
           is_finite(fy) and math.abs(fy) <= MAX_COORD and
           (fx ~= 0 or fy ~= 0)
end

local function cp_cap(c)
    return {
        controller = rawget(c, "controller"),
        npc = rawget(c, "npc"),
        cell = rawget(c, "cell"),
        generation = rawget(c, "generation"),
        alive = true,
        resident = true,
        cancelled = false,
        x = rawget(c, "x") + 0.0,
        y = rawget(c, "y") + 0.0,
        z = rawget(c, "z") + 0.0,
        fx = rawget(c, "fx") + 0.0,
        fy = rawget(c, "fy") + 0.0,
    }
end

local function cap_eq(a, b)
    if not a or not b then return false end
    return a.controller == b.controller and a.npc == b.npc and a.cell == b.cell and a.generation == b.generation and
           a.alive == b.alive and a.resident == b.resident and a.cancelled == b.cancelled and
           a.x == b.x and a.y == b.y and a.z == b.z and a.fx == b.fx and a.fy == b.fy
end

local function option(options, key, default, maximum, integer)
    if type(options) ~= "table" then return default end
    local value = rawget(options, key)
    if value == nil then value = default end
    assert(is_finite(value) and value > 0 and value <= maximum and
           (not integer or value == math.floor(value)), "invalid " .. key)
    return value
end

local function inspect_collection(coll)
    if coll == nil then return nil, nil, "nil_collection" end
    if type(coll) ~= "table" and type(coll) ~= "userdata" then
        return nil, nil, "invalid_collection_type"
    end
    local size_fn = nil
    pcall(function() size_fn = coll.size end)
    if type(size_fn) == "function" then
        local ok, sz = pcall(size_fn, coll)
        if ok and is_int(sz) and sz >= 0 then
            return math.floor(sz), true, nil
        end
        return nil, nil, "invalid_collection_size"
    end
    if type(coll) == "table" then
        local n = #coll
        if is_int(n) and n >= 0 then
            return n, false, nil
        end
        return nil, nil, "invalid_collection_size"
    end
    return nil, nil, "unsupported_collection"
end

local function get_collection_item(coll, idx_1based, is_java)
    if is_java then
        local ok, item = pcall(coll.get, coll, idx_1based - 1)
        if ok then return item, nil end
        return nil, "get_failed"
    else
        return coll[idx_1based], nil
    end
end

-- Property reader distinguishing unavailable, throwing, legitimate nil, and ok.
-- Never falls back to raw fields if authoritative getter is present and throws or returns nil.
-- Distinguishes member-lookup exceptions from unavailable getters.
local function invoke_getter(obj, getter_name)
    local fn = nil
    local get_ok = pcall(function() fn = obj[getter_name] end)
    if not get_ok then
        return nil, "throwing"
    end
    if type(fn) == "function" then
        local call_ok, val = pcall(fn, obj)
        if not call_ok then
            return nil, "throwing"
        end
        if val == nil then
            return nil, "legitimate_nil"
        end
        return val, "ok"
    elseif fn ~= nil then
        -- Member lookup returned a non-nil non-function value: malformed getter
        return nil, "throwing"
    end
    return nil, "unavailable"
end

local function read_field(obj, field_name)
    local val = nil
    local get_ok = pcall(function() val = obj[field_name] end)
    if not get_ok then
        return nil, "throwing"
    end
    if val == nil then
        return nil, "legitimate_nil"
    end
    return val, "ok"
end

local function read_property(obj, getter_name, field_name, charge_read)
    if type(obj) ~= "table" and type(obj) ~= "userdata" then
        return nil, "invalid_object"
    end

    if not charge_read("getter") then
        return nil, "budget_exhausted"
    end

    local g_val, g_status = invoke_getter(obj, getter_name)
    if g_status == "ok" then
        return g_val, "ok"
    elseif g_status == "legitimate_nil" then
        return nil, "legitimate_nil"
    elseif g_status == "throwing" then
        -- Getter threw or member lookup threw: MUST NOT silently succeed through raw-field fallback!
        return nil, "throwing"
    end

    -- Getter was truly unavailable (fn == nil and lookup succeeded); inspect raw field
    if not charge_read("getter") then
        return nil, "budget_exhausted"
    end
    local f_val, f_status = read_field(obj, field_name)
    if f_status == "ok" then
        return f_val, "ok"
    elseif f_status == "legitimate_nil" then
        return nil, "legitimate_nil"
    elseif f_status == "throwing" then
        return nil, "throwing"
    end

    return nil, "unavailable"
end

local function parse_source(src, charge_read)
    if type(src) ~= "table" and type(src) ~= "userdata" then return nil, "invalid_source_type" end

    local x, x_st = read_property(src, "getX", "x", charge_read)
    if x_st == "budget_exhausted" then return nil, "budget_exhausted" end
    if x_st ~= "ok" or not is_int(x) or math.abs(x) > MAX_COORD then return nil, "invalid_x" end

    local y, y_st = read_property(src, "getY", "y", charge_read)
    if y_st == "budget_exhausted" then return nil, "budget_exhausted" end
    if y_st ~= "ok" or not is_int(y) or math.abs(y) > MAX_COORD then return nil, "invalid_y" end

    local z, z_st = read_property(src, "getZ", "z", charge_read)
    if z_st == "budget_exhausted" then return nil, "budget_exhausted" end
    if z_st ~= "ok" or not is_int(z) or z < MIN_Z or z > MAX_Z then return nil, "invalid_z" end

    local r, r_st = read_property(src, "getR", "r", charge_read)
    if r_st == "budget_exhausted" then return nil, "budget_exhausted" end
    if r_st ~= "ok" or not is_finite(r) or r < 0.0 or r > MAX_COLOR then return nil, "invalid_r" end

    local g, g_st = read_property(src, "getG", "g", charge_read)
    if g_st == "budget_exhausted" then return nil, "budget_exhausted" end
    if g_st ~= "ok" or not is_finite(g) or g < 0.0 or g > MAX_COLOR then return nil, "invalid_g" end

    local b, b_st = read_property(src, "getB", "b", charge_read)
    if b_st == "budget_exhausted" then return nil, "budget_exhausted" end
    if b_st ~= "ok" or not is_finite(b) or b < 0.0 or b > MAX_COLOR then return nil, "invalid_b" end

    local radius, rad_st = read_property(src, "getRadius", "radius", charge_read)
    if rad_st == "budget_exhausted" then return nil, "budget_exhausted" end
    if rad_st ~= "ok" or not is_int(radius) or radius < 1 or radius > MAX_RADIUS then return nil, "invalid_radius" end

    local active, act_st = read_property(src, "isActive", "active", charge_read)
    if act_st == "budget_exhausted" then return nil, "budget_exhausted" end
    if act_st ~= "ok" or type(active) ~= "boolean" then return nil, "invalid_active" end

    local hydro, hyd_st = read_property(src, "isHydroPowered", "hydroPowered", charge_read)
    if hyd_st == "budget_exhausted" then return nil, "budget_exhausted" end
    if hyd_st ~= "ok" or type(hydro) ~= "boolean" then return nil, "invalid_hydroPowered" end

    local src_id, id_st = read_property(src, "getId", "id", charge_read)
    if id_st == "budget_exhausted" then return nil, "budget_exhausted" end

    -- Building restriction:
    -- Only a successful authoritative building getter returning nil establishes unrestricted.
    -- Missing/malformed building metadata must remain unknown.
    local building_restriction = "unknown"
    local building_id = nil

    if not charge_read("getter") then
        return nil, "budget_exhausted"
    end
    local building_ref, b_st = invoke_getter(src, "getLocalToBuilding")
    if b_st == "legitimate_nil" then
        building_restriction = "unrestricted"
        building_id = nil
    elseif b_st == "ok" and building_ref ~= nil then
        building_restriction = "restricted"
        local bid, bid_st = read_property(building_ref, "getId", "id", charge_read)
        if bid_st == "budget_exhausted" then
            return nil, "budget_exhausted"
        end
        if bid_st == "ok" and is_int(bid) then
            building_id = math.floor(bid)
        else
            local def_ref, def_st = read_property(building_ref, "getDef", "def", charge_read)
            if def_st == "budget_exhausted" then
                return nil, "budget_exhausted"
            end
            if def_st == "ok" and (type(def_ref) == "table" or type(def_ref) == "userdata") then
                local did, did_st = read_property(def_ref, "getId", "id", charge_read)
                if did_st == "budget_exhausted" then
                    return nil, "budget_exhausted"
                end
                if did_st == "ok" and is_int(did) then
                    building_id = math.floor(did)
                end
            end
        end
        if building_id == nil then
            building_restriction = "unknown"
        end
    else
        building_restriction = "unknown"
        building_id = nil
    end

    -- Switches inspection:
    -- Only a validated empty switch collection establishes zero switches.
    -- Missing/malformed switch metadata must remain unknown (nil).
    local switch_count = nil

    if not charge_read("getter") then
        return nil, "budget_exhausted"
    end
    local sw_ref, sw_st = invoke_getter(src, "getSwitches")
    if sw_st == "ok" and (type(sw_ref) == "table" or type(sw_ref) == "userdata") then
        -- Switch-size query charged against maxReads
        if not charge_read("getter") then
            return nil, "budget_exhausted"
        end
        local sz, _, sz_err = inspect_collection(sw_ref)
        if not sz_err and is_int(sz) and sz >= 0 then
            switch_count = math.floor(sz)
        else
            switch_count = nil
        end
    else
        switch_count = nil
    end

    return {
        x = math.floor(x),
        y = math.floor(y),
        z = math.floor(z),
        r = r + 0.0,
        g = g + 0.0,
        b = b + 0.0,
        radius = math.floor(radius),
        active = active,
        hydroPowered = hydro,
        buildingRestriction = building_restriction,
        buildingId = building_id,
        switchCount = switch_count,
        srcId = is_int(src_id) and math.floor(src_id) or nil,
    }, nil
end

-- Power semantics: haveElectricity checks generator supply; hasGridPower checks grid supply.
-- A false generator result must not prevent checking grid power.
-- Unsupported switch/source rules remain unknown.
local function check_square_power(sq, hydroPowered, active, switchCount, charge_read)
    if not hydroPowered then
        return "not_required", nil, nil, "unknown"
    end

    if not charge_read("power") then
        return "budget_exhausted"
    end
    local gen_power = nil
    local fn_gen = nil
    pcall(function() fn_gen = sq.haveElectricity end)
    if type(fn_gen) == "function" then
        local gok, gval = pcall(fn_gen, sq)
        if gok and type(gval) == "boolean" then
            gen_power = gval
        end
    end

    if not charge_read("power") then
        return "budget_exhausted"
    end
    local grid_power = nil
    local fn_grid = nil
    pcall(function() fn_grid = sq.hasGridPower end)
    if type(fn_grid) == "function" then
        local rok, rval = pcall(fn_grid, sq)
        if rok and type(rval) == "boolean" then
            grid_power = rval
        end
    end

    local power_status = "unknown"
    if grid_power == true or gen_power == true then
        power_status = "powered"
    elseif grid_power == false and gen_power == false then
        power_status = "unpowered"
    else
        power_status = "unknown"
    end

    -- If switches are present and switch circuits are unsupported, power status remains unknown
    if switchCount == nil or switchCount > 0 then
        power_status = "unknown"
    end

    -- Freshness: agreement or hydroPowered=false does NOT prove freshness.
    -- Positive discrepancy (power lost while active) is stale; otherwise unknown.
    local freshness = "unknown"
    if power_status == "unpowered" and active == true then
        freshness = "stale"
    else
        freshness = "unknown"
    end

    return power_status, gen_power, grid_power, freshness
end

function LightSourceSnapshot.new(options)
    local max_coll = option(options, "maxCollectionSize", DEFAULT_MAX_COLLECTION, HARD_MAX_COLLECTION, true)
    local max_reads = option(options, "maxReads", DEFAULT_MAX_READS, HARD_MAX_READS, true)
    local max_squares = option(options, "maxSquares", DEFAULT_MAX_SQUARES, HARD_MAX_SQUARES, true)
    local max_captures = option(options, "maxCaptures", DEFAULT_MAX_CAPTURES, HARD_MAX_CAPTURES, true)
    local max_output = option(options, "maxOutputSources", DEFAULT_MAX_OUTPUT, HARD_MAX_OUTPUT, true)

    local busy = false
    local revision = 1
    local pass_seq = 0

    local t_passes = 0
    local t_reads = 0
    local t_squares = 0
    local t_captures = 0
    local t_sources = 0

    local inst = {}

    local function reset(self)
        revision = revision + 1
        pass_seq = 0
    end

    local function state(self)
        return {
            revision = revision,
            total_passes = t_passes,
            total_reads = t_reads,
            total_squares = t_squares,
            total_captures = t_captures,
            total_sources = t_sources,
        }
    end

    local function snapshot(self_arg, api_arg)
        local api = api_arg
        if api == nil and type(self_arg) == "table" and rawget(self_arg, "snapshot") == nil then
            api = self_arg
        end

        local counts = {
            collection_size = 0,
            source_reads = 0,
            getter_reads = 0,
            square_lookups = 0,
            power_queries = 0,
            total_reads = 0,
            captures = 0,
            valid_sources = 0,
            unloaded_squares = 0,
            malformed_sources = 0,
            stale_sources = 0,
            unverified_power = 0,
        }

        if busy then
            return {
                status = "reentrancy_rejected",
                reason = "reentrant_call",
                incomplete = true,
                sources = {},
                counts = counts,
            }
        end

        if type(api) ~= "table" then
            return {
                status = "aborted",
                reason = "invalid_api",
                incomplete = true,
                sources = {},
                counts = counts,
            }
        end

        local get_cap = rawget(api, "capture")
        local get_sources = rawget(api, "getLightSources")
        local get_sq = rawget(api, "getSquare")

        if type(get_cap) ~= "function" or type(get_sources) ~= "function" or type(get_sq) ~= "function" then
            return {
                status = "aborted",
                reason = "invalid_api",
                incomplete = true,
                sources = {},
                counts = counts,
            }
        end

        -- Ensure unexpected exceptions ALWAYS release the reentrancy guard
        busy = true
        local p_rev = revision
        local run_ok, run_result = pcall(function()
            pass_seq = pass_seq + 1
            t_passes = t_passes + 1
            local this_pass_seq = pass_seq

            local function charge_read(kind)
                if counts.total_reads >= max_reads then
                    return false
                end
                if kind == "getter" then
                    counts.getter_reads = counts.getter_reads + 1
                elseif kind == "square" then
                    counts.square_lookups = counts.square_lookups + 1
                    t_squares = t_squares + 1
                elseif kind == "power" then
                    counts.power_queries = counts.power_queries + 1
                else
                    error("unknown read kind: " .. tostring(kind))
                end
                counts.total_reads = counts.getter_reads + counts.square_lookups + counts.power_queries
                t_reads = t_reads + 1
                return true
            end

            local function chk_cap()
                if counts.captures >= max_captures then return nil, "capture_limit_reached" end
                counts.captures = counts.captures + 1
                t_captures = t_captures + 1
                local ok, res = pcall(get_cap)
                if revision ~= p_rev then return nil, "reset_during_snapshot" end
                if not ok or not val_cap(res) then return nil, "lifecycle_invalid" end
                return cp_cap(res), nil
            end

            local init_cap, cap_err = chk_cap()
            if not init_cap then
                return {
                    status = "aborted",
                    reason = cap_err or "lifecycle_invalid",
                    incomplete = true,
                    sources = {},
                    counts = counts,
                }
            end

            local function chk_life()
                if revision ~= p_rev then return false, "reset_during_snapshot" end
                local c, e = chk_cap()
                if revision ~= p_rev then return false, "reset_during_snapshot" end
                if not c or e then return false, e or "lifecycle_invalid" end
                if not cap_eq(init_cap, c) then return false, "lifecycle_drift" end
                return true, nil
            end

            if not charge_read("getter") then
                return {
                    status = "budget_exhausted",
                    reason = "read_limit_reached",
                    incomplete = true,
                    sources = {},
                    counts = counts,
                }
            end
            local coll_ok, coll = pcall(get_sources)
            if not coll_ok then
                return {
                    status = "aborted",
                    reason = "get_sources_failed",
                    incomplete = true,
                    sources = {},
                    counts = counts,
                }
            end

            if not charge_read("getter") then
                return {
                    status = "budget_exhausted",
                    reason = "read_limit_reached",
                    incomplete = true,
                    sources = {},
                    counts = counts,
                }
            end
            local coll_size, is_java, coll_err = inspect_collection(coll)
            if coll_err then
                return {
                    status = "aborted",
                    reason = coll_err,
                    incomplete = true,
                    sources = {},
                    counts = counts,
                }
            end

            counts.collection_size = coll_size

            if coll_size > max_coll then
                return {
                    status = "collection_oversized",
                    reason = "collection_exceeds_budget",
                    incomplete = true,
                    sources = {},
                    counts = counts,
                }
            end

            -- Capture bounded exact reference snapshot of items to detect same-size replacement/reordering
            local initial_refs = {}
            for k = 1, coll_size do
                if not charge_read("getter") then
                    return {
                        status = "budget_exhausted",
                        reason = "read_limit_reached",
                        incomplete = true,
                        sources = {},
                        counts = counts,
                    }
                end
                local it, it_err = get_collection_item(coll, k, is_java)
                if it_err then
                    return {
                        status = "collection_mutated",
                        reason = "collection_changed_during_iteration",
                        incomplete = true,
                        sources = {},
                        counts = counts,
                    }
                end
                initial_refs[k] = it
            end

            local sources = {}
            local p_status = "completed"
            local p_reason = nil
            local incomplete = false

            for i = 1, coll_size do
                if i % 8 == 1 then
                    local lok, lerr = chk_life()
                    if not lok then
                        return {
                            status = "aborted",
                            reason = lerr,
                            incomplete = true,
                            sources = sources,
                            counts = counts,
                        }
                    end
                end

                -- Detect size change or reference replacement mid-read
                if not charge_read("getter") then
                    p_status, p_reason, incomplete = "budget_exhausted", "read_limit_reached", true
                    break
                end
                local cur_sz, _, mut_err = inspect_collection(coll)
                if mut_err or cur_sz ~= coll_size then
                    return {
                        status = "collection_mutated",
                        reason = "size_changed_during_iteration",
                        incomplete = true,
                        sources = {},
                        counts = counts,
                    }
                end

                if not charge_read("getter") then
                    p_status, p_reason, incomplete = "budget_exhausted", "read_limit_reached", true
                    break
                end
                local item, item_err = get_collection_item(coll, i, is_java)
                if item_err or item ~= initial_refs[i] then
                    return {
                        status = "collection_mutated",
                        reason = "collection_changed_during_iteration",
                        incomplete = true,
                        sources = {},
                        counts = counts,
                    }
                end

                counts.source_reads = counts.source_reads + 1

                if item == nil then
                    counts.malformed_sources = counts.malformed_sources + 1
                    incomplete = true
                else
                    local src_data, parse_err = parse_source(item, charge_read)
                    if parse_err == "budget_exhausted" then
                        p_status, p_reason, incomplete = "budget_exhausted", "read_limit_reached", true
                        break
                    elseif parse_err or not src_data then
                        counts.malformed_sources = counts.malformed_sources + 1
                        incomplete = true
                    else
                        if counts.square_lookups >= max_squares then
                            p_status, p_reason, incomplete = "budget_exhausted", "square_limit_reached", true
                            break
                        end

                        if not charge_read("square") then
                            p_status, p_reason, incomplete = "budget_exhausted", "read_limit_reached", true
                            break
                        end

                        local sq_ok, sq = pcall(get_sq, src_data.x, src_data.y, src_data.z)

                        local square_loaded = false
                        local power_status = "unloaded"
                        local gen_power = nil
                        local grid_power = nil
                        local freshness = "unknown"

                        if not sq_ok or sq == nil or sq == false then
                            counts.unloaded_squares = counts.unloaded_squares + 1
                            incomplete = true
                        else
                            square_loaded = true
                            power_status, gen_power, grid_power, freshness = check_square_power(sq, src_data.hydroPowered, src_data.active, src_data.switchCount, charge_read)
                            if power_status == "budget_exhausted" then
                                p_status, p_reason, incomplete = "budget_exhausted", "read_limit_reached", true
                                break
                            end
                            if freshness == "stale" then
                                counts.stale_sources = counts.stale_sources + 1
                                incomplete = true
                            elseif freshness == "unknown" or power_status == "unknown" then
                                counts.unverified_power = counts.unverified_power + 1
                                incomplete = true
                            end
                        end

                        if #sources >= max_output then
                            p_status, p_reason, incomplete = "budget_exhausted", "output_limit_reached", true
                            break
                        end

                        local s_id = "src:" .. this_pass_seq .. ":" .. i
                        if src_data.srcId and src_data.srcId > 0 then
                            s_id = "src:" .. src_data.srcId .. ":" .. this_pass_seq .. ":" .. i
                        end

                        sources[#sources + 1] = {
                            id = s_id,
                            x = src_data.x,
                            y = src_data.y,
                            z = src_data.z,
                            r = src_data.r,
                            g = src_data.g,
                            b = src_data.b,
                            radius = src_data.radius,
                            active = src_data.active,
                            hydroPowered = src_data.hydroPowered,
                            buildingRestriction = src_data.buildingRestriction,
                            buildingId = src_data.buildingId,
                            switchCount = src_data.switchCount,
                            squareLoaded = square_loaded,
                            powerStatus = power_status,
                            generatorPower = gen_power,
                            gridPower = grid_power,
                            freshness = freshness,
                        }
                        counts.valid_sources = #sources
                        t_sources = t_sources + 1
                    end
                end
            end

            -- Final consistency verification pass across all references (including after final getter)
            if p_status == "completed" then
                if not charge_read("getter") then
                    return {
                        status = "budget_exhausted",
                        reason = "read_limit_reached",
                        incomplete = true,
                        sources = sources,
                        counts = counts,
                    }
                end
                local post_sz, _, post_mut_err = inspect_collection(coll)
                if post_mut_err or post_sz ~= coll_size then
                    return {
                        status = "collection_mutated",
                        reason = "collection_changed_during_iteration",
                        incomplete = true,
                        sources = {},
                        counts = counts,
                    }
                end
                for k = 1, coll_size do
                    if not charge_read("getter") then
                        return {
                            status = "budget_exhausted",
                            reason = "read_limit_reached",
                            incomplete = true,
                            sources = sources,
                            counts = counts,
                        }
                    end
                    local post_it, post_err = get_collection_item(coll, k, is_java)
                    if post_err or post_it ~= initial_refs[k] then
                        return {
                            status = "collection_mutated",
                            reason = "collection_changed_during_iteration",
                            incomplete = true,
                            sources = {},
                            counts = counts,
                        }
                    end
                end

                local end_lok, end_lerr = chk_life()
                if not end_lok then
                    return {
                        status = "aborted",
                        reason = end_lerr,
                        incomplete = true,
                        sources = {},
                        counts = counts,
                    }
                end
            end

            if p_status == "completed" then
                if incomplete then
                    if not p_reason then
                        if counts.malformed_sources > 0 then
                            p_reason = "malformed_sources_detected"
                        elseif counts.unloaded_squares > 0 then
                            p_reason = "unloaded_squares_detected"
                        elseif counts.stale_sources > 0 then
                            p_reason = "stale_sources_detected"
                        elseif counts.unverified_power > 0 then
                            p_reason = "unverified_power_detected"
                        end
                    end
                else
                    p_reason = "ok"
                end
            end

            return {
                status = p_status,
                reason = p_reason,
                incomplete = incomplete,
                sources = sources,
                counts = counts,
            }
        end)

        busy = false

        if not run_ok then
            return {
                status = "aborted",
                reason = "unexpected_error",
                incomplete = true,
                sources = {},
                counts = counts,
            }
        end

        return run_result
    end

    inst.snapshot = snapshot
    inst.reset = reset
    inst.state = state

    return inst
end

function LightSourceSnapshot.snapshot(api, options)
    local s = LightSourceSnapshot.new(options)
    return s:snapshot(api)
end

return LightSourceSnapshot
