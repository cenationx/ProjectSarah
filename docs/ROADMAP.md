## Current milestone overview (reviewed 2026-10-07)

This overview supersedes historical progress labels below. Checkboxes in dated
sections describe their stated evidence, not automatic native acceptance.
See MILESTONE-REVIEW-2026-10-07.md for scope and acceptance requirements.

| Milestone | Outcome | Current state | Exit gate |
|---|---|---|---|
| M0 Foundation | One persistent NPC; safe death/unload/recovery | Narrow native evidence accepted; wider limits open | Supported-scope recovery and no duplicates/resurrection |
| M1 First playable companion | Console, Walk Here, smooth Follow, Stop, nearby rendering | Implemented; partial live evidence; current pace/render gate pending | Current deployed revision passes movement/Stop, reload and wall/floor/look-away checks |
| M2a Independent observations | Sarah-relative geometry, admitted lighting and bounded memory | Offline candidates and source snapshot verified; native lighting OPEN | Native exposure/coverage, calibrated lighting, expiry and lifecycle resets |
| M2b Equipment and exchange | Melee equip, one garment, one-item give/take | Policy/proposals; native adapters unaccepted | Exact item conservation, appearance, capacity, cancellation and restart |
| M2c Commanded work | One-container loot, then room/house; equipment improvement | Planned | Accepted discovery, reachability, partial results, capacity and Stop |
| M2d Defense and construction | One-threat defense/retreat; one real build action | Planned | Native hit/cooldown, resource consumption and safe interruption |
| M3 External AI | One model-to-accepted-command loop | ON HOLD | Useful native core accepted, then explicit user approval |
| M4 Continuity/personality | Selected dialogue and continuity | Proposed | Scope based on demonstrated needs |
| M5 Release | Version-scoped installable/recoverable mod | Proposed | Install/uninstall, backup/restore, compatibility and licensing checks |

Track each capability as not started, implemented, offline verified, native
accepted or blocked. Record owner, code revision, deployed revision, evidence,
limitation and next action. Test totals are not completion percentages.

Priority: inert light-source snapshot accepted offline; run a small
isolated Follow/Stop/render and clock acceptance batch; calibrate one explicit
lamp; decide the lighting route. Independent manual equip work may proceed where
its action/target safety is established, without granting autonomous sight.
No source presence or geometric clarity implies confirmed sight.

Add acceptance criteria for Stop during commit boundaries, inventory/appearance
persistence, no stale task resumption, measured performance, ordinary travel and
floor transitions, and truthful partial-failure results. Keep larger user goals;
do not add hunger/hearing/multiplayer/distant simulation as current blockers.

## Bounded perception budget and lifecycle correction offline (2026-10-08)

Gemini completed offline correction and verification of perception read-budget bypass in `Engine.lua` (strict pre-invocation read charging and boundary check before each `list.get` call; stopping before exceeding `readLimit`) and lifecycle invalidation mismatch in `Commands.lua` (resetting Knowledge and perception on all non-active non-busy states including `blocked`, `deferred`, `unavailable`, and observation errors; deliberate transient `busy` handling preserving active action, memory, and Stop). Integrated regressions added in `test_render.py` (31 checks) and `test_commands.py` (68 checks). Confirmed production memory remains empty because lighting is unknown; does not imply sight or autonomous behavior. Retired-action ownership guards and Stop guarantees preserved. Full test runner: 787 checks across 17 suites, 11 runner self-tests, 42 preflight self-tests PASS. Milestone scope preserved: M1 movement/Stop acceptance remains immediate gate; independent lighting OPEN; external AI ON HOLD.

## Light source snapshot prototype defects corrected offline (2026-10-07)

