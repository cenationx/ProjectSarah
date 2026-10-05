# Native adapter diagnostic specification

2026-10-06. Reviewed design only, based on offline checkpoint aa7595f.
Gemini 3.8 Flash HIGH drafted through a temporary user-visible Remote Control
session with NO TOOLS; Codex reviewed and owns all checkout changes. No collector,
native probe, integration or deployment is implemented by this document.

## Evidence and unresolved gates

Read NATIVE-PERCEPTION-ADAPTER-RESEARCH.md, COVERAGE-OFFLINE.md and PERCEPTION-V1.md.
Installed class registration/public signatures are offline exposure candidates,
not proof that actual game Lua can invoke a particular overload or read an enum.
Candidates include facing access, existing-cell square lookup, moving-object
lists and LosUtil.lineClear. The enum class is zombie.iso.LosUtil$TestResults.
Overload resolution, wrapper identity, residency, liveness and getter side
effects need separate native validation. Do not infer these from mocks.

Direct bytecode confirms that the playerIndex -1 lighting path skips native
refresh, reads shared lightInts and writes square.lightLevel. Reject that path
and getLightLevel2 as independent read-only light evidence. No certified
Sarah-independent light query has been found; this is not proof none exists.
Lighting remains unknown. Player vision/light caches and CanSee alone cannot
certify Sarah's sight. Follow/rendering acceptance remains separately pending.

## Future probe boundary

An eventual explicitly invoked one-shot probe must remain inert: no tick/event
registration, actions, movement, spawning, square creation/loading, room-seen
writes, highlighting, save writes or automatic repeated sampling. Audit native
getters before invocation; catch query and optional introspection failures.
Never treat tostring, ordinal values or metatable shape as enum proof.
No illumination query is authorized by this specification.

Use injected cancellation and lifecycle checks before/after bounded work blocks.
A synchronous pass does not promise delivery of a user key in the middle of a
native call. Preserve the existing Stop path; never start/resume movement or
register cleanup that could weaken its guarantees.

Capture private controller, Sarah and cell identities, valid finite position,
nonzero finite facing and caller-supplied session generation. Generation is a
policy token, not a verified native chunk-generation API. Recheck capture at
block boundaries and before publication; any replacement, death, lost residency,
position/facing change or generation change discards the entire pass. Reset on
session/Sarah replacement, death or unload. Do not infer world consistency merely
because no Lua yield occurred. Partial coverage never certifies an absent square.

## Proposed collector bounds (not measured performance)

The next pure collector uses injected square/list/object functions only. Initial
scope is a fixed 12-tile horizontal radius and same floored z, with a deterministic
25x25 offset domain. Validate number type, NaN/infinity and absolute coordinates
<=1,000,000 before arithmetic; use floor for negative fractions. Filter actual
snapshot distance separately. Larger radii require an explicit design revision.

Per pass hard ceilings: 64 square lookups, 128 object reads, 128 list metadata
queries, 256 lifecycle-check calls, 32 accepted unique candidates, and 64 retained list cursors/identity
entries. Each attempted native/injected call consumes its applicable budget,
including errors, nil and invalid results. Lifecycle checks consume their own budget at fixed work-block boundaries; never retry until successful. These proposed ceilings
require fixture validation and later native cost observation.

Inspect at most 16 objects from any one list per visit. Retain a rotating domain
cursor and bounded coordinate/index cursor records, never lists or squares.
Resume at index modulo current valid size; empty/shrunken/replaced lists are
handled explicitly. Query size only within the metadata budget; validate before
each access, stop that list on mutation/error and mark truncation/unknown.
Advance the square cursor even for oversized lists. Evict cursors deterministically
at the cap. Stable lists get round-robin opportunities; arbitrary continuous
reordering, cursor eviction or spawning cannot have guaranteed discovery fairness.

No enumeration-to-coverage budget substitution: one shared Coverage context per
pass has its existing defaults (1024 candidate/4096 sample reads) and hard limits.
At most 32 candidates proceed to coverage/obstruction, with separately bounded
obstruction calls. Budget exhaustion is explicit incomplete evidence. Validate
the final lifecycle capture before committing staged cursor/identity changes or
publishing any partial result. A discarded pass publishes no candidates or memory.

