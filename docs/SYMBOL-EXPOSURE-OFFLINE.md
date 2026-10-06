# Narrowed symbol exposure policy

2026-10-06. Baseline f289c49; offline only. Gemini3.8 Flash HIGH authored
source/base fixtures from a standalone contract; Codex reviewed/applied/tested.
Codex remains sole checkout editor. No native resolver or runtime caller.

## API and evidence scope

`tools/SymbolExposureProbe.lua` exports `new():run(api)`, `reset()` and `snapshot()`.
It serves the future exposure-only role without weakening or modifying
NativeExposureProbe or DiagnosticSampler. No production imports/events are added.

API raw callbacks captureMarker/readSymbol are frozen before the first callback.
Marker requires raw framework/revision strings1..96 and cancelled=false. These
are caller assertions, not native identity or world generation. No coordinates,
facing, alive, resident, controller/NPC/cell fields are required or inspected.
Extra fields are ignored. Framework/revision are freshly captured and copied
at each barrier; repeated stale provider values cannot prove actual continuity.

Fixed13 aliases are the same facing/cell/square/list/LOS/global-getCell and five
enum candidates documented in NATIVE-BINDING-LIFECYCLE-REVIEW.md. Each is read
twice with pre/post markers, plus initial/final markers: max26 reads/54 captures.
A full completed pass reaches these counts; abort stops early. Reset/cancellation,
invalid/throwing marker or marker drift aborts with empty rows and no later calls.
Busy reentry returns reentrancy_rejected without affecting the outer pass. Invalid
APIs/reentry do not increment started attempts. Snapshot contains numeric
attempts/completed/aborted only; no callbacks, markers or handles are retained.

Row status priority: query_error > missing > type_mismatch > unstable_reference
> reference_matched. Functions require exact type=function; enum candidates
require table/userdata. valueType is the first successful non-nil read's type,
otherwise nil. Reference comparison uses rawequal only. Returned functions,
metamethods, names, strings and ordinals are never invoked for interpretation.
Five matched pairwise distinct enum references yield distinct_references;
otherwise unknown. This does not certify actual enum mapping or marshalling.

Every outcome includes evidenceScope=supplied_reference_comparison,
observerLiveness/residency/nativeIdentity/worldGeneration/methodInvocation all
unassessed, lighting=unknown, nativeAcceptance=false. Completion reason is
plan_completed. Invalid API and early aborts preserve that evidence envelope.
Output consists of scalar leaves only; no raw errors/tokens/positions/handles.

## Caller obligations and limitations

Injected callbacks may themselves execute native work. Ceilings count callback
attempts, not hidden Java/JNI work or latency. Actual userdata property resolution
requires its own audit and accounting; this module has no native resolver,
CaptureAccounting orchestration, lifecycle token issuer or Stop wiring.
Synthetic Lua wrappers cannot prove native symbol exposure. Callable userdata
may fail the function policy without establishing native API absence. Supplied
reference equality does not certify native object identity. Missing enum explicit
registration does not establish absence. No native acceptance is claimed.

## Verification and handoff

41 actual-module Lua fixture groups through Lupa Lua55 PASS. Intended source
syntax is Lua5.1-compatible; native Kahlua acceptance is separate. Codex corrected
Gemini's fixture syntax error, nil-first invalid-API list, missing-cancel reason,
and nominal environment test, then added12 review groups. Coverage includes all
54 cancellation/error/reset boundaries with exact early-stop counts, all26
resolver-reset points, drift, returned-function non-invocation, hostile metadata,
frozen API, reentry at capture/read, raw input, scalar output, userdata limits,
fixed plan and Lua weak-ref cleanup. Lua GC evidence does not prove JVM lifetime.

All649 suite checks across15 suites +11 runner +19 preflight self-tests PASS.
Runner report inspected directly after a report-filename glob failed; the suite
itself passed. No production edits/deployment/game launches/saves/settings changes.
Stop unchanged, lighting unknown; deployed isolated baseline remains5fa6b9c.
Raw exports remain ignored under runtime/symbol-gemini-20261006/.

This completes the bounded offline diagnostic contract work. Stop additional
generic scaffolding. Next meaningful work is the deferred native acceptance batch
with an audited resolver/capture operation manifest and exact staging revision:
actual Lua types/receiver/overloads/enum paths, identity/membership/loaded coverage,
then pending Follow/rendering. Independent light remains unresolved. Live testing
requires explicit user resumption, fresh disposable backups and restore plan;
Codex alone deploys/launches. External/model AI stays ON HOLD.