Gemini corrected and verified offline the diagnostic-only light source snapshot prototype (`LightSourceSnapshot.lua`, 53 tests in `test_light_snapshot.py`) resolving all review defects: strict pre-operation budget enforcement (total_reads never exceeds maxReads on any path; tiny budgets maxReads=1..15 halt cleanly with exact call-count match), missing/malformed building and switch metadata strictly preserved as unknown (requiring authoritative getLocalToBuilding returning nil for unrestricted, and authoritative getSwitches returning sz=0 for switchCount=0; unknown switches force powerStatus=unknown), getter member-lookup exception isolation (never falling back to raw fields on throwing lookups; marked malformed), freshness defaulting to unknown (stale on positive discrepancy), independent generator vs grid power evaluation, same-size collection replacement/reordering detection via initial snapshot and full post-read re-verification pass, exception-safe reentrancy guard (`pcall` releasing busy), and honest read accounting. Separate source facts from sight; no confirmed target illumination or sight evaluated. Knowledge admission remains disabled; independent lighting blocker remains OPEN; external/model AI ON HOLD. Full test runner passes 784 checks across 17 suites, 11 runner self-tests, 42 preflight self-tests.

## Codex lighting follow-up: source reconstruction route (2026-10-07)

Codex owns checkout. Fresh offline inspection distinguishes globally registered
light-source parameters from player-indexed render outputs. Read-only source
getters offer a candidate for an authored Sarah-owned model, not an admitted
native illumination query. Power freshness, loaded source coverage, light
transmission and thresholds remain unresolved. Single-player torch registration
enumerates IsoPlayer.players; Sarah carried-lamp rendering is separately unproven.
See SARAH-LIGHTING-SOURCE-CANDIDATE.md for evidence and the smallest calibration
boundary. No code/deployment/launch/save/settings changes. Lighting stays unknown;
external/model AI remains ON HOLD. Existing 731+11+42 baseline is unchanged.
Next: bounded source snapshot investigation, then isolated calibration only after
fresh backup. No model may feed confirmed sight or memory before native acceptance.

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

## Batch B: Monotonic memory clock integrated offline; independent lighting remains open (2026-10-07)

