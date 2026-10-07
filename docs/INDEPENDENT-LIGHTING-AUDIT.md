## Codex-reviewed extended lighting audit (2026-10-07)

Documentation-only investigation; no usable independent lighting route admitted.
Installed archive hash matches the pinned SHA256. Selected source checks confirm
CanSee is geometric, zombie vision uses player lighting/climate, and getSkyLightLevel
reads player render settings and conditionally invalidates global lights.
The broader candidate matrix is static evidence, not an exhaustive engine proof.
Native C++ internals were not inspected. Explicit registration-list absence does
not establish that an object or method is unreachable through Lua return values.
Light-source lists and fire influence arrays lack verified total illumination
provenance; exclusive producer and whole-engine absence claims are not established.
For any future invariance test keep Sarah, player and target positions fixed;
change only player facing and compare stable identities. Moving the player changes
an observed target and may change loaded coverage. Matching counts alone prove
neither independent lighting nor absence of camera-cache borrowing.
Independent lighting remains OPEN; visual stays unknown. No code, deployment,
launch or save/settings changes. Codex owns the checkout. Existing 731+11+42
baseline remains unchanged; the sampler policy checks were rerun for this audit.
Next useful work is isolated native diagnostic/Follow acceptance after fresh backup,
or a separately bounded new lighting route; no sight-driven behavior is enabled.

# Project Sarah: Bounded Offline Lighting Candidate Audit

**Checkpoint:** `51079b5`
**Scope:** Bounded static inspection of installed classes, CFR decompiled sources, and confirmed bytecode offsets
**Binary Reference:** Installed JAR SHA256 `E1A69EB743EDE60B213A0FE7F8B83D4FCAB773036D256CC4543A336F3B058A33`
**Review Authority:** Codex

This document consolidates and extends the bounded offline investigation of independent lighting candidates in Project Zomboid Build 42.21.0. No game classes were executed, no native/JNI methods were called, no game processes were launched, no saves/settings were altered, and no deployment was performed. All decompiled artifacts and raw analysis tools reside under ignored runtime paths (`runtime/gemini-investigation-20261007/`).

---

## 1. Scope & Objective

Sarah's autonomous perception requires determining whether a target grid square is sufficiently illuminated for visual detection independently of the local human player's viewport, camera angle, and seen-cache.

This investigation evaluates:
1. Candidate lighting and visibility interfaces beyond the initial set rejected in prior batches.
2. Whether any engine-populated caches expose fresh, target-square illumination independently of human player camera slots.
3. Whether relevant Java interfaces are exposed to Lua via Kahlua in Build 42.21.

The objective is to establish whether any candidate qualifies for admission, requires live native proof, or is rejected. If no candidate qualifies, the blocker is documented honestly; no speculative scaffolding or fake lighting is introduced.

---

## 2. Comprehensive Candidate Evaluation Matrix

