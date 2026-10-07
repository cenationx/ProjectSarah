## Codex-reviewed extended lighting audit (2026-10-07)

Documentation-only investigation; no usable independent lighting route admitted.
Installed archive hash matches the pinned SHA256. Selected source checks confirm
CanSee is geometric, zombie vision uses player lighting/climate, and getSkyLightLevel
reads player render settings and conditionally invalidates global lights.
The broader candidate matrix is static evidence, not an exhaustive engine proof.
Native C++ internals were not inspected. Explicit registration-list absence does
not establish that an object or method is unreachable through Lua return values.
Light-source lists and fire influence arrays lack verified total illumination
provenance; exclusive producer and whole-engine absence claims are not established.
For any future invariance test keep Sarah, player and target positions fixed;
change only player facing and compare stable identities. Moving the player changes
an observed target and may change loaded coverage. Matching counts alone prove
neither independent lighting nor absence of camera-cache borrowing.
Independent lighting remains OPEN; visual stays unknown. No code, deployment,
launch or save/settings changes. Codex owns the checkout. Existing 731+11+42
baseline remains unchanged; the sampler policy checks were rerun for this audit.
Next useful work is isolated native diagnostic/Follow acceptance after fresh backup,
or a separately bounded new lighting route; no sight-driven behavior is enabled.

## Codex review: offline memory clock candidate (2026-10-07)

Gemini returned checkout ownership to Codex. Independently verified 731 checks
across 16 suites, 11 runner self-tests and 42 preflight self-tests, all PASS.
Clock failure and recovery clear observation memory; unverified pause state
fails closed. The clock accumulates engine simulation delta, with no additional
clamp. Static timing inspection and mocked fixtures do not establish native
Lua exposure, pause/speed behavior or actual memory expiry.
Independent lighting remains OPEN; visual results remain unknown and native
confirmed memory is not admitted. Prior unavailable-clock notes are historical.
No game process detected during this review; no deployment, launch or
save/settings changes. External/model AI remains ON HOLD.
Next: isolated native acceptance only after a fresh verified world/mod/profile
backup and process check. Gemini may continue bounded offline work with explicit
ownership handoff; no sight-driven behavior may bypass the open lighting gate.

## Codex-reviewed Batch B diagnostic candidate (2026-10-07)

Gemini handed ownership back. Codex reviewed cross-pass snapshot/version changes
and reproduced721 checks/16 suites +11 runner +42 preflight PASS.
Explicit look/perceive wiring is a diagnostic candidate only; no autonomous
behavior. Exact-reference square snapshots capped at128 entries, lists over64
rejected, unchanged cursor tokens retained and mutations receive new versions.
Idle lifecycle invalidation and read-only diagnostic command guards implemented.
No verified independent lighting: visual detection remains unknown/zero.
Console time intentionally unavailable; native confirmed-memory admission/expiry
is blocked until a verified monotonic seconds source is supplied. No claim that
all possible engine clocks were exhaustively excluded. API exposure, line-clear
enum behavior, loaded coverage and actual collector costs remain native gates.
No deployment/launch/save/settings changes. Follow pace and rendering native
acceptance also pending. Next Codex live batch must first recheck process state
and freshly preserve disposable world/mod/profile with a verified restore plan.
Batch C can do independent offline adapter inspection; do not enable ungated
equipment, transfers or behavior. External/model AI remains ON HOLD.
## Batch B: Cross-sample list identity and fairness correction completed offline (2026-10-07)

Gemini completed offline coding and verification for Batch B cross-sample list identity and fairness corrections, resolving the cross-sample list token blocker:
- Source changes completed offline:
  * Engine.lua: Persistent bounded snapshot storage on `adapter` (`adapter.snapshots` and `adapter.snapshotFIFO` capped at 128) preserved across `samplePerception` passes and cleared on `resetPerception()`. Stable tokens for unchanged lists so `CandidateCollector`'s cursor fairness works without restarting or starving later candidates. Nonreused tokens allocated via monotonic `adapter.snapSeq` on any list change, reordering, or tail mutation, triggering clean cursor reset in CandidateCollector. Dynamic lifecycle capture in `adapter.samplePerception`: queries dynamic generation (`gen_` .. `sampleGeneration`), cell (`tostring(getCell())`), controller token (`ctrl_` .. `tostring(adapter)`), and NPC token (`npc_` .. `tostring(npc)`), eliminating constant string literals and detecting cell/generation/controller drift during sampling passes. Native enumeration error handling: throws on query error so CandidateCollector increments `query_error` (never empty success). Bounded exact-reference snapshot (`currentRefs` compared to `prev.refs`) detecting same-size list replacement, reordering, and tail-element changes with 100% certainty (replacing 32-bit hash). Unsupported oversized lists (`sz > 64`) fail closed immediately. Native work budget: accounts for snapshot element reads and object reads in `api.nativeReads` against `adapter.readBudget or 512`. Strict boolean living state required (rejects unknown liveness). Short identity tokens (`so:e<epoch>:s<seq>:<kind>:<oid>`) placing sequence and epoch at the front to ensure uniqueness cannot be truncated away. Added `Engine.isCurrentOwner(npc, adapter)`.
  * Console.lua: Added `resetPerceptionSarah()` calling `controller.adapter.resetPerception()` and wired to `state.reset` and `Commands.new` 9th argument. Leaves `getTimeSeconds()` returning `nil` (time unavailable) because native PZ lacks a verified monotonic clock (`getTimestampMs`/`getTimeInMillis` wrap non-monotonic wall-clock `System.currentTimeMillis`).
  * Commands.lua: Extended constructor with `resetPerceptionCallback` and helper `self:resetPerception()`. Idle lifecycle check: `checkLifecycle()` evaluates observations and controller/NPC identity even while no movement action is active (`self.active == nil`), detecting Sarah death, unload, absent state, and controller/NPC replacement during idle ticks, invalidating Knowledge and adapter perception without initiating/cancelling movement or emitting notices. Validates injected monotonic time in `self:getNow()`; on clock reversal (`t < self.lastNow`), immediately invalidates Knowledge memory (`self:resetKnowledge()`), resets `self.lastNow = nil`, and fails closed. Made `look` / `perceive` strictly require active observation state (rejects blocked, busy, unavailable, dead, unloaded, absent, deferred) without invoking movement-cancelling `checkLifecycle`.
