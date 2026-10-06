# Project Sarah: Bounded Offline Equipment Action Research & Native Bridge Review (Revised)

## 1. Executive Scope & Evidence Baseline
- **Baseline:** Started clean main `c30e5db`; prior baseline649 offline checks/15 suites plus11 runner and19 preflight self-tests. Suite execution is Lupa Lua55; Python runner/preflight self-tests are separate. No suites rerun for this source-unchanged research batch. Zero native equipment acceptance has occurred.
- **Operational Boundary:** Strictly bounded offline research review. No code, helpers, auto-equipment heuristics, inventory transfers, or combat routines are proposed or authorized. Codex retains exclusive checkout editing ownership.
- **Preparatory Scope Notice:** This document synthesizes static inspection of installed scripts and decompiled bytecode (`JAR SHA256: E1A69EB743EDE60B213A0FE7F8B83D4FCAB773036D256CC4543A336F3B058A33`). It does **not** advance native core acceptance or prove runtime compatibility for non-player characters (NPCs).
- **User Directives:** Live testing, game execution, deployments, save/setting modifications, and external/model AI remain explicitly deferred.

---

## 2. Statically Narrowed Engine Routing: `perform` vs. `complete`

Fresh bytecode corroboration of `LuaTimedActionNew.java` and `IsoGameCharacter.java` resolves the high-level native execution order in single-player:

1. **Native Call Sequence Narrowed:** In `IsoGameCharacter.updateInternal` (lines 8318–8330; Code offsets 1334–1344), action finish triggers `BaseAction.perform` (Code 1334) followed by `BaseAction.complete` (Code 1344 if not `GameClient.client`). In `LuaTimedActionNew.java`, `perform` (line 169) invokes `BaseAction.perform` then Lua `perform` via `LuaCaller.pcall` (Code 28, 53). Subsequently, `complete` (line 179) invokes `BaseAction.complete` (line 203, empty) then Lua `complete` via `pcall` (Code 28, 58). In single-player, **native `perform` runs before native `complete`**.
2. **The Queue Advance Hazard:** `ISBaseTimedAction.perform` (line 68) calls `queue.onCompleted`, which advances the queue and starts the next action *before* `complete` executes. Therefore, the engine queue may dispatch a subsequent action before equipment mutations are committed. Future completion settlement must be anchored to verified post-commit state, never to `perform` or queue advancement alone.
3. **Discarded Returns & Exception Handling:** `LuaTimedActionNew` discards Lua return arrays at call sites. Furthermore, `MethodCaller.call` catches `Throwable`, logs it to disk, and returns void/nil without rethrowing (though logging itself may throw). Consequently, `pcall == true` does not prove successful mutation, and engine callbacks cannot be relied upon to signal failure. Callers must never issue a manual `complete` alongside engine dispatch (risk of double-commit).

---

## 3. Lifecycle, UI & Mutation Risk Matrix

| Action Lifecycle Stage | `ISEquipWeaponAction.lua` Observed Facts | `ISWearClothing.lua` Observed Facts | Bridge Risk & Caller Assessment |
| :--- | :--- | :--- | :--- |
| **Validation (`isValid`)** | **[Static Fact]** Line 5 rebinds `self.item = character.inventory.getItemWithID(item.ID)`.<br>**[Native Gate]** Lookup depth in Java uninspected. `contains == true` does not prove direct root container ownership. | **[Static Fact]** Line 5 rejects `nil` or broken items. In single-player, checks `inventory.contains(item)`.<br>**[Native Gate]** Identity and nested container semantics unknown. | **[Recommendation]** Caller must establish direct root ownership and reacquire the selected item ID before creation and immediately before commit. `getContainer` versus inventory reference comparison is an inspected candidate contract, with native lookup/wrapper behavior still to verify. |
| **Start & Queue (`start`, `new`)** | **[Static Fact]** `new` line 269 calls `getPlayerHotbar` on non-server. Line 48 (`animEvent` `detachConnect`) calls `getPlayerHotbar(playerNum).chr.removeAttachedItem`. | **[Static Fact]** Line 164 sets `fromHotbar=true` (comment: "disable hotbar update"), `clothingAction=true`. `start` sets body location variables and audio. | **[Native Gate]** Delivery of `animEvent` `detachConnect` to NPCs is unverified. Whether `fromHotbar=true` completely isolates hotbars is unproven. |
| **Execution (`perform`)** | **[Static Fact]** Line 113 executes sound/job cleanup, `container:drawDirty()`, conditional backpack refresh (line 129 if wearable container). Does not mutate hand fields. | **[Static Fact]** Line 82 executes sound/job cleanup, `container:drawDirty()`, conditional backpack refresh (line 89), clothing update event, `ISInventoryPage.renderDirty` (line 96). | **[Static Fact]** `BaseAction.perform` (line 196) calls `UIManager.trySetProgressBarValue` using `(IsoPlayer)chr.getIndex()` (Code 11). Native base couples player progress UI. |
| **Settlement (`complete`)** | **[Static Fact]** Line 138 rejects already equipped. Handles `BACK REPLACE_PRIMARY` sprayer conversion (`ISClothingExtraAction`), worn removal, `forceDropHeavyItems` (line 175, drops items to world grid!), primary/secondary hand mutation, and unconditional non-server `getPlayerInventory(playerNum).refreshBackpacks(242)`. No fresh ownership re-check. | **[Static Fact]** Line 101 rejects already worn. `REPLACE_PRIMARY` mutates primary hand; container path updates hands and calls `setWornItem`; ordinary clothing calls `setWornItem`; `HAT`/`FULL_HAT` resets hair model. No fresh broken or ownership re-check. | **[Recommendation]** Pre-existing loadout (two-handed weapons, heavy items, replacement sprayers) induces destructive side-effects (world floor drops). Must verify hands empty prior to execution. |
| **Cancellation (`stop`)** | **[Static Fact]** Line 62 resets job delta, calls `restoreWeaponType`, and invokes `Base.stop` (line 63 resets queue). | **[Static Fact]** Line 76 resets job delta, stops sounds, and invokes `Base.stop`. | **[Native Gate]** `Stop` does not guarantee immediate native thread interruption or rollback if native commit is already in flight. |