| Candidate Interface / Method | Source Location | Read-Only Safety | Player Independence | Target Association & Freshness | Lua Exposure | Operational Verdict |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| `IsoGridSquare.getLightLevel(-1)` / `getLightLevel2()` | `IsoGridSquare.java:9101-9113` | **Non-read-only** (writes `square.lightLevel` at offset 315) | Bypasses slot check via `-1` | Stale shared buffer; JNI native refresh skipped (offsets 91/128) | Exposed on `IsoGridSquare` | **REJECTED:** Bytecode proves refresh bypass and field mutation. |
| `IsoGridSquare.getLightLevel(playerIndex)` | `IsoGridSquare.java:9101-9107` | **Non-read-only** (triggers `checkRoomSeen(playerIndex)`) | Coupled to human player slots `0..3` | Coupled to player camera / render updates | Exposed on `IsoGridSquare` | **REJECTED:** Mutates world seen discovery state; player-bound. |
| `IsoGridSquare.getLightInfo(playerNumber)` | `IsoGridSquare.java:6951-6953` | Read-only field read | Coupled to human player slots `0..3` | Frame-cached array from prior render | Exposed on `IsoGridSquare` | **REJECTED:** Reflects player render camera frame cache. |
| Packed `IsoGridSquare.lightLevel` (`GetRLightLevel`, etc.) | `IsoGridSquare.java:625-635` | Read-only field read | Indirectly player-coupled | Passive; no refresh performed on access | Exposed on `IsoGridSquare` | **REJECTED:** Passive cached int; no refresh or provenance on access. |
| `IsoGridSquare.getLampostTotalR/G/B()` | `IsoGridSquare.java:8043-8065` | Read-only | Hardcoded to slot 0 | Constant `0.0f` under `LightingJNI` | Exposed on `IsoGridSquare` | **REJECTED:** Dead legacy stub in JNI mode; returns zero. |
| `ClimateManager.getAmbient()` / `getDayLightStrength()` | `ClimateManager.java:515-528, 581-587` | Read-only | Macro-level; cheat-override vulnerable | No spatial `(x, y, z)` target association | Exposed on `ClimateManager` | **REJECTED:** Macro atmospheric context, not target illumination. |
| `ClimateManager.getGlobalLight()` / `getGlobalLightIntensity()` | `ClimateManager.java:475-486` | Read-only | Macro-level | No spatial `(x, y, z)` target association | Exposed on `ClimateManager` | **REJECTED:** Macro atmospheric context, not target illumination. |
| `IsoGameCharacter.getLightInfo2()` | `IsoGameCharacter.java:15916-15945` | Read-only field read | Coupled to character model shader | Model shader rendering info, not tile illumination | Exposed on `IsoGameCharacter` | **REJECTED:** Shader rendering parameter for character mesh. |
| `IsoZombie` vision lighting check | `IsoZombie.java:1903-1905, 2208-2212, 4770-4773` | **Non-read-only** (borrows player slot -> `checkRoomSeen`) | Borrows target player slot (`0..3`), defaults to `0` | Borrows player's prior render cache or falls back to global climate | Not an independent API | **REJECTED:** These inspected AI paths do not establish independent lighting. |
| `IsoGameCharacter.CanSee(IsoMovingObject / IsoObject)` | `IsoGameCharacter.java:4729-4735` | Read-only | Independent of player camera | Geometric raycast (`LosUtil.lineClear != Blocked`) | Exposed on `IsoGameCharacter` | **REJECTED:** Pure geometric line-clear; zero illumination awareness. |
| `IsoGridSquare.interpolateLight(ColorInfo, float, float)` | `IsoGridSquare.java:4236-4260` | Mutates passed `ColorInfo` | Hardcoded to `IsoCamera.frameState.playerIndex` | Render-time vertex interpolation | Exposed on `IsoGridSquare` | **REJECTED:** Hardcoded to active human player camera. |
| `IsoGridSquare.getDarkMulti(int playerIndex)` / `getVertLight` | `IsoGridSquare.java:8083-8095, 8328-8330` | Field read | Coupled to human player slots `0..3` | Vertices updated only during player viewport render | Exposed on `IsoGridSquare` | **REJECTED:** Coupled to player slots `0..3`. |
| `IsoGridSquare.resultLightCount()` / `getResultLight(i)` | `IsoGridSquare.java:10625-10631` | Read-only | Independent | Returns constant `0` / `null` under `LightingJNI` | Exposed on `IsoGridSquare` | **REJECTED:** Dead legacy stub in JNI mode. |
| `IsoGridSquare.getLightInfluenceR/G/B()` | `IsoGridSquare.java:7910-7932` | Read-only | Independent | No general freshness or illumination provenance established | Exposed on `IsoGridSquare` | **REJECTED:** Specialized fire flicker array, not general illumination. |
| `IsoCell.getLamppostPositions()` / `IsoLightSource` | `IsoCell.java:2554-2565`, `IsoLightSource.java:34-263` | Read-only list traversal | Light sources independent; raycast engine in JNI | Only explicit lamp objects; ignores sunlight/sky/darkness | Exposed on `IsoCell`, `IsoLightSource` | **REJECTED:** JNI computes lightmaps only for players; ignores sun/ambient. |
| `RoomDef.lightsActive` / `IsoRoomLight` | `RoomDef.java:57`, `IsoRoomLight.java:26-91` | Read-only boolean read | Independent of player slot | Blueprint switch flag; ignores power/daylight/windows | `RoomDef` exposed; `IsoRoomLight` NOT exposed | **REJECTED:** Switch state, not tile illumination (no sunlight/power awareness). |
| `ServerLOS` / `ServerLOS$ServerLighting` | `ServerLOS.java:20-178` | Synchronized server thread | Dedicated multiplayer server only | Per-client LOS grid | **No explicit registration found; Lua reachability unverified** | **REJECTED:** Uninitialized in single-player; dedicated server only. |
| `GameTime.getSkyLightLevel()` | `GameTime.java:685-705` | **Non-read-only** (calls `doInvalidateGlobalLights`) | Hardcoded to `IsoPlayer.getPlayerIndex()` | Macro sky value; no spatial coordinates | Exposed on `GameTime` | **REJECTED:** Player-coupled and mutates engine global lighting state. |
| `IsoChunk.lightCheck` / `lightingNeverDone` | `IsoChunk.java:384-385, 510-580` | Read-only array reads | Fixed size 4 (`new boolean[4]`) for human player slots | Dirty flags for chunk lighting, not illumination levels | Exposed on `IsoChunk` | **REJECTED:** Hardcoded to player slots `0..3`. |

