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

| Milestone | Outcome | Status |
|---|---|---|
| M0: Compatibility and feasibility | Establish a working NPC on installed PZ 42.21.0 | Narrow feasibility PASS; full PZNS FAIL |
| M0 hardening | Safe NPC lifecycle, recovery and repeatable test setup | Bounded evidence complete; broader acceptance OPEN |
| M1: Manual console and action interface | Configurable in-game console with checked commands/observations | IN PROGRESS; slice A native passed, slice B smoke passed, slice C implemented offline, follow command implemented offline |
| M2: Native survivor core | Own perception, equipment, defense, bounded looting, exchange and one build action | RESEARCH/PLAN; see SURVIVOR-CORE-PLAN.md |
| M3: External AI vertical slice | One bounded model-to-action loop after native core | ON HOLD; explicit user approval required |
| M4: Broader behavior and continuity | Personality and expanded behaviors | PROPOSED |
| M5: Release candidate | Installation, regression checks and user documentation | PROPOSED |

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

## M2: small native survivor core (research and planning)

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