- [x] Slice 6: Offline candidate native enumeration and Sarah-relative facing (`IsoGameCharacter.getForwardDirectionX/Y`). Bounded exact-reference snapshot enumeration via `sq:getMovingObjects()`, cross-sample list identity with stable tokens for unchanged lists (cursor fairness) and nonreused tokens for changed/reordered lists, bounded lifecycle-cleared snapshots (FIFO 128), fail-closed rejection for oversized lists (>64), native read budget accounting, strict boolean liveness requirement, collision-safe short identity tokens (`so:e<epoch>:s<seq>:<kind>:<oid>`), exclusion of dead/self/non-characters, no permanent Java handles.
- [x] Slice 7: Conservative loaded coverage (`Coverage.lua`) and exact obstruction normalization (`ObstructionNormalizer.lua`), preserving door/window distinctions. Unloaded intermediate squares and missing geometry fail closed to unknown.
- [x] Slice 8: Extended independent lighting investigation (`INDEPENDENT-LIGHTING-AUDIT.md`) and diagnostic-only light source snapshot prototype (`LightSourceSnapshot.lua`, `SARAH-LIGHTING-SOURCE-CANDIDATE.md`). Refused JNI -1 mutation and player camera slots. Inspected `IsoZombie` vision logic, `IsoGameCharacter.CanSee`, `interpolateLight`, `getDarkMulti`/`getVertLight`, `resultLightCount`, `lightInfluence`, `IsoLightSource`, `RoomDef.lightsActive`, `ServerLOS`, `getSkyLightLevel`, and `IsoChunk` player lighting arrays. All candidates rejected; lighting strictly preserved as `lighting = "unknown"` unconditionally and the independent lighting blocker remains OPEN. No claim that no suitable API exists anywhere in the engine. Unknown lighting never implies sight (visual confirmed = 0). Implemented and corrected inert diagnostic light source snapshot prototype capturing copied parameters, loaded squares, independent generator/grid power availability, freshness (defaults to unknown; stale on positive discrepancy), and distinct building restrictions with strict budgets, same-size mutation detection, getter failure isolation, and honest read accounting; separate source facts from sight; no confirmed target illumination or sight evaluated. Knowledge admission remains disabled.
- [x] Slice 9: Diagnostic commands `'look'` and `'perceive'` in `Commands.lua` and `Console.lua`. Read-only execution (strictly requires active observation state; never invokes checkLifecycle or disturbs follow/walk). Geometry and visual results reported separately; bounded memory snapshots with last-seen age in seconds (`math.max(0, now - rec.observedAt)`). Monotonic time provider injected via bounded engine delta accumulation (`getGameTime():getTimeDelta()`, fail-closed pause validation via boolean pause state or speed controls, speed-scaled, unclamped simulation delta to prevent discarding elapsed time or prolonging freshness, fail-closed without silent zero or wall-clock fallbacks); missing, throwing, or invalid delta invalidates observation memory immediately and recovery does not retain records of unknown elapsed age; memory invalidated on clock reversal; `state.reset()` clears accumulated time. Full pipeline idle lifecycle checks wired: `checkLifecycle()` detects death, unload, and controller/NPC replacement while idle, invalidating Knowledge and adapter perception without initiating/cancelling movement.
- [x] Offline test suite updated and passing: 771 suite checks across 17 suites (+40 checks in `tools/test_light_snapshot.py`, +29 prior Batch B checks across `tools/test_commands.py`, `tools/test_console.py`, `tools/test_render.py`), 11 runner self-tests, 42 preflight self-tests.
- [ ] Gate B: Codex review, isolated live acceptance (front/behind, player facing away, walls/doors/windows, darkness, missing squares, memory expiry, one artificial lamp probe plan). Independent sight must pass before sight-driven combat or looting is enabled. Independent lighting blocker remains OPEN.

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
## Batch A: Follow pace, stop failure propagation, ownership, and reentrant step corrections implemented offline (2026-10-06)

- [x] Observations.read player running sampling via confirmed methods (isRunning, isSprinting).
- [x] Commands.invokeWalk contract tuple/single compatibility with Console.walkSarah.
- [x] Engine.SarahWalkAction instance adapter/token binding and ownership guarding.
- [x] NPC modData live object removal; runtime ownership record in Engine.runtimeOwnership with explicit lifecycle cleanup.
- [x] Stale adapter.stop protection: prevents clearing newer same-NPC ownership, running flag, queue, or path.
- [x] Ownership checks fail closed when runtime record is missing, invalid, or unreadable.
- [x] Queue admission safety against failure, synchronous completion, and re-entry; rejected walk admission on failed setOwnership prevents ownerless actions.
- [x] Engine runtime ownership continuity across module reload on SAME NPC via _G._SarahRuntimeOwnership.
- [x] adapter.stop failure propagation: attempts all safe cleanup and returns false, reason; Console/Commands stopFailed blocking preserved.
- [x] Retired actions guarded from base methods that mutate pathfinding/queues.
- [x] Follow step pace matching, mid-stride acceleration/deceleration, deadzone reset, WalkHere walking invariant.
- [x] Dispatcher stepAction assignment and failure handling guarded against synchronous callbacks, retirement, cancellation, and re-entry (never clobbers newer step generations).
- [x] Offline test suite updated and passing: 702 suite checks (+4 new checks) across 16 suites, 11 runner self-tests, 42 preflight self-tests.
- [ ] Gate A: Codex review, closed-game fresh backup, deployment, and isolated live acceptance testing.

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

## Current offline next step (2026-10-06)

- [x] Caller-token identity and exact-reference obstruction policies: inert/offline.
- [x] Injected one-shot DiagnosticSampler: shared coverage budget, lifecycle
  invalidation, unknown lighting, scalar-only results and abort cursor reset.
  Gemini authored; Codex reviewed/applied. 57 sampler checks; all 507 suite checks
  across 12 suites +11 runner +19 preflight self-tests PASS.