---

## 3. Detailed Findings by Candidate Access Path

### 3.1 The `-1` Player Index JNI Bypass
Static decompilation of `IsoGridSquare.java:9101-9113` demonstrates that passing `playerIndex = -1` invokes `getLightLevel2()`, allocating a temporary `LightingJNI.JNILighting(-1, this)` and reading its `lightInfo()`.

Bytecode inspection of `LightingJNI$JNILighting.update()` reveals the execution path when `playerIndex == -1`:
- **Offsets 5->19, 24->40, and 45->134** separately bypass the FBO path, initial indexed counter guard, and native refresh condition for `playerIndex == -1`.
- **Offsets 63..131 Bypassed:** In standard indexed updates, offsets 63..131 call static native methods `LightingJNI.getSquareDirty` (offset 91) and `LightingJNI.getSquareLighting` (offset 128) to populate `LightingJNI$JNILighting.lightInts`.
- **Offsets 171..307:** The method unpacks values from the shared static array `lightInts`. Because native synchronization was bypassed, the buffer reflects whatever data was previously stored there rather than freshly computed values for the target square.
- **Offset 315:** A `putfield` instruction writes the unpacked light level into `IsoGridSquare.lightLevel` (`LightingJNI$JNILighting.java:190, 307`).

Calling `getLightLevel(-1)` or `getLightLevel2()` mutates `square.lightLevel` and reads unrefreshed shared memory. It fails both read-only safety and freshness requirements.

### 3.2 Indexed Lighting Mutation and Player Coupling
For valid player indices (`0..3`), `IsoGridSquare.getLightLevel(int)` delegates to `this.lighting[playerIndex].lightInfo()` (`IsoGridSquare.java:9105-9106`). Under JNI, `lightInfo()` triggers `update()` (`LightingJNI$JNILighting.java:107-109`).

`update()` is not read-only:
- It mutates instance fields `vis`, `cacheDarkMulti`, `cacheTargetDarkMulti`, and writes to `this.square.lightLevel` (`LightingJNI$JNILighting.java:181-190, 293-307`).
- If `vis` indicates the square is seen, it executes room discovery logic: calling `this.square.checkRoomSeen(playerIndex)` and potentially notifying `Meta.instance.dealWithSquareSeen` (`LightingJNI$JNILighting.java:254-267`).
- In `LightingJNI.java:819-847`, updates are scheduled exclusively per active human player (`IsoPlayer.numPlayers`), chunk maps, and player render settings. An NPC-owned independent lighting slot does not exist on these structures. Querying a local-player slot borrows that player's view state and triggers room-seen side effects.

### 3.3 Cached Lighting Accessors
`IsoGridSquare.getLightInfo(int)` (`IsoGridSquare.java:6951-6953`) directly returns `this.lightInfo[playerNumber]`. This field is an array of `ColorInfo` structures populated during `cacheLightInfo()` (`IsoGridSquare.java:6955-6958`) based on `IsoCamera.frameState.playerIndex`.

