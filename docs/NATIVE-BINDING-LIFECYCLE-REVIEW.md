# Project Sarah: Concrete Caller/Resolver Binding and Lifecycle Review (Revised)

## 1. Audit Baseline & Operational Scope
- **Repository State:** Main branch checkpoint `795db52` (clean tree; 555 suite checks across 13 suites, +11 runner assertions, +19 preflight checks passing).
- **Installed Build Artifact:** Target JAR SHA256 `E1A69EB743EDE60B213A0FE7F8B83D4FCAB773036D256CC4543A336F3B058A33` verified unchanged.
- **Operational Boundary:** Strictly bounded offline review. Gemini used NO TOOLS and made no checkout edits. Codex inspected local source/class attributes and writes this reviewed report. No game instances launched and no native functions invoked. Codex maintains sole editing, review, and test execution ownership.
- **Scope:** Corrects registration citations, establishes inspected overload and collection definitions, evaluates probe contract semantics, and formalizes caller lifecycle boundaries strictly against verified source and bytecode facts.

---

## 2. Inspected Candidate Binding Paths & Exposure Points

Inspection of `LuaManager.java` establishes explicit `setExposed` registration calls and the public exposure loop (`LuaManager.java:3518-3535`):
- `setExposed(IsoGameCharacter.class)` at line 2623.
- `setExposed(IsoCell.class)` at line 2987.
- `setExposed(IsoGridSquare.class)` at line 2991.
- `setExposed(ArrayList.class)` at line 2515.
- `setExposed(HashSet.class)` at line 2519.
- `setExposed(LosUtil.class)` at line 3010.

Candidate lookup paths for the 13 probe aliases are mapped as follows (all method references remain uninvoked during probe evaluations):

1. `forward_x`: Candidate property/method lookup `npc.getForwardDirectionX` (`IsoGameCharacter.java:2574-2576`, returns float).
2. `forward_y`: Candidate property/method lookup `npc.getForwardDirectionY` (`IsoGameCharacter.java:2578-2580`, returns float).
3. `cell_get_square`: Candidate `cell.getGridSquare` (`IsoCell.java`). Three inspected overloads exist:
   - `public IsoGridSquare getGridSquare(double x, double y, double z)` at line 2864.
   - `public IsoGridSquare getGridSquare(Double x, Double y, Double z)` at line 2927.
   - `public IsoGridSquare getGridSquare(int x, int y, int z)` at line 2931.
   *Overload selection and dispatch behavior in Kahlua remain unproven offline.*
4. `square_get_moving_objects`: Candidate `knownsquare.getMovingObjects` (`IsoGridSquare.java:7959-7961`, returns `ArrayList<IsoMovingObject>`).
5. `list_size`: Candidate `knownmovinglist.size` (`ArrayList.class`, exposed at line 2515).
6. `list_get`: Candidate `knownmovinglist.get` (`ArrayList.class`, exposed at line 2515).
7. `los_line_clear`: Candidate `LosUtil.lineClear` (`LosUtil.java:28-32`). Java method takes `(IsoCell cell, int x0, int y0, int z0, int x1, int y1, int z1, boolean bIgnoreDoors)` plus an optional `rangeTillWindows` int parameter.
8. `get_cell`: Candidate global `getCell`. Direct bytecode attribute read confirms `LuaManager$GlobalObject.getCell()` has public static flags 0x9 and `@LuaMethod(name="getCell", global=true)`. Bytecode loads `IsoWorld.instance` at offset 0 and invokes `IsoWorld.getCell()` at offset 3. `IsoWorld.getCell()` reads instance field `currentCell` at offset 1. This strengthens static exposure candidacy, but does not constitute proof of Lua invocation.
9-13. Enum Candidates (`LosUtil.TestResults`):
   - `enum_clear`: Candidate constant `Clear`.
   - `enum_open_door`: Candidate constant `ClearThroughOpenDoor`.
   - `enum_window`: Candidate constant `ClearThroughWindow`.
   - `enum_blocked`: Candidate constant `Blocked`.
   - `enum_closed_door`: Candidate constant `ClearThroughClosedDoor`.
   *Exposure Status:* Unresolved. No explicit registration of `LosUtil.TestResults` appears in the inspected `setExposed` calls. However, lack of explicit registration does not prove constants are nil, unavailable, or absent from nested globals. Resolution path remains UNKNOWN; exports must not be invented.

---

## 3. Method References, Synthetic Closures & Probe Contracts

