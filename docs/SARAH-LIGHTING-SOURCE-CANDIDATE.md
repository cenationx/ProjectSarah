# Sarah-owned lighting: source reconstruction candidate

2026-10-07. Codex offline follow-up to the extended audit. NOT IMPLEMENTED;
NOT NATIVE-VERIFIED. Independent lighting remains OPEN. No gameplay changes.

## New distinction

The Java lighting bridge registers explicit source parameters without a player
index: LightingJNI.addLight and addRoomLight. Its output/update scheduling uses
player slots. This does not prove native calculations are observer-independent,
but it means global source state should not be rejected merely because the final
render caches are player-indexed. A Sarah-owned calculation from source facts is
a different approach from reading those caches. It is an authored perception
model, not a claim to reproduce the native renderer.

## Read-only primitive candidates

Sources inspected under ignored runtime paths:
- research-adapter-20261005/fresh/zombie/iso/LightingJNI.java:
  checkLights at the source loop around280-340 reconciles activity/power and
  registers coordinate, radius, RGB and building restrictions. At361-399 room
  lights reconcile room switch state and switch electricity before registration.
  Source state is updated asynchronously with engine scheduling; isActive alone
  does not establish freshness or present electrical supply.
- research-adapter-20261005/fresh/zombie/iso/IsoCell.java:
  getLamppostPositions at2554 returns a live source stack; getLightSourceAt at2558
  searches by position. This stack is not a complete list of all illumination.
- gemini-investigation-20261007/src/zombie/iso/IsoLightSource.java:
  getters at142-200 return coordinates, RGB, radius and activity; at255-263 return
  hydro-power and building restriction. These are field reads. update(), clear()
  and setters must never be invoked by an observer. isInBounds uses chunk maps,
  and checkLights removes out-of-bounds sources, so coverage remains constrained
  by loaded-world management. No positive source means unknown, not darkness.
- research-engine-20261005/fresh/zombie/characters/IsoGameCharacter.java:
  getActiveLightItems at13179 copies held/attached emitting items into a supplied
  list. Inspect item getter semantics and use a fresh private list before any
  native admission. Installed Lua already calls item.getLightStrength.
- LightingJNI.java at410-431: single-player torch registration enumerates
  IsoPlayer.players. Sarah being an IsoPlayer does not by itself prove that her
  carried lamp is registered. Treat NPC emitted-light rendering as a separate
  native gate; do not invent a sensory light absent from the visible world.
- LightingJNI.java around640-725 passes door, curtain, barricade and window
  transmission facts to JNI. Geometric line-clear alone is not light transport.

## Minimum experiment before implementation

Start with one explicit non-hydro artificial lamp in a loaded, same-floor scene.
Read only its source getters and independently verify loaded source/target/path
coverage. Keep model state isolated from movement and Stop; no timed actions.
Compare on/off, distance, solid wall, closed/open door, curtain and unload cases.
Keep player and Sarah positions fixed when testing player-facing independence.
Calibrate any attenuation and detectable threshold against isolated observations;
never invent a threshold and call it native-compatible. The old deprecated
Java falloff is a candidate formula only, not proof of current JNI behavior.

Unknown source freshness, unsupported obstruction/transmission, missing squares,
unsupported source type or budget exhaustion must yield unknown. No-source and
artificial-light-negative results must also yield unknown while sunlight, room
lighting, vehicles, fire and torches are incomplete. Emit modeled values with
provenance separately from confirmed visual detections. Knowledge admission must
remain disabled until the model has explicit native acceptance.

## Recommendation

Investigate bounded source snapshots next, followed by one isolated calibration
batch. Do not build a speculative whole-engine light solver or repurpose player
slots. A custom model may provide useful independent perception, but cannot yet
close the lighting gate. A native bridge is another future option and would need
its own supported interface and safety evidence; none was established here.

## Diagnostic-only light-source snapshot prototype (2026-10-07)