The packed RGB getters (`GetRLightLevel`, `GetGLightLevel`, `GetBLightLevel` at `IsoGridSquare.java:625-635`) perform bitwise extraction on `this.lightLevel`. They do not trigger an update or refresh, reflecting only whatever integer was last assigned to `this.lightLevel`.

### 3.4 Lighting Implementation Selection and Lampost Stubs
`IsoGridSquare.java:3994-4002` demonstrates lighting slot instantiation:
- If `GameServer.server` is true, slot 0 receives `ServerLOS.ServerLighting`.
- In client mode, slots receive `LightingJNI.JNILighting` if `LightingJNI.init` is true; otherwise, they fall back to legacy `new Lighting()`.

`IsoGridSquare.getLampostTotalR/G/B()` (`IsoGridSquare.java:8043-8065`) queries `this.lighting[0].lampostTotalR/G/B()`. In `LightingJNI$JNILighting.java:71-81`, these methods are hardcoded to return `0.0f`. Under JNI, legacy lamp totals return zero, which cannot be interpreted as target darkness.

### 3.5 Climate Subsystem Boundaries
`ClimateManager.java:475-587` provides global celestial parameters:
- `getAmbient()`, `getDayLightStrength()`, and `getNightStrength()` call `IsoPlayer.getInstance().isAlwaysDayCheat()`, returning constant values if the human player has cheat mode enabled.
- `getGlobalLight()` and `getGlobalLightIntensity()` (`ClimateManager.java:475-486`) return global climate color and intensity without spatial `(x, y, z)` target association.
- None of these getters calculate local tile attenuation, indoor shadows, roof occlusion, or artificial light sources.

### 3.6 Vanilla Zombie Vision Target Coupling
Decompilation of `IsoZombie.java:1903-1905, 2208-2212, 4770-4773` reveals how the engine's own AI evaluates target visibility:
- In `IsoZombie.update()`:
  Game implementation details are referenced by source locations above; decompiled excerpts remain in ignored runtime artifacts.
- In `IsoZombie.updateVisionRadius()`:
  Game implementation details are referenced by source locations above; decompiled excerpts remain in ignored runtime artifacts.
These inspected zombie paths do not establish independent target lighting. It either borrows the target human player's viewport slot (`character.getIndex()`) or falls back to global celestial ambient. Replicating this for Sarah would couple her sensory results to human player 0 and trigger `checkRoomSeen(playerIndex)`.

### 3.7 Geometric Raycast Character Vision (`IsoGameCharacter.CanSee`)
Inspection of `IsoGameCharacter.java:4729-4735` reveals:
Game implementation details are referenced by source locations above; decompiled excerpts remain in ignored runtime artifacts.
`CanSee` is purely a geometric raycast through `LosUtil.lineClear`. It has zero awareness of ambient light, torch illumination, darkness, or shadows. Per project policy, geometric line-clear must never imply confirmed sight.

### 3.8 Render-Time Vertex Interpolation (`IsoGridSquare.interpolateLight`)
In `IsoGridSquare.java:4250-4254`:
Game implementation details are referenced by source locations above; decompiled excerpts remain in ignored runtime artifacts.
`interpolateLight` explicitly extracts the current rendering camera's `playerIndex` and queries `getVertLight(..., playerIndex)`. It is bound to the human player camera and mutates the passed `ColorInfo`.

### 3.9 Dead Legacy Stubs under LightingJNI (`resultLightCount`, `getResultLight`)
In `IsoGridSquare.java:10625-10631`, `resultLightCount()` returns constant `0` and `getResultLight(i)` returns `null`. These are unpopulated legacy stubs from pre-JNI builds.

### 3.10 Cell Light Source Stack (`IsoCell.getLamppostPositions`, `IsoLightSource`)
`IsoCell.getLamppostPositions()` returns a `Stack<IsoLightSource>` of registered active light sources (lamps, streetlights, campfires, flashlights). In `LightingJNI.java:280-352`, these objects are transferred to native C++ via `LightingJNI.addLight(...)`, whose inspected Java scheduling uses active player viewports `0..3`*.
The inspected deprecated source update checks power and may change activity; it is not an admitted read-only illumination query. Furthermore, light source stacks do not account for daylight, sky light, or wall/window shadow attenuation.