1. **Receiver Requirements:** Uncurried method references extracted from userdata can require an explicit receiver. Actual Kahlua wrapper types, method handles, and overload behaviors are not proven.
2. **Synthetic Closure Pitfall:** Wrapping an unverified or absent native method in a synthetic Lua closure (`function(...) return obj:method(...) end`) always yields `type(v) == "function"`. Synthetic closures must never be presented as proof of native symbol presence.
3. **Getter Side-Effects:** Indexing properties on native userdata can trigger native getter execution. Userdata-index getter side-effects must be audited before any native use.
4. **Probe Status Semantics:** `NativeExposureProbe` evaluates provided references directly via `rawequal` without invocation. Overall probe outcomes are strictly `completed`, `aborted`, or `reentrancy_rejected`. Missing individual rows do not abort the probe run; there are no `incomplete` or `degraded` statuses.
5. **Identity Boundaries:** Reference comparisons in the probe describe provided Lua references only. Wrapper stability and underlying native object identity remain separate gates.

---

## 4. IsoCell Collections & Invocation Accounting

1. **Collection Structure:** In `IsoCell.java`, `objectList`, `addList`, and `removeList` are fields of type `HashSet<IsoMovingObject>` / `Set` (fields 296 and 305; getters `getObjectList` at line 2441, `getRemoveList` at line 2478, `getAddList` at line 2482), NOT `ArrayList`. `HashSet` is exposed in `LuaManager.java:2519`.
2. **Materialization Hazard:** `IsoCell.getObjectListForLua` (lines 2446-2447) executes `objectList.stream().toList()`, materializing the whole collection into a new list. This method must be excluded from bounded probe designs.
3. **`Engine.isResident` Source Invocations:** The implementation in `Engine.lua:49-52` evaluates short-circuit logic bounded at the source level to at most:
   - 1 `npc:getCurrentSquare()` check
   - 3 global `getCell()` calls
   - 3 set getters (`getObjectList`, `getAddList`, `getRemoveList`)
   - 3 `contains(npc)` calls
   This totals a maximum of 10 explicit Lua-to-API call expressions per evaluation. Underlying execution time and complexity of `contains` are unmeasured; no assumptions regarding complexity class, entity counts, or GC overhead are asserted.
4. **Budget Separation:** `NativeExposureProbe` enforces a ceiling of 54 captures. `DiagnosticSampler` enforces a ceiling of 512 captures. These distinct budgets must not be conflated.
5. **Rejection of Unverified Residency Alternatives:** Checking `getCurrentSquare()`, `getChunk()`, or `isDead` cannot substitute for actual cell membership proof. Native chunk getter semantics are uninspected, and `IsoGameCharacter.isDead` (line 4645, checking character or BodyDamage health <= 0) has unverified concurrency/Lua semantics. Furthermore, caching residency across ticks without invalidation hooks risks missing entity removal during active passes.

---

## 5. Lifecycle Tokens & Demarcation Boundaries

1. **Controller State:** `SarahFoundation.lua:17-21` preserves `controller` across Lua reloads (`reloadLua`), but sets it to `nil` on `OnMainMenuEnter` and `OnGameStart`. Controller identity alone cannot disambiguate reloads; caller orchestration must maintain distinct epoch and revision counters across resets and reloads (no engine hooks are added in this review).
2. **Token Semantics:** Capture tokens are caller-issued nonempty strings of1..96 characters; capture does not impose a namespace pattern. SessionIdentity namespace validation is a separate1..32-character contract. A future caller epoch policy needs explicit overflow handling. They do not represent native engine identifiers.
3. **Generation Token:** The `generation` token is strictly caller-issued. No authoritative world or chunk generation API has been established in this scope. Caller generation tokens do not freeze or synchronize loaded world state.
4. **Stability Limits:** Native userdata wrapper stability across frames remains UNKNOWN. `SessionIdentity` enforces FIFO bounds on caller tokens, but cannot stabilize arbitrary native pointers. Probe reset or cancelled captures abort active passes without resumption; it is not currently wired to the user Stop action.

## 6. Codex review findings and evidence boundaries

Source citations under `runtime/research-adapter-20261005/fresh/` and
`runtime/research-engine-20261005/fresh/` refer to ignored CFR snapshots; dependency
resolution is incomplete. Project Engine.lua and SarahFoundation.lua citations
refer to `foundation/SarahFoundation/42/media/lua/client/`. No game source or
class files are published with this report. Fresh archive hash matches snapshots.