Implemented offline in `foundation/SarahFoundation/42/media/lua/client/Sarah/LightSourceSnapshot.lua`:
- Pure inert prototype; no automatic callbacks, production perception wiring, or native invocation during development.
- Copied snapshot records containing only plain Lua primitives:
  * `id`: session/pass token string (`src:<pass>:<index>` or `src:<srcId>:<pass>:<index>`).
  * `x, y, z`: validated integer coordinates within world bounds (`[-1e6, 1e6]`, `z` in `[-32, 31]`).
  * `r, g, b`: validated non-negative numbers in `[0.0, 10.0]`.
  * `radius`: validated positive integer in `[1, 64]`.
  * `active`: validated boolean.
  * `hydroPowered`: validated boolean.
  * `buildingRestriction`: `"unrestricted"` (outdoors or legitimate nil building reference), `"restricted"` (valid building ID), or `"unknown"` (throwing or unresolvable building reference).
  * `buildingId`: integer building ID if restricted to building (`localToBuilding`), or `nil`. Never retains Java building reference.
  * `squareLoaded`: boolean (true if source square is loaded, false if unloaded/missing).
  * `powerStatus`: `"not_required"`, `"powered"`, `"unpowered"`, `"unloaded"`, or `"unknown"`. Switch presence (`switchCount > 0`) keeps power status `"unknown"`.
  * `generatorPower`: boolean or nil (reports `sq:haveElectricity()`).
  * `gridPower`: boolean or nil (reports `sq:hasGridPower()`).
  * `freshness`: `"stale"` (positive discrepancy: square unpowered while active flag remains true) or `"unknown"`. Never promoted to `"verified"` from mere state agreement or `hydroPowered=false`.
- Strict collection, read, square, capture, and output budgets:
  * Oversized collections (`coll_size > maxCollectionSize`, default 128) fail closed with `status = "collection_oversized"`, `reason = "collection_exceeds_budget"`, `incomplete = true`, empty sources (never silently truncated).
  * Collection integrity and mutation detection: takes a bounded exact reference snapshot of items at start, checks size and item identity mid-traversal, and performs a full re-verification pass across all references after all source and getter reads (including after the final getter). Fails closed on any mutation, size change, or same-size reordering/replacement with `status = "collection_mutated"`, `reason = "size_changed_during_iteration"` or `"collection_changed_during_iteration"`, empty sources.
  * Getter failure isolation: `read_property` / `invoke_getter` distinguishes `"ok"`, `"legitimate_nil"`, `"throwing"`, and `"unavailable"`. Authoritative getters that throw or return nil NEVER silently fall back to raw fields. Raw fields are inspected only if the getter is unavailable.
  * Reentrancy exception safety: execution wrapped in `pcall` ensuring `busy = false` is unconditionally restored even on unhandled exceptions. Integral collection size validation rejects non-integers, strings, and NaNs.
  * Honest read accounting: tracks `getter_reads`, `square_lookups`, `power_queries`, and `total_reads` (sum of all native calls), enforcing `maxReads` against `total_reads`.
- Strict lifecycle identity:
  * Injected `api.capture()` validates caller identity and living/resident state at start, mid-pass, and end.
  * Drift or reset during pass triggers immediate fail-closed abort (`status = "aborted"`, `reason = "lifecycle_drift"` or `"reset_during_snapshot"`).
  * Re-entrancy guarded and rejected cleanly.
- Reference safety:
  * No persistent Java references stored or returned; all values are copied plain tables.
  * Mutation of returned snapshot table does not affect source objects.
  * `inst:reset()` clears internal sequence and state, increments revision.
- Separate source facts from sight:
  * Does NOT evaluate target illumination or return visual detections.
  * Source presence does NOT imply sight; absent sources do NOT imply darkness.
  * Knowledge admission remains disabled.

### Static API evidence, exposure uncertainties, and freshness limits

1. **Static API Evidence**:
   - `IsoLightSource.java:34-263`: Class annotated `@UsedFromLua`. Public getters `getX()`, `getY()`, `getZ()`, `getR()`, `getG()`, `getB()`, `getRadius()`, `isActive()`, `wasActive()`, `isHydroPowered()`, `getLocalToBuilding()`, `getSwitches()`. Forbidden methods: `update()` (deprecated, mutates light totals and life, checks player index), `clearInfluence()` (mutates square light totals), setters (`setX`, `setR`, etc.).
   - `IsoCell.java:2554-2565`: `getLamppostPositions()` returns live `Stack<IsoLightSource>` (a `Vector`). Exposes `size()` and `get(i)`. `getLightSourceAt(x, y, z)` performs linear scan.
   - `IsoGridSquare.java:8426, 10353`: `haveElectricity()` verifies exterior generator and chunk generator power; `hasGridPower()` checks world hydro power grid or generator. A false generator result does not prevent checking grid power. Both are queried and reported independently.
   - `LightingJNI.java:280-352`: `checkLights()` reconciles `lightSource.active` against `haveElectricity()` and `switches` periodically.
