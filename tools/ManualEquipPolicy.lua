-- tools/ManualEquipPolicy.lua
-- Bounded fixture-only manual equipment policy for Project Sarah.
-- Intended Lua 5.1-compatible syntax; native Kahlua compatibility unverified. Zero engine/native imports, globals, or event hooks.
-- NOTICE: Fixture-only verification policy (evidenceScope="fixture_only").
-- Native admission remains unresolved: native IsoGameCharacter.setPrimaryHandItem
-- writes leftHandItem before triggering OnEquipPrimary synchronously, risking cross-player
-- interference (e.g. FishingHandler destroying player 0's fishing manager).
-- This module establishes no native safety certificate and yields nativeAcceptance=false.

local ManualEquipPolicy = {}

local MAX_ROOT_COUNT = 64
local MAX_STR_LEN = 96
local MAX_INT = 2147483647

local function is_valid_str96(s)
    return type(s) == "string" and #s >= 1 and #s <= MAX_STR_LEN
end

local function is_valid_int(n)
    return type(n) == "number" and n == n and n ~= 1/0 and n ~= -1/0 and math.floor(n) == n and n >= 0 and n <= MAX_INT
end

local function make_result(status, reason, commit_attempted, post_verified)
    return {
        status = status,
        reason = reason,
        commitAttempted = commit_attempted == true,
        postVerified = post_verified == true,
        nativeAcceptance = false,
        evidenceScope = "fixture_only",
    }
end

function ManualEquipPolicy.new()
    local busy = false
    local revision = 1

    local inst = {}

    local function reset(self)
        revision = revision + 1
        -- In-flight busy is intentionally NOT released here
    end

    local function run(self, api_arg)
        local api = api_arg
        if api == nil and type(self) == "table" and rawget(self, "run") == nil then
            api = self
        end

        if busy then
            return make_result("rejected", "busy", false, false)
        end

        if type(api) ~= "table" then
            return make_result("rejected", "invalid_api", false, false)
        end

        local cb_capture = rawget(api, "capture")
        local cb_inspect = rawget(api, "inspect")
        local cb_commit = rawget(api, "commit")

        if type(cb_capture) ~= "function" or type(cb_inspect) ~= "function" or type(cb_commit) ~= "function" then
            return make_result("rejected", "invalid_api", false, false)
        end

        busy = true
        local pass_rev = revision
        local commit_attempted = false
        local post_verified = false
        local failure_status, failure_reason

        local ok, res = pcall(function()
            local anchor_session = nil
            local anchor_revision = nil

            local anchor_actor = nil
            local anchor_root = nil
            local anchor_item = nil
            local anchor_item_id = nil
            local anchor_worn_stamp = nil

            local function fail(reason, was_cancelled)
                if commit_attempted then
                    failure_status, failure_reason = "failed_after_commit", reason
                    error(false)
                elseif was_cancelled then
                    failure_status, failure_reason = "cancelled_before_commit", reason
                    error(false)
                else
                    failure_status, failure_reason = "rejected", reason
                    error(false)
                end
            end

            local function do_capture()
                if revision ~= pass_rev then
                    fail("reset_during_request", true)
                end
                local cap_ok, c = pcall(cb_capture)
                if revision ~= pass_rev then
                    fail("reset_during_request", true)
                end
                if not cap_ok or type(c) ~= "table" then
                    fail("capture_failed", false)
                end

                local scope = rawget(c, "evidenceScope")
                local iso = rawget(c, "eventIsolation")
                local sess = rawget(c, "session")
                local rev = rawget(c, "revision")
                local canc = rawget(c, "cancelled")
                local valid = rawget(c, "actorValid")
                local alive = rawget(c, "alive")
                local resi = rawget(c, "resident")
                local idle = rawget(c, "idle")

                if canc == true then
                    fail("cancelled", true)
                end

                if scope ~= "fixture_only" or iso ~= "fixture_only" or
                   valid ~= true or alive ~= true or resi ~= true or idle ~= true or
                   canc ~= false or not is_valid_str96(sess) or not is_valid_str96(rev) then
                    fail("capture_invalid", false)
                end

                if anchor_session == nil then
                    anchor_session = sess
                    anchor_revision = rev
                else
                    if sess ~= anchor_session or rev ~= anchor_revision then
                        fail("session_drift", true)
                    end
                end
            end

            local function validate_snapshot(s, phase)
                if type(s) ~= "table" then
                    fail("inspect_not_table", false)
                end
                if rawget(s, "scope") ~= "fixture_only" then
                    fail("scope_mismatch", false)
                end

                local actor = rawget(s, "actor")
                local root = rawget(s, "root")
                local item = rawget(s, "item")
                local sel_container = rawget(s, "selectedContainer")
                local item_id = rawget(s, "itemId")
                local root_count = rawget(s, "rootCount")
                local entries = rawget(s, "entries")
                local primary = rawget(s, "primary")
                local secondary = rawget(s, "secondary")
                local worn_stamp = rawget(s, "wornStamp")

                if (type(actor) ~= "table" and type(actor) ~= "userdata") or
                   (type(root) ~= "table" and type(root) ~= "userdata") or
                   (type(item) ~= "table" and type(item) ~= "userdata") then
                    fail("invalid_opaque_handles", false)
                end

                if not rawequal(sel_container, root) then
                    fail("selected_container_not_root", false)
                end

                if not is_valid_int(item_id) or not is_valid_str96(worn_stamp) then
                    fail("invalid_id_or_worn_stamp", false)
                end

                if rawget(s, "directContains") ~= true or
                   rawget(s, "melee") ~= true or
                   rawget(s, "oneHanded") ~= true or
                   rawget(s, "conditionValid") ~= true or
                   rawget(s, "attached") ~= false or
                   rawget(s, "worn") ~= false or
                   rawget(s, "activationDependent") ~= false or
                   rawget(s, "forceDropHeavy") ~= false or
                   rawget(s, "loadoutConflict") ~= false then
                    fail("capability_flag_rejected", false)
                end

                if phase == "pre" then
                    anchor_actor = actor
                    anchor_root = root
                    anchor_item = item
                    anchor_item_id = item_id
                    anchor_worn_stamp = worn_stamp
                else
                    if not rawequal(actor, anchor_actor) or
                       not rawequal(root, anchor_root) or
                       not rawequal(item, anchor_item) then
                        fail("identity_drift", false)
                    end
                    if item_id ~= anchor_item_id then
                        fail("item_id_drift", false)
                    end
                    if worn_stamp ~= anchor_worn_stamp then
                        fail("worn_stamp_drift", false)
                    end
                end

                if secondary ~= nil then
                    fail("secondary_hand_not_empty", false)
                end
                if phase == "pre" or phase == "barrier" then
                    if primary ~= nil then
                        fail("primary_hand_not_empty", false)
                    end
                elseif phase == "post" then
                    if not rawequal(primary, anchor_item) then
                        fail("primary_hand_mismatch", false)
                    end
                end

                if type(root_count) ~= "number" or root_count < 1 or root_count > MAX_ROOT_COUNT or math.floor(root_count) ~= root_count then
                    fail("root_count_invalid", false)
                end
                if type(entries) ~= "table" then
                    fail("entries_not_table", false)
                end

                local selected_ref_count = 0
                local selected_id_count = 0
                for i = 1, root_count do
                    local e = rawget(entries, i)
                    if type(e) ~= "table" then
                        fail("entry_invalid", false)
                    end
                    local e_ref = rawget(e, "ref")
                    local e_id = rawget(e, "id")
                    if (type(e_ref) ~= "table" and type(e_ref) ~= "userdata") or not is_valid_int(e_id) then
                        fail("entry_fields_invalid", false)
                    end
                    local is_ref = rawequal(e_ref, anchor_item)
                    local is_id = (e_id == anchor_item_id)
                    if is_ref then
                        selected_ref_count = selected_ref_count + 1
                    end
                    if is_id then
                        selected_id_count = selected_id_count + 1
                    end
                    if is_ref ~= is_id then
                        fail("entry_id_ref_mismatch", false)
                    end
                end

                if selected_ref_count ~= 1 or selected_id_count ~= 1 then
                    fail("multiplicity_invalid", false)
                end
            end

            local function freeze_snapshot(s)
                if type(s) ~= "table" then return s end
                local copy = {}
                local keys = {"scope", "actor", "root", "item", "selectedContainer",
                    "itemId", "rootCount", "primary", "secondary", "wornStamp",
                    "directContains", "melee", "oneHanded", "conditionValid",
                    "attached", "worn", "activationDependent", "forceDropHeavy",
                    "loadoutConflict"}
                for i = 1, #keys do copy[keys[i]] = rawget(s, keys[i]) end
                local entries = rawget(s, "entries")
                copy.entries = entries
                if type(entries) == "table" then
                    copy.entries = {}
                    local count = copy.rootCount
                    if is_valid_int(count) and count >= 1 and count <= MAX_ROOT_COUNT then
                        for i = 1, count do
                            local e = rawget(entries, i)
                            if type(e) == "table" then
                                copy.entries[i] = {ref = rawget(e, "ref"), id = rawget(e, "id")}
                            else
                                copy.entries[i] = e
                            end
                        end
                    end
                end
                return copy
            end

            local function do_inspect_phase(phase)
                do_capture()
                if revision ~= pass_rev then
                    fail("reset_during_request", true)
                end
                local insp_ok, s = pcall(cb_inspect, phase)
                if revision ~= pass_rev then
                    fail("reset_during_request", true)
                end
                if not insp_ok then
                    fail("inspect_threw", false)
                end
                s = freeze_snapshot(s)
                do_capture()
                validate_snapshot(s, phase)
            end

            do_capture()
            do_inspect_phase("pre")
            do_inspect_phase("barrier")
            do_capture()

            commit_attempted = true
            if revision ~= pass_rev then
                fail("reset_during_request", true)
            end
            local com_ok, _ = pcall(cb_commit)
            if revision ~= pass_rev then
                fail("reset_after_commit", true)
            end

            if not com_ok then
                fail("commit_threw", false)
            end
            do_capture()

            do_inspect_phase("post")
            post_verified = true

            do_capture()

            return make_result("completed", "policy_verified", true, true)
        end)

        busy = false

        if not ok then
            if failure_status then
                return make_result(failure_status, failure_reason, commit_attempted, false)
            end
            if commit_attempted then
                return make_result("failed_after_commit", "internal_error", true, false)
            else
                return make_result("rejected", "internal_error", false, false)
            end
        end

        return res
    end

    inst.run = run
    inst.reset = reset

    return inst
end

return ManualEquipPolicy