Direct Code/annotation parsing independently confirmed the public global getCell
metadata/currentCell access, the three square-lookup descriptors, public facing
field reads and movingObjects getter. The double square lookup is annotated
LuaMethod(name=getGridSquare); boxed-Double and int overloads are public. The int
lookup inspects active local-player chunk maps in the selected client path.
Loaded lookup remains streaming coverage, not a promise of Sarah-owned distant
world access. No square creation/loading is proposed. LOS descriptors contain
cell+six int coordinates+boolean, plus an extra int in its overload.

ArrayList aliases describe the square movingObjects collection. Residency
object/add/remove containers are separate Sets backed by HashSet (fields296,304,305).
Direct Code reads confirm their getters return Set fields; getObjectListForLua
calls Set.stream/Stream.toList. A callback ceiling alone cannot certify hidden
resolver work or a latency bound. The10 call-expression upper bound excludes
method lookup/marshalling, nested Java calls and all other capture fields. For
example global getCell calls IsoWorld.getCell internally. Native costs require
separate observation; do not substitute a made-up timing target or entity count.

Reload replaces the top-level SarahFoundation Lua table at line18 while keeping
the prior controller. A future caller can observe that plain-Lua table identity
as a framework/reload marker, separately from controller/NPC/cell identity. This
is inspected project behavior, not proof of native wrapper stability. Menu/game
start also clear the controller. Reset propagation/epoch ownership are not yet
implemented; no events or hooks were added here. Caller-issued tokens cannot
repair untrustworthy native identity.

Codex rejected the first Gemini draft's incorrect enum names/registration lines,
synthetic-closure proof, invented native statuses/latency and ArrayList residency
claims. The reviewed revision preserves unknown on unresolved native evidence.
48 existing probe fixtures rerun PASS. Runtime source unchanged; prior full555
suite checks/13 suites +11 runner +19 preflight baseline was not rerun for this
documentation-only batch. All supplied binding paths remain native candidates.

## 7. Deferred native acceptance cases (not performed)

- Explicit user resumption, exact reviewed revision, game closed before staging,
  fresh disposable-world/deployed-mod backups and recorded restore plan. Preserve
  latest test state before restoration; normal saves/settings stay untouched.
- Audit resolver/property access paths for side effects BEFORE native invocation.
  Then record actual Lua symbol types and paired refs, without calling resolved
  functions or substituting synthetic closures to manufacture exposed status.
- Separately invoke audited facing/square/list methods with explicit receiver
  handling and bounded arguments. Observe integer/double/boxed overload behavior;
  negative fractions and boundaries must agree with the selected floor policy.
  No create/load-square fallback, lighting queries or room-seen writes.
- Establish actual enum lookup paths and exact identity/marshalling. Observe LOS
  returned representation only AFTER fresh conservative loaded coverage. Missing,
  unstable or unsupported representations remain unknown, never string/ordinal
  normalization. Material cases do not certify illumination.
- Observe controller/NPC/cell identity and membership under death, removal,
  unload, replacement, game/menu transition and script reload with controller
  preserved. Confirm cancellation/reset discards output and prevents subsequent
  reads; no actions resume. Do not carry cached residency through invalidation.
- Count capture/resolver operations separately from hidden/native work; exercise
  missing tiles, crowded collections and changing membership. Max54 probe and
  max512 sampler captures are distinct policy ceilings, not native time bounds.
  Exclude whole-set list materialization from the diagnostic path.
- Verify scalar-only output, no hidden locators or exposed handles; no long-lived
  native references intended. Lua fixture weak-ref evidence does not prove JVM GC.
  Actual wrapper stability and lifetime remain separately assessed.
- Follow/rendering and independent-light gates remain separate and pending.
  This checklist does not authorize deployment, a game launch or model AI.

## 8. Next bounded offline task

Gemini drafts an inert caller epoch/reset policy with separate framework marker
and caller-issued controller/NPC/cell tokens, explicit bounded epoch/overflow
behavior and invalidation contract. Codex reviews/applies/tests it without native
bindings, runtime callbacks or gameplay changes. Include a concrete capture-call
accounting contract so internal work is not hidden behind callback counts.
Reuse existing probe/reset contracts and SessionIdentity where appropriate; do
not replace Engine.isResident with a coordinate/chunk shortcut or simulate native
residency. Live acceptance stays deferred, external/model AI ON HOLD.