2. **Lua Exposure Uncertainties**:
   - `IsoLightSource` and `IsoCell` are exposed in `LuaManager$Exposer.java`. However, whether `cell:getLamppostPositions()` in live gameplay returns all active world lamps or only a subset managed by cell loading remains a native runtime uncertainty.
   - Room lights (`cell.roomLights` / `IsoRoomLight`) are NOT exposed to Lua and are distinct from `IsoLightSource`.
   - Single-player torch registration in `LightingJNI.java:422-430` enumerates `IsoPlayer.players[0..3]`, ignoring NPC characters.
3. **Freshness Limits**:
   - `lightSource.active` reflects internal engine field state, but is only reconciled when `LightingJNI.checkLights()` executes.
   - Neither state agreement nor `hydroPowered = false` proves source freshness this frame; freshness must remain `"unknown"`.
   - If grid power cuts out, an `IsoLightSource` may have `active = true` until the next engine check; `LightSourceSnapshot` detects this positive discrepancy as `powerStatus = "unpowered"` and flags `freshness = "stale"`.

### Short manual native probe plan for one artificial lamp (Codex isolated Gate B)

Prerequisites: isolated sandbox profile, game closed. The operator must take a fresh disposable world backup and verify its restoration before testing (preflight only checks backup file presence, it does not take or verify a fresh backup).

1. **Test Setup**:
   - Place one movable or fixed electrical lamp (non-hydro or generator-powered) on square `(x, y, z)` in a loaded interior room.
   - Position Sarah within 5 tiles of the lamp.
2. **Case 1: Lamp ON / OFF**:
   - With generator/grid power active, turn the lamp switch ON. Verify snapshot reports:
     `active = true`, `squareLoaded = true`, `powerStatus = "unknown"` (if switch present) or `"powered"`, `freshness = "unknown"`.
   - Turn the lamp switch OFF. Verify snapshot reports:
     `active = false`, `squareLoaded = true`, `freshness = "unknown"`.
3. **Case 2: Power Loss (Freshness reconciliation)**:
   - Turn lamp switch ON. Turn off the generator / cut power to the square.
   - Immediately query snapshot: verify whether `sq:haveElectricity()` and `sq:hasGridPower()` return false while `source:isActive()` is still true -> snapshot must report `powerStatus = "unpowered"`, `freshness = "stale"`.
   - After engine tick/delay, verify if engine reconciles `active = false` -> snapshot reports `freshness = "unknown"`.
4. **Case 3: Chunk Unload**:
   - Move player away until the lamp chunk unloads.
   - Query snapshot: if source is still in `lamppostPositions`, `sq = getSquare(x,y,z)` returns nil -> snapshot reports `squareLoaded = false`, `powerStatus = "unloaded"`, `freshness = "unknown"`.
5. **Case 4: Player-Facing Independence**:
   - Keep Sarah, lamp, and player stationary.
   - Rotate human player 180 degrees away from the lamp.
   - Query snapshot: verify that coordinates, RGB, radius, active, and power status outputs remain identical under fixed conditions. Note: this is an observation test only under fixed positions; matching outputs show that this query path did not change with camera angle, but do NOT prove complete independence from underlying engine lighting caches or off-screen cullers.

### Status & Guardrails
- 53 actual-Lua unit test checks pass in `tools/test_light_snapshot.py`; 784 checks across 17 suites pass in `tools/run_tests.py`.
- Strict pre-operation budget enforcement (total_reads never exceeds maxReads on any exit), missing/malformed building/switch metadata preserved as unknown, getter member-lookup exceptions isolated without field fallback.
- Independent lighting remains OPEN. Lighting and visual confirmation remain unknown; Knowledge admission stays disabled. External/model AI remains ON HOLD.
