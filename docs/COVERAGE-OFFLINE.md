# Conservative loaded-world coverage helper (offline only)

2026-10-06. Implemented and fixture-tested, not integrated, deployed or natively
accepted. Codex owns checkout; live testing and external/model AI remain deferred.

## API

Coverage.lua is an inert module. Nothing in main, Engine or the event loop imports
it. It has no Java/native calls, registered callbacks, movement or saved state.

```lua
local context = Coverage.newContext({range=12, candidateBudget=1024, sampleBudget=4096})
local result = context:check(observer, candidate, getSquare)
-- Equivalent explicit entry point:
local result = Coverage.check(observer, candidate, getSquare, context)
local counters = context:snapshot()
```

Observer/candidate are plain {x,y,z} snapshots; identity/facing belong to Perception.
getSquare(x,y,z) is injected and must be read-only, returning an existing loaded
square fixture/reference or nil/false. All nonnil/nonfalse values are accepted as
presence evidence under this caller contract; the helper cannot validate a native
square's provenance or freshness. Production adapters must validate their getter.
No square/reference is retained in context or result. The helper reads snapshot
fields directly without invoking metatable accessors and does not modify inputs.

Result contains status=covered/unknown, covered=true only for covered, reason,
reads for actual getter invocations, and area once computed. Reasons include
invalid_context/options/observer/candidate/coordinates, missing_getter,
different_floor, out_of_range, candidate_budget_exceeded, sample_budget_exceeded,
missing_square, query_error and reentrant_check. Covered has reason=ok.
Unknown never grants coverage. Different floor/range here mean unsupported
coverage; Perception independently classifies them as geometric blocked.

Options are validated once. Only nil means default options. Budgets must be
positive finite integers: defaults 1024 per candidate and 4096 per sample; hard
ceilings 2048 and 8192. Range defaults 12, must be finite, >0 and <=64. Invalid
options raise an error before creating a context; budgets/range are rejected,
not silently expanded or clamped. Context check has no per-call overrides.

## Coverage and bounds

Coordinates must be finite and within +/-1,000,000 before arithmetic. Fractional
x/y/z use math.floor, including negative values. Endpoints must be on the same
floored z and within configured Euclidean horizontal range. The inclusive
floored endpoint x/y bounding rectangle gets a one-tile halo on each side.
Every square in that rectangle is checked once for that candidate. Diagonal
side dependencies are covered deliberately; this is more conservative than
an exact ray and can report unknown for irrelevant unloaded side squares.
A coincident endpoint checks the 3x3 halo; Perception still treats a coincident
target as unknown rather than detectable.

Area exceeding candidate budget, or exceeding remaining sample budget, refuses
before querying with reads=0. Every actual getter call consumes one remaining
sample read, including nil/false/exception. First missing/error stops the check;
unused reads stay available. Counters are private closures; snapshot returns a
fresh plain numeric copy. Assigning public fields or modifying that copy cannot
renew/expand a budget. Reentrant checks from inside the getter return unknown
without additional reads. Constants exported for documentation cannot expand
internal hard limits.

A context is explicitly created for ONE synchronous sampling pass. Pass the
same context across its candidates to share the sample budget. Creating a new
context per candidate would defeat the aggregate budget and is not supported
caller use. There is no reset/automatic renewal: discard it and create a new
context for a later sampling pass/session/world. No positive or negative square
cache exists even within the sample. Overlapping/repeated candidates requery
all their squares, so earlier success cannot hide a newly missing square or a
changed getter. Unique-coordinate deduplication applies within one candidate
rectangle only. Total native getter calls cannot exceed the configured sample
budget; max 32 candidates is still enforced by Perception/the future caller.

The caller must abandon the pass on lifecycle/world/identity change and keep
coverage and subsequent obstruction queries synchronous without yielding.
Loaded-square existence does not establish current vision matrices, native
object integrity, obstruction or illumination. No square creation/loading,
player light/visibility caches, movement queue or action dispatch is permitted.

## Perception boundary

Inject coverage callback returning result.covered == true, with the same context
for that pass. Obstruction is a separate normalized query. Unknown lighting
still yields geometric-only data, no confirmed visual position and no Knowledge
record. No automatic Perception wiring or native enumeration has been added.

## Verification and delegation

Gemini 3.8 Flash HIGH supplied an offline code/test proposal without tools.
Normal headless coding was stopped by the CLI's RunCommand permission; Codex did
not bypass it or change settings. Saved credentials worked outside Codex sandbox.
Codex reviewed/applied the proposal, removed cross-call square caching, made
budgets private, rejected oversized/invalid options, added reentrancy protection,
and expanded meaningful safety regressions. Gemini did not edit the checkout.

64 actual-Lua coverage checks include ray shapes/directions, all halo sides,
missing endpoints/interior, negative fractions, numeric/configuration failures,
zero-length/range/floor boundaries, candidate/shared budgets, failed-call accounting,
repeated-query freshness, handle-free results, immutable budget copies, reentrancy,
Perception cap and Knowledge no-update under unknown light. A property fixture
removes each rectangle square in turn for ten directed ray cases and verifies
coverage cannot succeed. The runner includes this ninth offline suite.

Codex independently confirmed the -1 light path from class bytecode; see
NATIVE-PERCEPTION-ADAPTER-RESEARCH.md. No live light query or game class initialized.

Next: prepare an inert native adapter diagnostic specification covering exposure,
normalized enums, bounded enumeration/fairness/session IDs and lifecycle invalidation;
independent lighting remains unresolved. Actual Follow/rendering/perception
acceptance requires a separately resumed backed-up isolated gameplay batch.