- Offline tests: 721 checks across 16 suites in `run_tests.py` PASS (+19 new checks across Batch B: +12 in `tools/test_commands.py` [66 checks total] and +7 in `tools/test_render.py` [29 checks total]); 11 runner self-tests PASS; 42 preflight self-tests PASS.
- Verification & boundary status:
  * Implemented code: `Engine.lua`, `Console.lua`, `Commands.lua`.
  * Offline verification: 721 checks across 16 suites in `run_tests.py` PASS.
  * Pending native acceptance: Gate B (front/behind, player facing away, walls/doors/windows, darkness, missing squares, memory expiry) strictly pending Codex live verification in the isolated profile. No autonomous actions, combat, or looting enabled. Methods are offline candidates verified against static signatures and mocked tests, not native engine features.
- Live checklist & safety requirements for Codex:
  1. Verify Project Zomboid is CLOSED.
  2. Take a separate fresh verified backup of the disposable world, deployed mod, and isolated profile BEFORE deploying or launching.
  3. Deploy reviewed files from `foundation/SarahFoundation/` to `runtime/isolated/mods/SarahFoundation/`.
  4. Launch isolated profile (`tools/launch-isolated.ps1`).
  5. Test `look` / `perceive` via Sarah Console: verify geometry counts, visual confirmation = 0, unknown lighting message, and memory snapshots.
- Checkout handoff: Released to Codex for review, deployment, and live testing. Working tree contains uncommitted Batch B changes for inspection.

## Codex-reviewed Follow pace candidate checkpoint (2026-10-06)

Gemini handed ownership back; Codex reviewed actual source and reproduced702
checks/16 suites +11 runner +42 preflight PASS. Stop cleanup errors propagate
through Console into dispatcher blocking. Runtime ownership stays outside saved
modData and survives Engine reload; same-NPC stale action/adapter, failed ownership
admission, partial queue startup and reentrant step regressions included.
Candidate approved for isolated live evaluation, not native acceptance.
No deployment/launch/save/settings changes. Rendering guard remains unchanged;
independent rendering remains an open gate, not a completed feature.
Next: recheck closed-game state, fresh verified disposable world/mod/profile
backup and restore plan, then deploy reviewed source and test pace, Stop,
WalkHere and reload. No AI integration. Batch B may do independent offline
inspection; do not enable later native behavior before applicable gates pass.
## Batch A: Stop failure propagation, admission rejection, reload continuity, and reentrant step corrections completed offline (2026-10-06)

Gemini completed offline coding and verification for Batch A, addressing all items in the latest Codex review. Checkout is prepared for Codex review:
- Source changes completed offline:
  * Observations.lua: sampled player isRunning and isSprinting via pcall; speculative IsRunning and raw running/sprinting fields eliminated.
  * Console.lua: walkSarah forwards action.pace to adapter.walk; stopSarah captures `ret == false` and propagates failure reason (`false, err`) so Commands.lua properly triggers stopFailed blocking.
  * Commands.lua: invokeWalk accepts (true, actionObj) tuple return while preserving backward compatibility; dispatchFollowStep matches player pace; tickFollow adjusts pace mid-stride and resets to walk when entering deadzone; WalkHere invariant enforces strictly walking; stepAction assignment and failure handling after invokeWalk guard against clobbering or cancelling newer step generations.
  * Engine.lua: Removed live action objects from NPC modData (SarahActiveAction completely eliminated). Created runtime ownership record anchored to `_G._SarahRuntimeOwnership` across module reloads; isCurrentOwner() fails closed if record is missing, invalid, or unreadable; rejected walk admission if setOwnership fails (never queues ownerless action); adapter.stop attempts all safe cleanup steps and propagates failures as `false, reason` when native cleanup methods throw.
- Offline tests: 702 checks across 16 suites in run_tests.py PASS (+4 new checks in test_render.py [22 checks] and test_follow.py [71 checks]); 11 runner self-tests PASS; 42 preflight self-tests PASS.
- Rendering independence review: Native IsoPlayer rendering requires playerIndex square visibility and light info in the engine FBO pass. No fake visibility introduced; independent rendering remains pending native engine investigation.
- Verification & boundary status:
  * Implemented code: Observations.lua, Console.lua, Engine.lua, Commands.lua.
  * Offline verification: 702 checks across 16 suites in run_tests.py PASS.
  * Pending native acceptance: All native behavior (pace matching, deadzone halting, WalkHere invariant, mid-stride Stop, same-NPC adapter recreation, reload continuity, and rendering independence) strictly pending Codex live verification in the isolated profile.
