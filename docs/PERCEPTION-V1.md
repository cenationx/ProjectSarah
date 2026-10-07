# Perception V1: offline policy and later native batch

2026-10-05. Implemented offline; not integrated, deployed or natively accepted.
External/model AI remains ON HOLD. Codex owns checkout.

## API and scope

`Perception.new({range=12, coneDegrees=90}):sample(observer, candidates, queries)`
returns `{results, processed, truncated}`. Observer is `{x,y,z,forward={x,y}}`;
candidates are a dense array of plain `{id,kind,x,y,z}` snapshots. ID is a
nonempty session-local string up to 96 characters; kind is player or zombie.
Only the first 32 entries are processed, in caller order. The caller must bound
enumeration separately and rotate/otherwise schedule candidates fairly if a
crowd exceeds the cap. This module does not enumerate native objects.

Query callbacks receive observer and candidate and must be read-only:
- coverage: exactly true only after endpoints AND intervening sampled geometry
  are known loaded; anything else is unknown.
- obstruction: normalized clear / blocked / unknown. Native enum strings are
  never automatically accepted. A future adapter must document door/window
  interpretation from installed code and tests.
- lighting: detectable / undetectable / unknown. No verified query means unknown.

Each result has id/kind when valid, geometric/visual status and reason. Position
is copied only for confirmed visual detection. Out-of-cone/range/floor is blocked;
invalid or coincident positions, invalid facing, missing coverage and exceptions
are unknown. A clear geometric result with unverified lighting remains visually
unknown. No hearing or near-field exception. Range/cone are prototype defaults;
configuration bounds are positive range up to 64 tiles and cone up to 360 degrees.

`Knowledge.new()` exposes `update(sample, nowSeconds)`, `snapshot(nowSeconds)`
and `reset()`. Time is nonnegative monotonic seconds supplied by the caller,
not game ticks or wall clock guessed internally. A backward clock clears memory.
Only confirmed visual/geometric records enter memory; snapshots and input
positions are copied. Cap 32 records, expiry at age >=10 seconds, oldest
observation evicted first (insertion sequence breaks ties). Hidden/omitted
candidates do not refresh records. No native object handles or saved state.

A future integration MUST call reset on session change, Sarah replacement,
unload and death. No callbacks are registered in this package, so these reset
boundaries are caller obligations tested offline, not live wiring. Stop need not
clear passive memory and cannot cause either module to initiate an action.

## Installed engine candidates

See COMPANION-ENGINE-RESEARCH.md for jar hash and fresh decompilation provenance.

| Concern | Candidate / inspected evidence | Status |
|---|---|---|
| Facing | IsoGameCharacter.getForwardDirectionX/Y return forward-vector components (fresh lines 2574/2578) | Implementation inspected; Lua exposure and correctness during turning/off-camera unverified |
| Local enumeration | IsoGridSquare.getMovingObjects used by installed character code around line 6951; bound square queries around Sarah | Call site inspected; collector cost, exposure, filtering and fair cap scheduling unverified |
| Loaded coverage | cell.getGridSquare; LosUtil.lineClear skips adjacency checks when squares missing | Implementation inspected; conservative bounded rectangle helper implemented offline (COVERAGE-OFFLINE.md); native coverage unverified |
| Obstructions | CanSee -> LosUtil.lineClear; separate clear/window/open-door/closed-door results | Implementation inspected; exact material/door mapping and Lua enum access unverified |
| Lighting | current renderer uses square:getLightInfo(playerIndex) | Player-relative call inspected; no verified independent sensory lighting query available |
| Character identity | caller-provided session IDs | Offline contract only; native session ID registry still required, must not imply persistence |

No production adapter is added until these gaps are resolved. Candidate
enumeration is not knowledge. Player sight and light caches cannot be substituted
for Sarah's independent sense. Geometric diagnostics must not trigger behavior.

## Later isolated batch (prepared checklist, not executed)

Prerequisites: resolve adapter/light exposure; build diagnostic-only sampler;
prove conservative loaded coverage and lifecycle resets offline; review and
record the exact deployed revision. Keep current Stop guarantees. No autonomous
combat, looting or work is enabled by this batch.

