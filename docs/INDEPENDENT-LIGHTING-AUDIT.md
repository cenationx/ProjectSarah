# Project Sarah: Bounded Offline Lighting Candidate Audit

**Checkpoint:** `2cce1d8`  
**Scope:** Bounded static inspection of supplied source files and confirmed bytecode offsets  
**Binary Reference:** Installed JAR SHA256 `E1A69EB743EDE60B213A0FE7F8B83D4FCAB773036D256CC4543A336F3B058A33`  
**Review Authority:** Codex

Gemini 3.8 Flash HIGH drafted/revised through NO-TOOLS CLI exports; Codex
corrected remaining branch-target, safety and scope statements and verified the
installed hash plus selected Code attributes. No Gemini checkout edits.
Source locations below are relative to ignored `runtime/research-adapter-20261005/fresh/`;
CFR snapshots have unresolved dependencies. No game classes initialized, JNI
called, native Lua probed, deployment performed or saves/settings changed.  

---

## 1. Scope & Objective

This audit evaluates whether any candidate method or field within the supplied Project Zomboid codebase (`IsoGridSquare`, `LightingJNI`, and `ClimateManager`) can provide read-only, target-square illumination independent of local human player slots for Sarah's autonomous perception.

This analysis is strictly bounded to the supplied source snapshot and verified bytecode attributes. It does not assert that no other engine lighting interfaces exist, nor does it claim native execution or live Lua testing. The objective is to determine if any supplied candidate justifies native wiring or if the diagnostic adapter must continue forcing `lighting = "unknown"`.

---

## 2. Candidate Evaluation Matrix

| Candidate Method / Field | Source Location | Read-Only Safety | Player Independence | Target Association & Freshness | Operational Verdict |
| :--- | :--- | :--- | :--- | :--- | :--- |
| `IsoGridSquare.getLightLevel(-1)` / `getLightLevel2()` | `IsoGridSquare.java:9101-9113` | **Non-read-only** (writes `square.lightLevel`) | Bypasses slot check via `-1` | Unrefreshed shared buffer; target association unverified | **REJECTED:** Bytecode proves native refresh bypass and field mutation. |
| `IsoGridSquare.getLightLevel(playerIndex)` | `IsoGridSquare.java:9101-9107` | **Non-read-only** under JNI (`update()` side-effects) | Coupled to player slots `0..3` | Coupled to player camera / render updates | **REJECTED:** Mutates internal cache/seen state; player-bound. |
| `IsoGridSquare.getLightInfo(playerNumber)` | `IsoGridSquare.java:6951-6953` | Read-only field read | Coupled to player slots `0..3` | Frame-cached array from prior render | **REJECTED:** Reflects player render camera frame cache. |
| Packed `IsoGridSquare.lightLevel` (`GetRLightLevel`, etc.) | `IsoGridSquare.java:625-635` | Read-only field read | Indirectly player-coupled | Passive; no refresh performed on access | **UNSUITABLE WITHOUT FRESHNESS PROOF:** Passive cached int; no refresh or provenance on access. |
| `IsoGridSquare.getLampostTotalR/G/B()` | `IsoGridSquare.java:8043-8065` | Read-only | Hardcoded to slot 0 | Constant `0.0f` under `LightingJNI` | **REJECTED:** Dead accessor in JNI mode; returns zero. |
| `ClimateManager.getAmbient()` / `getDayLightStrength()` | `ClimateManager.java:515-528, 581-587` | Read-only | Macro-level; cheat-override vulnerable | No spatial `(x, y, z)` target association | **REJECTED:** Macro environmental context, not target illumination. |
| `ClimateManager.getGlobalLight()` / `getGlobalLightIntensity()` | `ClimateManager.java:475-486` | Read-only | Macro-level | No spatial `(x, y, z)` target association | **REJECTED:** Macro environmental context, not target illumination. |

---

## 3. Detailed Findings by Access Path

### 3.1 The `-1` Player Index JNI Bypass
Static decompilation of `IsoGridSquare.java:9101-9113` shows that passing `playerIndex = -1` invokes `getLightLevel2()`, allocating a temporary `LightingJNI.JNILighting(-1, this)` and reading its `lightInfo()`.

Bytecode inspection of `LightingJNI$JNILighting.update()` reveals the execution path when `playerIndex == -1`:
- **Offset 5 jumps to19, offset24 jumps to40, and offset45 jumps to134** for `playerIndex == -1`. These separately bypass the FBO path, initial indexed counter guard and native refresh condition.
- **Offsets 63..131 Bypassed:** In standard indexed updates, offsets 63..131 call static native methods `LightingJNI.getSquareDirty` (offset 91) and `LightingJNI.getSquareLighting` (offset 128) to populate `LightingJNI$JNILighting.lightInts`.
- **Offsets 171..307:** The method unpacks values from the shared static array `lightInts`. Because native synchronization was bypassed, the buffer reflects whatever data was previously stored there rather than freshly computed values for the target square.
- **Offset 315:** A `putfield` instruction writes the unpacked light level into `IsoGridSquare.lightLevel` (`LightingJNI$JNILighting.java:190, 307`).

Calling `getLightLevel(-1)` or `getLightLevel2()` mutates `square.lightLevel` and reads un-refreshed shared memory. It does not provide safe, verified target illumination.

### 3.2 Indexed Lighting Mutation and Player Coupling
For valid player indices (`0..3`), `IsoGridSquare.getLightLevel(int)` delegates to `this.lighting[playerIndex].lightInfo()` (`IsoGridSquare.java:9105-9106`). Under JNI, `lightInfo()` triggers `update()` (`LightingJNI$JNILighting.java:107-109`).