- Live checklist & safety requirements for Codex:
  1. Verify Project Zomboid is CLOSED (no javaw.exe / java.exe process, no Project Zomboid window).
  2. Take a separate fresh verified backup of the disposable world, deployed mod, and isolated profile BEFORE deploying or launching. (Note: tools/preflight.py is strictly a read-only validator and DOES NOT create backups).
  3. Deploy reviewed files from foundation/SarahFoundation/ to runtime/isolated/mods/SarahFoundation/.
  4. Launch isolated profile (tools/launch-isolated.ps1).
  5. Verify 5 observable criteria in live gameplay:
     - Pace matching: Sarah runs when player runs, walks when player walks, and accelerates/decelerates mid-stride.
     - Deadzone halt: Sarah halts cleanly within 2 tiles and pace resets to walk.
     - WalkHere invariant: 'walk here' strictly walks regardless of player running.
     - Mid-stride Stop: immediate halt, no automatic resume, no queue corruption.
     - Same-NPC recreation / reload safety: recreation of adapter or controller does not cause stale actions to cancel newer movement or corrupt queues.
- Checkout handoff: Released to Codex for review, deployment, and live testing. Working tree contains uncommitted Batch A changes for inspection.

## Manual Gemini coding batches authorized (2026-10-06)

User requested substantial ordered coding slices to move most implementation and
offline testing to Gemini, with Codex review/deployment/live tests here.
See GEMINI-CODING-QUEUE.md: 18 slices, five batches with native admission gates.
This expands the older research-only scope; model AI stays ON HOLD.
Manual Antigravity prompts replace CLI dispatch. Codex currently owns checkout;
Gemini editing starts only on explicit user handoff. Start Batch A (corrected
pace implementation, ownership/handle fixes, rendering review and live checklist).
No batch has been applied yet; current game/runtime state must be rechecked.
No deployment/save/settings changes or new source tests in this queue checkpoint.
## Pace access result (2026-10-06)

The user resumed the debugger. The wrapped collection probe completed and logged
AIComponent method lookup failure: getHumanControlVars is not exposed to Lua on
Sarah's actual component. This closes the direct-controller-access candidate for
the current runtime. No final AI-only probe is needed; do not ask the user to
repeat it. Protected calls still triggered Break On Error, causing the blocking
debugger; avoid further invalid component indexing. No running flags mutated.
Next: offline review of exposed movement hooks and timing, then a bounded Gemini
implementation only if a supported route is established. Pace remains unfixed.
Do not claim a fixture or setter signature proves native running. Game remains
open; no deployment until clean exit and fresh disposable-state preservation.
## IN PROGRESS: Follow pace correction (2026-10-06)

User confirmed smoother Follow direction changes and mid-stride Stop/no automatic
resume in the isolated session. Codex visually confirmed Stop #9 completed and
the game paused, Sarah idle. These are user-observed behavior results, not measured
movement timing. User found Sarah walks when the player runs; pace matching is
the next fix, not accepted yet. Rendering independence remains pending.

Codex owns the checkout. Gemini 3.8 Flash HIGH reviewed a sanitized pace contract;
no Gemini checkout edits. Static inspection suggests the native NPC controller
overwrites the ordinary running flag. Live read-only probe confirmed isRunning,
setRunning and getECSComponentMap are callable methods. Controller control access
and actual run behavior remain unverified; second read-only probe pending.
No pace code or deployment yet. Do not blindly apply setRunning or scalar speed
multipliers. Preserve 8-tile leash, 2-tile deadzone and Stop/ownership cleanup.
Game PID48240 remains open and paused; do not deploy while open. Existing backup:
runtime/backups/follow-resume-20261006-111728-UTC. Before restart/deployment, close
cleanly and freshly preserve the current disposable world/mod/profile.
690 suite checks +11 runner +42 preflight last passed at source baseline8ae4301;
not rerun for these notes. Normal saves/settings untouched; model AI ON HOLD.
Earlier live-launch/deferral blocks below are historical.

## IN PROGRESS: isolated live acceptance resumed (2026-10-06)

User authorized resuming live tests. Codex sole editor/live operator.
Baseline8ae4301 clean and690-test report synced; game closed verified via process
query and window inventory. Fresh381-file world backup verified:
runtime/backups/follow-resume-20261006-111728-UTC (world, deployed mod, profile).
RESTORE.txt requires preserving current test state before scoped restore.
Updated only isolated Commands.lua from reviewed source; preflight READY.
Launched PID48240 with isolated cachedir; Continue selected existing disposable
Sandbox/2026-10-05_19-04-21. Native console Status #1 completed:
Sarah active; Action idle; player8263.17,11679.95,0; npc8273.45,11679.50,0.
No new Follow/render acceptance. Player initially ~10.3 tiles away, beyond8 leash.
Console closed for user movement toward Sarah; game remains running.
Next: user physically approach within8tiles; open console/Follow, test midwalk
retarget and Stop, then rendering observations. Injected F9 did not open console;
mouse context Sarah:console worked. No automatic Follow or AI/native equip wiring.
Normal saves/settings untouched; independent lighting still unknown.
Offline690+11runner+42preflight last PASS; no source changes in this launch session.
Older deferred-testing notes below are historical; latest user explicitly resumed.
## Latest checkpoint: preflight report completeness fix (2026-10-06)

Started clean main515edcf; Codex sole editor. Gemini3.8 Flash HIGH authored
an internal report validator and15 regression groups; Codex reviewed/integrated,
corrected edge cases and added8 review groups. No game-runtime changes.
Reproduced coherent one-suite passing report wrongly accepted as synced;
now incomplete and blocks preflight readiness. Required names sourced from
run_tests.DEFAULT_SUITES, no duplicated list. Report totals/rows/types/exit codes
validated before Git freshness; unavailable report Git cannot establish sync.
Full690 checks/16 suites +11 runner +42 preflight self-tests PASS.
See verification-workflow.md and sanitized preflight evidence.
Older/partial summary-only reports now require a full default test run.
Native adapter/event/UI isolation and Follow/rendering remain unverified.
Live testing deferred; no deployment/game launch/saves/settings changes.
Stop unchanged; independent light unknown; external/model AI ON HOLD;
deployed5fa6b9c untouched. Older notes below are historical and superseded.
## Latest checkpoint: fixture-only manual equip policy (2026-10-06)

