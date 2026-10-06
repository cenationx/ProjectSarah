# Project Sarah: Bounded Offline Manual Equip Adapter Design Proposal (Baseline `3692172`)

## 1. Executive Scope & Architectural Candidate Evaluation
- **Baseline:** Main branch checkpoint `3692172`. Game JAR hash `E1A69EB743EDE60B213A0FE7F8B83D4FCAB773036D256CC4543A336F3B058A33` verified unchanged. Prior test baseline (649 offline checks across 15 suites + 11 runner assertions + 19 preflight checks) unchanged and not rerun; Lupa Lua55 and Python preflight results do not establish native Kahlua runtime compatibility.
- **Scope:** Pure preparatory design proposal for a narrow, dormant manual equipment adapter. No source code implementation, generic helper forest, native fixture framework, or wiring is authorized in this batch. User is explicitly not ready for live testing; external/model AI remains on hold.

### Comparison of Approaches A, B, and C

| Candidate Approach | Inspected Execution Characteristics | Identified Hazards & Coupled Logic | Architectural Decision |
| :--- | :--- | :--- | :--- |
| **Option A: Reuse `ISEquipWeaponAction`** | Standard Player Timed Action | Unconditional `getPlayerInventory(playerNum).refreshBackpacks(242)`. Directly calls `getPlayerHotbar(playerNum).chr.removeAttachedItem(48)`. Drops heavy items to world grid (`forceDropHeavyItems(175)`). Native `perform` advances queue *before* `complete` commits mutations. | **REJECTED.** Inspected coupling can advance the queue before equipment settlement and includes conditional world floor drops. (Rejection is based on inspected coupling, not an empirical crash claim). |
| **Option B: Custom Timed Action** | Subclass extending `ISBaseTimedAction` | Still inherits `BaseAction.perform` (line 196), which couples player progress UI via `UIManager.trySetProgressBarValue` using `(IsoPlayer)chr.getIndex()` (Code 11). Retains queue advance before mutation. | **NOT SELECTED.** Avoids full player action, but inherits native progress bar coupling and asynchronous queue complexity. (Not universally impossible, but deferred). |
| **Option C: Direct Native Setter Commit** | Synchronous call to `IsoGameCharacter.setPrimaryHandItem` | Bypasses timed action queues, player hotbar detachment, and backpack refreshes. Retains engine equip parents, ballistics cache resets, and model updates. Fires synchronous `OnEquipPrimary` event *after* field write. | **PREFERRED DORMANT CANDIDATE.** Minimal discrete native state transition. Preferred for offline specification, but **not proven free of player UI coupling**. Requires strict refusal baseline. |

---

## 2. Static Native Insights: Setter Commit & Event Dispatch Hazards

Direct bytecode corroboration of `IsoGameCharacter.setPrimaryHandItem` (line 2987) establishes the internal commit sequence:
1. Early return if target item is identical to existing `leftHandItem` reference.
2. Releases prior animal holding; checks `checkAnimalAttachedToRope(newitem)` if actor is `IsoPlayer`.
3. Updates `equipParent` on old and new items (registering flag if new item matches secondary hand).
4. Assigns internal field `leftHandItem` at **Code offset 143**.
5. Fires engine event `LuaEventManager.triggerEvent("OnEquipPrimary", this, item)` at **Code offset 156**.
6. Calls `resetEquippedHandsModels()` at **Code offset 160**.

### The Post-Mutation Event & UI Cross-Talk Hazard
Because `leftHandItem` is written at offset 143 **before** `OnEquipPrimary` triggers at offset 156, any failure, cancellation, or runtime exception during event dispatch occurs *post-mutation*. It cannot be cleanly cancelled before commit; the adapter must record a truthful partial state (`failed_after_commit`) without attempting blind rollbacks.

