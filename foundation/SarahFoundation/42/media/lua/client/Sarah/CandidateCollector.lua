-- Offline injected collector; no native integration.
-- Gemini-authored policy, reviewed by Codex. Candidates are PRIVATE adapter
-- snapshots, not confirmed knowledge or gameplay-facing diagnostics.
local CandidateCollector = {}
local OFFSETS = {}
for dy = -12, 12 do
    for dx = -12, 12 do OFFSETS[#OFFSETS + 1] = { dx = dx, dy = dy } end
end
local function is_finite(n) return type(n) == "number" and n == n and n ~= 1/0 and n ~= -1/0 end
local function is_str96(s) return type(s) == "string" and #s > 0 and #s <= 96 end
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
    return { controller = rawget(c, "controller"), npc = rawget(c, "npc"), cell = rawget(c, "cell"),
             generation = rawget(c, "generation"), alive = true, resident = true, cancelled = false,
             x = rawget(c, "x") + 0.0, y = rawget(c, "y") + 0.0, z = rawget(c, "z") + 0.0,
             fx = rawget(c, "fx") + 0.0, fy = rawget(c, "fy") + 0.0 }
end
local function cap_eq(a, b)
    if not a or not b then return false end
    return a.controller == b.controller and a.npc == b.npc and a.cell == b.cell and a.generation == b.generation and
           a.alive == b.alive and a.resident == b.resident and a.cancelled == b.cancelled and
           a.x == b.x and a.y == b.y and a.z == b.z and a.fx == b.fx and a.fy == b.fy
end
local function cp_cur(cur, keys)
    local c, k = {}, {}
    for id, v in pairs(cur) do c[id] = { index = v.index, token = v.token } end
    for i = 1, #keys do k[i] = keys[i] end
    return c, k
end
function CandidateCollector.new()
    local in_collect, rev, was_reset, off_cur = false, 1, false, 1
    local cursors, cursor_keys, session = {}, {}, nil
    local t_pass, t_sq, t_obj, t_li, t_cap, t_cand = 0, 0, 0, 0, 0, 0
    local self_obj = {}
    local function do_reset()
        rev = rev + 1
        was_reset = true
        off_cur, cursors, cursor_keys, session = 1, {}, {}, nil
    end
    local function do_snapshot()
        local count = 0; for _ in pairs(cursors) do count = count + 1 end
        return { total_passes = t_pass, total_squares = t_sq, total_objects = t_obj, total_list_infos = t_li,
                 total_captures = t_cap, total_candidates = t_cand, active_cursors = count, offset_cursor = off_cur }
    end
    local function do_collect(self_arg, api_arg)
        local api = api_arg
        if api == nil and type(self_arg) == "table" and rawget(self_arg, "collect") == nil then api = self_arg end
        if in_collect then
            return { status = "reentrancy_rejected", reason = "reentrant_call", incomplete = true, candidates = {},
                     counts = { squares = 0, objects = 0, list_infos = 0, captures = 0, candidates = 0,
                                missing_square = 0, query_error = 0, invalid_list = 0, list_changed = 0, invalid_snapshot = 0 } }
        end
        if type(api) ~= "table" then
            return { status = "aborted", reason = "invalid_api", incomplete = true, candidates = {},
                     counts = { squares = 0, objects = 0, list_infos = 0, captures = 0, candidates = 0,
                                missing_square = 0, query_error = 0, invalid_list = 0, list_changed = 0, invalid_snapshot = 0 } }
        end
        local get_cap, get_sq = rawget(api, "capture"), rawget(api, "getSquare")
        local get_li, get_ro = rawget(api, "listInfo"), rawget(api, "readObject")
        if type(get_cap) ~= "function" or type(get_sq) ~= "function" or type(get_li) ~= "function" or type(get_ro) ~= "function" then
            return { status = "aborted", reason = "invalid_api", incomplete = true, candidates = {},
                     counts = { squares = 0, objects = 0, list_infos = 0, captures = 0, candidates = 0,
                                missing_square = 0, query_error = 0, invalid_list = 0, list_changed = 0, invalid_snapshot = 0 } }
        end
        in_collect, was_reset = true, false
        local p_rev = rev
        local counts = { squares = 0, objects = 0, list_infos = 0, captures = 0, candidates = 0,
                         missing_square = 0, query_error = 0, invalid_list = 0, list_changed = 0, invalid_snapshot = 0 }
        local p_status, p_reason = "completed", nil
        local st_off, st_cur, st_keys = off_cur, cp_cur(cursors, cursor_keys)
        local st_sess = session
        local st_cands, seen_ids = {}, {}
        local function chk_cap()
            if counts.captures >= 256 then return nil, "budget_exhausted" end
            counts.captures = counts.captures + 1
            local ok, res = pcall(get_cap)
            if rev ~= p_rev or was_reset then return nil, "reset_during_collect" end
            if not ok or not val_cap(res) then return nil, "capture_invalid" end
            return cp_cap(res), nil
        end
        local init_cap, init_err = chk_cap()
        local ret_val = nil
        local ok, err = pcall(function()
            if not init_cap then error({ abort = true, reason = init_err or "initial_capture_failed" }) end
            if st_sess and not cap_eq(st_sess, init_cap) then st_off, st_cur, st_keys = 1, {}, {} end
            st_sess = cp_cap(init_cap)
            local function chk_life()
                if rev ~= p_rev or was_reset then return false, "reset_during_collect" end
                local c, e = chk_cap()
                if rev ~= p_rev or was_reset then return false, "reset_during_collect" end
                if not c or e then return false, e or "lifecycle_capture_failed" end
                if not cap_eq(init_cap, c) then return false, "lifecycle_drift" end
                return true, nil
            end
            local s_z, s_x, s_y = math.floor(init_cap.z), init_cap.x, init_cap.y
            while counts.squares < 64 do
                if counts.captures + 4 + 1 > 256 then p_status, p_reason = "budget_exhausted", "capture_limit_reached"; break end
                if counts.candidates >= 32 then p_status, p_reason = "budget_exhausted", "candidate_limit_reached"; break end
                if counts.objects >= 128 then p_status, p_reason = "budget_exhausted", "object_limit_reached"; break end
                if counts.list_infos >= 128 then p_status, p_reason = "budget_exhausted", "list_info_limit_reached"; break end
                local off_idx = st_off
                st_off = (st_off % 625) + 1
                local off = OFFSETS[off_idx]
                local tx, ty, tz = math.floor(s_x) + off.dx, math.floor(s_y) + off.dy, s_z
                local coord_key = tx .. "," .. ty .. "," .. tz
                local l_ok, l_err = chk_life(); if not l_ok then error({ abort = true, reason = l_err }) end
                counts.squares = counts.squares + 1
                local sq_ok, sq = pcall(get_sq, tx, ty, tz)
                l_ok, l_err = chk_life(); if not l_ok then error({ abort = true, reason = l_err }) end
                if not sq_ok then
                    counts.query_error = counts.query_error + 1
                elseif sq == nil or sq == false then
                    counts.missing_square = counts.missing_square + 1
                else
                    l_ok, l_err = chk_life(); if not l_ok then error({ abort = true, reason = l_err }) end
                    counts.list_infos = counts.list_infos + 1
                    local li_ok, sz, tok = pcall(get_li, sq)
                    l_ok, l_err = chk_life(); if not l_ok then error({ abort = true, reason = l_err }) end
                    if not li_ok then
                        counts.query_error = counts.query_error + 1
                    else
                        local v_li = type(sz) == "number" and sz >= 0 and sz <= 1e6 and math.floor(sz) == sz and is_str96(tok)
                        if not v_li then
                            counts.invalid_list = counts.invalid_list + 1
                        elseif sz > 0 then
                            local cur = st_cur[coord_key]
                            local start_idx = (cur and cur.token == tok) and (cur.index % sz) or 0
                            local to_read = math.min(sz, 16)
                            local sq_cands, sq_seen, committed_reads, mutated = {}, {}, 0, false
                            for step = 0, to_read - 1 do
                                if counts.objects >= 128 or (counts.candidates + #sq_cands) >= 32 or
                                   counts.list_infos + 2 > 128 or counts.captures + 6 + 1 > 256 then
                                    p_status = "budget_exhausted"
                                    p_reason = (counts.candidates + #sq_cands >= 32) and "candidate_limit_reached" or
                                               ((counts.captures + 6 + 1 > 256) and "capture_limit_reached" or
                                               ((counts.objects >= 128) and "object_limit_reached" or "list_info_limit_reached"))
                                    -- A stable list receiving no reads must not be skipped on
                                    -- every sweep due to its position at the budget boundary.
                                    if committed_reads == 0 then st_off = off_idx end
                                    break
                                end
                                local r_idx = (start_idx + step) % sz
                                l_ok, l_err = chk_life(); if not l_ok then error({ abort = true, reason = l_err }) end
                                counts.list_infos = counts.list_infos + 1
                                local p_ok, p_sz, p_tok = pcall(get_li, sq)
                                l_ok, l_err = chk_life(); if not l_ok then error({ abort = true, reason = l_err }) end
                                if not p_ok or p_sz ~= sz or p_tok ~= tok or r_idx >= p_sz then
                                    counts.list_changed = counts.list_changed + 1; mutated = true; break
                                end
                                l_ok, l_err = chk_life(); if not l_ok then error({ abort = true, reason = l_err }) end
                                counts.objects = counts.objects + 1
                                local ro_ok, raw_o = pcall(get_ro, sq, r_idx)
                                l_ok, l_err = chk_life(); if not l_ok then error({ abort = true, reason = l_err }) end
                                l_ok, l_err = chk_life(); if not l_ok then error({ abort = true, reason = l_err }) end
                                counts.list_infos = counts.list_infos + 1
                                local q_ok, q_sz, q_tok = pcall(get_li, sq)
                                l_ok, l_err = chk_life(); if not l_ok then error({ abort = true, reason = l_err }) end
                                if not q_ok or q_sz ~= sz or q_tok ~= tok then
                                    counts.list_changed = counts.list_changed + 1; mutated = true; break
                                end
                                if not ro_ok or type(raw_o) ~= "table" then
                                    counts.invalid_snapshot = counts.invalid_snapshot + 1; mutated = true; break
                                end
                                committed_reads = committed_reads + 1
                                local oid, okind = rawget(raw_o, "id"), rawget(raw_o, "kind")
                                local ox, oy, oz = rawget(raw_o, "x"), rawget(raw_o, "y"), rawget(raw_o, "z")
                                if is_str96(oid) and (okind == "player" or okind == "zombie") and
                                   is_finite(ox) and math.abs(ox) <= 1e6 and is_finite(oy) and math.abs(oy) <= 1e6 and
                                   is_finite(oz) and math.abs(oz) <= 1e6 and math.floor(oz) == s_z then
                                    local dx, dy = ox - s_x, oy - s_y
                                    if (dx * dx + dy * dy) <= 144 then
                                        if not seen_ids[oid] and not sq_seen[oid] then
                                            sq_seen[oid] = true
                                            sq_cands[#sq_cands + 1] = { id = oid, kind = okind, x = ox + 0.0, y = oy + 0.0, z = oz + 0.0 }
                                        end
                                    end
                                else
                                    counts.invalid_snapshot = counts.invalid_snapshot + 1
                                end
                            end
                            if mutated then
                                sq_cands = {}
                            else
                                for i = 1, #sq_cands do
                                    if counts.candidates >= 32 then p_status, p_reason = "budget_exhausted", "candidate_limit_reached"; break end
                                    local c = sq_cands[i]
                                    if not seen_ids[c.id] then
                                        seen_ids[c.id] = true
                                        st_cands[#st_cands + 1] = c
                                        counts.candidates = counts.candidates + 1
                                    end
                                end
                                if committed_reads > 0 then
                                    local n_idx = (start_idx + committed_reads) % sz
                                    if not st_cur[coord_key] then
                                        if #st_keys >= 64 then st_cur[table.remove(st_keys, 1)] = nil end
                                        st_keys[#st_keys + 1] = coord_key
                                    end
                                    st_cur[coord_key] = { index = n_idx, token = tok }
                                end
                            end
                            if p_status == "budget_exhausted" then break end
                        end
                    end
                end
            end
            local fin_ok, fin_err = chk_life()
            if not fin_ok then error({ abort = true, reason = fin_err }) end
            off_cur, cursors, cursor_keys, session = st_off, st_cur, st_keys, st_sess
            t_sq, t_obj, t_li = t_sq + counts.squares, t_obj + counts.objects, t_li + counts.list_infos
            t_cap, t_cand, t_pass = t_cap + counts.captures, t_cand + counts.candidates, t_pass + 1
            ret_val = { status = p_status, reason = p_reason, incomplete = true, candidates = st_cands, counts = counts }
        end)
        in_collect = false
        if not ok then
            if type(err) == "table" and err.abort then
                t_sq, t_obj, t_li = t_sq + counts.squares, t_obj + counts.objects, t_li + counts.list_infos
                t_cap, t_pass = t_cap + counts.captures, t_pass + 1
                return { status = "aborted", reason = err.reason, incomplete = true, candidates = {}, counts = counts }
            end
            return { status = "aborted", reason = "internal_error", incomplete = true, candidates = {}, counts = counts }
        end
        return ret_val
    end
    self_obj.collect, self_obj.reset, self_obj.snapshot = do_collect, do_reset, do_snapshot
    return self_obj
end
return CandidateCollector