Started clean main0814d5c; Codex sole editor. Gemini3.8 Flash HIGH authored
tools/ManualEquipPolicy.lua and29 initial groups; Codex applied, corrected and
added12 review groups. See MANUAL-EQUIP-POLICY-OFFLINE.md.
41 manual groups PASS; full690 checks/16 suites +11 runner +19 preflight PASS.
This is tools-only supplied-fixture policy, NOT a native adapter or integration.
All outcomes nativeAcceptance=false; completed means fixture policy only.
Cancellation/reset/drift, bounded ownership/ID/reference checks, guarded post-state,
re-entry and partial-commit failures covered. No retries/rollback/queue/Stop edits.
No production imports/native resolver/event registration/admission certificate.
Next gate: actual native exposure/event/UI isolation and Follow/rendering;
do not add generic scaffolding to substitute for native evidence.
User not ready for live testing. No game launch/deployment/saves/settings changes.
Independent light unknown; external/model AI ON HOLD; deployed5fa6b9c untouched.
Older blocks below are historical and superseded.
## Latest checkpoint: reviewed manual equip proposal (2026-10-06)

Started clean main3692172; Codex sole editor. Gemini3.8 Flash HIGH authored
and revised the bounded proposal; Codex corrected/reviewed against selected
installed source and direct class Code. See MANUAL-EQUIP-ADAPTER-PROPOSAL.md.
Prefer dormant direct-primary-setter candidate over player timed equip action.
Setter mutates equip parents/hand before equip events; no atomic Stop guarantee.
Selected fishing handler can destroy an existing manager for a non-rod item.
isLocal defaults true without NetworkComponent; actual Sarah context unobserved.
Event/UI isolation remains an admission gate, not a caller boolean certificate.
No implementation/runtime hooks/new tests. Prior649+11+19 baseline unchanged,
not rerun for documentation-only work. Native equipment/Follow/rendering pending.
Next Gemini coding: narrow dormant request/state logic with a concrete injected
operation contract and rejection/cancellation/partial-commit tests; no native
resolver, invented admission proof or generic helper framework.
Live testing remains deferred. No deployment/game launch/saves/settings changes.
Stop unchanged, independent light unknown, external/model AI ON HOLD;
deployed5fa6b9c untouched. Older blocks below are historical and superseded.
## Latest checkpoint: ownership and worn-slot audit (2026-10-06)

Started clean main2676f98; Codex sole editor. Gemini3.8 Flash HIGH reviewed
sanitized findings; Codex corrected/reviewed and corroborated selected direct
class Code paths without target initialization. See OWNERSHIP-WORN-SLOT-OFFLINE.md.
getItemWithID(int)/contains(InventoryItem) are direct in inspected overloads;
getItemById(long)/getItemWithIDRecursiv recurse. Backpointer/ID alone insufficient.
Worn setter removes first nonmulti target entry and all exclusive worn entries;
character default setter can drop captured prior target item under capacity/floor
conditions. Empty target doesn't rule out conflicts elsewhere. Actual Lua exposure,
overloads, item identity/uniqueness and native behavior remain pending.
No runtime implementation/helper/new tests. Prior649+11+19 baseline unchanged,
not rerun docs-only research. No new equipment/Follow/rendering acceptance.
Recommended next Gemini offline task: concrete narrow owned-onehanded manual equip
adapter proposal, resolve UI/precommit integration choice before implementation.
User not ready for live testing. No deployment/game launch/saves/settings changes.
Stop unchanged, light unknown, external/model AI ON HOLD; deployed5fa6b9c.
Older checkpoint/workflow blocks below are historical and superseded here.

## Latest checkpoint: offline equipment action review (2026-10-06)

User not ready for live testing; requested useful continued Gemini work. Started
clean mainc30e5db, Codex sole editor. Gemini3.8 Flash HIGH reviewed sanitized
installed equip/wear/base/queue findings; Codex corrected invented API/ownership/
Stop claims and independently narrowed native single-player routing with fresh
class Code inspection. See EQUIPMENT-ACTION-OFFLINE-REVIEW.md and sanitized evidence.
Player equip/wear actions couple hotbar/inventory/progress UI and can drop heavy
items/convert special clothing. No unchanged-action reuse or native safety claim.
Inspected engine path perform THEN complete; perform may advance queue before
slot mutation. Future settlement needs verified post-commit identity/ownership/
slots, no blind rollback/retry, existing Stop preserved. No equipment code/helpers.
Prior649 suite +11 runner +19 preflight baseline unchanged; no tests rerun for
source-unchanged research. No new native equipment/Follow/rendering acceptance.
Possible next Gemini offline task: concrete ownership/container/worn-slot conflict
semantics audit; narrow NPC adapter proposal only if selected, no auto-equipment.
No game launch/deployment/saves/settings changes; live tests remain deferred.
Stop unchanged, light unknown, external/model AI ON HOLD; deployed5fa6b9c.
Older checkpoint/workflow blocks below are historical and superseded here.

## Latest checkpoint: read-only native resolver audit (2026-10-06)