### 3.11 Room Definition Switch State (`RoomDef.lightsActive`, `IsoRoomLight`)
`RoomDef.lightsActive` (`RoomDef.java:57`) is a boolean indicating whether a room's light switch is toggled on. It cannot establish tile illumination:
1. It ignores whether electrical power is available (no generator/hydro = room is dark even if switch is ON).
2. It ignores daytime sunlight through windows (room can be brightly lit at noon even if switch is OFF).
3. Outdoor squares have no `RoomDef` (`room == null`).
4. `IsoRoomLight` is an internal engine class and is not exposed to Lua in `LuaManager$Exposer`.

### 3.12 Server-Side LOS Network Subsystem (`ServerLOS`)
`ServerLOS.java:20-178` manages server-side visibility grids in multiplayer (`GameServer.server`). It is uninitialized in single-player sandbox play (`ServerLOS.instance == null`) and is not exposed to Lua.

### 3.13 Global Sky Light Level Mutation (`GameTime.getSkyLightLevel`)
In `GameTime.java:685-705`:
Game implementation details are referenced by source locations above; decompiled excerpts remain in ignored runtime artifacts.
`getSkyLightLevel()` queries the human player's render settings and, when the level changes, calls native `LightingJNI.doInvalidateGlobalLights(...)`, mutating global engine lighting state as a side effect. It lacks target-square spatial association.

### 3.14 Chunk Player Lighting Arrays (`IsoChunk.lightCheck`, `lightingNeverDone`)
In `IsoChunk.java:384-385, 510-580`, `lightCheck` and `lightingNeverDone` are fixed arrays of size 4 (`new boolean[4]`) indexed by human player splitscreen slots `0..3`. No independent NPC lighting slot is established by these inspected arrays.

---

## 4. Lua Exposure Analysis in Build 42.21

Inspection of `zombie/Lua/LuaManager$Exposer.java` (explicit setExposed registrations, including IsoLightSource at2320 and RoomDef at2337 in this snapshot) confirms:
- **Exposed Classes:** `IsoGridSquare`, `IsoCell`, `IsoChunk`, `IsoBuilding`, `IsoRoom`, `BuildingDef`, `RoomDef`, `IsoLightSwitch`, `IsoLightSource`, `ClimateManager`, `LosUtil`, and `GameTime`.
- **Unexposed / Internal Classes:** `LightingJNI`, `LightingJNI$JNILighting`, `IsoRoomLight`, `ServerLOS`, `ServerLOS$ServerLighting`, and `LightingThread` were not found in the inspected explicit registration list; actual Lua reachability remains unverified.
- **Exposure boundary:** Class registration is a static candidate signal, not proof of method overload exposure or reachability through returned objects. Actual Lua access remains a native gate.

---

## 5. Conclusions & Recommendations

1. **Bounded audit result:** No inspected candidate established read-only, fresh, player-independent target-square illumination. Every examined route either:
   - Couples directly to local human player camera viewports `0..3`,
   - Mutates engine seen-cache or lighting state (`checkRoomSeen`, `doInvalidateGlobalLights`, field write at offset 315),
   - Is a dead legacy stub returning constant zero or null under JNI,
   - Is purely geometric raycasting without illumination awareness (`LosUtil.lineClear`, `CanSee`), or
   - Is an electrical switch boolean that fails daylight, window, and power-grid reality checks.
2. **Recommendation:** **REJECT ALL CANDIDATES.** Independent lighting remains strictly **OPEN**. No speculative scaffolding or mock lighting is created. `DiagnosticSampler.lua` must continue unconditionally returning `lighting = "unknown"` and `visual = "unknown"` (confirmed visual count = 0).
3. **Smallest Proposed Native Verification for Codex (Gate B):**
   When live testing Gate B in the isolated profile:
   - Position Sarah in a windowless room with no lights at midnight.
   - Confirm via `look` / `perceive` diagnostic commands that geometry detects objects within range, but visual confirmation remains strictly `0` with `lighting: unknown`.
   - Rotate the human player 180 degrees away or move the player outside: verify that Sarah's observation counts and unknown lighting output remain strictly identical, as an observation only, not proof of cache independence.