Furthermore, inspected event subscribers present severe cross-player coupling risks:
- `FishingHandler.onEquipPrimary` (line 15): Checks `if player:isLocal() then handleFishing(player)`. `handleFishing` (line 24) retrieves the fishing manager keyed by `player.getPlayerNum()`. **If the new item is NOT a fishing rod and a manager exists at that key, it destroys and nils the manager.** Excluding fishing rods does *not* protect the manager; equipping a non-rod actively destroys an existing manager.
- `IsoGameCharacter.isLocal` (line 13595): Corroborated bytecode reads `PZOptional.ifPresent(tryGetECSComponent(NetworkComponent), true, NetworkComponent.isLocal)`, defaulting to `true` when the component is absent. `isLocal` is **not** a synonym for `isLocalPlayer` or `notNPC`.
- `IsoPlayer.getPlayerNum` (line 978): Delegates to `getIndex` (line 972), reading `playerIndex`. Actual Sarah ECS components and player indices are unobserved in live runtime. Changing `playerIndex` or `isLocal` to bypass gates is strictly prohibited.

*Rule:* Caller passing `eventSafe=true` cannot establish event safety. A source implementation must **default to refuse execution** unless runtime isolation prerequisites are independently established by audited platform context.

---

## 3. Admission Refusal Rules & Semantic Allowlist

### Admission Refusals (Fail-Closed Gates)
- **Active Commands / Actions:** Refuse if Sarah is currently executing a timed action, pathfinding, moving, aiming, or if a prior stop failed. Never interrupt, auto-queue, or restore previous orders.
- **Actor State:** Refuse if actor is null, non-resident, dead, or if the caller session epoch is invalid.
- **Hands Not Empty:** Refuse if `getPrimaryHandItem() ~= nil` or `getSecondaryHandItem() ~= nil`. Both hands must be completely empty.
- **Prior Loadout Conflict:** Refuse if Sarah wears a back item tagged `REPLACE_PRIMARY` (conservative exclusion of clothing replacement branches; direct setter does not execute conversion, but loadout is disallowed).

### Target Item Allowlist (Slice 1: Single Owned One-Handed Melee Weapon)
- **Tripartite Root Ownership:** Must confirm direct root containment (`root:contains(item)` via Code 5), consistent backpointer (`item:getContainer() == root`), and exact ID multiplicity within a bounded root inventory count budget. Reject nested sub-containers, backpointer drift, or duplicate ID collisions.
- **Class & Capability:** Must be an instance of candidate class `HandWeapon` with `isTwoHandWeapon() == false` and `isRequiresEquippedBothHands() == false`.
- **Semantic Exclusions:** Refuse if inspected `isForceDropHeavyItem` candidate is true; refuse firearms, fishing rods, radios, musical instruments, flashlights, animals, sprayers, activation-dependent items, and attached/hotbar items. (Do not query wrong-player hotbar as proof of non-attachment).

---

## 4. English Phase-Aware Execution Sequence (Design Pseudocode)

Execution is synchronous and immediate. It does not spawn queued pseudo-async states. All work is enclosed in a protected execution block with guaranteed cleanup.

```
[Phase 1: Entry & Lock] ──► [Phase 2: Pre-Commit Checks] ──► [Phase 3: Final Barrier]
                                                                      │
[Phase 6: Result & Exit] ◄── [Phase 5: Post-State Audit] ◄── [Phase 4: Native Commit]
```

### Phase 1: Entry & Protected Lock
- Freeze caller contract and callbacks.
- Verify private `busy` lock. If busy, immediately return scalar `{ status = "rejected", reason = "adapter_busy" }` without modifying outer pass.
- Acquire private `busy` lock (held through all exit paths and guaranteed cleanup).
- Initialize `commitAttempted = false`.

### Phase 2: Pre-Commit Boundary Checks
- Check cancellation and session token. If cancelled/invalid, abort as `cancelled_before_commit`.
- Deduct precharge before each risky inspect call.
- Separately invoke read getters: verify actor is alive and resident; verify both hands are empty.
- Perform Tripartite Root Ownership audit: direct containment, matching container backpointer, and ID multiplicity.
- Validate target item against semantic allowlist.
- Check cancellation and session token after each inspection step.

### Phase 3: Final Pre-Commit Barrier
- Perform immediate final check of session token and cancel signal.
- If cancelled or drifted, abort with `{ status = "cancelled_before_commit", reason = "cancelled_at_barrier" }`.

### Phase 4: Native Setter Commit
- Mark `commitAttempted = true`.
- Invoke native setter `actor:setPrimaryHandItem(item)` within protected call.
- Note: Internal field `leftHandItem` is assigned at Code offset 143; `OnEquipPrimary` event fires at Code offset 156. If event callbacks throw, mutate state, or signal stop, execution proceeds to Phase 5 as a post-mutation event.

