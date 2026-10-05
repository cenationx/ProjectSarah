# Project Sarah roadmap

The intended direction is a dependable Sarah NPC foundation, followed by a small
AI-controlled vertical slice if the user approves starting AI. Later milestones
are planning proposals, not authorization or promises. Finish the current gate
before adding broader features. Multiplayer is outside the initial scope.

| Milestone | Outcome | Status |
|---|---|---|
| M0: Compatibility and feasibility | Establish a working NPC on installed PZ 42.21.0 | Narrow feasibility PASS; full PZNS FAIL |
| M0 hardening | Safe NPC lifecycle, recovery and repeatable test setup | Bounded evidence complete; broader acceptance OPEN |
| M1: Manual console and action interface | Configurable in-game console with checked commands/observations | IN PROGRESS; slice A native passed, slice B smoke passed, slice C implemented offline |
| M2: Minimal AI vertical slice | One bounded model-to-action loop | ON HOLD; explicit user approval required |
| M3: Sarah behavior and continuity | Personality, limited memory and useful behaviors | PROPOSED |
| M4: Release candidate | Installation, regression checks and user documentation | PROPOSED |

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
  tracking, timeout, busy/invalid-target rejection, synchronous callback hardening, session-reset collision protection, console mouse buttons toolbar, and sustained halt acceptance verification (146 automated checks pass across 6 suites plus 11 runner self-tests; native live movement, arrival, cancellation, and mouse UI acceptance pending Codex check per docs/M1-slice-c-checklist.md).
- [x] Reset/invalidate actions on unload, death, controller change and world switch.
- [ ] Native live command/focus/rebind/movement/restart tests in backed-up
  isolated cases; one Sarah and local player preserved.
- [ ] Optional guarded restore/save/unload developer commands only after A-C.

Gate: commands demonstrably work and fail safely before a model can invoke them.
Carry all M0 limitations and safeguards forward. The console contains no model
integration; accepting this plan does not authorize M2.

## M2: AI vertical slice (on hold)

- [ ] Obtain explicit approval to begin AI; agree local/hosted model and costs.
- [ ] Agree a narrow demonstration and acceptance criteria with the user.
- [ ] Connect one model through validated commands; keep engine operations on
  the game's supported thread and bound delays/retries.
- [ ] Validate model output and refuse unknown commands or invalid targets.
- [ ] Test timeouts, unavailable model, malformed output and manual stop.
- [ ] Demonstrate one repeatable useful behavior before expanding.

## M3 and M4: proposals to refine after the vertical slice

M3: personality and dialogue, minimal saved memory, a small set of useful tasks,
and behavior evaluations. Decide each addition from demonstrated needs.

M4: packaging, version compatibility checks, installation/uninstall instructions,
backup guidance, regression checklist, third-party notices and a limited release.
No multiplayer or broad PZNS modernization commitment is implied.