Started clean main7d7d37d; Codex sole editor. Installed jar hash unchanged.
Selected Kahlua lookup/type/equality/receiver/exception paths freshly inspected
and corroborated by direct class Code/exception-table reads, no target execution.
Gemini3.8 Flash HIGH reviewed sanitized findings; Codex corrected overclaims.
See NATIVE-RESOLVER-AUDIT.md and evidence/resolver-audit-offline-20261006.txt.
Standard class method lookup retrieves stored invokers; JavaFunction maps to Lua
function. Callable __index paths/cache mutations prevent universal purity claims.
MethodCaller can log/consume target exceptions: pcall success alone insufficient;
expected return domain plus separate native/log evidence needed for later getters.
41 symbol fixtures rerun PASS. Prior649 suite +11 runner +19 preflight baseline
unchanged, full suite not rerun for docs-only work. No runtime/helper changes.
Next: explicitly resume isolated native Follow/rendering acceptance; later resolver/
getter diagnostics require audited paths/operation manifest and staging revision.
Stop generic scaffolding. Live tests remain deferred until user explicitly resumes.
No deployment/game launch/saves/settings changes. Stop unchanged, light unknown,
model AI ON HOLD; deployed baseline5fa6b9c. Codex alone later deploys/launches.
Older checkpoint/workflow blocks below are historical and superseded here.

## Latest checkpoint: narrowed symbol diagnostic (2026-10-06)

Started clean main f289c49; Codex sole editor. Gemini3.8 Flash HIGH authored
standalone SymbolExposureProbe/base fixtures; Codex corrected fixtures and added
12 review groups. 41 symbol cases; all649 suite checks/15 suites +11 runner +19
preflight self-tests PASS. See SYMBOL-EXPOSURE-OFFLINE.md and sanitized evidence.
Markers require only framework/revision/cancelled, freshly compared; no observer
coordinates/alive/resident assumptions. Every outcome explicitly leaves native
identity/liveness/residency/world generation/invocation unassessed. Max54 marker
captures/26 supplied-reference reads; no native resolver or automatic Stop wiring.
Existing NativeExposureProbe/DiagnosticSampler remain unchanged; no production
imports/hooks/actions, deployment, game launch or saves/settings changes.
Next: stop generic offline scaffolding. Actual binding/resolver and native
Follow/rendering acceptance require explicitly resumed isolated testing and an
audited operation manifest/staging revision. Lighting remains unknown; model AI
ON HOLD; Stop unchanged; deployed baseline5fa6b9c. Codex alone deploys/launches.
Older checkpoint/workflow blocks below are historical and superseded here.

## Latest checkpoint: dormant bridge design review (2026-10-06)

Started clean main ab3c548; Codex remains sole checkout editor. User explicitly
approved the named document export to Gemini3.8 Flash HIGH. Codex reviewed the
NO-TOOLS requested draft/revision and rejected cached captures, frozen tokens,
namespace reuse and incomplete native accounting in proposed pseudocode.
See DORMANT-BRIDGE-DESIGN.md. No bridge/source implementation in this batch.
Prefer narrowing the next symbol diagnostic contract: exposure evidence must not
require fabricated spatial captures or claim native liveness/residency/identity.
Fresh audited observer getters would be a separate broader native diagnostic.
48 probe +53 caller fixtures rerun PASS. Prior full608 suite +11 runner +19
preflight baseline unchanged; full suite not rerun for this documentation batch.
Next Gemini coding: bounded narrowed symbol diagnostic with injected lifecycle
markers, explicit unassessed capabilities and cancellation fixtures; no runtime
wiring, token registry or residency simulation. Then stop generic scaffolding.
Native questions and Follow/rendering await explicitly resumed isolated tests.
No native invocation, hooks, deployment, game launch or saves/settings changes.
Stop unchanged; light unknown; external/model AI ON HOLD; deployed baseline5fa6b9c.
Older checkpoint/workflow blocks below are historical and superseded here.

## Latest checkpoint: inert caller epoch and accounting (2026-10-06)

Started clean main dac6c1f; Codex remains sole shared-checkout editor. Gemini3.8
Flash HIGH authored NO-TOOLS tools/CallerEpoch.lua and CaptureAccounting.lua with
base fixtures. Codex reviewed/applied, corrected a nil-hole fixture and added
14 regressions, including mandatory overflow paths and actual probe composition.
53 caller cases; all608 suite checks/14 suites +11 runner +19 preflight PASS.
CallerEpoch copies five caller-issued scalar tokens with framework separate from
controller, bounded non-reused epoch tickets and permanent exhaustion. It does
not establish native identity, generation or residency. CaptureAccounting is a
fresh per-pass precharge ledger, not a native-work/timing sandbox. No automatic
reset propagation is implemented; caller must stop on denial and close ledgers.
See CALLER-CONTEXT-OFFLINE.md and evidence/caller-context-offline-20261006.txt.
Actual probe model:54 captures/26 reads/566 charges complete;565 charges abort.
No production imports/native caller/events/deployment/game launch/save/settings
changes. Stop unchanged, lightunknown; deployed baseline remains5fa6b9c.
Next bounded offline task: review dormant one-shot caller/bridge design with token
provenance, reset propagation and per-operation accounting prerequisites.
Native identity/exposure/enum/loaded-world/light and Follow/rendering remain open.
Live tests stay here and deferred; external/model AI ON HOLD. Gemini drafts code;
Codex applies/reviews/tests/commits/pushes and alone later deploys/launches.
Older checkpoint/workflow blocks below are historical and superseded here.

## Latest checkpoint: native binding/lifecycle review (2026-10-06)