### Phase 5: Post-Commit State Audit
- Assess current actor validity. If actor is null, dead, unloaded, or non-resident, **skip all post-state property reads** and record `postVerified = false`.
- If actor is valid and resident, execute minimum read-only inspection: verify `actor:getPrimaryHandItem()` matches the trusted target item handle; verify `actor:getSecondaryHandItem() == nil`; verify target item remains contained in root inventory with matching backpointer; verify required worn slots remain intact.

### Phase 6: Final Barrier & Safe Teardown
- Execute final session and cancellation check.
- If `commitAttempted` is true and any post-check, event callback, or final barrier failed: return `{ status = "failed_after_commit", reason = "postcondition_unverified", commitAttempted = true, postVerified = false }`.
- If all checks pass under valid final barrier: return `{ status = "completed", reason = "verified_commit", commitAttempted = true, postVerified = true }`.
- Guaranteed cleanup: release private `busy` lock. Ensure zero raw error objects, tokens, or native item handles leak into the scalar result record.

---

## 5. Declared Boundary Operation Manifest

Operations are categorized by boundary type without invented timing or complete callback assumptions:

| Phase | Target Object & Operation | Category | Underlying Engine Impact & Logging Risks |
| :--- | :--- | :--- | :--- |
| **Phase 1** | Local scalar checks | Adapter Internal | Zero engine calls; validates frozen contract. |
| **Phase 2** | `actor:getPrimaryHandItem()`, `getSecondaryHandItem()` | Userdata Getter | Field reads; safe if actor resident. |
| **Phase 2** | `inv:contains(item)`, `item:getContainer()` | Userdata Method & Field | Direct `ArrayList.contains` (Code 5) and field read (Code 1). Unbounded internal list scan; bounded by root count check. |
| **Phase 4** | `actor:setPrimaryHandItem(item)` | Native Method | Mutates field (Code 143), triggers `OnEquipPrimary` (Code 156), updates models (Code 160). |
| **Phase 4** | Engine `OnEquipPrimary` subscriber callbacks | Lua Event Dispatch | May execute arbitrary mod logic; risk of `FishingHandler` manager destruction or human UI cross-talk. |
| **Phase 5** | `actor:getPrimaryHandItem()`, `inv:contains(item)` | Userdata Getter & Method | Read-only post-check (conditional on resident actor). Engine exceptions may be consumed by `MethodCaller`. |

---

## 6. Deferred Native Acceptance Matrix & Conclusion

| Deferred Case | Failure Condition / Invariant Tested | Verification Level |
| :--- | :--- | :--- |
| **Case 1: Stop Before Commit** | Cancel signal received during Phase 2. Verify clean refusal (`cancelled_before_commit`) with zero hand mutation. | Native Deferred |
| **Case 2: Stop During / After Setter** | Cancel signal or event error occurs during Phase 4/5. Verify adapter reports `failed_after_commit` without automated rollback. | Native Deferred |
| **Case 3: Re-entry Rejection** | Re-entrant call attempted during Phase 4 event window. Verify inner call returns `rejected` without altering outer pass. | Native Deferred |
| **Case 4: Getter Error Privacy** | Userdata getter throws during Phase 2. Verify lock is released and zero raw error strings leak. | Native Deferred |
| **Case 5: Actor Death / Unload** | Actor dies or chunk unloads during setter invocation. Verify post-reads are skipped and `failed_after_commit` is returned. | Native Deferred |
| **Case 6: ID Replacement / Collision** | Item removed or replaced by another sharing same ID. Verify Pre-Commit Gate halts settlement. | Native Deferred |
| **Case 7: Local Player UI Independence** | Monitor human player inventory, hotbar, and selection state during NPC equip. Verify zero selection loss or state mutation. | Native Deferred |
| **Case 8: Fishing Manager Survival** | Human player has active fishing manager (`playerNum == 0`). Verify NPC equip does not destroy manager via `FishingHandler`. | Native Deferred |
| **Case 9: Secondary Hand Preservation** | Verify secondary hand remains strictly `nil` throughout execution. | Native Deferred |
| **Case 10: Item Conservation** | Verify item count and multiplicity conserved; zero items dropped to world floor. | Native Deferred |
| **Case 11: Full Restart Persistence** | Verify equipped hand reference survives script reload (`reloadLua`), world streaming, and full game restart. | Native Deferred |

