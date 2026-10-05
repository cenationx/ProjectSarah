# Bounded candidate collector (offline only)

2026-10-06. Implemented and actual-Lua fixture tested, not imported by production,
integrated, deployed or natively accepted. Codex owns checkout. Gemini 3.8 Flash
HIGH authored the module and base fixtures through NO-TOOLS coding drafts and
structured CLI exports; Codex applied/reviewed them, corrected budget-boundary
starvation and fixture assumptions, and added review regressions. Live testing
is deferred; external/model AI remains ON HOLD.

## Contract

`CandidateCollector.new()` returns private-closure methods `collect(api)`,
`reset()` and `snapshot()`. Use `collector:collect(api)` and colon calls for the
other methods. No public fields can alter private state or ceilings.

The caller provides four read-only functions; they are copied with rawget before
any callback runs. The module performs no native calls, imports, events, actions,
logging, illumination queries or saved state itself.

- `capture()` returns plain controller/npc/cell/generation string tokens, each
  nonempty and <=96 characters; alive=true, resident=true, cancelled=false;
  finite x/y/z/fx/fy within +/-1,000,000, facing not both zero. Tokens must be
  caller-issued stable session identities, never names/coordinates/tostring.
- `getSquare(x,y,z)` returns an existing square fixture/reference or nil/false.
  It must not create/load squares. Native residency/provenance is unverified.
- `listInfo(square)` returns integer size 0..1,000,000 and nonempty <=96-character
  stable list token. A replacement must change that token. Same-size reordering
  cannot be detected unless the caller changes its token.
- `readObject(square,zeroBasedIndex)` returns plain id/kind/x/y/z. ID is a
  caller-issued stable string <=96 characters, kind player/zombie. This module
  does not implement a native identity registry or verify wrapper stability.

Capture and candidate fields use rawget, not metatable accessors. Validation does
not mutate supplied tables. Results copy only the supported scalar fields.
Adapters must satisfy callback contracts; an injected callback can have arbitrary
side effects or duration. Call ceilings are not a native latency guarantee.

## Bounds and rotation

Fixed 625 offsets cover [-12,12] x [-12,12] around floored observer coordinates,
row-major. z uses floor, including negative fractions. Candidate admission uses
same floored z and horizontal Euclidean distance <=12 from the original snapshot.
There is no cone filtering here; Perception owns that policy. Derived square
coordinates may extend 12 tiles beyond the snapshot coordinate bound.

Each pass attempts at most 64 square lookups, 128 object reads, 128 list metadata
queries and 256 capture calls, and admits at most 32 unique candidates. Every
attempt, including an exception or invalid result, counts. Lifecycle checks run
before/after each square/list/object query and once before publication. Reserve
calls for the complete upcoming work block plus the final check before starting
it. Some ceilings therefore cannot be reached simultaneously: two metadata
queries and six capture checks per object usually exhaust another budget first.
An empty-present grid fixture visits 63 squares/254 captures; a nil grid visits
64 squares/130 captures. These are policy counts, not measured native timings.

Visit at most 16 items per list, resume actual committed reads modulo current
size, and reset index when its list token changes. Keep at most 64 world-coordinate
cursor records with deterministic FIFO eviction. Duplicate IDs do not fill the
candidate cap. Check size/token before and after every read; mutation/read failure
discards that square's staged candidates and does not advance its list cursor.

Rotate the square cursor between passes even for oversized lists. If a stable
list gets zero reads because a budget runs out, retry that square at the beginning
of the next pass; otherwise a repeated budget boundary could starve it. A partial
list visit advances only by actual reads, never the planned 16. Focused fixtures
exercise 48 stable IDs over 50 passes, bounded cursor eviction and three crowded
lists with partial-read resumption across 40 passes.

Fairness is bounded best effort. Continuous mutation, >64 retained-list demand,
same-size reordering, moving entities and repeated observer/session changes can
prevent complete discovery. Observer capture changes between passes stage a new
domain/cursor set, including position/facing changes. There is no promise of a
complete scan while Sarah moves or turns. Every result has incomplete=true.

## Transaction and evidence boundary

Results contain status completed/budget_exhausted/aborted/reentrancy_rejected,
reason, counts and candidates. Completed means this bounded pass finished, not
that its 625-tile domain was fully inspected. Unknown evidence is explicit through
missing_square/query_error/invalid_list/list_changed/invalid_snapshot counts.
Read exceptions are counted as invalid_snapshot; metadata errors during per-object
validation are counted as list_changed. Other square/initial metadata errors use
query_error. Counts.candidates can describe staged candidates in an aborted pass;
its returned candidates array is always empty and lifetime published count is
not increased. No counter is confirmed sight or a threat count.

Candidates are PRIVATE adapter input, not public gameplay-facing knowledge or a
diagnostic locator list. Keep coordinates/distance/bearing away from gameplay
until Perception confirms vision. Public operator summaries should copy aggregate
counts/reasons only. No native handles are retained in cursor/session state or
copied candidate output. No actual native identity has been established.

Any invalid capture, death/unload/cancellation, controller/NPC/cell/generation,
position or facing change during a pass aborts and publishes no candidates.
Session/cursor changes commit only after final validation. Explicit reset during
any callback invalidates the pass and stays reset; it never resurrects pre-reset
cursors. Reentrant collection fails closed. Snapshot returns fresh numeric
lifetime counters and cursor count/offset. Reset clears anchor/cursors and advances
private revision; lifetime diagnostic counters remain. Future callers must reset
on lifecycle teardown; there is no registered hook in this inert module.

Generation is an injected policy token, not a verified native engine counter.
No-yield sampling is not a world freeze; a native list may mutate between checks.
Existing Stop behavior is unchanged. Unknown lighting still produces no confirmed
visual position or new Knowledge record; one fixture composes the pure modules
to establish that boundary without adding production wiring.

## Verification and next task

69 collector checks; full runner 401 checks across 10 suites +11 runner +19
preflight self-tests PASS. These execute actual Lua against injected fixtures,
not Kahlua/native API exposure, engine identity, lighting, pathfinding or rendering.
Early Gemini drafts were rejected; exported draft fixtures failed before correction.
Code passed only after the reviewed starvation fix and corrected meaningful tests.

Next bounded offline investigation: specify/test the native adapter's stable
identity/token and exact-enum boundary using installed-code evidence and injected
fixtures. Actual Lua exposure and Sarah-independent lighting remain unresolved.
Do not wire this collector to Perception/ticks/actions or deploy it. Native
Follow/rendering acceptance remains pending and requires separately resumed,
backed-up disposable-profile testing.