Started clean main795db52; Codex sole checkout editor. Gemini3.8 Flash HIGH
NO-TOOLS evidence draft/revision reviewed against installed class/source facts.
See NATIVE-BINDING-LIFECYCLE-REVIEW.md and evidence/binding-review-offline-20261006.txt.
Concrete candidate mappings recorded for13 probe aliases; actual Lua invocation,
enum paths/types and native wrapper identity remain UNKNOWN. Three square lookup
overloads and public global getCell metadata independently confirmed offline.
Residency object/add/remove collections are Set/HashSet, not ArrayList; exclude
whole-collection getObjectListForLua materialization. Engine.isResident has at
most10 explicit Lua-to-API call expressions, not a measured native cost bound.
Reload replaces the SarahFoundation table but preserves controller; future caller
needs a separate framework/epoch/reset contract. No native caller is implemented.
48 probe checks rerun PASS; runtime code unchanged. Prior full555 checks/13 suites
+11 runner +19 preflight baseline not rerun for this documentation-only batch.
Next bounded offline Gemini coding: inert caller epoch/reset policy and capture
operation accounting contract, no native residency simulation or runtime hooks.
Codex reviews/applies/tests/commits/pushes. Live testing stays here and deferred.
Lighting unknown, external/model AI ON HOLD, Stop unchanged. No deployment/game
launch/save/settings changes; deployed baseline5fa6b9c. Follow/rendering pending.
Older blocks below are historical and superseded here.

## Latest checkpoint: inert symbol exposure probe (2026-10-06)

Started clean main40bc5aa; Codex retains sole shared-checkout editing ownership.
Gemini 3.8 Flash HIGH authored NO-TOOLS source/base fixtures; Codex reviewed,
applied and strengthened actual-stage/privacy/reference regressions.
tools/NativeExposureProbe.lua is implemented/tested OFFLINE ONLY, with fixed
13 aliases, at most26 symbol reads/54 lifecycle captures. It never invokes
resolved methods or enum metadata and returns scalar diagnostics only.
No native resolver/engine bridge is included. Exposed/distinct_references are
statements about supplied fixture references, NOT verified engine compatibility.
Lighting stays unknown; nativeAcceptance=false. No production imports/wiring,
deployment, game launches, actions or saves/settings changes. Stop untouched.
48 probe checks; all555 checks/13 suites +11 runner +19 preflight PASS.
See EXPOSURE-PROBE-OFFLINE.md and evidence/exposure-probe-offline-20261006.txt.
Next bounded offline step: review concrete native caller/resolver mapping and
lifecycle-token evidence; prepare deferred overload/enum/reset acceptance cases.
Do not infer native symbol availability or wrapper stability from these fixtures.
Codex alone reviews/applies/tests/commits/pushes and later deploys/launches.
Live tests stay here and deferred. Deployed baseline remains5fa6b9c; external/model
AI ON HOLD. Native Follow/rendering, identity/exposure/light remain pending.
Older checkpoint/workflow blocks below are historical and superseded here.

## Latest checkpoint: bounded independent-light audit (2026-10-06)

Codex owns the shared checkout; clean main2cce1d8 verified at start. Gemini
3.8 Flash HIGH reviewed supplied evidence with NO TOOLS; Codex rejected overclaims,
reviewed the revision and independently confirmed selected bytecode/getter paths.
See INDEPENDENT-LIGHTING-AUDIT.md and evidence/lighting-audit-offline-20261006.txt.
No supplied candidate establishes trustworthy read-only, Sarah-independent target
illumination. Packed RGB is passive cache; JNI lamp totals are zero (fallback
stores values); climate ambient/day/night can use local-player cheat overrides.
Indexed JNI lightInfo may update caches/room-seen state. -1 refresh bypass and
square field write reconfirmed. This bounded result does not prove no other API exists.
Sampler lighting remains unknown; no runtime code or Knowledge policy changed.
57 sampler checks rerun PASS. Prior full507 checks/12 suites +11 runner +19 preflight
baseline remains valid for unchanged source; full suite not rerun for this docs batch.
No native/game calls, deployment, saves/settings changes. Deployed baseline5fa6b9c.
Next bounded offline coding batch: Gemini drafts an inert native exposure diagnostic
artifact from NATIVE-ADAPTER-DIAGNOSTIC-SPEC.md; Codex reviews/applies/tests.
Actual Lua invocation, identity/exposure, loaded-world proof and Follow/rendering
remain pending. Live tests stay here and deferred; external/model AI ON HOLD.
Older checkpoint/workflow blocks below are historical, superseded here.

## Latest checkpoint: inert diagnostic sampler (2026-10-06)

Gemini 3.8 Flash HIGH authored the sampler/base fixtures through NO-TOOLS CLI
exports; Codex remains sole checkout editor and applied/reviewed/corrected/tested
this batch. DiagnosticSampler.lua composes the actual existing Collector,
Coverage, Perception and ObstructionNormalizer through injected read-only APIs.
It is OFFLINE ONLY: no production import, native binding, tick/event integration,
deployment or game launch. Lighting is deliberately unknown; scalar diagnostics
publish no positions and cannot add confirmed observations to Knowledge.
57 sampler checks; all 507 checks across 12 suites +11 runner +19 preflight PASS.
See SAMPLER-OFFLINE.md and evidence/sampler-offline-20261006.txt for boundaries.
Codex corrected forged-enum expectations/63-square fixture assumptions and added
cleanup protection, abort cursor reset and actual-stage/Knowledge regressions.
Started from clean main 2391581. Shared checkout remains owned by Codex.
Live tests remain deferred and stay in this chat. Saves/settings untouched;
deployed isolated baseline remains 5fa6b9c. External/model AI remains ON HOLD.
Next bounded offline task: Sarah-independent lighting evidence audit. Native
identity/Lua exposure, loaded-world lifecycle proof, Follow/rendering acceptance
remain open. Do not wire or deploy this sampler until those gates are resolved.
Older checkpoint and workflow blocks below are historical and superseded here.