## Identity and visibility boundaries

Private identity registry: at most 64 entries, fresh epoch at lifecycle reset,
monotonic nonreused string IDs within the epoch, nonempty and <=96 characters to
match Perception. Candidate field is kind, not type. IDs are session-only and
never saved. Evicted identities reobserved later receive a new ID; this may
fragment expiring memory but must not alias a different object. Define overflow
and epoch rollover fixtures before implementation.

Native object/wrapper identity must first be verified stable. A bounded strong
registry is an alternative only if stable identity is established and weak keys
are unsuitable; it cannot repair unstable wrappers. Without reliable identity,
skip the candidate as unknown. Names, coordinates and tostring are not identities.
Clear private references on lifecycle reset; no handles in public snapshots.

Unseen coordinates, square indices, offsets, distance and bearing must not enter
gameplay-facing knowledge: distance+bearing could reconstruct hidden position.
Keep operator-only diagnostic geometry separate from Perception/Knowledge and
never feed it to actions. Public diagnostics favor aggregate bounded counters and
reasons; existing Perception IDs/statuses are not confirmed sightings. Only a
confirmed visual observation may carry a position into Knowledge.

Current unknown lighting means visual status unknown, never a definitive false
sighting or confirmed position. Knowledge receives no new record. Enum mapping
is a future native gate: compare exact verified TestResults identities; Clear,
ClearThroughOpenDoor and ClearThroughWindow are obstruction policy candidates
only after coverage. Blocked is blocked; ClearThroughClosedDoor and every unknown
value remain unknown pending an explicit tested policy. No unverified material
or glass semantics are asserted. Obstruction clear still does not imply vision.

No automatic disk logging. If later approved, a bounded copied diagnostic ring
(proposed 32 entries) may hold counts/reasons and caller-provided time, without
native handles or hidden locators. No invented timings or latency guarantees.

## Required offline fixtures before native wiring

- Invalid/negative/fractional coordinates, floor/range boundaries, all invalid
  facing forms; target admission independent of player-facing inputs.
- Empty, crowded, sparse and oversized lists; stable round-robin progress;
  shrink/grow/reorder/replacement, metadata errors and out-of-range access.
- Every call budget at and beyond its boundary, failed-call accounting, repeated
  candidates, cursor eviction and bounded retained state over many passes.
- Stable/unstable identity tokens, duplicate objects, registry eviction, ID length,
  rollover and no reuse/alias across replacements or resets.
- Controller/NPC/cell/generation changes and cancellation at each work boundary;
  staged state discarded, no stale coverage context reused and no retained handles
  in output. Tests establish observable bounds, not native GC/leak guarantees.
- Exact injected enum identities versus strings/ordinals/errors; missing halo
  coverage; unknown lighting produces no confirmed position or new memory.
- No unseen locator fields, mutations, action callbacks, engine imports or event
  registration. Existing Stop and all current suites remain passing.

## Later native acceptance (deferred, not performed)

Only after the user resumes live testing: Codex reviews the exact probe revision,
closes the isolated game, backs up the disposable world and deployed mod, records
restore steps and preserves the latest test state before any restoration. Normal
saves/settings and installed game files remain untouched. Codex alone deploys
and launches; this document does not authorize those actions.

First confirm Lua exposure/overloads/enums, stable identity and audited read-only
getters. Then observe loaded boundaries, list mutation/crowding and lifecycle
invalidation in the disposable profile. Record controlled facing/range/obstruction
cases separately from illumination. Day/night observations alone cannot prove an
independent light source; no player-cache fallback. Label actual observations and
untested cases honestly. Complete Follow/rendering gates separately.

## Next bounded task

Implement only the inert injected CandidateCollector.lua policy under
foundation/SarahFoundation/42/media/lua/client/Sarah with meaningful actual-Lua
fixtures for enumeration budgets, fairness and transactional lifecycle discard.
Resolve its exact identity-token contract offline before a native registry.
Do not wire native methods, enum discovery, Perception ticks, logging or actions.
External/model AI remains ON HOLD; saves/deployment/live tests stay deferred.
