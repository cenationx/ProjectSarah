# Project Sarah: Bounded Offline Equipment Action & Direct Bytecode Review (Checkpoint `2676f98`)

## 1. Executive Scope & Direct Bytecode Corroboration
- **Baseline:** Main branch checkpoint `2676f98`. Game JAR hash `E1A69EB743EDE60B213A0FE7F8B83D4FCAB773036D256CC4543A336F3B058A33` verified unchanged. Prior test baseline (649 offline checks across 15 suites + 11 runner assertions + 19 preflight checks) was not rerun in this research batch; Lupa Lua55 and Python preflight results do not establish native Kahlua runtime compatibility.
- **Scope:** Pure preparatory research. Codex remains sole checkout editor. No code, helpers, native invocations, game launches, deployments, saves, or settings changes are authorized. User is explicitly not ready for live testing.
- **Direct Code Corroboration (Static Bytecode, No Class Init):**
  - `ItemContainer.contains(InventoryItem)`: invokes `ArrayList.contains` at Code offset 5 (direct, non-recursive).
  - `ItemContainer.getItemWithID(int)`: reads `item.id` at Code offset 26 (direct loop, non-recursive, first match).
  - `ItemContainer.getItemById(long)`: recursive call at Code offset 83 (`@Deprecated` annotation confirmed).
  - `InventoryItem.getContainer()`: reads field `container` at Code offset 1.
  - `WornItems.setItem(ItemBodyLocation, InventoryItem)`: checks `group.isMultiItem` at Code offset 5, invokes `List.remove` for first matching location entry at 27, iterates all entries checking `group.isExclusive` at 73, removes exclusive entry at 87, branches on `item == null` at 100, and removes prior occurrence of same item at 106.
  - `WornItems.getItem(ItemBodyLocation)`: returns first matching index at Code offset 2.
  - `IsoGameCharacter.setWornItem(ItemBodyLocation, InventoryItem, boolean)`: calls `wornItems.setItem` at Code offset 48; capacity check `hasRoomFor` at 104, `ItemContainer.Remove` at169, and `IsoGridSquare.AddWorldInventoryItem` at222; 2-arg overload delegation with `forceDropTooHeavy = true` confirmed.

---

## 2. Ownership & Container Traversal Semantics

| Method & Signature | Corroborated Bytecode Behavior | Traversal Depth | Boundary Role in Timed Actions |
| :--- | :--- | :--- | :--- |
| `contains(InventoryItem)` (Code 5) | Direct `ArrayList.contains` on root list. Uses `equals` contract. | **Direct** | Used by `ISWearClothing.isValid` in single-player. |
| `getItemWithID(int)` (Code 26) | Direct loop matching primitive `item.id == id`. Returns first match. | **Direct** | Used by `ISEquipWeaponAction.isValid`. |
| `getItemById(long)` (Code 83) | Recurses nested `InventoryContainer` objects. `@Deprecated`. | **Recursive** | Used by `ISWearClothing.start` in MP client only. |
| `getItemWithIDRecursiv(int)` | Recurses nested `InventoryContainer` sub-containers. | **Recursive** | Not used in standard equip/wear actions. |

### Direct Ownership Evaluation
At the inspected Java overload, invoking candidate `root:contains(item)` establishes direct list membership in `root` (no invented Lua `root.items` property access is approved). However, `contains` alone does not verify consistent container backpointers (`item:getContainer() == root`), ID uniqueness, native numeric conversion (`int` vs `long`), or wrapper reference stability. First-match ID lookup introduces collision hazards if multiple items share an ID. Direct root ownership requires verifying direct containment, matching container backpointer, and asserting expected ID multiplicity within a bounded inventory count, avoiding unbounded scans or new token registries.

---

## 3. `WornItems` Exclusivity, Model Hiding & Character Capacity Drops

| Subsystem / Hook | Inspected Bytecode / Script Behavior | Inventory & World Floor Impact |
| :--- | :--- | :--- |
| `WornItems.setItem` (Code 5–106) | If non-multi, removes the **first** entry at `location` (Code 27). Iterates all worn items and removes any entry matching `group.isExclusive` (Code 73, 87) **before** evaluating `item == null` (Code 100). | Mutates `wornItems` list only. Removes entries from worn slots, but does **not** drop or delete items from inventory. |
| `WornItems.getItem` (Code 2) | Returns `indexOf(location)` $\rightarrow$ first matching entry. If `nil`, confirms no item at that specific location. | Does **not** prove absence of exclusive conflicts in other locations. Full worn set inspection against exclusivity pairs is mandatory. |
| `IsoGameCharacter.setWornItem` (Code 48–222) | Captures first prior target item (`itemCur`). If `forceDropTooHeavy && itemCur != null && actor instanceof IsoPlayer && !inventory.hasRoomFor(itemCur) && !GameClient.client`, attempts the prior-item floor-drop path, which additionally requires a suitable floor square. | Drops **only the first target item (`itemCur`)** if over capacity. Exclusive removed items are **not** dropped to the floor by this call. |
| `BodyLocationGroup.setHideModel` | Defines visual occlusions. Installed `NPCs/BodyLocations.lua`: `Jacket` hides `LeftWrist`/`RightWrist` (lines 606–607). | Visual relationship only; does not remove worn items. (`FULL_HAT`/`HAT` exclusive line 129; `BANDAGE`/`WOUND`/`ZED_DMG` multi-item lines 857–859). |