- [x] Bounded independent-light evidence audit: no suitable supplied query
  established. See INDEPENDENT-LIGHTING-AUDIT.md; this is not exhaustive API proof.
- [x] Inert tools/NativeExposureProbe.lua, Gemini authoring/Codex review:
  48 probe checks; full555 checks/13 suites +11 runner +19 preflight PASS.
  No native resolver/invocation; symbol/enum reference fixtures are not engine proof.
- [x] Concrete native candidate/resolver mapping and lifecycle review:
  NATIVE-BINDING-LIFECYCLE-REVIEW.md, deferred cases prepared, native gates open.
- [x] Inert CallerEpoch/CaptureAccounting tools, Gemini coding/Codex review:
  53 caller cases; all608 suite checks/14 suites +11 runner +19 preflight PASS.
  No native token proof or automatic reset propagation.
- [x] Review dormant one-shot caller/bridge design: exact token provenance, reset
  propagation and per-operation accounting, no native invocation or runtime hooks.
- [x] Narrow symbol diagnostic contract/code with injected markers and explicit
  unassessed native capabilities; no runtime wiring.41 cases;649+11+19 PASS.
  Stop generic scaffolding; see SYMBOL-EXPOSURE-OFFLINE.md.
- [x] Bounded read-only Kahlua resolver/type/exception audit; see
  NATIVE-RESOLVER-AUDIT.md. No runtime caller or native acceptance.
- [x] Bounded offline equipment-action/UI/commit review; see
  EQUIPMENT-ACTION-OFFLINE-REVIEW.md. Preparatory only, no equipment implementation.
- [x] Concrete ownership/container and
  worn-slot conflict audit: OWNERSHIP-WORN-SLOT-OFFLINE.md. Static only.
- [x] Concrete narrow manual equip adapter proposal resolving UI/precommit
  integration before implementation; no auto-selection or runtime wiring.
- [x] Dormant narrow manual-equip request/state coding, fixture-only policy;
  41 groups;690 suite +11 runner +19 preflight PASS. See MANUAL-EQUIP-POLICY-OFFLINE.md.
  Actual native adapter/event/UI isolation still unimplemented and unverified.
- [x] Preflight report completeness/consistency fix: partial passing report blocks;
  required suites share runner defaults.690 suite +11 runner +42 preflight PASS.
- [ ] IN PROGRESS: user resumed isolated native Follow/rendering acceptance, then audited
  exposure/getter paths and loaded-world evidence; no more generic scaffolding.

See SAMPLER-OFFLINE.md. Gemini handles coding drafts; Codex alone edits/reviews/
tests/commits/pushes. Live tests remain here and deferred. Model AI ON HOLD.

# Project Sarah roadmap

The intended direction is a dependable Sarah NPC foundation, followed by a small
native survivor core. External/model AI comes near the end, after useful core
mechanics pass acceptance and the user explicitly approves integration. Later milestones
are planning proposals, not authorization or promises. Finish the current gate
before adding broader features. Multiplayer is outside the initial scope.

Historical overview superseded by the current milestone overview above.

## M0: completed evidence

- [x] Pin and inspect unmodified PZNS; preserve original MIT source.
- [x] Verify installed version and missing/replacement engine APIs.
- [x] Use independent minimal NPC prototype rather than a broad PZNS rewrite.
- [x] Live-test spawn, one walking action, inventory transfer, death/removal,
  alive NPC persistence through full restart.
- [x] Put source and sanitized evidence in GitHub with clear licensing boundaries.

## M0 hardening: current gate