## Latest checkpoint: inert adapter boundary policies (2026-10-06)

Gemini handles coding drafts; Codex alone applies/reviews/tests/commits/pushes.
Live testing stays in this chat and remains explicitly deferred. Codex owns checkout.
SessionIdentity.lua and ObstructionNormalizer.lua are implemented/tested OFFLINE,
not imported/integrated/deployed. See ADAPTER-BOUNDARY-OFFLINE.md for caller-token
provenance/unique namespaces, FIFO64 IDs and exact-reference enum interpretation.
Native wrapper identity, Lua exposure and independent lighting remain unverified.
Gemini authored code/base fixtures with NO TOOLS; Codex corrected nil-hole false
positives, mandatory overflow fixtures and actual Perception/Knowledge composition.
49 boundary checks; all 450 suite checks/11 suites +11 runner +19 preflight PASS.
No game launches, saves/settings changes, movement/events or external/model AI.
Latest deployed baseline remains 5fa6b9c; isolated world/backups unchanged.
Next offline work: one-shot injected sampling coordinator contract with shared
budgets/lifecycle invalidation and independent-light evidence audit; no native wiring.
Follow/rendering native gates remain pending. Older state blocks are historical.

## Corrected user workflow and current task (2026-10-06)

Gemini handles the NEXT coding task; Codex alone applies, reviews, tests and
commits/pushes. Live testing stays in this chat and remains deferred until explicitly
resumed. This corrects the earlier ambiguous Codex-coding reminder.
Starting clean main 9046099; Codex retains sole checkout editing ownership.
Historical start of completed batch: Gemini NO-TOOLS implementation/fixtures for a bounded caller-token
session registry and exact-reference obstruction normalizer. No engine identity
or enum exposure is assumed verified. No production wiring, deployment/game
launches, saves/settings changes or model AI integration.

## Current user workflow preference (2026-10-06)

User now requests Codex handles coding; live testing stays in this chat.
This supersedes the earlier preference to delegate coding to Gemini.
Live testing remains deferred until explicitly resumed; Codex alone deploys and
launches with disposable-profile backups. No game/save/settings change authorized
by this workflow reminder. Offline checkpoint remains 4449666 (401+11+19 PASS).

## Latest checkpoint: offline candidate collector (2026-10-06)

Codex owns checkout. CandidateCollector.lua is implemented OFFLINE and inert,
with injected read-only queries, private state, fixed call/candidate/cursor limits,
round-robin list cursors and transactional lifecycle discard. See COLLECTOR-OFFLINE.md.
Gemini 3.8 Flash HIGH authored code/base fixtures via NO-TOOLS drafts/structured
CLI exports; Codex applied/reviewed, fixed a budget-boundary starvation bug,
corrected fixture assumptions and added review regressions. Gemini did not edit
checkout. Earlier batch used Gemini coding drafts with Codex review/tests; see current preference above.
All 401 suite checks across 10 suites +11 runner +19 preflight self-tests PASS.
No native imports/production wiring/deployment/game launches or saves/settings
changes. Latest deployed baseline remains 5fa6b9c; disposable world/backups unchanged.
Tokens are caller-issued strings only; native identity/exposure and independent
lighting remain unresolved. Follow/rendering native gates pending, live tests
deferred, external/model AI ON HOLD. Next offline task: adapter identity/token and
exact-enum boundary investigation/fixtures, not gameplay or tick integration.
Temporary Remote Control session remains available in empty Admin visibility-test;
visible drafts were followed by structured CLI source exports for reproducibility.
Older state/counts below are historical and superseded by this block.

## Latest checkpoint: reviewed adapter diagnostic design (2026-10-06)

Codex owns the checkout. NATIVE-ADAPTER-DIAGNOSTIC-SPEC.md is a reviewed design,
not an implemented collector or native probe. Gemini 3.8 Flash HIGH drafted with
NO TOOLS through the user-visible temporary interactive Remote Control session;
Codex corrected hidden-position leakage, unsupported generation/identity claims,
enumeration fairness and explicit budget/lifecycle boundaries. Gemini did not edit
this checkout. No production changes, deployment, game launches or saves/settings
changes. Independent lighting and native Follow/rendering remain unresolved.
The verified code baseline remains aa7595f: 332 suite checks +11 runner +19 preflight
self-tests passed there. This docs-only checkpoint validates text/diff consistency;
those suites were not rerun. Latest deployed baseline remains 5fa6b9c.
Next: pure injected CandidateCollector policy and actual-Lua budget/fairness/reset
fixtures; resolve identity tokens offline before any native registry. No native
wiring. Live testing deferred; external/model AI ON HOLD. Temporary Gemini session
remains available for visible NO-TOOLS drafts, in the empty Admin visibility-test
workspace. It grants no Sarah checkout editing ownership or gameplay permissions.
Earlier state blocks and counts below are historical.

# Current Codex resume: offline coverage helper (2026-10-06)

Codex owns G:\Codex\Project Sarah. Read AGENTS, STATUS, ROADMAP, HANDOFF,
PERCEPTION-V1, COVERAGE-OFFLINE and NATIVE-PERCEPTION-ADAPTER-RESEARCH before editing.
Verify clean Git main/origin and ownership. Coverage helper is implemented offline
with injected queries/private budgets/no cross-call cache and 64 actual-Lua checks.
All 332 suite +11 runner +19 preflight self-tests PASS. No production integration,
deployment, game launch, saves/settings changes. Independent light unresolved:
-1 light path refresh bypass/shared-buffer read/square write confirmed in bytecode.
Next offline task: inert native adapter diagnostic specification for exposure,
enums, bounded enumeration/fairness, session IDs and lifecycle reset boundaries.
Live Follow/rendering tests remain pending and deferred; external/model AI ON HOLD.
Gemini HIGH authentication works outside sandbox but headless command permission
was denied. No bypass used; source-in-prompt NO-TOOLS proposals worked. Codex
applies/reviews/tests and alone edits/commits/pushes. Historical guidance follows.