---

## 4. Sliced Scope Definition: Minimal Safe Candidate Slices

### Slice 1: Single Owned One-Handed Melee Weapon (Primary Hand)
- **Pre-Conditions (Prior Loadout Refusal):**
  - Sarah's hands must be completely empty (`getPrimaryHandItem() == nil` and `getSecondaryHandItem() == nil`).
  - Target item must have verified direct root inventory ownership; container comparison is a candidate check, not proven native identity.
  - Target item must be an instance of candidate class `HandWeapon` with `isTwoHandWeapon() == false` and `isRequiresEquippedBothHands() == false`.
  - Refuse candidate if inspected `isForceDropHeavyItem` candidate is true or if it has attached hotbar status (`isItemAttached() == true`).
  - Exclude replacement/sprayer candidates and refuse a pre-existing back garment tagged REPLACE_PRIMARY, since that prior loadout can trigger conversion even when the new item is ordinary. Exclude firearm/activation/clothing/container cases from the first semantic allowlist; actual supported item types remain to be selected and verified.
  - Candidate item ID, container handle, and condition must be confirmed valid immediately prior to action creation.

### Slice 2: Single Ordinary Owned Garment (Deferred Follow-Up)
- **Pre-Conditions:** Target body location must be completely empty (`getWornItem(loc) == nil`). Item must reside in root inventory, must not be broken, must not be a wearable container, and must not occupy head/hair locations (`HAT`, `FULL_HAT`, `MASK`).

---

## 5. Lifecycle Proposal, UI Isolation & Conservation Invariants

```
[Idle] ──► [Accepted] ──► [Running] ──► [Pre-Commit Gate] ──► [Committing] ──► [Completed / Failed Partial]
                                │                │
                                └──► [Cancelled] └──► [Failed: Revalidation Error]
```

### Proposed Governance Rules (Design Only — No Implemented Hook)
1. **Cancellation & Commit Boundary:** Before commit, cancellation must be observed by the proposed pre-commit gate and must prevent the mutation; that gate is not implemented by these existing scripts. Calling Stop or clearing the queue alone is not proof that an in-flight commit is prevented. After commit begins, Stop cannot be assumed to undo native state; callers must never attempt blind rollbacks. If settlement fails, record the truthful partial state and fail closed.
2. **UI Isolation Standard:** Rather than requiring zero global UI redraws (unrealistic due to global dirty flags), verification must enforce **no mutation of human player hotbars, inventory slots, or selection states**.
3. **Item Conservation Invariant:** Full runtime inventory scans are rejected. For controlled testing, capture a bounded snapshot of the selected item ID multiplicity, root inventory presence, hand/worn references, and verify zero unexpected drops on the world grid.

---

## 6. Deferred Test Matrix & Next Gate