- [x] Duplicate prevention and partial-construction safeguards.
- [x] Alternating checkpoints, prior good copy, failure-policy tests.
- [x] Live corrupted latest-checkpoint recovery without fresh replacement.
- [x] Live death tombstone and no resurrection after full restart.
- [x] Automated callback reload/session-reset checks.
- [x] Independent alive/dead disposable worlds pass session assertions across
  full process restarts (not same-process world switching).
- [x] Live menu return, same-world Continue and alive/dead/alive switching in
  one process, using the temporary mouse entrypoint into the real pause menu.
- [x] Live main-script reload: retained controller/NPC, one tick per frame and
  one save callback after two reloads.
- [x] Engine/Lifecycle/main reloads retain controller/NPC and single callbacks;
  injected interruption after native removal preserves the real unfinished
  reference across reload/later ticks, refuses replacement/unsafe save and
  recovers from the good checkpoint on full restart. Native spontaneous or
  silent cleanup failures and hot schema upgrades remain unverified.
- [x] Actual-NPC clothing/model viewer inspection before/after full restart.
- [x] Direct ordinary world-scene visibility, separated positions and diagnosis;
  bounded B42 FBO hook passed restored/fresh NPC scenes. Broad cutaways/floors
  and event availability remain limitations in `M0-world-render-test.md`.
- [x] Fresh no-mod control reproduces duplicate/invalid room metadata errors;
  root cause remains unknown, with no Sarah fix justified by this comparison.
- [x] Define preventive travel suspension and deferred saved-location recovery;
  controlled player travel passed actual square unloading, away restart and
  return. Ordinary walking/driving and abrupt-movement boundaries remain open.
- [x] Live locked existing-file failure, safe retention, retry and full restart;
  fresh-token readback rejects swallowed native write errors. Disk-full/partial
  writes and exceptional native cleanup remain limitations.
- [x] Six-minute idle-room session: 12 unload/restores, 25 verified saves,
  verifier/world-list cleanup after ticks and full restart without duplication.
  Hours-long play and complete native resource reclamation remain unverified.
- [x] Document supported scope, remaining risks and bounded development handoff
  in `M0-supported-scope.md`; broad hardening/release acceptance remains open.

Gate: mark hardening complete only when the relevant checks have direct evidence
or the user explicitly accepts a documented limitation. Keep the AI hold intact.

## M1: manual console and action interface (in progress)

- [x] Plan the user's key-toggle console and staged commands in `M1-console-plan.md`.
- [x] Slice A implementation: shared parser/observations and help/status/inventory panel; read-only
  commands must not implicitly spawn, restore, save or repair Sarah.
- [x] Twelve command and eleven simulated console checks (71 automated total); live menu open,
  typed commands, Enter/Run, mouse close, and physical Escape fix verified (first Escape closes
  console without menu; subsequent Escape opens menu). See `M1-console-test.md`.
- [x] User-operated physical F9 open/status/close, corroborated by probe samples;
  full restart with one Sarah/local player and final native scrolling output.
- [x] Configurable unused binding: provisional F9, conflict checks and actual
  key delivery verified; safe input focus, close and mouse fallback.
- [x] Slice B: stop, cancellation and bounded request/result history; 94 automated checks and native idle-stop/history/session-reset smoke checks passed. Native active-action cancellation remains required alongside slice C.
- [x] Slice C: walk here, initially nearby/same-floor; one action, true completion
  tracking, timeout, busy/invalid-target rejection, synchronous callback hardening, session-reset collision protection, console mouse buttons toolbar, movable console dragging with bounds clamping, and sustained halt acceptance verification (153 automated checks pass across 6 suites plus 11 runner self-tests and 19 preflight tests; bounded native live walk, cancellation, and reload reset passed; remaining native checks prepared for batched acceptance per docs/M1-batched-acceptance.md and docs/HANDOFF.md).