1. Close isolated game. Back up current disposable world, keys/settings and log
   into a new timestamped project-local group. Current case is
   runtime/isolated/Saves/Sandbox/2026-10-05_19-04-21; recheck shared HANDOFF before
   use. Preserve any newer state before restoring; normal profile stays untouched.
2. Deploy reviewed diagnostic build only to isolated profile. Use a zero-zombie
   controlled case and deliberately introduced test target only when appropriate.
3. Fix Sarah/target positions; rotate Sarah and player independently. Log facing,
   distance, coverage, obstruction, geometric/visual state, light status and
   last-seen position/time. Unknown lighting is an explicit incomplete gate.
4. Test front/behind, exact range/cone boundaries, opaque wall, closed/open door,
   window, missing world coverage, and noon/night/dark interior/flashlight.
5. Observe target, occlude it and move it: memory retains old position, expires
   after 10 seconds, and updates only when reacquired. Player turning must not
   alter Sarah's sensory result by itself.
6. Separate rendering check: nearby look-away, wall and floor occlusion. Do not
   remove renderer guards as part of perception. Current rendering may still
   hide Sarah; log evidence is separate from visual acceptance.
7. Pending Follow regression: responsive retargeting, moving/standing player,
   Stop mid-stride/no resumption, stall across replacements, obstacle/startup
   delays, leash, reload and user WASD. Record path progress/jitter limitations.
8. Menu/world teardown, reload and replacement clear sensory memory; verify no
   extra callbacks/actions. Clean exit, archive sanitized evidence and final save.

Recovery: close game first; archive failed/newer case before restoration; restore
only the explicitly selected disposable backup and compatible isolated deployed
revision. Never overwrite the only copy of latest test state.

## Evidence and research handling

46 actual-Lua perception/memory checks pass; full runner 268 checks, plus 11
runner and 19 preflight self-tests pass. First aggregate run rejected this suite's
summary format; corrected to standard RESULT line, then all suites passed.
No gameplay acceptance follows from these fixtures.

The pasted deep-research report has unresolved retrieval citation tokens. Its
additional Kenshi, CDDA and State of Decay claims are NOT promoted to verified
project evidence. Previously pinned/linked findings remain in the engine report;
future additions require direct source links, pinned symbols and verification.
The report's automatic-resume policy and near-field exception are not adopted.

Roadmap sequence remains foundation acceptance -> sight -> directed equipment
and transfers -> bounded defense -> one container/house -> exchange -> one
native barricade -> separately authorized external AI. Each stage retains native
acceptance gates. Next offline work is exposure/coverage/lighting investigation,
not autonomous behaviors or deployment.

## Subsequent offline adapter investigation (2026-10-05)

See [NATIVE-PERCEPTION-ADAPTER-RESEARCH.md](NATIVE-PERCEPTION-ADAPTER-RESEARCH.md)
for fresh Lua registration, diagonal coverage dependencies and the unverified
getLightLevel(-1) shared-buffer path. It supersedes earlier exposure/coverage/light
candidate summaries without establishing native capability. Coverage helper is
proposed only; lighting remains unknown. No integration/deployment/live tests.
All 268 suite +11 runner +19 preflight self-tests passed; Codex owns checkout.

## Coverage helper checkpoint (2026-10-05)

Coverage.lua remains offline, with an explicit shared sample context and no
cross-call square cache; see COVERAGE-OFFLINE.md. All 332 suite checks (including
64 coverage) +11 runner +19 preflight self-tests PASS. Direct bytecode inspection
confirmed the -1 light branch bypasses refresh and writes square.lightLevel;
keep lighting unknown. No new callbacks, sight/memory wiring, deployment or
live acceptance. Native independent light and Follow/rendering remain open.

## Monotonic memory clock offline candidate and open lighting blocker (2026-10-07)

