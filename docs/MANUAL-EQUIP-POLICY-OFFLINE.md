# Manual equip request policy: offline only

Gemini 3.8 Flash HIGH authored tools/ManualEquipPolicy.lua and its initial
29 test groups through Antigravity. Codex applied and reviewed the draft, fixed
failure/cleanup and test-harness issues, and added 12 review groups. Baseline
0814d5c; Codex remained the sole checkout editor.

## What this implements

This tools-only module checks one explicit selected item's fixture request.
It supports new(), run(api), reset(); no production module imports it.
It performs no native lookup or direct engine invocation. Injected callbacks
can execute arbitrary work: this contract is not a sandbox.

All outcomes explicitly report evidenceScope="fixture_only" and
nativeAcceptance=false. completed means that the supplied fixture met the policy,
not that native equipment is safe or that gameplay was accepted.
Only fixture_only capture/eventIsolation/snapshot scopes are admitted.
These strings cannot certify actual event/UI isolation.

A private busy lock prevents re-entry. reset invalidates an in-flight request
without clearing its lock. Callback references are frozen from raw API fields.
Protected execution releases the lock; raw callback errors are never returned.
The private reset revision is local invalidation, not native entity identity.

## Supplied contract

api has Lua function callbacks capture(), inspect(phase), commit().
capture supplies raw fixture scope, session/revision strings (1..96), explicit
cancelled=false, actorValid/alive/resident/idle=true, eventIsolation=fixture_only.
Session and revision must stay equal to the initial marker. Unknown admission
refuses; cancellation/reset/session drift before attempt cancels.

inspect receives pre, barrier, post. Its raw snapshot supplies:
- scope=fixture_only, opaque actor/root/item references, selectedContainer=root;
- itemId integer0..2147483647, rootCount integer1..64;
- entries[1..rootCount], each with an opaque ref and valid integer id;
- directContains/melee/oneHanded/conditionValid=true;
- attached/worn/activationDependent/forceDropHeavy/loadoutConflict=false;
- secondary=nil, primary=nil before commit, selected reference after commit;
- wornStamp string1..96 unchanged across snapshots.

Selected reference and selected ID must each occur exactly once at the same entry.
Actor/root/item identity, selected ID and wornStamp must match the pre snapshot.
Identity uses raw reference comparisons, not names, metamethod equality or ID alone.
Raw snapshot fields/entry records are copied before the following capture callback;
later edits to a returned snapshot cannot retroactively repair its admission.

The root count, containment, item predicates and worn stamp are supplied fixture
facts. This does not establish native inventory enumeration, a complete worn
snapshot, stable identity, or total inventory conservation. No native API or
overload is inferred from field names.

## Execution and failure boundary

Nominal ceiling: 10 capture, 3 inspect, 1 commit callbacks:
initial capture; before/after pre inspect; before/after barrier inspect;
immediately before/after commit; before/after post inspect; final capture.
The fixed sequence and at most64 supplied entries bound fixture work, not callback
time, native scans, listener cost or world changes. There is no native operation
accounting implementation or world lock.

commitAttempted is set before the sole mutating callback. Its return value is
ignored: a true return without the expected post-state fails verification.
Throws, cancellation/reset/drift or unknown admission stop subsequent callbacks.
If actor admission fails after attempt, no post inspect is performed.
Failures after attempt report failed_after_commit and postVerified=false, even
if an earlier post snapshot passed. No rollback, retry, automatic Stop/queue,
prior-command resumption or timed-action completion occurs.

Results contain only status/reason, commitAttempted/postVerified, evidenceScope
and nativeAcceptance. Actual native Stop remains unchanged; synchronous native
setter interruption is not promised.

## Verification and review

41 manual-equip groups PASS: 29 generated groups plus12 independent review groups.
Review covers cancellation/reset/throw at every capture boundary, commit re-entry,
cleanup and subsequent reuse, actual64-entry admission, post ID/reference
multiplicity, snapshot retcon attempts, opaque userdata, missing flags,
malformed/nonfinite data, unsafe post-read avoidance and hostile metatables.

Codex corrected:
- Python callbacks converted to Lua functions and project-local Lupa import path;
- valid RESULT summary for the test runner, no inspection-fabricated hand mutation;
- session drift classified as pre-commit cancellation;
- no callback after a thrown commit;
- late invalidation never leaves postVerified true;
- failure handling uses private sanitized status/reason rather than error objects;
- bounded snapshot copying before later callbacks can change supplied data.

Full690 checks across16 suites +11 runner +19 preflight self-tests PASS.
Lupa Lua55 executes actual source; intended Lua5.1-compatible syntax does not
prove native Kahlua compatibility. Reports/raw Gemini exports stay ignored.

## Remaining gate

Native adapter, runtime admission and event/UI isolation are NOT implemented.
Inspected direct setter can mutate before equip events; Sarah's actual locality,
player index, listener context and invocation semantics remain unverified.
Do not wire this policy to native callbacks or add more generic scaffolding as
a substitute for that evidence. Follow/rendering acceptance and independent
lighting remain open. Keep native integration deferred until the user resumes
isolated acceptance and the relevant exposure/event context is established.

No deployment, game launch or saves/settings changes. Deployed5fa6b9c untouched.
External/model AI remains ON HOLD.