| Deferred Case | Failure Condition / Invariant Tested | Verification Level |
| :--- | :--- | :--- |
| **Case 1: Stale Item / ID Replacement** | Item transferred or ID replaced during `Running`. Verify Pre-Commit Gate halts settlement without hand mutation. | Native Deferred |
| **Case 2: Broken Condition Mid-Action** | Item condition drops to zero while `Running`. Verify Pre-Commit Gate rejects equip. | Native Deferred |
| **Case 3: Stop Timing Boundary** | `Stop` invoked before commit (clean queue reset) vs. after commit (truthful partial state recorded; no blind rollback). | Native Deferred |
| **Case 4: Local Player UI Independence** | NPC equips weapon while human player inventory/hotbar is monitored. Verify zero selection/slot mutation on human UI. | Native Deferred |
| **Case 5: Engine Queue Desynchronization** | Engine queue advances via `perform` before `complete` finishes. Verify caller settles only on confirmed slot commit. | Native Deferred |
| **Case 6: Persistence Boundary** | Verify hand slot contents across script reloads (`reloadLua`), world streaming/unloads, and character death. | Native Deferred |

### Summary & Next Step
- Native call routing (`perform` then `complete`) is now **statically narrowed**. This narrows the inspected single-player update path; other routing, callback inheritance/multiplicity and live NPC behavior remain unverified.
- Future live adapters must independently audit UI decoupling and concrete ownership APIs, but no coding or deployment is authorized. All live execution remains deferred.

## Codex review, provenance and handoff

Gemini3.8 Flash HIGH reviewed sanitized findings; Codex inspected installed Lua
and selected native classes, reviewed draft/revision and corrected remaining
baseline, direct-ownership, cancellation and universal-routing claims. No raw
installed source/classes exported. Raw artifacts remain ignored under
runtime/equipment-review-gemini-20261006/. Codex owns checkout; no source edits,
new helpers, native calls, deployment, game launch or saves/settings changes.

Lua hashes (installed source read-only):

| Script under installed media/lua | SHA256 |
|---|---|
| shared/TimedActions/ISEquipWeaponAction.lua | 5AAF0E6942D83CAED3DF3ACAE63AA10C3B77BF9618208067B81D579A6E2BF66F |
| shared/TimedActions/ISWearClothing.lua | 146C66743D8593581BAE58E7E1D954886F73A1E6B8BC51720FD2271AFBB50524 |
| shared/TimedActions/ISBaseTimedAction.lua | AD72E57F976BD1564D59D08D98D06F8C8D4ACEA6386AACE48E0D99CE9D02A1F0 |
| client/TimedActions/ISTimedActionQueue.lua | 23C98152728172B44CCB41BC8DDC97798FEE7A91B57B20620FB11D5F41E7792C |

CFR0.152 fresh LuaTimedActionNew/BaseAction snapshots have unresolved dependencies;
IsoGameCharacter uses the prior same-hash snapshot, with fresh Code parsing of
updateInternal corroborating perform1334/client1337/complete1344 order. Selected
LuaTimedActionNew.perform/complete and BaseAction.perform instructions also
corroborated directly without target-class initialization. No runtime routing
or callback scheduling experiment performed. Native complete-before-final-result
verification is a future integration obligation, not an existing callback API.

Native BaseAction.perform additionally updates player progress UI through the
IsoPlayer index. Sarah being IsoPlayer avoids assuming a non-IsoPlayer cast fault,
but does not prove the index maps to safe NPC UI. The inspected script branches
also reach player hotbar/inventory UI; wrong-player behavior remains unobserved.
Missing UI and detachConnect delivery belong in deferred tests, not claims of
actual crashes. Do not repurpose local player slots or change local settings.

Future action states accepted/running/rejected/failed/cancelled/completed are
caller policy proposals. Settle once after actual postconditions; never infer
success from animation, queue advancement, a true complete return or pcall alone.
Do not call complete manually in addition to engine dispatch. Unexpected partial
state is reported truthfully, without blind retry, rollback or replacement item.
Garment worn-slot conflicts/exclusive layers need their own audit; an empty slot
alone does not prove no other slot can change. No automatic equipment ranking.

Item conservation checks must include selected identity/multiplicity, direct
ownership and hand/worn references plus unexpected replacement/world drops in
bounded controlled cases. Equal total counts alone cannot detect substitution.
Stale ID/handle, removed item, broken condition, death/unload, menu/reload,
Stop-before/after-commit, existing two-hand/heavy/back replacement gear, absent UI,
local-player state and full save/restart persistence all remain deferred cases.
Existing Sarah binary checkpoints do not certify arbitrary new equipment across
reload/restart; do not create another persistence table or token registry here.

This prepares a future narrow NPC equipment adapter decision. The next possible
Gemini offline research is concrete ownership/container lookup and worn-slot
conflict semantics, or a source-only minimal adapter proposal if that scope is
selected. Do not reuse entire player actions unchanged, implement automatic
selection, add more generic diagnostic layers, or declare equipment accepted.
Native Follow/rendering remains pending and cannot be replaced by this research.
User is not ready for live testing; keep it deferred without repeated launch
questions. Stop unchanged, lighting unknown, model AI ON HOLD; deployed5fa6b9c.