1. **Independent Lighting**: Evaluated candidate engine classes (`IsoGridSquare`, `LightingJNI`, `ClimateManager`, `IsoGameCharacter.getLightInfo2()`, `LuaManager$Exposer`). No admissible independent lighting route was established among these candidates; the independent lighting blocker remains OPEN. This analysis does not assert that no suitable API exists anywhere in the engine, but confirms that evaluated candidates fail read-only, freshness, or player-independence requirements:
   - Native JNI lighting in `LightingJNI` is strictly bound to human player camera viewports (`0..3`). No NPC sensory lighting slot exists on these inspected structures.
   - The `-1` index bypasses native JNI refresh (offsets 91/128), unpacks stale buffers, and writes to `square.lightLevel` (bytecode offset 315).
   - Calling player indices (`0..3`) mutates room-seen discovery state (`checkRoomSeen`).
   - Passive getters (`GetRLightLevel`, `getLightInfo`) read unrefreshed render caches without freshness guarantees.
   - Climate getters are non-spatial macro celestial parameters subject to human player cheat flags.
   - Character `getLightInfo2()` computes model shader rendering info, not target tile illumination.
   - Therefore, `lighting = "unknown"` is strictly preserved across all perception passes. Visual detection remains `visual = "unknown"` (confirmed = 0); unknown lighting never implies sight. The independent lighting blocker remains OPEN.
2. **Monotonic Memory Clock**: Injected into `Console.lua` via bounded accumulation of engine simulation delta:
   - Evaluated `GameTime.getTimeDelta()` implementation, multiplier chain, sleeping branch, and `OnTick` ordering:
     * Multiplier chain: Active-play `getTimeDelta()` computes `multiplier / 0.8f / multiplierBias / 60.0f` where normal active-play `multiplier = speedMultiplier * fpsMultiplier * multiplierBias * perObjectMultiplier * slomo * 0.8f`.
     * The `0.8f` factor and `multiplierBias` cancel out algebraically.
     * Separate all-players-asleep branch: `GameTime.getMultiplier()` has an explicit branch for sleeping characters (lines 941-944) returning `200.0f * (30.0f / (float)PerformanceSettings.getLockFPS())`; the normal multiplier formula does not cover this branch.
     * FPSTracking cap and simulation time semantics: `FPSTracking.java` caps its multiplier at `5.0f` (`fpsMultiplier <= 5.0f`), so `getTimeDelta()` represents engine simulation time, not guaranteed wall-clock real time.
     * Units and speed semantics: Units are simulation elapsed seconds per frame. At 1x speed this matches stepped simulation frame delta; at fast-forward and accelerated sleep it scales with engine simulation speed.
     * `OnTick` ordering: In `IngameState.java`, `UpdateStuff()` executes at line 1779; inside `UpdateStuff()`, `GameTime.getInstance().update(...)` runs at line 773. Subsequent subsystem updates (`ScriptManager`, `WorldSoundManager`, etc.) execute before line 1788 invokes `this.onTick()`. Thus `UpdateStuff` runs before `OnTick`, and `GameTime.update` is not immediately adjacent to `Events.OnTick`.
     * Arbitrary 5.0s delta clamp removed: Clamping discards legitimate elapsed simulation time during fast-forward or sleep acceleration, artificially prolonging observation memory freshness.
   - Fail-closed pause handling: `getEngineDelta()` strictly requires a successfully validated boolean pause state from `gt.isGamePaused()` or valid non-negative speed-control result from `UIManager.getSpeedControls().getCurrentGameSpeed()`. If both checks are missing, throwing, or malformed, it invalidates observation memory immediately (`resetKnowledge()`), flags discontinuity (`clockDiscontinuous = true`), and fails closed (`nil, "pause state unavailable or unverified"`).
   - Clock discontinuities: Missing, throwing, or invalid deltas (`nil`, error, negative, NaN, infinite) invalidate observation memory immediately (`resetKnowledge()`), flag discontinuity, and fail closed without silent zero or wall-clock fallbacks.
   - Failure & Recovery: Recovery resumes clean accumulation without silently retaining records whose elapsed age was unknown.
   - Invalidation on clock reversal: Non-monotonic time (`t < lastNow`) triggers immediate memory invalidation.
   - Fully verified offline with production-source regressions in `tools/test_console.py` (45 checks) and `tools/test_commands.py` (67 checks); 731 suite checks across 16 suites pass. Diagnostic-only; native timing and acceptance remain pending Gate B live testing. Independent lighting blocker remains OPEN.

## Extended independent lighting candidate investigation and open blocker (2026-10-07)

Gemini completed bounded static inspection of new independent lighting candidates across Build 42.21 decompiled classes, confirmed bytecode offsets, and Lua exposure mappings (see `docs/INDEPENDENT-LIGHTING-AUDIT.md` for the full matrix):