*Note on Direct Invocation:* Calling 3-arg `setWornItem` with `false` is not guaranteed pure or hook-free. Calling `WornItems.setItem(location, nil)` directly executes exclusive removals before its nil-item return. The character setter instead returns immediately when new item and captured first target item are the same reference (including nil/nil). Bypassing character hooks via direct `wornItems` manipulation is rejected.

---

## 4. Minimal Slices & Pre-Condition Refusals

### Slice 1: Single Owned One-Handed Melee Weapon (Immediate Proposal)
- **Pre-Conditions (Prior Loadout Refusal):**
  - Sarah's hands must be completely empty: `getPrimaryHandItem() == nil` and `getSecondaryHandItem() == nil`.
  - Must exclude any pre-existing worn back garment with `REPLACE_PRIMARY` tag (avoids the inspected back-garment conversion branch).
  - Target item must reside directly in root inventory via `root:contains(item)` and matching `item:getContainer() == root`.
  - Item must belong to candidate class `HandWeapon` with `isTwoHandWeapon() == false` and `isRequiresEquippedBothHands() == false`.
  - Refuse candidate if inspected `isForceDropHeavyItem` candidate is true, or if item is a firearm, container, activation-dependent, or attached to hotbar. (Hotbar status query coupling on NPCs is unverified; do not query wrong-player hotbar as proof of non-attachment).

### Slice 2: Single Ordinary Garment (Deferred Follow-Up)
- **Pre-Conditions:** Target body location must return `getItem(loc) == nil`. Entire active worn set must be audited against typed `ItemBodyLocation` exclusivity pairs (using configured group data, not string names). For the initial garment proposal, refuse displacement, multi-item targets and unknown conflict policy entirely. With an empty target the captured prior item is nil, so the inspected prior-target capacity-drop branch is not entered; actual native state must still be rechecked. Later clothing swaps need a separate capacity/displacement audit.

---

## 5. Proposed Pre-Commit / Post-Condition Protocol & Cancellation Boundaries

```
[Pre-Action Validation] ──► [Queue / In-Flight] ──► [Pre-Commit Gate] ──► [Native Commit] ──► [Post-Verification]
  - Both Hands Empty          - Perform runs         - Check Cancel Signal   - Lua complete      - Target in Hand/Slot
  - Direct Root Ownership       before Complete      - Re-verify Root/ID                         - Multiplicity Conserved
  - No Conflicting Loadout                           - Epoch Unchanged                           - Zero World Floor Drops
```

- **Cancellation Boundaries:** `Stop` before commit does not guarantee immediate native thread halting or prevent in-flight mutation; the proposed pre-commit gate must explicitly check cancellation and refuse execution *before* native dispatch. If `Stop` occurs after commit begins, native state cannot be assumed cleanly reversible; caller must record truthful partial failure without blind rollback or automated retries.
- **UI Decoupling Standard:** Verify zero state, slot, or selection mutation on human player hotbar and inventory windows (a mere global render dirty flag is not proof of corruption).

---

## 6. Deferred Acceptance Gates & Recommended Next Step

| Deferred Case | Failure Condition / Invariant Tested | Verification Level |
| :--- | :--- | :--- |
| **Case 1: Nested Bag Rejection** | Item in sub-bag (`item:getContainer() ~= root`). Verify pre-action refusal. | Native Deferred |
| **Case 2: Backpointer Inconsistency** | `root:contains` true but backpointer drifted (or vice versa). Verify rejection. | Native Deferred |
| **Case 3: ID Collision / Replacement** | Item removed or replaced by another sharing same ID. Verify Pre-Commit Gate halts settlement. | Native Deferred |
| **Case 4: Exclusive Worn / Multi-Item Conflict** | Garment conflicts with existing exclusive pair or multi-item rule. Verify refusal. | Native Deferred |
| **Case 5: Capacity Drop Prevention** | Inventory full during clothing swap. Verify pre-check detects floor-drop hazard and aborts. | Native Deferred |
| **Case 6: Stop Timing Boundaries** | Cancel signaled before commit (pre-commit gate refusal) vs after commit (truthful partial state; no blind rollback). | Native Deferred |
| **Case 7: Local Player UI Independence** | Monitor human player inventory/hotbar during NPC equip. Verify zero selection/slot mutation. | Native Deferred |
| **Case 8: Engine Persistence** | Verify hand/worn contents survive script reloads (`reloadLua`), world streaming/unloads, and full restart. | Native Deferred |