`update()` is not read-only:
- It mutates instance fields `vis`, `cacheDarkMulti`, `cacheTargetDarkMulti`, and writes to `this.square.lightLevel` (`LightingJNI$JNILighting.java:181-190, 293-307`).
- If `vis` indicates the square is seen, it executes room discovery logic: calling `this.square.checkRoomSeen(playerIndex)` and potentially notifying `Meta.instance.dealWithSquareSeen` (`LightingJNI$JNILighting.java:254-267`).
- In `LightingJNI.java:819-847`, updates are scheduled per active human player (`IsoPlayer.numPlayers`), chunk maps, and player render settings. A Sarah-owned independent lighting slot has not been established. Querying a local-player slot borrows that player's view state and can trigger room-seen side effects.

### 3.3 Cached Lighting Accessors
`IsoGridSquare.getLightInfo(int)` (`IsoGridSquare.java:6951-6953`) directly returns `this.lightInfo[playerNumber]`. This field is an array of `ColorInfo` structures on `IsoGridSquare`, distinct from `this.lighting[playerIndex].lightInfo()`. It is populated during `cacheLightInfo()` (`IsoGridSquare.java:6955-6958`) based on `IsoCamera.frameState.playerIndex`.

The packed RGB getters (`GetRLightLevel`, `GetGLightLevel`, `GetBLightLevel` at `IsoGridSquare.java:625-635`) perform bitwise extraction on `this.lightLevel`. They do not trigger an update or refresh. They reflect whatever integer was last assigned to `this.lightLevel`, providing no guarantee of freshness.

### 3.4 Lighting Implementation Selection and Lampost Stubs
`IsoGridSquare.java:3994-4002` demonstrates lighting slot instantiation:
- If `GameServer.server` is true, slot 0 receives `ServerLOS.ServerLighting`.
- In client mode, slots receive `LightingJNI.JNILighting` if `LightingJNI.init` is true; otherwise, they fall back to `new Lighting()`.

`IsoGridSquare.getLampostTotalR/G/B()` (`IsoGridSquare.java:8043-8065`) queries `this.lighting[0].lampostTotalR/G/B()`. In `LightingJNI$JNILighting.java:71-81`, these methods are hardcoded to return `0.0f`. The inspected fallback `IsoGridSquare$Lighting.java:31-41` getters read stored lamp totals instead; this is not an independent freshness/target proof. Under JNI the totals return zero, which must not be interpreted as target darkness. ServerLighting semantics were not audited in this batch.

### 3.5 Climate Subsystem Boundaries
`ClimateManager.java:475-587` provides global celestial parameters:
- `getAmbient()`, `getDayLightStrength()`, and `getNightStrength()` include branches returning constant `1.0f` or `0.0f` if `IsoPlayer.getInstance().isAlwaysDayCheat()` is active.
- `getGlobalLight()` and `getGlobalLightIntensity()` (`ClimateManager.java:475-486`) return global climate color and intensity without that cheat check in the inspected lines.
- None of these getters accept `(x, y, z)` spatial coordinates. They describe macro-environmental atmospheric conditions. They do not compute local tile attenuation, indoor shadows, roof occlusion, or artificial light sources.

---

## 4. Architectural & Pipeline Implications

1. **Perception vs. Sampler Boundaries:** `Perception.lua` supports injected lighting callbacks (`query("lighting")`), which can return `"detectable"`, `"undetectable"`, or `nil`. `DiagnosticSampler.lua` intentionally omits this callback, locking ambient evaluation to `lighting = "unknown"`. This design ensures geometric checks remain testable while blocking unearned visual confirmation.
2. **Knowledge Integrity:** DiagnosticSampler does not call Knowledge. Existing records remain governed by Knowledge's normal expiry/reset policy. Forcing `lighting = "unknown"` guarantees that no *new* visual records or target positions are committed based on unverified lighting.
3. **Prerequisites for Future Lighting Integration:** To establish valid lighting semantics in a future phase, a candidate query must demonstrate: verified freshness, verified spatial target association, read-only safety (no engine state mutation or room-seen side effects), and independence from human player camera slots. A safely populated read-only cache satisfying these criteria would be acceptable; C++ native purity is not required.

---

## 5. Conclusion

No candidate within this bounded supplied-source inspection establishes trustworthy read-only, player-independent target illumination. `DiagnosticSampler` must continue enforcing `lighting = "unknown"`.

## Codex verification and next offline boundary

Fresh installed hash matches the pinned archive. Direct parsing of existing
Code attributes reconfirmed the -1 path (45->134, native calls91/128 skipped,
square field write315). Additional selected method attributes confirm packed RGB
accessors read lightLevel at offset1, getLightInfo reads the cached array at1,
lamp totals delegate through the lighting array, and climate ambient/day/night
call IsoPlayer.getInstance/isAlwaysDayCheat before their climate values. These
are symbolic inspection facts, not reproduced native behavior.

The 57 existing sampler composition fixtures were rerun successfully, including
unknown lighting and actual Knowledge rejection. This documentation-only batch
does not rerun or increase the prior full507+11+19 baseline. No runtime code changed.
Local inspection readers/exports remain ignored under
`runtime/lighting-audit-gemini-20261006/` and
`runtime/coverage-gemini-20261005/`; no game source, class files or raw exports
are committed. See `evidence/lighting-audit-offline-20261006.txt`.

Next offline coding batch: Gemini authors an inert, bounded native exposure
diagnostic artifact against `NATIVE-ADAPTER-DIAGNOSTIC-SPEC.md`; Codex applies/
reviews/tests it without native invocation. Its purpose is to prepare explicit
future checks for Lua overloads/enum wrappers and lifecycle, not to certify
actual exposure offline. It must never query the rejected lighting methods or
register callbacks/actions. Native execution/deployment and Follow/rendering
acceptance remain deferred. External/model AI stays ON HOLD.
