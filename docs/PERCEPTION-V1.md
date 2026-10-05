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
| Loaded coverage | cell.getGridSquare; LosUtil.lineClear skips adjacency checks when squares missing | Implementation inspected; complete conservative coverage walker not implemented |
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