# Superseding workflow note (2026-10-04)

The Escape coding fix was completed at `88fbafc`, deployed to the isolated mod,
and verified natively by the user as PASS (first Escape closes console without pause menu;
subsequent Escape opens normal pause menu). Corroborated by probe samples (`guard=true`,
swallow armed and expired).

The user now uses Codex for sustained coding and native testing, with Gemini assisting
on bounded tasks. Claude is reserved only for explicit user requests. Read `docs/STATUS.md`,
`docs/HANDOFF.md`, and `docs/M1-batched-acceptance.md` for current owner and remaining acceptance gates.
External in-game AI remains on hold.

---
# Historical: Escape failure coding handoff (2026-10-04, completed)

*Status: COMPLETED at `88fbafc` and natively verified.*

This task requested a narrow fix for the first-Escape pause menu bug:
Inspect actual Build 42.21.0 input ordering (`ToggleEscapeMenu` on `OnKeyPressed`).
`Console.lua` was modified to arm a one-shot swallow on Escape close and wrap
`ToggleEscapeMenu` with `SarahConsole.guard` to consume that single release.
All 71 automated checks passed (3 new console cases). Natively verified by user.

---
# Historical: Claude initial resume guide (2026-10-04)

Open the existing Antigravity Project Sarah project, local execution, canonical
folder `G:\Codex\Project Sarah`. Claude Sonnet 5.5 Medium was visible in the model
selector during setup; recheck your chosen model before sending the prompt.
The user will start Claude; no second coding agent has been started by Codex.

## Resume prompt

Continue Project Sarah in this existing checkout. Read AGENTS.md, CLAUDE.md,
docs/STATUS.md, docs/ROADMAP.md and docs/HANDOFF.md first. The latest implementation
checkpoint is 8f4f882; read docs/M1-console-test.md for the precise evidence.
Finish M1 slice A acceptance: native hold-repeat, Escape, rebind/conflict
persistence, English labels in Options, restored movement input and same-process
menu/world teardown. Physical F9 open/status/close already passed a user-operated
check. Back up a new disposable case game-closed before more live tests; preserve
the completed SarahConsoleCase and its Final-console backup. Do not rerun old
one-shot fault drivers or use normal saves. Keep installed game files read-only.
After each bounded task, update shared notes, commit source/evidence together,
push main and verify the remote. Keep external AI on hold. Add stop/cancellation
and bounded walk here only after slice A's remaining gate passes. Work autonomously
within this scope and ask only for missing information or actions that need it.

## Immediate local state

- Game closed at the previous checkpoint; recheck native window/process state.
- Continue selects isolated `Rising/SarahConsoleNativeCase`, only SarahFoundation enabled.
- Final exit saved a; one Sarah restored before checks.
- Temporary console probe disabled under runtime/disabled-probes; production
  console/modules/English UI.json deployed to the isolated mod.
- Latest backup group: runtime/backups/input-comparison-20261004/After-comparison.
- GitHub: https://github.com/cenationx/ProjectSarah, branch main. Git author already
  configured. Authentication in this separate app still needs a harmless check.
- Saves/logs/backups/dependencies are local and ignored, not included in GitHub.

## Automated checks

Working directory: `G:\Codex\Project Sarah`. Local Python:
`C:\Users\rudol\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe`.
Each suite imports Lupa from tools/dependencies/python; no install is required.

Run all 6 suites via the single-entry verification runner (153 checks total):
```powershell
$sarahPython = 'C:\Users\rudol\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe'
& $sarahPython tools/run_tests.py
```
See `docs/verification-workflow.md` for runner options, interpreter resolution, and generated Markdown/JSON reports in `tools/reports/`.
To test the runner itself (11 unit tests):
```powershell
& $sarahPython tools/test_runner.py
```

Run acceptance preflight tool before native testing (read-only inspection):
```powershell
& $sarahPython tools/preflight.py
```
To test the preflight tool itself (19 unit tests):
```powershell
& $sarahPython tools/test_preflight.py
```

Expected totals across 6 offline suites: 29 + 15 + 8 + 54 + 33 + 14 = 153 checks, plus 11 runner self-tests and 19 preflight tests. These execute actual Lua with simulated
engine/UI fixtures. They do not establish native game compatibility or input.
For consolidated native acceptance, follow `docs/M1-batched-acceptance.md`. Bulk Unicode typing and automated function keys were
unreliable in this game; physical/user checks and real observations must be labelled.

## Permissions and scope

The user authorized broad G-drive file access and PowerShell commands for
Antigravity Project Sarah to reduce routine prompts. Local app permission settings
are separate from Git and project instructions. File Allow rules for G:\ reads
and writes, plus a Terminal Commands Allow * rule were saved and visually checked.
The terminal wildcard covers all terminal commands, including PowerShell/native
tools; it is not a shell-only or G-drive-only execution boundary. Global/inherited
policies and other tool categories may still prompt. No command execution was
started through Claude to test approval behavior.

Broad capability does not change Sarah's work scope: keep project outputs under
the canonical checkout, preserve normal saves and installed game files, and do
not start the external AI layer. App permissions do not travel with this repo.