1. **New Inspected Candidates & Findings**:
   - `IsoZombie` vision checks (`IsoZombie.java:1903-1905, 2208-2212, 4770-4773`): The inspected zombie paths use player lighting or climate values. It borrows the target human player's viewport slot (`character.getIndex()`) to read `lighting[playerIndex]` (triggering `checkRoomSeen`) or falls back to global celestial ambient. Replicating this couples Sarah to player 0 and mutates room-seen state. REJECTED.
   - `IsoGameCharacter.CanSee` (`IsoGameCharacter.java:4729-4735`): Pure geometric raycast delegating to `LosUtil.lineClear != LosUtil.TestResults.Blocked`; zero illumination awareness. REJECTED.
   - `IsoGridSquare.interpolateLight` (`IsoGridSquare.java:4236-4260`): Directly extracts `IsoCamera.frameState.playerIndex` at lines 4250-4254; bound to human player rendering camera and mutates passed `ColorInfo`. REJECTED.
   - `IsoGridSquare.getDarkMulti / getVertLight` (`IsoGridSquare.java:8083-8095, 8328-8330`): Coupled to human player splitscreen slots `0..3`. REJECTED.
   - `IsoGridSquare.resultLightCount / getResultLight` (`IsoGridSquare.java:10625-10631`): Dead legacy stubs returning constant `0` / `null` under `LightingJNI`. REJECTED.
   - `IsoGridSquare.getLightInfluenceR/G/B` (`IsoGridSquare.java:7910-7932`): Populated only by `IsoFireManager` for fire flicker effects; null on all normal non-burning tiles. REJECTED.
   - `IsoLightSource` & `IsoCell.getLamppostPositions` (`IsoLightSource.java:34-263`, `IsoCell.java:2554-2565`): Registered lamp objects are passed to native C++ where `LightingJNI` computes lightmaps only for human viewports `0..3`. Discards sunlight, sky light, and ambient darkness. REJECTED.
   - `RoomDef.lightsActive` (`RoomDef.java:57`): Blueprint electrical switch flag; fails daylight/window illumination, power-grid validation, and outdoor tiles. `IsoRoomLight` is internal and not exposed to Lua. REJECTED.
   - `ServerLOS` (`ServerLOS.java:20-178`): Dedicated server multiplayer only; uninitialized in single-player sandbox and not exposed to Lua. REJECTED.
   - `GameTime.getSkyLightLevel` (`GameTime.java:685-705`): Queries player 0 render settings and mutates global engine lighting state (`LightingJNI.doInvalidateGlobalLights`). Lacks target-square spatial association. REJECTED.
   - `IsoChunk.lightCheck / lightingNeverDone` (`IsoChunk.java:384-385, 510-580`): Fixed arrays of size 4 (`new boolean[4]`) indexed by human player splitscreen slots `0..3`. REJECTED.

2. **Lua Exposure Constraints**:
   - `LuaManager$Exposer.java` exposes `IsoGridSquare`, `IsoCell`, `IsoChunk`, `RoomDef`, `IsoLightSource`, and `ClimateManager`, but none expose a parameterless or player-independent method that returns fresh, read-only tile illumination.
   - `LightingJNI`, `IsoRoomLight`, and `ServerLOS` were not found in the inspected explicit class registration list; actual Lua reachability remains unverified.

3. **Blocker Status & Policy**:
   - ALL CANDIDATES REJECTED. No inspected candidate established read-only, fresh, player-independent target tile illumination.
   - Independent lighting blocker remains strictly and honestly OPEN. No speculative scaffolding or mock lighting is introduced.
   - `lighting = "unknown"` preserved unconditionally across all perception passes; visual detection remains `visual = "unknown"` (confirmed = 0); unknown lighting never implies sight.
   - External/model AI strictly ON HOLD.

4. **Smallest Proposed Native Verification for Gate B**:
   - In isolated profile, position Sarah in an unlit windowless room at midnight. Verify `look` / `perceive` report geometry counts while visual confirmation remains strictly `0` with `lighting: unknown`.
   - Rotate human player away or step outside: verify Sarah's outputs remain identical, as an observation only, not proof of cache independence.
