# Diagnostic sampler: offline composition only

2026-10-06. Gemini 3.8 Flash HIGH authored source/base fixtures via NO-TOOLS CLI
exports in the existing Antigravity conversation. Codex applied/reviewed/tested;
Gemini did not edit the checkout. This module has no production imports/events.
There was no native invocation, deployment, game launch or save/settings change.

## Injected API

`DiagnosticSampler.new({CandidateCollector, Coverage, Perception,
ObstructionNormalizer})` freezes factory functions and owns one private collector
and one Perception instance (range12, cone90). Methods: `:sample(api)`, `:reset()`,
`:snapshot()`. The existing module implementations are trusted dependencies.

`api` requires `capture`, `getSquare`, `listInfo`, `readObject`; optional
`obstruction` must be a function or nil. Optional `bindings` provides the five
ObstructionNormalizer enum references. All functions and the five raw references
are copied before the first callback. `api.lighting` is never queried.
Callback signatures/token contracts are those in COLLECTOR-OFFLINE.md. Obstruction
receives fresh observer/candidate copies and must perform a read-only query.
Caller IDs and lifecycle tokens are supplied externally; this coordinator does
not allocate identities, retain native handles or update Knowledge.

`capture()` must return finite bounded coordinates/facing, controller/npc/cell/
generation strings, alive/resident true, cancelled false. All fields must equal
the initial copied capture. The caller must advance generation on invalidating
world changes. Reset during any callback or any detected drift/failure aborts
and discards all results, resets collector cursors, and prevents later original
queries in that pass. Final lifecycle check precedes publication.

## Bounds and query ordering

Collector limits remain 64 square reads, 128 object/list metadata attempts,
256 internal captures, 32 unique candidates, and 64 private rotating cursors.
A present empty grid visits 63 squares because its capture limit stops further
work; a missing grid can reach64. The coordinator reserves its final capture.
Total sampler ceilings:512 captures,4160 square callbacks (64 enumeration +
4096 coverage),32 obstruction calls. Actual attempts, including errors, count.

One fresh Coverage context is shared across the entire pass:range12,
candidateBudget1024, sampleBudget4096. Perception first rejects out-of-range,
out-of-cone, wrong-floor or invalid candidates. Only its coverage callback
checks the inclusive bounding rectangle plus one-square halo. No coverage cache
or retained squares. Missing/throwing squares fail to unknown. A insufficient
remaining rectangle budget refuses the candidate before any getter call.

Coverage lifecycle checks bracket each complete bounded coverage block, not each
individual tile. This is not a frozen-world guarantee: a change that occurs and
reverts between capture boundaries is undetectable. A native integration must
establish trustworthy generation/lifecycle and loaded-world semantics first.

Obstruction runs only after exact covered=true, with valid exact-reference
bindings and lifecycle checks before/after the call. Clear/open-door/window
results mean geometric clearance only; blocked means geometric/visual blocked;
closed-door, unknown refs or query errors mean unknown. Native Java enum
reference identity and Lua exposure are still unverified.

## Publication and cleanup

Sample returns status sampled/aborted/reentrancy_rejected, reason, incomplete=true,
lighting=unknown, numeric counts and at most32 scalar result records with
id/kind/geometric/visual/reason. No positions, distances, bearings, capture data,
enums or native handles. Forced unknown lighting prevents visual=visible and
confirmed Knowledge observations. This is not a discovery-completeness claim.

Normalizer invalidation is protected during final cleanup. The reentrancy lock
stays held until cleanup finishes. Unexpected dependency failure after collector
commit resets its cursors; cleanup failure returns aborted/empty output. Lifetime
snapshot counters contain scalars and collector cursor count. Injected policies
are trusted code, not a sandbox against malicious module implementations.

## Verified evidence and next step

57 fixtures execute the actual modules through Lupa Lua55. Includes shared
4032 coverage reads for28 of32 diagonal candidates (remaining64 refuses four),
exact callback counters, missing halo, exact enum policy, binding/API mutation,
unknown-lighting rejection by actual Knowledge, lifecycle drift/reset, true
coverage-stage reset, reentrancy, unexpected factory failure and cleanup failure.
Codex corrected fixture assumptions and added cleanup/cursor protections.
All507 checks in12 suites plus11 runner and19 preflight checks pass. See sanitized
`evidence/sampler-offline-20261006.txt`. These results do not prove native Kahlua,
engine wrapper/exposure, loaded-world stability, rendering or Follow acceptance.

Next: bounded offline Sarah-independent light evidence audit before native wiring.
Live testing remains deferred; external/model AI stays ON HOLD. Latest deployed
isolated baseline remains5fa6b9c and existing disposable backups remain untouched.
