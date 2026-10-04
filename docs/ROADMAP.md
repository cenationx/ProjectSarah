# Project Sarah roadmap

The intended direction is a dependable Sarah NPC foundation, followed by a small
AI-controlled vertical slice if the user approves starting AI. Later milestones
are planning proposals, not authorization or promises. Finish the current gate
before adding broader features. Multiplayer is outside the initial scope.

| Milestone | Outcome | Status |
|---|---|---|
| M0: Compatibility and feasibility | Establish a working NPC on installed PZ 42.21.0 | Narrow feasibility PASS; full PZNS FAIL |
| M0 hardening | Safe NPC lifecycle, recovery and repeatable test setup | IN PROGRESS |
| M1: Deterministic action interface | Small checked set of commands and observations | PLANNED; no model required |
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
- [ ] Broader module reload and actual incomplete-cleanup reference checks.
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
- [ ] Bounded longer-session test with repeat saves/reloads and no duplication.
- [ ] Document supported scope, remaining risks and M0 handoff decision.

Gate: mark hardening complete only when the relevant checks have direct evidence
or the user explicitly accepts a documented limitation. Keep the AI hold intact.

## M1: action interface (planned)

- [ ] Define a small observation record: Sarah/player positions, alive state,
  inventory summary and action status. Avoid unrestricted engine access.
- [ ] Define deterministic commands: initially walk, stop and inspect inventory.
- [ ] Validate targets, lifecycle state and action preconditions; return explicit
  success/failure. Queue at most the permitted amount of work.
- [ ] Test commands in the isolated game without an external model.

Gate: commands demonstrably work and fail safely before a model can invoke them.

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