### Recommendation
- Direct bytecode corroboration confirms container traversal depths, `WornItems` exclusivity ordering, and capacity drop rules. Full player timed action reuse and generic helpers remain rejected.
- **Recommended Next Step:** Author a narrow, concrete manual equip adapter design proposal covering Slice 1 pre-commit gates and post-condition checks, without implementation or live deployment.

## Codex verification and evidence boundary

Codex started clean main2676f98 and remained sole editor. Gemini3.8 Flash HIGH
reviewed sanitized facts with NO TOOLS requested; no raw game source/classes or
project documents exported. Codex corrected first-draft ownership, null-getter,
setter-removal, cancellation, invented access and universal policy claims, then
reviewed the revision. This batch changes documentation only. No runtime/helper
implementation, target-class initialization, native game calls or save/settings
changes. Prior649 suite checks/15 suites +11 runner +19 preflight baseline unchanged
and not rerun for source-unchanged research. No new native equipment acceptance.

Fresh CFR0.152 snapshots and selected direct Code reports remain ignored under
runtime/ownership-review-gemini-20261006/. Dependencies unresolved. Class paths:
zombie/inventory/ItemContainer, InventoryItem; zombie/characters/WornItems/
WornItems, BodyLocationGroup, BodyLocation. IsoGameCharacter uses the earlier
same-hash snapshot plus fresh direct Code corroboration. Named Code offsets
refer to individual methods, not Java source lines or runtime measurements.
getItemWithIDRecursiv's recursive call is at76, getItemById's at83. Public fields
or decompiled signatures do not establish actual Lua overload/access behavior.

InventoryItem.getContainer reads its container field. Checking that reference
alone is insufficient; the actual selected overload, direct membership, stable
selected item identity and ID multiplicity must agree. ArrayList.contains uses
its equals contract; actual item subclass equality was not exhaustively audited.
First-match ID lookup is not an identity reservation or uniqueness guarantee.
ID-based reacquisition must not silently accept a different same-ID item.

Native setters use ItemBodyLocation values, not guessed string names. Installed
NPCs/BodyLocations.lua SHA256 is
CD1A7F06EE4AAAAF2B7267CCAB5B69BFC9B1E37441FDA93551D6E9BC725D29FA.
Observed examples: FULL_HAT/HAT exclusive at129; JACKET hiding wrist models at
606-607; BANDAGE/WOUND/ZED_DMG multi-item at857-859. Hide-model relationships
are stored separately from exclusivity; complete rendering behavior and actual
runtime/mod-modified group are unverified. Unknown target location can cause
null location access in group queries; never manufacture a string conversion.

WornItems non-multi removal affects only the first same-location entry; exclusive
removal scans all entries before the nil-item return. Its item-reference lookup
uses Java identity; location lookup uses equals. First-item getters cannot
inventory all entries, though a nil result indicates no matching non-null item
in the normal inspected Java state. This does not rule out conflicts elsewhere.
The character setter's default overload enables capacity-drop logic for captured
prior target item. Removed exclusive worn entries are not automatically inventory
deletions/drops. Passing false to the third argument does not bypass all other
processing/model/parent/network hooks and is not an approved shortcut.

Ownership and worn list operations can internally scan collections; callback
ceilings are not per-entry/time bounds. Future concrete work needs an audited
bounded-count policy and fails closed if counts/identity/policy cannot be established.
No recursive inventory scans, group mutations, new token registry, fake native
fixtures or broad helper framework are implemented here.

Broken item, excessive count, unknown location, same-ID replacement, multi-item/
exclusive conflicts, capacity drop, missing UI, Stop before/after commit,
death/unload/menu/reload and full save/restart remain deferred acceptance cases.
No new action can resume after Stop; no manual complete alongside engine dispatch,
blind rollback or duplicate retry. Existing native Follow/rendering gates remain
open. Recommended next offline task is a concrete narrow manual equip adapter
proposal, resolving its UI and pre-commit integration choice before code changes.
User not ready for live tests; no repeated launch request. External/model AI ON
HOLD, light unknown, Stop unchanged; isolated deployed baseline remains5fa6b9c.