- [x] Manual follow command: bounded offline follow-player behavior reusing existing dispatcher, 2-tile deadzone, 8-tile leash, floor checking, adjacent candidate targeting, stop mid-stride cancellation, stop failure blocking, console Follow mouse button, status distinctions (walking, in-range waiting vs before next walk during cooldown, disengaged with reason, engine stop failure warning), asynchronous one-time failure feedback without polling or replay, responsive mid-walk retargeting with bounded frequency, and bounded progress protection against stall masking (222 automated checks pass across 7 suites; native acceptance strictly pending Codex live verification).
- [x] Reset/invalidate actions on unload, death, controller change and world switch.
- [ ] Native live command/focus/rebind/movement/restart tests in backed-up
  isolated cases; one Sarah and local player preserved.
- [ ] Optional guarded restore/save/unload developer commands only after A-C.

Gate: commands demonstrably work and fail safely before a model can invoke them.
Carry all M0 limitations and safeguards forward. The console contains no model
integration; accepting the console plan does not establish native survivor acceptance or authorize external AI.

## M2: small native survivor core (implementation and native acceptance pending)

User direction updated 2026-10-05: meaningful native mechanics first; external
AI is one of the last additions. See [SURVIVOR-CORE-PLAN.md](SURVIVOR-CORE-PLAN.md)
for inspected references, slice boundaries, uncertainties and acceptance.

- [ ] Resolve pending foundation/Follow native checks and nearby rendering independence.
- [x] Offline native adapter investigation: registered geometry APIs, conservative loaded-coverage proposal, independent lighting remains unverified; see NATIVE-PERCEPTION-ADAPTER-RESEARCH.md. No integration or native acceptance.
- [x] Offline conservative loaded-coverage helper: 64 actual-Lua checks, explicit private sample budgets and no cross-call cache; no native wiring/deployment. Light refresh bypass confirmed in bytecode; independent lighting unresolved. See COVERAGE-OFFLINE.md.
- [ ] Independent Sarah sight: offline policy/memory implemented (46 fixtures), native integration/lighting/acceptance pending; see PERCEPTION-V1.md.
- [ ] Real inventory transfer and supported weapon/clothing equipment.
- [ ] Bounded self-defense against one threat, with retreat and cancellation policy.
- [ ] Loot one container, then a selected room/house with capacity and interruption handling.
- [ ] Explainable equipment improvements from owned supported items.
- [ ] Player-Sarah item exchange, followed by bounded barter if desired.
- [ ] One specified native construction action consuming real tools/materials.

Gate: useful native survivor behavior demonstrated in isolated gameplay before
external/model integration. This is the proposed sequence, not implementation
or acceptance of every feature.

## M3: external AI vertical slice (on hold until native core)

- [ ] Obtain explicit approval to begin AI; agree local/hosted model and costs.
- [ ] Agree a narrow demonstration and acceptance criteria with the user.
- [ ] Connect one model through validated commands; keep engine operations on
  the game's supported thread and bound delays/retries.
- [ ] Validate model output and refuse unknown commands or invalid targets.
- [ ] Test timeouts, unavailable model, malformed output and manual stop.
- [ ] Demonstrate one repeatable useful behavior before expanding.

## M4 and M5: proposals to refine after the native core

M4: personality and dialogue, minimal saved memory, a small set of useful tasks,
and behavior evaluations. Decide each addition from demonstrated needs.

M5: packaging, version compatibility checks, installation/uninstall instructions,
backup guidance, regression checklist, third-party notices and a limited release.
No multiplayer or broad PZNS modernization commitment is implied.

Native slice C update (2026-10-05): nearby arrival, already-at-target, sustained cancellation/resumption, mouse toolbar and context-menu success, same-process history reset verified. Distance refusal/red feedback and post-reload user movement remain pending. See evidence/slice-c-native-partial.txt; no full native acceptance claim.

Follow responsiveness & stress pass: 222 offline suite checks (66 follow) plus 11 runner/19 preflight pass; advancing simulation and bounded progress protection verified offline; native regression pending. See latest STATUS/HANDOFF.
