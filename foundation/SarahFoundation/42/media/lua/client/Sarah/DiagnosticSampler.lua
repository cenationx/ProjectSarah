-- Gemini authored; Codex reviewed. Offline injected diagnostic only. No engine wiring.
local DiagnosticSampler = {}

local MAX_CAPTURES = 512
local MAX_TOTAL_SQUARES = 4160
local MAX_ENUM_SQUARES = 64
local MAX_OBSTRUCTIONS = 32
local MAX_CANDIDATES = 32

local function is_finite(n)
    return type(n) == "number" and n == n and n ~= 1/0 and n ~= -1/0
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
           is_finite(x) and math.abs(x) <= 1e6 and is_finite(y) and math.abs(y) <= 1e6 and is_finite(z) and math.abs(z) <= 1e6 and
           is_finite(fx) and math.abs(fx) <= 1e6 and is_finite(fy) and math.abs(fy) <= 1e6 and (fx ~= 0 or fy ~= 0)
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

function DiagnosticSampler.new(modules)
    if type(modules) ~= "table" then
        error("DiagnosticSampler.new: modules must be a table", 2)
    end
    local CC = rawget(modules, "CandidateCollector")
    local Cov = rawget(modules, "Coverage")
    local Perc = rawget(modules, "Perception")
    local Obs = rawget(modules, "ObstructionNormalizer")
    if type(CC) ~= "table" or type(rawget(CC, "new")) ~= "function" then
        error("DiagnosticSampler.new: invalid CandidateCollector module", 2)
    end
    if type(Cov) ~= "table" or type(rawget(Cov, "newContext")) ~= "function" then
        error("DiagnosticSampler.new: invalid Coverage module", 2)
    end
    if type(Perc) ~= "table" or type(rawget(Perc, "new")) ~= "function" then
        error("DiagnosticSampler.new: invalid Perception module", 2)
    end
    if type(Obs) ~= "table" or type(rawget(Obs, "new")) ~= "function" then
        error("DiagnosticSampler.new: invalid ObstructionNormalizer module", 2)
    end

    local cc_new = rawget(CC, "new")
    local cov_newContext = rawget(Cov, "newContext")
    local perc_new = rawget(Perc, "new")
    local obs_new = rawget(Obs, "new")

    local collector = cc_new()
    local perception = perc_new({ range = 12, coneDegrees = 90 })

    local busy = false
    local revision = 1

    local t_samples = 0
    local t_aborted = 0
    local t_captures = 0
    local t_squares = 0
    local t_enum_sq = 0
    local t_cov_reads = 0
    local t_objects = 0
    local t_list_infos = 0
    local t_obstructions = 0

    local inst = {}

    local function reset(self)
        revision = revision + 1
        collector:reset()
    end

    local function snapshot(self)
        local coll_snap = collector:snapshot()
        return {
            total_samples = t_samples,
            total_aborted = t_aborted,
            total_captures = t_captures,
            total_squares = t_squares,
            total_enumeration_squares = t_enum_sq,
            total_coverage_reads = t_cov_reads,
            total_objects = t_objects,
            total_list_infos = t_list_infos,
            total_obstructions = t_obstructions,
            collector_cursors = coll_snap.active_cursors,
        }
    end

    local function sample(self, api_arg)
        local api = api_arg
        if api == nil and type(self) == "table" and rawget(self, "sample") == nil then
            api = self
        end
        if busy then
            return {
                status = "reentrancy_rejected",
                reason = "reentrant_call",
                incomplete = true,
                lighting = "unknown",
                results = {},
                counts = {
                    captures = 0,
                    squares = 0,
                    enumerationSquares = 0,
                    coverageReads = 0,
                    objects = 0,
                    listInfos = 0,
                    obstructions = 0,
                    processed = 0,
                    candidates = 0,
                },
            }
        end

        local counts = {
            captures = 0,
            squares = 0,
            enumerationSquares = 0,
            coverageReads = 0,
            objects = 0,
            listInfos = 0,
            obstructions = 0,
            processed = 0,
            candidates = 0,
        }

        if type(api) ~= "table" then
            return {
                status = "aborted",
                reason = "invalid_api",
                incomplete = true,
                lighting = "unknown",
                results = {},
                counts = counts,
            }
        end

        local api_cap = rawget(api, "capture")
        local api_sq = rawget(api, "getSquare")
        local api_li = rawget(api, "listInfo")
        local api_ro = rawget(api, "readObject")
        local api_obs = rawget(api, "obstruction")
        local raw_bindings = rawget(api, "bindings")

        if type(api_cap) ~= "function" or type(api_sq) ~= "function" or
           type(api_li) ~= "function" or type(api_ro) ~= "function" then
            return {
                status = "aborted",
                reason = "invalid_api",
                incomplete = true,
                lighting = "unknown",
                results = {},
                counts = counts,
            }
        end
        if api_obs ~= nil and type(api_obs) ~= "function" then
            return {
                status = "aborted",
                reason = "invalid_api",
                incomplete = true,
                lighting = "unknown",
                results = {},
                counts = counts,
            }
        end

        local frozen_bindings = nil
        if type(raw_bindings) == "table" then
            frozen_bindings = {
                Clear = rawget(raw_bindings, "Clear"),
                ClearThroughOpenDoor = rawget(raw_bindings, "ClearThroughOpenDoor"),
                ClearThroughWindow = rawget(raw_bindings, "ClearThroughWindow"),
                Blocked = rawget(raw_bindings, "Blocked"),
                ClearThroughClosedDoor = rawget(raw_bindings, "ClearThroughClosedDoor"),
            }
        end

        busy = true
        local pass_rev = revision
        local invalidated = false
        local first_abort_reason = nil
        local normalizer = nil
        local normalizer_valid = false
        local should_reset_collector = false
        local ret_val = nil

        local function mark_invalid(r)
            if not invalidated then
                invalidated = true
                first_abort_reason = r or "lifecycle_invalidated"
            end
        end

        local function do_capture()
            if revision ~= pass_rev then
                mark_invalid("reset_during_collect")
                return nil, first_abort_reason
            end
            if invalidated then
                return nil, first_abort_reason
            end
            if counts.captures >= MAX_CAPTURES then
                mark_invalid("capture_limit_reached")
                return nil, first_abort_reason
            end
            counts.captures = counts.captures + 1
            local ok, res = pcall(api_cap)
            if revision ~= pass_rev then
                mark_invalid("reset_during_collect")
                return nil, first_abort_reason
            end
            if not ok or not val_cap(res) then
                mark_invalid("capture_invalid")
                return nil, first_abort_reason
            end
            return cp_cap(res), nil
        end

        local run_ok, run_err = pcall(function()
            local anchor, a_err = do_capture()
            if not anchor then
                error({ abort = true, reason = a_err or "initial_capture_failed" })
            end

            local function chk_life()
                if revision ~= pass_rev then
                    mark_invalid("reset_during_collect")
                    return false, first_abort_reason
                end
                if invalidated then
                    return false, first_abort_reason
                end
                local c, e = do_capture()
                if revision ~= pass_rev then
                    mark_invalid("reset_during_collect")
                    return false, first_abort_reason
                end
                if not c or e then
                    return false, first_abort_reason
                end
                if not cap_eq(anchor, c) then
                    mark_invalid("lifecycle_drift")
                    return false, first_abort_reason
                end
                return true, nil
            end

            normalizer = obs_new(frozen_bindings)
            normalizer_valid = normalizer:snapshot().valid

            local wrapped_api = {}
            wrapped_api.capture = function()
                if revision ~= pass_rev then
                    mark_invalid("reset_during_collect")
                    return nil
                end
                if invalidated or counts.captures >= (MAX_CAPTURES - 1) then
                    mark_invalid("capture_limit_reached")
                    return nil
                end
                local c, e = do_capture()
                if not c or e then return nil end
                if not cap_eq(anchor, c) then
                    mark_invalid("lifecycle_drift")
                    return nil
                end
                return c
            end

            wrapped_api.getSquare = function(x, y, z)
                if revision ~= pass_rev then
                    mark_invalid("reset_during_collect")
                    return nil
                end
                if invalidated or counts.squares >= MAX_TOTAL_SQUARES or counts.enumerationSquares >= MAX_ENUM_SQUARES then
                    return nil
                end
                counts.squares = counts.squares + 1
                counts.enumerationSquares = counts.enumerationSquares + 1
                local ok, sq = pcall(api_sq, x, y, z)
                if revision ~= pass_rev then
                    mark_invalid("reset_during_collect")
                    return nil
                end
                if not ok then return nil end
                return sq
            end

            wrapped_api.listInfo = function(sq)
                if revision ~= pass_rev then
                    mark_invalid("reset_during_collect")
                    return nil
                end
                if invalidated then return nil end
                counts.listInfos = counts.listInfos + 1
                local ok, sz, tok = pcall(api_li, sq)
                if revision ~= pass_rev then
                    mark_invalid("reset_during_collect")
                    return nil
                end
                if not ok then return nil end
                return sz, tok
            end

            wrapped_api.readObject = function(sq, idx)
                if revision ~= pass_rev then
                    mark_invalid("reset_during_collect")
                    return nil
                end
                if invalidated then return nil end
                counts.objects = counts.objects + 1
                local ok, obj = pcall(api_ro, sq, idx)
                if revision ~= pass_rev then
                    mark_invalid("reset_during_collect")
                    return nil
                end
                if not ok then return nil end
                return obj
            end

            local coll_res = collector:collect(wrapped_api)
            if coll_res.status == "aborted" or invalidated then
                should_reset_collector = true
                error({ abort = true, reason = first_abort_reason or coll_res.reason or "collector_aborted" })
            end

            local raw_candidates = coll_res.candidates
            counts.candidates = #raw_candidates

            local cov_context = cov_newContext({ range = 12, candidateBudget = 1024, sampleBudget = 4096 })
            local covered_flags = {}
            local obs_pos = { x = anchor.x, y = anchor.y, z = anchor.z }

            local function cov_getSquare(x, y, z)
                if revision ~= pass_rev then
                    mark_invalid("reset_during_collect")
                    return nil
                end
                if invalidated or counts.squares >= MAX_TOTAL_SQUARES then
                    return nil
                end
                counts.squares = counts.squares + 1
                counts.coverageReads = counts.coverageReads + 1
                local ok, sq = pcall(api_sq, x, y, z)
                if revision ~= pass_rev then
                    mark_invalid("reset_during_collect")
                    return nil
                end
                if not ok or sq == nil or sq == false then return nil end
                return sq
            end

            local perc_obs = {
                x = anchor.x,
                y = anchor.y,
                z = anchor.z,
                forward = { x = anchor.fx, y = anchor.fy },
            }

            local perc_queries = {}
            perc_queries.coverage = function(obs, cand)
                if revision ~= pass_rev then
                    mark_invalid("reset_during_collect")
                    return false
                end
                if invalidated or counts.captures + 2 + 1 > MAX_CAPTURES then
                    mark_invalid("capture_limit_reached")
                    return false
                end
                local l_ok_pre, _ = chk_life()
                if not l_ok_pre then return false end

                local cand_pos = { x = cand.x, y = cand.y, z = cand.z }
                local cov_res = cov_context:check(obs_pos, cand_pos, cov_getSquare)

                local l_ok_post, _ = chk_life()
                if not l_ok_post then return false end

                if cov_res.status == "covered" and cov_res.covered == true then
                    covered_flags[cand.id] = true
                    return true
                else
                    covered_flags[cand.id] = false
                    return false
                end
            end

            perc_queries.obstruction = function(obs, cand)
                if not normalizer_valid then
                    return nil
                end
                if covered_flags[cand.id] ~= true then
                    return nil
                end
                if type(api_obs) ~= "function" then
                    return nil
                end
                if counts.obstructions >= MAX_OBSTRUCTIONS then
                    return nil
                end
                if revision ~= pass_rev then
                    mark_invalid("reset_during_collect")
                    return nil
                end
                if invalidated or counts.captures + 2 + 1 > MAX_CAPTURES then
                    mark_invalid("capture_limit_reached")
                    return nil
                end

                local l_ok_pre, _ = chk_life()
                if not l_ok_pre then return nil end

                counts.obstructions = counts.obstructions + 1
                local cp_o = {
                    x = obs.x,
                    y = obs.y,
                    z = obs.z,
                    forward = { x = obs.forward.x, y = obs.forward.y },
                }
                local cp_c = {
                    id = cand.id,
                    kind = cand.kind,
                    x = cand.x,
                    y = cand.y,
                    z = cand.z,
                }

                local ok, raw_obs = pcall(api_obs, cp_o, cp_c)

                if revision ~= pass_rev then
                    mark_invalid("reset_during_collect")
                    return nil
                end
                local l_ok_post, _ = chk_life()
                if not l_ok_post then return nil end

                if not ok then return "unknown" end
                local norm = normalizer:normalize(raw_obs, true)
                return norm.status
            end

            local perc_out = perception:sample(perc_obs, raw_candidates, perc_queries)
            counts.processed = perc_out.processed

            if invalidated then
                should_reset_collector = true
                error({ abort = true, reason = first_abort_reason })
            end

            local fin_ok, fin_err = chk_life()
            if not fin_ok then
                should_reset_collector = true
                error({ abort = true, reason = first_abort_reason or fin_err })
            end

            local clean_results = {}
            for i = 1, math.min(#perc_out.results, 32) do
                local r = perc_out.results[i]
                clean_results[i] = {
                    id = r.id,
                    kind = r.kind,
                    geometric = r.geometric,
                    visual = r.visual,
                    reason = r.reason,
                }
            end

            ret_val = {
                status = "sampled",
                reason = nil,
                incomplete = true,
                lighting = "unknown",
                results = clean_results,
                counts = counts,
            }
        end)

        -- Keep the lock through cleanup; discard every failed pass, including
        -- unexpected dependency failures after the collector committed cursors.
        local cleanup_ok = pcall(function()
            if normalizer then normalizer:invalidate() end
        end)
        if not cleanup_ok then
            run_ok = false
            run_err = { abort = true, reason = first_abort_reason or "cleanup_error" }
        end
        if not run_ok or should_reset_collector then
            pcall(function() collector:reset() end)
        end
        busy = false
        t_captures = t_captures + counts.captures
        t_squares = t_squares + counts.squares
        t_enum_sq = t_enum_sq + counts.enumerationSquares
        t_cov_reads = t_cov_reads + counts.coverageReads
        t_objects = t_objects + counts.objects
        t_list_infos = t_list_infos + counts.listInfos
        t_obstructions = t_obstructions + counts.obstructions

        if not run_ok then
            t_aborted = t_aborted + 1
            if type(run_err) == "table" and run_err.abort then
                return {
                    status = "aborted",
                    reason = run_err.reason,
                    incomplete = true,
                    lighting = "unknown",
                    results = {},
                    counts = counts,
                }
            end
            return {
                status = "aborted",
                reason = first_abort_reason or "internal_error",
                incomplete = true,
                lighting = "unknown",
                results = {},
                counts = counts,
            }
        end

        t_samples = t_samples + 1
        return ret_val
    end

    inst.sample = sample
    inst.reset = reset
    inst.snapshot = snapshot

    return inst
end

return DiagnosticSampler
