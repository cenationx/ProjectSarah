# Dormant native bridge design review

2026-10-06. Baseline ab3c548. Design only; no bridge implementation, production
imports, events, native calls, deployment or game launch. Codex owns checkout.
Gemini3.8 Flash HIGH reviewed the user-approved supplied documents through
Antigravity; Codex corrected the returned design. Live testing remains deferred.

## Decision and scope

Do not build another generic helper layer. Before implementing a native caller,
narrow the exposure diagnostic contract so it does not require spatial observer
state or claim liveness/residency. This is the preferred next bounded coding
change, with explicit fixture coverage and no runtime wiring. Keep the existing
probe intact until the replacement contract is reviewed; do not weaken the
DiagnosticSampler's stronger lifecycle/coverage requirements.

NativeExposureProbe currently requires fresh controller/NPC/cell/generation,
position, facing, alive and resident captures. Its resolved symbols are never
invoked, but acquiring truthful native captures would require a separate audited
getter/membership diagnostic. Calling the whole operation symbol-only would hide
that work. A cached valid snapshot repeated at every barrier masks drift and is
not an acceptable substitute. A full completed fixture pass has54 captures;
54 is a ceiling, not a requirement for early-aborted passes.

A narrowed symbol contract may check supplied lifecycle markers and cancellation,
but must explicitly report that observer liveness, residency, native identity,
world generation and method invocation are unverified. Actual property resolution
can itself enter bridge code; reference inspection is not automatically free
of native execution. No resolver path becomes authorized merely by this design.
Missing enum registration is not evidence of absence. A missing enum row need
not prevent an exposure report; it does prevent claiming validated enum mapping.

## Minimum future caller contract

The proposed caller is dormant and explicitly invoked once, without registration
or actions. It uses a private busy gate; a rejected reentry must not reset or
invalidate the outer pass. Ownership of lifecycle tickets spans any calls that
claim continuity; namespaces must not be reused across recreated instances.
Do not create CallerEpoch.new("sarah_diag") on every call and claim unique tickets.

| Marker | Inspected source or required provenance | Evidence boundary |
|---|---|---|
| framework | SarahFoundation.lua replaces the top-level plain Lua table on reload | Caller must issue a changed token for changed table identity; no token issuer exists yet |
| controller | Plain Lua controller retained on reload, cleared by session reset | Inspected project behavior; controller alone misses reload |
| npc | Caller token tied to independently established object continuity | Native wrapper/object identity UNKNOWN; no tostring, address or hash shortcut |
| cell | Caller token tied to audited active-cell observation | Global getCell is a static candidate; actual wrapper identity UNKNOWN |
| worldRevision | Caller-owned invalidation revision | Not authoritative engine/chunk generation, not world freeze |

CallerEpoch accepts copied strings1..96; it does not derive these identities.
A missing or untrustworthy provenance obligation fails closed for any report
that needs it. A narrowed report can declare a capability unassessed rather than
manufacturing alive=true/resident=true, coordinates or a nonzero facing vector.
No authoritative world-generation API was established in this bounded study;
that does not prove none exists.

Design sequence, not executable Lua:

1. Validate plain inputs and frozen callback contract; acquire the busy gate.
2. Inside a protected region create a fresh per-pass ledger. Establish only the
   provenance required by the selected, explicitly limited report contract.
3. At each barrier read fresh required markers, check cancellation and revision,
   and observe the ticket policy. Do not freeze initial tokens across the pass.
4. Immediately before each potentially bridged lookup or invocation, charge its
   declared group; execute only after a granted charge. Check invalidation before
   and after return. A failed attempt retains its charge; refusal prevents it.
5. Resolve only fixed candidate aliases; compare returned references directly.
   Never use a synthetic wrapper to manufacture type=function exposure. Native
   callable userdata can fail the function type policy without proving absence.
6. On reset/cancellation/drift, mark the pass invalid, invalidate its ledger and
   reset the active probe explicitly. Advance/invalidate the epoch when its
   ownership boundary changes. No further resolver/getter operations or output.
7. In protected final cleanup, close the ledger, release temporary references
   and release the busy gate even if setup/callback/cleanup fails. Publish copied
   scalar diagnostics only after a final valid barrier. Never publish raw errors,
   handles, tokens, coordinates or resolver closures. Cleanup failure aborts.

The existing Stop handler is unchanged. Future integration must explicitly
propagate its cancellation to a diagnostic pass without replacing or delaying
Stop's action/path cancellation. Reset cannot interrupt a synchronous Java call
already in progress; it prevents later calls/output at the next boundary. No
automatic propagation is claimed or implemented in this batch.

## Accounting and capture alternatives

CaptureAccounting groups world/membership/state/symbol are declarations about
instrumented operations. Charge potentially bridged property lookup separately
from invocation when both occur; charge token/provenance acquisition too where
it enters the bridge. Plain raw Lua table reads need no invented native charge.
Never hide an uninstrumented aggregate native callback behind one charge.
Exclude whole-collection getObjectListForLua materialization.

The prior566-operation fixture is54 captures times a declared10-operation model
plus26 symbol reads. It is NOT a native caller budget: death, coordinates, facing,
extra cell acquisition, lookup and marshalling boundaries were not accounted
there. Engine.isResident's up-to10 explicit API call expressions are inspected
source, not a native time/CPU/JNI-work bound. A real caller needs a complete
operation manifest before selecting a limit; no native timing is established.

If spatial capture is later needed, use separately audited fresh getter and
membership checks at every barrier. That broader diagnostic is not exposure-only.
Neither option establishes world freeze or catches mutations that revert between
barriers. Lighting stays unknown; no Knowledge observations/actions follow.

## Acceptance and deferred work

| Evidence | Verified boundary | Still open |
|---|---|---|
| Lupa Lua55 fixtures, intended Lua5.1-compatible source | Probe48 and caller53 cases rerun PASS | Native Kahlua behavior |
| Inspected project source | Framework replacement, controller retention, residency call expressions | Live propagation and Stop interaction |
| Prior direct class/annotation inspection | getCell candidate, three square overloads, Set/HashSet residency containers | Lua types/receiver/overloads, native wrapper identity |
| This design review | Contract mismatch and proposed narrowed report documented | No bridge or narrowed probe implemented |
| Native gameplay | No new evidence in this batch | Exposure/enum, loaded coverage, independent lighting, Follow/rendering |

Codex rejected the initial cached-snapshot recommendation and revised pseudocode
with fixed initial tokens, repeated namespace, incomplete native accounting and
unguarded setup/cleanup. Incorrect test-file references and inferred JNI claims
were also omitted. Actual fixtures are tools/test_exposure_probe.py and
tools/test_caller_context.py; class provenance remains in
NATIVE-BINDING-LIFECYCLE-REVIEW.md. Raw exports stay ignored under
runtime/bridge-review-gemini-20261006/.

Next: Gemini drafts a narrowly scoped replacement symbol diagnostic contract and
code with injected markers, explicit unassessed capabilities and cancellation
fixtures; Codex reviews/applies/tests. No new token registry, residency simulation
or runtime bridge. Stop further generic scaffolding after that change. Actual
binding and gameplay questions remain for an explicitly resumed isolated batch:
game closed before staging, fresh disposable-world/deployed-mod backups, recorded
restore plan, normal saves/settings untouched, Codex alone deploys/launches.
External/model AI remains ON HOLD. Deployed baseline remains5fa6b9c.