### Conclusion & Next Step
- Direct setter invocation (Option C) is the preferred dormant candidate, but cannot be claimed free of UI or event coupling.
- **Recommended Next Step:** Author a concrete, dormant source file (`ManualEquipAdapter.lua`) implementing this phase sequence with a default-refusal baseline for unverified event/UI environments, without generic helper frameworks or live deployment.
## 7. Codex review requirements (binding qualifications)

This is a design candidate, not approval of a working native adapter. The English
sequence above is incomplete without these requirements. No adapter was implemented.

- All admission, lookup, getter, setter and verification operations belong inside
  protected execution with private lock cleanup. Re-entry must not clear or reset
  the outer request. Freeze injected callbacks; reject malformed contracts.
- Check existing Commands/Driver ownership, stopping failures, native queue/path,
  actor/session validity and cancellation. Never replace a running command,
  automatically Stop it, or resume it after equip.
- Charge method lookup separately from invocation before either boundary.
  Root collection enumeration and ID multiplicity need an explicit entry cap and
  a verified native access path. Count limits do not bound internal engine cost,
  event listener work, allocation or elapsed time. The manifest in section 5 is
  illustrative and incomplete, not an executable accounting specification.
- Revalidate after each risky boundary and immediately before the setter.
  A cancellation-only final check cannot establish unchanged ownership, hand
  state or item identity. No world lock or atomic snapshot is established.
- Set commitAttempted before the sole mutating call. Stop during a synchronous
  setter cannot interrupt it or guarantee zero mutation. Even an error before
  the inspected field assignment remains conservatively failed_after_commit
  once the call was attempted, because equip-parent changes occur earlier.
- Verify session/actor admission before post-state dereferences; skip unsafe
  reads if identity, life or residency cannot be established. Protect each
  verification boundary and recheck cancellation/session afterward.
- Post-state verification must include primary trusted reference, secondary nil,
  direct root membership, matching backpointer, bounded ID multiplicity and
  required unchanged worn state. End with a fresh validity/cancellation barrier.
  If any condition is unknown, do not report completed.
- A bridge pcall success does not prove getter or setter success: inspected
  MethodCaller can log and consume invocation errors. Separate native error-log
  acceptance remains required. Results contain only scalar status/reason and
  commitAttempted/postVerified; never raw errors, handles or caller tokens.
- No rollback, automatic retry, direct field writes, event suppression, modified
  playerIndex/isLocal, borrowed player UI context, or manual timed-action complete.
- Semantic method names above remain candidates with actual Lua exposure and
  overload selection unverified. No invented predicate, boolean eventSafe flag
  or caller assertion may certify the native environment.
- The fishing subscriber concern is conditional, not observed harm. Selected
  handlers are not an exhaustive event audit. isLocal defaults true without the
  network component; Sarah's actual component/index and all installed listeners
  are unobserved. Removing fishing rods from the allowlist does not protect an
  existing manager from the non-rod branch.

The preferred candidate is a single explicit owned one-handed melee item in an
empty primary/secondary loadout, applied synchronously with no timed-animation
promise. Clothing, transfers, auto-selection and combat remain outside this slice.

Next bounded Gemini coding task: draft the dormant manual-equip request/state
logic against a concrete injected operation contract, with meaningful rejection,
re-entry, cancellation and post-mutation failure tests. No native resolver,
production import, event registration or runtime admission certificate may be
invented. Unverified native gates must refuse; Codex remains the sole checkout
editor/reviewer. If the contract cannot specify the ownership/event-isolation
gate truthfully, retain this proposal rather than adding placeholder frameworks.

Evidence boundary: sanitized static observations and reviewed design only.
Native equip, Follow/rendering, independent light and save/restart acceptance
remain pending. Prior 649 suite checks +11 runner +19 preflight passed at the
earlier implementation checkpoint; not rerun for this documentation-only batch.
No game launch, deployment, save or settings changes. External/model AI ON HOLD.