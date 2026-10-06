# tools/test_manual_equip.py
# Python test suite executing ManualEquipPolicy.lua via Lupa (Lua 5.5 / 5.1-compatible syntax).
# UTF-8 encoded. Tests meaningful races, boundary ceilings, and strict state invariants.

import os
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "tools/dependencies/python"))
from lupa import LuaRuntime

def main():
    lua = LuaRuntime(unpack_returned_tuples=True)
    script_dir = os.path.dirname(os.path.abspath(__file__))
    lua_path = os.path.join(script_dir, "ManualEquipPolicy.lua")

    with open(lua_path, "r", encoding="utf-8") as f:
        lua_code = f.read()

    policy_module = lua.execute(lua_code)
    wrap = lua.eval("function(f) return function(...) return f(...) end end")
    def run_policy(pol, api):
        if api is not None:
            for key in ("capture", "inspect", "commit"):
                value = api[key]
                if callable(value) and lua.eval("type")(value) != "function":
                    api[key] = wrap(value)
        return pol.run(api)


    passed_count = 0
    total_count = 0

    def test(name, fn):
        nonlocal passed_count, total_count
        total_count += 1
        try:
            fn()
            passed_count += 1
            print(f"PASS: {total_count:02d} - {name}")
        except Exception as e:
            print(f"FAIL: {total_count:02d} - {name}: {e}")
            raise e

    def create_fixture(mutations=None):
        actor = lua.eval("{}")
        root = lua.eval("{}")
        item = lua.eval("{}")
        item_id = 42
        worn_stamp = "worn_stamp_init"

        state = {
            "primary": None,
            "secondary": None,
            "cancelled": False,
            "session": "sess_v1",
            "revision": "rev_v1",
            "actorValid": True,
            "alive": True,
            "resident": True,
            "idle": True,
            "directContains": True,
            "melee": True,
            "oneHanded": True,
            "conditionValid": True,
            "attached": False,
            "worn": False,
            "activationDependent": False,
            "forceDropHeavy": False,
            "loadoutConflict": False,
            "scope": "fixture_only",
            "evidenceScope": "fixture_only",
            "eventIsolation": "fixture_only",
            "commit_mutates": True,
        }
        if mutations:
            state.update(mutations)

        counts = {"capture": 0, "inspect": 0, "commit": 0}
        inspect_phases = []

        def cb_capture():
            counts["capture"] += 1
            t = lua.table(
                evidenceScope=state["evidenceScope"],
                eventIsolation=state["eventIsolation"],
                session=state["session"],
                revision=state["revision"],
                cancelled=state["cancelled"],
                actorValid=state["actorValid"],
                alive=state["alive"],
                resident=state["resident"],
                idle=state["idle"],
            )
            return t

        def cb_inspect(phase):
            counts["inspect"] += 1
            inspect_phases.append(phase)
            cur_prim = state["primary"]
            entries = lua.eval("{}")
            entries[1] = lua.table(ref=item, id=item_id)
            entries[2] = lua.table(ref=lua.eval("{}"), id=99)

            snap = lua.table(
                scope=state["scope"],
                actor=actor,
                root=root,
                item=item,
                selectedContainer=root,
                itemId=item_id,
                rootCount=2,
                entries=entries,
                primary=cur_prim,
                secondary=state["secondary"],
                wornStamp=worn_stamp,
                directContains=state["directContains"],
                melee=state["melee"],
                oneHanded=state["oneHanded"],
                conditionValid=state["conditionValid"],
                attached=state["attached"],
                worn=state["worn"],
                activationDependent=state["activationDependent"],
                forceDropHeavy=state["forceDropHeavy"],
                loadoutConflict=state["loadoutConflict"],
            )
            return snap

        def cb_commit():
            counts["commit"] += 1
            if state["commit_mutates"]:
                state["primary"] = item
            return True

        api = lua.table(
            capture=cb_capture,
            inspect=cb_inspect,
            commit=cb_commit,
        )
        return api, counts, inspect_phases, state, actor, root, item

    # 01. Nominal Complete Exact Ceilings
    def test_nominal():
        pol = policy_module.new()
        api, counts, phases, state, actor, root, item = create_fixture()
        res = run_policy(pol, api)
        assert res["status"] == "completed"
        assert res["reason"] == "policy_verified"
        assert res["commitAttempted"] is True
        assert res["postVerified"] is True
        assert res["nativeAcceptance"] is False
        assert res["evidenceScope"] == "fixture_only"
        assert counts["capture"] == 10
        assert counts["inspect"] == 3
        assert counts["commit"] == 1
        assert phases == ["pre", "barrier", "post"]
    test("nominal_exact_boundary_ceilings", test_nominal)

    # 02. Invalid API Handling
    def test_invalid_api():
        pol = policy_module.new()
        res1 = run_policy(pol, None)
        assert res1["status"] == "rejected" and res1["reason"] == "invalid_api"
        res2 = run_policy(pol, lua.table(capture=lambda: None))
        assert res2["status"] == "rejected" and res2["reason"] == "invalid_api"
    test("invalid_api_rejected", test_invalid_api)

    # 03. Missing Evidence Scope in Capture
    def test_missing_evidence_scope():
        pol = policy_module.new()
        api, counts, _, _, _, _, _ = create_fixture({"evidenceScope": "live_engine"})
        res = run_policy(pol, api)
        assert res["status"] == "rejected"
        assert res["reason"] == "capture_invalid"
        assert counts["capture"] == 1
    test("capture_missing_evidence_scope_rejected", test_missing_evidence_scope)

    # 04. Actor Not Idle / Resident / Alive / Valid
    def test_actor_flags():
        for flag in ["actorValid", "alive", "resident", "idle"]:
            pol = policy_module.new()
            api, counts, _, _, _, _, _ = create_fixture({flag: False})
            res = run_policy(pol, api)
            assert res["status"] == "rejected"
            assert res["reason"] == "capture_invalid"
            assert counts["capture"] == 1
    test("actor_admission_flags_rejected", test_actor_flags)

    # 05. Initial Cancelled Flag
    def test_initial_cancelled():
        pol = policy_module.new()
        api, counts, _, _, _, _, _ = create_fixture({"cancelled": True})
        res = run_policy(pol, api)
        assert res["status"] == "cancelled_before_commit"
        assert res["reason"] == "cancelled"
        assert res["commitAttempted"] is False
        assert counts["capture"] == 1
    test("initial_cancelled_status", test_initial_cancelled)

    # 06. Cancelled At Each Boundary Before Commit
    def test_cancel_boundaries_before_commit():
        for target_boundary in [2, 3, 4, 5, 6]:
            pol = policy_module.new()
            call_c = 0
            def cancel_at_k(b_idx):
                api, counts, _, state, _, _, _ = create_fixture()
                old_cap = api["capture"]
                def cap_wrapper():
                    nonlocal call_c
                    call_c += 1
                    if call_c == b_idx:
                        state["cancelled"] = True
                    return old_cap()
                api["capture"] = cap_wrapper
                return api
            res = run_policy(pol, cancel_at_k(target_boundary))
            assert res["status"] == "cancelled_before_commit", f"Failed at boundary {target_boundary}"
            assert res["commitAttempted"] is False
    test("cancel_at_pre_and_barrier_boundaries", test_cancel_boundaries_before_commit)

    # 07. Cancelled After Commit Boundary
    def test_cancel_after_commit():
        pol = policy_module.new()
        call_c = 0
        api, counts, _, state, _, _, _ = create_fixture()
        old_cap = api["capture"]
        def cap_wrapper():
            nonlocal call_c
            call_c += 1
            if call_c == 7:  # boundary 7 is capture after commit
                state["cancelled"] = True
            return old_cap()
        api["capture"] = cap_wrapper
        res = run_policy(pol, api)
        assert res["status"] == "failed_after_commit"
        assert res["commitAttempted"] is True
        assert res["postVerified"] is False
        assert counts["inspect"] == 2  # post inspect was never invoked
    test("cancelled_after_commit_fails_closed", test_cancel_after_commit)

    # 08. Final Capture Cancelled
    def test_cancel_final_capture():
        pol = policy_module.new()
        call_c = 0
        api, counts, _, state, _, _, _ = create_fixture()
        old_cap = api["capture"]
        def cap_wrapper():
            nonlocal call_c
            call_c += 1
            if call_c == 10:  # final capture
                state["cancelled"] = True
            return old_cap()
        api["capture"] = cap_wrapper
        res = run_policy(pol, api)
        assert res["status"] == "failed_after_commit"
        assert res["commitAttempted"] is True
        assert res["postVerified"] is False
    test("cancel_at_final_capture", test_cancel_final_capture)

    # 09. Session Drift Rejection
    def test_session_drift():
        pol = policy_module.new()
        call_c = 0
        api, counts, _, state, _, _, _ = create_fixture()
        old_cap = api["capture"]
        def cap_wrapper():
            nonlocal call_c
            call_c += 1
            if call_c == 4:
                state["session"] = "drifted_session"
            return old_cap()
        api["capture"] = cap_wrapper
        res = run_policy(pol, api)
        assert res["status"] == "cancelled_before_commit"
        assert res["reason"] == "session_drift"
    test("session_drift_rejected", test_session_drift)

    # 10. Re-entry Rejected During Execution
    def test_reentry_rejected():
        pol = policy_module.new()
        inner_res = None
        api, counts, _, _, _, _, _ = create_fixture()
        old_insp = api["inspect"]
        def insp_wrapper(phase):
            nonlocal inner_res
            if phase == "barrier":
                inner_res = run_policy(pol, api)
            return old_insp(phase)
        api["inspect"] = insp_wrapper
        outer_res = run_policy(pol, api)
        assert outer_res["status"] == "completed"
        assert inner_res["status"] == "rejected"
        assert inner_res["reason"] == "busy"
    test("reentry_rejected_preserves_outer", test_reentry_rejected)

    # 11. Reset Invalidation During Inspect
    def test_reset_during_inspect():
        pol = policy_module.new()
        api, counts, _, _, _, _, _ = create_fixture()
        old_insp = api["inspect"]
        def insp_wrapper(phase):
            if phase == "pre":
                pol.reset()
            return old_insp(phase)
        api["inspect"] = insp_wrapper
        res = run_policy(pol, api)
        assert res["status"] == "cancelled_before_commit"
        assert res["reason"] == "reset_during_request"
        assert res["commitAttempted"] is False
    test("reset_during_inspect_invalidates", test_reset_during_inspect)

    # 12. Reset Invalidation During Commit
    def test_reset_during_commit():
        pol = policy_module.new()
        api, counts, _, _, _, _, _ = create_fixture()
        old_com = api["commit"]
        def com_wrapper():
            pol.reset()
            return old_com()
        api["commit"] = com_wrapper
        res = run_policy(pol, api)
        assert res["status"] == "failed_after_commit"
        assert res["reason"] == "reset_after_commit"
        assert res["commitAttempted"] is True
        assert res["postVerified"] is False
    test("reset_during_commit_fails_closed", test_reset_during_commit)

    # 13. Thrown Capture Releases Lock
    def test_thrown_capture_lock_reuse():
        pol = policy_module.new()
        api, _, _, _, _, _, _ = create_fixture()
        api["capture"] = lambda: lua.eval("error('capture_exploded')")
        res1 = run_policy(pol, api)
        assert res1["status"] == "rejected"
        # Next run should succeed on clean api
        clean_api, _, _, _, _, _, _ = create_fixture()
        res2 = run_policy(pol, clean_api)
        assert res2["status"] == "completed"
    test("thrown_capture_cleanup_and_reuse", test_thrown_capture_lock_reuse)

    # 14. Thrown Inspect Releases Lock
    def test_thrown_inspect_lock_reuse():
        pol = policy_module.new()
        api, _, _, _, _, _, _ = create_fixture()
        api["inspect"] = lambda p: lua.eval("error('inspect_exploded')")
        res1 = run_policy(pol, api)
        assert res1["status"] == "rejected"
        assert res1["reason"] == "inspect_threw"
        clean_api, _, _, _, _, _, _ = create_fixture()
        res2 = run_policy(pol, clean_api)
        assert res2["status"] == "completed"
    test("thrown_inspect_cleanup_and_reuse", test_thrown_inspect_lock_reuse)

    # 15. Thrown Commit Fails After Commit and Releases Lock
    def test_thrown_commit_lock_reuse():
        pol = policy_module.new()
        api, counts, _, _, _, _, _ = create_fixture()
        api["commit"] = lambda: lua.eval("error('commit_exploded')")
        res1 = run_policy(pol, api)
        assert res1["status"] == "failed_after_commit"
        assert res1["reason"] == "commit_threw"
        assert res1["commitAttempted"] is True
        assert counts["inspect"] == 2  # Post inspect skipped
        clean_api, _, _, _, _, _, _ = create_fixture()
        res2 = run_policy(pol, clean_api)
        assert res2["status"] == "completed"
    test("thrown_commit_fails_after_commit_and_lock_reuse", test_thrown_commit_lock_reuse)

    # 16. Actor Death After Commit Skips Post Read
    def test_actor_death_after_commit():
        pol = policy_module.new()
        call_c = 0
        api, counts, _, state, _, _, _ = create_fixture()
        old_cap = api["capture"]
        def cap_wrapper():
            nonlocal call_c
            call_c += 1
            if call_c == 7:  # capture immediately after commit
                state["alive"] = False
            return old_cap()
        api["capture"] = cap_wrapper
        res = run_policy(pol, api)
        assert res["status"] == "failed_after_commit"
        assert res["reason"] == "capture_invalid"
        assert res["commitAttempted"] is True
        assert res["postVerified"] is False
        assert counts["inspect"] == 2
    test("actor_death_after_commit_skips_post_read", test_actor_death_after_commit)

    # 17. Selected Same ID New Ref Rejected
    def test_same_id_new_ref_rejected():
        pol = policy_module.new()
        api, counts, _, _, _, _, _ = create_fixture()
        old_insp = api["inspect"]
        def insp_wrapper(phase):
            snap = old_insp(phase)
            if phase == "barrier":
                snap["item"] = lua.eval("{}")  # new table object
            return snap
        api["inspect"] = insp_wrapper
        res = run_policy(pol, api)
        assert res["status"] == "rejected"
        assert res["reason"] == "identity_drift"
    test("selected_same_id_new_ref_rejected", test_same_id_new_ref_rejected)

    # 18. Duplicate ID / Ref in Entries Rejected
    def test_duplicate_id_ref_rejected():
        pol = policy_module.new()
        api, counts, _, _, _, _, item = create_fixture()
        old_insp = api["inspect"]
        def insp_wrapper(phase):
            snap = old_insp(phase)
            # Duplicate item ref at entry 2
            snap["entries"][2]["ref"] = item
            snap["entries"][2]["id"] = 42
            return snap
        api["inspect"] = insp_wrapper
        res = run_policy(pol, api)
        assert res["status"] == "rejected"
        assert res["reason"] == "multiplicity_invalid"
    test("duplicate_id_ref_multiplicity_rejected", test_duplicate_id_ref_rejected)

    # 19. Root Count 64 vs 65
    def test_root_count_bounds():
        pol = policy_module.new()
        api, counts, _, _, _, _, _ = create_fixture()
        old_insp = api["inspect"]
        def insp_wrapper(phase):
            snap = old_insp(phase)
            snap["rootCount"] = 65
            return snap
        api["inspect"] = insp_wrapper
        res = run_policy(pol, api)
        assert res["status"] == "rejected"
        assert res["reason"] == "root_count_invalid"
    test("root_count_bounds_enforced", test_root_count_bounds)

    # 20. Backpointer Drift at Barrier
    def test_backpointer_drift_barrier():
        pol = policy_module.new()
        api, counts, _, _, _, _, _ = create_fixture()
        old_insp = api["inspect"]
        def insp_wrapper(phase):
            snap = old_insp(phase)
            if phase == "barrier":
                snap["selectedContainer"] = lua.eval("{}")
            return snap
        api["inspect"] = insp_wrapper
        res = run_policy(pol, api)
        assert res["status"] == "rejected"
        assert res["reason"] == "selected_container_not_root"
    test("backpointer_drift_barrier_rejected", test_backpointer_drift_barrier)

    # 21. Backpointer Drift at Post
    def test_backpointer_drift_post():
        pol = policy_module.new()
        api, counts, _, _, _, _, _ = create_fixture()
        old_insp = api["inspect"]
        def insp_wrapper(phase):
            snap = old_insp(phase)
            if phase == "post":
                snap["selectedContainer"] = lua.eval("{}")
            return snap
        api["inspect"] = insp_wrapper
        res = run_policy(pol, api)
        assert res["status"] == "failed_after_commit"
        assert res["reason"] == "selected_container_not_root"
    test("backpointer_drift_post_fails_after_commit", test_backpointer_drift_post)

    # 22. Hand Changed at Barrier (Primary Non-Empty)
    def test_hand_changed_at_barrier():
        pol = policy_module.new()
        api, counts, _, _, _, _, _ = create_fixture()
        old_insp = api["inspect"]
        def insp_wrapper(phase):
            snap = old_insp(phase)
            if phase == "barrier":
                snap["primary"] = lua.eval("{}")
            return snap
        api["inspect"] = insp_wrapper
        res = run_policy(pol, api)
        assert res["status"] == "rejected"
        assert res["reason"] == "primary_hand_not_empty"
    test("hand_changed_at_barrier_rejected", test_hand_changed_at_barrier)

    # 23. Incorrect Post Primary Mismatch
    def test_incorrect_post_primary():
        pol = policy_module.new()
        api, counts, _, _, _, _, _ = create_fixture()
        old_insp = api["inspect"]
        def insp_wrapper(phase):
            snap = old_insp(phase)
            if phase == "post":
                snap["primary"] = lua.eval("{}")  # Wrong item
            return snap
        api["inspect"] = insp_wrapper
        res = run_policy(pol, api)
        assert res["status"] == "failed_after_commit"
        assert res["reason"] == "primary_hand_mismatch"
    test("incorrect_post_primary_mismatch", test_incorrect_post_primary)

    # 24. Incorrect Post Secondary Non-Nil
    def test_incorrect_post_secondary():
        pol = policy_module.new()
        api, counts, _, _, _, _, _ = create_fixture()
        old_insp = api["inspect"]
        def insp_wrapper(phase):
            snap = old_insp(phase)
            if phase == "post":
                snap["secondary"] = lua.eval("{}")
            return snap
        api["inspect"] = insp_wrapper
        res = run_policy(pol, api)
        assert res["status"] == "failed_after_commit"
        assert res["reason"] == "secondary_hand_not_empty"
    test("incorrect_post_secondary_not_empty", test_incorrect_post_secondary)

    # 25. Incorrect Post Worn Stamp Drift
    def test_incorrect_post_worn_stamp():
        pol = policy_module.new()
        api, counts, _, _, _, _, _ = create_fixture()
        old_insp = api["inspect"]
        def insp_wrapper(phase):
            snap = old_insp(phase)
            if phase == "post":
                snap["wornStamp"] = "mutated_worn_stamp"
            return snap
        api["inspect"] = insp_wrapper
        res = run_policy(pol, api)
        assert res["status"] == "failed_after_commit"
        assert res["reason"] == "worn_stamp_drift"
    test("post_worn_stamp_drift_fails_after_commit", test_incorrect_post_worn_stamp)

    # 26. Callback API Mutation After Freeze Ignored
    def test_callback_api_mutation_frozen():
        pol = policy_module.new()
        api, counts, _, _, _, _, _ = create_fixture()
        old_cap = api["capture"]
        def cap_wrapper():
            # Attempt tampering with api table
            api["inspect"] = None
            api["commit"] = None
            return old_cap()
        api["capture"] = cap_wrapper
        res = run_policy(pol, api)
        assert res["status"] == "completed"
    test("callback_api_mutation_frozen_cleanly", test_callback_api_mutation_frozen)

    # 27. Hostile Metamethods on Snapshot Do Not Fire
    def test_hostile_metamethods_uncalled():
        pol = policy_module.new()
        api, counts, _, _, _, _, _ = create_fixture()
        old_insp = api["inspect"]
        def insp_wrapper(phase):
            snap = old_insp(phase)
            hostile_mt = lua.eval("""{
                __index = function() error('HOSTILE __index called') end,
                __eq = function() error('HOSTILE __eq called') end,
                __len = function() error('HOSTILE __len called') end,
                __tostring = function() error('HOSTILE __tostring called') end
            }""")
            lua.eval("setmetatable")(snap, hostile_mt)
            return snap
        api["inspect"] = insp_wrapper
        res = run_policy(pol, api)
        assert res["status"] == "completed"
    test("hostile_snapshot_metamethods_uncalled", test_hostile_metamethods_uncalled)

    # 28. Commit True But No Mutation Fails Closed
    def test_commit_true_no_mutation_fails():
        pol = policy_module.new()
        api, counts, _, _, _, _, _ = create_fixture({"commit_mutates": False})
        res = run_policy(pol, api)
        assert res["status"] == "failed_after_commit"
        assert res["reason"] == "primary_hand_mismatch"
        assert res["commitAttempted"] is True
        assert res["postVerified"] is False
    test("commit_true_no_mutation_fails_closed", test_commit_true_no_mutation_fails)

    # 29. Scalar Only Output Structure (No Leaked Handles)
    def test_scalar_only_output():
        pol = policy_module.new()
        api, counts, _, _, _, _, _ = create_fixture()
        res = run_policy(pol, api)
        for k in res:
            v = res[k]
            assert isinstance(v, (str, int, float, bool)), f"Disallowed non-scalar type {type(v)} at key {k}"
    test("scalar_only_output_no_leaked_handles", test_scalar_only_output)


    # Codex review cases: strengthen the generated coverage with independent races.
    def test_all_late_cancellation():
        for boundary in range(7, 11):
            pol = policy_module.new()
            api, counts, _, state, _, _, _ = create_fixture()
            old = api["capture"]
            def capture():
                if counts["capture"] + 1 == boundary:
                    state["cancelled"] = True
                return old()
            api["capture"] = capture
            r = run_policy(pol, api)
            assert r["status"] == "failed_after_commit" and r["postVerified"] is False
            assert counts["capture"] == boundary and counts["commit"] == 1
    test("review_all_late_cancel_boundaries_sticky", test_all_late_cancellation)

    def test_throw_each_boundary():
        for kind, maximum in (("capture", 10), ("inspect", 3), ("commit", 1)):
            for index in range(1, maximum + 1):
                pol = policy_module.new()
                api, counts, _, _, _, _, _ = create_fixture()
                old = api[kind]
                throwing = lua.eval("""function(f, index)
                    local n=0
                    return function(...)
                        n=n+1
                        if n==index then error('SECRET callback error') end
                        return f(...)
                    end
                end""")
                api[kind] = throwing(wrap(old), index)
                r = run_policy(pol, api)
                before = kind == "capture" and index <= 6 or kind == "inspect" and index <= 2
                assert r["status"] == ("rejected" if before else "failed_after_commit"), (kind, index, dict(r.items()))
                assert r["postVerified"] is False
                if kind == "commit":
                    assert counts["capture"] == 6 and counts["inspect"] == 2
                clean = create_fixture()[0]
                assert run_policy(pol, clean)["status"] == "completed"
                assert "SECRET" not in str(dict(r.items()))
    test("review_every_callback_throw_and_lock_reuse", test_throw_each_boundary)

    def test_reset_each_capture():
        for index in range(1, 11):
            pol = policy_module.new()
            api, counts, _, _, _, _, _ = create_fixture()
            old = api["capture"]
            def capture():
                result = old()
                if counts["capture"] == index:
                    pol.reset()
                return result
            api["capture"] = capture
            r = run_policy(pol, api)
            assert r["status"] == ("cancelled_before_commit" if index <= 6 else "failed_after_commit")
            assert r["postVerified"] is False and counts["capture"] == index
    test("review_reset_every_capture_boundary", test_reset_each_capture)

    def test_commit_reentry_reset():
        pol = policy_module.new()
        api, counts, _, _, _, _, _ = create_fixture()
        old = api["commit"]
        inner = []
        def commit():
            pol.reset()
            inner.append(run_policy(pol, api))
            return old()
        api["commit"] = commit
        r = run_policy(pol, api)
        assert r["status"] == "failed_after_commit"
        assert inner[0]["reason"] == "busy" and counts["commit"] == 1
        assert run_policy(pol, create_fixture()[0])["status"] == "completed"
    test("review_commit_reentry_after_reset_keeps_lock", test_commit_reentry_reset)

    def test_valid_root64():
        pol = policy_module.new()
        api = create_fixture()[0]
        old = api["inspect"]
        def inspect(phase):
            snap = old(phase)
            snap["rootCount"] = 64
            for i in range(3, 65):
                snap["entries"][i] = lua.table(ref=lua.table(), id=100 + i)
            return snap
        api["inspect"] = inspect
        assert run_policy(pol, api)["status"] == "completed"
    test("review_actual_valid_64_entry_root", test_valid_root64)

    def test_selected_duplicates_post():
        for variant in ("id_only", "ref_only", "both", "missing"):
            pol = policy_module.new()
            api, counts, _, _, _, _, item = create_fixture()
            old = api["inspect"]
            def inspect(phase):
                snap = old(phase)
                if phase == "post":
                    if variant == "missing":
                        snap["entries"][1]["ref"] = lua.table()
                        snap["entries"][1]["id"] = 98
                    else:
                        if variant in ("ref_only", "both"):
                            snap["entries"][2]["ref"] = item
                        if variant in ("id_only", "both"):
                            snap["entries"][2]["id"] = 42
                return snap
            api["inspect"] = inspect
            r = run_policy(pol, api)
            assert r["status"] == "failed_after_commit" and not r["postVerified"]
            assert counts["commit"] == 1
    test("review_post_id_ref_multiplicity_all_variants", test_selected_duplicates_post)

    def test_snapshot_retcon():
        for phase, boundary in (("pre", 3), ("barrier", 5), ("post", 9)):
            pol = policy_module.new()
            api, counts, _, _, _, root, _ = create_fixture()
            old_i, old_c = api["inspect"], api["capture"]
            held = [None]
            def inspect(p):
                snap = old_i(p)
                if p == phase:
                    snap["selectedContainer"] = lua.table()
                    held[0] = snap
                return snap
            def capture():
                result = old_c()
                if counts["capture"] == boundary:
                    held[0]["selectedContainer"] = root
                return result
            api["inspect"], api["capture"] = inspect, capture
            r = run_policy(pol, api)
            assert r["status"] == ("failed_after_commit" if phase == "post" else "rejected")
            assert r["reason"] == "selected_container_not_root"
    test("review_after_capture_cannot_rewrite_returned_snapshot", test_snapshot_retcon)

    def test_opaque_userdata():
        pol = policy_module.new()
        api = create_fixture()[0]
        old = api["inspect"]
        actor, root, item = object(), object(), object()
        replacement = object()
        def inspect(phase):
            snap = old(phase)
            snap["actor"], snap["root"], snap["item"] = actor, root, item
            snap["selectedContainer"] = root
            snap["entries"][1]["ref"] = item
            if phase == "post":
                snap["primary"] = item
            return snap
        api["inspect"] = inspect
        assert run_policy(pol, api)["status"] == "completed"
        api = create_fixture()[0]
        old = api["inspect"]
        def drift(phase):
            snap = inspect(phase)
            if phase == "barrier":
                snap["item"] = replacement
            return snap
        api["inspect"] = drift
        r = run_policy(pol, api)
        assert r["reason"] == "identity_drift", dict(r.items())
    test("review_opaque_userdata_exact_reference_identity", test_opaque_userdata)

    def test_missing_flags_and_scope():
        keys = ("evidenceScope", "eventIsolation", "session", "revision", "cancelled",
                "actorValid", "alive", "resident", "idle")
        for key in keys:
            pol = policy_module.new()
            api = create_fixture()[0]
            old = api["capture"]
            def capture():
                result = old()
                result[key] = None
                return result
            api["capture"] = capture
            assert run_policy(pol, api)["status"] == "rejected"
        for phase in ("pre", "barrier", "post"):
            for key in ("scope", "directContains", "melee", "oneHanded",
                        "conditionValid", "attached", "worn", "activationDependent",
                        "forceDropHeavy", "loadoutConflict"):
                pol = policy_module.new()
                api = create_fixture()[0]
                old = api["inspect"]
                def inspect(p):
                    result = old(p)
                    if p == phase:
                        result[key] = None
                    return result
                api["inspect"] = inspect
                r = run_policy(pol, api)
                assert r["status"] == ("failed_after_commit" if phase == "post" else "rejected")
    test("review_missing_admission_and_semantic_flags", test_missing_flags_and_scope)

    def test_numbers_and_malformed_entries():
        for field in ("rootCount", "itemId"):
            for value in (float("nan"), float("inf"), -float("inf"), -1, 1.5, "2"):
                pol = policy_module.new()
                api = create_fixture()[0]
                old = api["inspect"]
                def inspect(phase):
                    snap = old(phase)
                    snap[field] = value
                    return snap
                api["inspect"] = inspect
                assert run_policy(pol, api)["status"] == "rejected"
        for bad in (None, 5, "invalid", lua.table(ref=lua.table(), id="42")):
            pol = policy_module.new()
            api = create_fixture()[0]
            old = api["inspect"]
            def inspect(phase):
                snap = old(phase)
                snap["entries"][1] = bad
                return snap
            api["inspect"] = inspect
            assert run_policy(pol, api)["status"] == "rejected"
    test("review_nonfinite_numbers_and_malformed_entries", test_numbers_and_malformed_entries)

    def test_invalid_actor_all_post_boundaries():
        for index in range(7, 11):
            for flag in ("actorValid", "alive", "resident", "idle"):
                pol = policy_module.new()
                api, counts, _, state, _, _, _ = create_fixture()
                old = api["capture"]
                def capture():
                    if counts["capture"] + 1 == index:
                        state[flag] = False
                    return old()
                api["capture"] = capture
                r = run_policy(pol, api)
                assert r["status"] == "failed_after_commit" and not r["postVerified"]
                assert counts["capture"] == index
                assert counts["inspect"] == (2 if index <= 8 else 3)
    test("review_invalid_actor_no_unsafe_post_reads", test_invalid_actor_all_post_boundaries)

    def test_hostile_api_marker_entry_handles():
        trap = lua.eval("""{__index=function() error('meta') end,
            __eq=function() error('meta') end, __len=function() error('meta') end,
            __tostring=function() error('meta') end}""")
        meta = lua.eval("setmetatable")
        pol = policy_module.new()
        api, _, _, _, actor, root, item = create_fixture()
        old_c, old_i = api["capture"], api["inspect"]
        for handle in (actor, root, item):
            meta(handle, trap)
        def capture():
            return meta(old_c(), trap)
        def inspect(phase):
            snap = old_i(phase)
            meta(snap["entries"], trap)
            meta(snap["entries"][1], trap)
            meta(snap["entries"][2], trap)
            return meta(snap, trap)
        api["capture"], api["inspect"] = capture, inspect
        meta(api, trap)
        assert run_policy(pol, api)["status"] == "completed"
    test("review_raw_access_hostile_all_contract_tables", test_hostile_api_marker_entry_handles)

    print(f"\nRESULT {passed_count} manual equip checks passed")
    assert passed_count == total_count and total_count >= 25

if __name__ == "__main__":
    main()
