# Gemini coding queue

2026-10-06. User authorizes substantial manual Gemini coding batches.
This expands implementation scope beyond the older research-only proposal.
External/model AI remains on hold. Codex handles review, deployment and live tests.

## How to execute

Open G:\Codex\Project Sarah in Antigravity. Read AGENTS.md, CLAUDE.md,
CLAUDE-RESUME.md, STATUS.md, ROADMAP.md and HANDOFF.md before starting.
Use Gemini 3.8 Flash HIGH. Do not invoke the CLI bridge.

Codex owns the checkout until the user hands editing to Gemini. Once handed over,
Gemini is the sole editor for that batch; Codex does not edit concurrently.
Gemini may implement and run offline tests, but must not deploy, launch the game,
alter any save/settings, commit or push. Installed game files are read-only.
Keep scripts, outputs and inspection artifacts under this project. Internal app
storage is app-managed. Never publish installed code/classes, saves or raw logs.

Work through ordered slices in the selected batch. Read existing implementations
first; do not duplicate completed tools/policies. Each slice needs an actual useful
change, meaningful runnable regression tests where appropriate, and precise
implemented/offline-tested/native-unverified notes. Avoid generic frameworks and
new fixture-only helper layers that merely postpone a native blocker.

Only use supported native APIs with installed evidence. If native admission is
unresolved, finish the concrete inspection/proposal, mark that slice BLOCKED and
continue only independent work. Never replace missing sight/light evidence with
player caches or permissive booleans. Passing fixtures do not accept gameplay.

Do not combine all batches into one unchecked change. Each batch finishes with
changed files, tests/counts, unresolved gates and a short live checklist. Codex
reviews and checkpoints it before the next batch. Features beyond the current
accepted gate remain disabled and cannot initiate actions automatically.

## Batch A: movement and foundation, next coding assignment

1. Correct the Follow pace draft. Sample confirmed player isRunning/isSprinting
   methods and drive the existing walk action's walk/run intent. Verify static
   update/animation ordering; physical running remains a live gate. Preserve
   leash 8, deadzone 2, physiology limits and WalkHere walking. No speed multiplier.
2. Fix movement handle propagation through invokeWalk and Console: preserve
   current callback compatibility while returning the actual action for updates.
3. Make pace ownership per action/adapter/NPC. Do not close a globally cached
   action class over the first adapter. Guard update, setPace and cleanup against
   stale owners. Queue admission failure and synchronous callbacks must not leave
   stale handles or clear a newer action. Stop/failure/arrival/reset/unload/death
   clear pace safely. Add executable lifecycle and re-entry regressions.
4. Review rendering independence using the existing FBO/render mechanism.
   Implement a narrow candidate only if justified; keep wall/floor and residency
   safeguards. Do not simply remove player-visibility guards. If unsupported,
   deliver the precise blocker and native experiment rather than fake visibility.
5. Prepare the movement/render acceptance batch: walking/running/deceleration,
   turns, leash/stall, mid-stride Stop/no resume, restart/reload, nearby look-away
   and wall/floor occlusion. Update shared notes and run the existing full suite,
   runner and preflight self-tests. No deployment; game must close before Codex
   takes a fresh disposable backup and deploys.

Gate A: Codex review and isolated movement/render testing before enabling later
native behavior. Independent offline inspection in later batches may proceed.

## Batch B: Sarah's observations, reuse existing perception and memory

6. Implement a concrete bounded native candidate/facing collector only after
   confirming callable methods. Enumerate around Sarah, deduplicate session IDs,
   budget square/entity work and avoid permanent Java handles. Test crowd fairness,
   missing/dead entities and replacement/session invalidation.
7. Bind conservative loaded-world coverage and exact obstruction results using
   existing coverage/probe policies. Preserve door/window distinctions; missing
   geometry and query failure stay unknown. Do not trust endpoint loading alone.
8. Resolve independent lighting with a supported query or mark it unknown.
   Do not borrow the player's light/sight slot, infer daylight detection, or claim
   geometric clarity means visual detection. A negative finding is not a feature.
9. Wire one explicit diagnostic command into existing Perception/Knowledge only
   when admitted. Report geometry and visual status separately, bounded snapshots
   and last-seen age. No autonomous decisions. Reset on lifecycle/session changes;
   memory must not track occluded movement or cause actions. Test actual wiring.

Gate B: native front/behind, player facing elsewhere, walls/doors/windows,
darkness, missing squares, memory expiry and lifecycle checks. Independent sight
must pass before sight-driven combat or looting is enabled.

## Batch C: manual inventory and equipment

10. Implement one supported manual melee equip adapter using the existing
    ManualEquipPolicy proposal. Establish event/UI isolation first. Revalidate
    exact owned item, condition and hands immediately before mutation; report
    partial failure truthfully. Do not blindly reuse player hotbar timed actions.
11. Implement one supported garment operation: real item, slot/layer conflicts,
    visible model update and lifecycle cleanup. Preserve existing appearance;
    no automatic clothing stripping or broad best-equipment selector.
12. Implement explicit give/take of one selected item between player and Sarah.
    Validate ownership/capacity/distance and conserve identity/count. Serialize
    operations under existing command ownership. No half-transfer hidden by retry,
    duplication or rollback claims without evidence. Verify save/reload boundaries.

Gate C: Codex isolated held/worn appearance, item conservation, capacity,
cancellation, event/UI isolation and restart tests before expanding transfer.

## Batch D: useful commanded work

13. Implement loot of one explicitly selected known container, reusing admitted
    transfer and movement. Approach/revalidate existence, reachability, contents
    and capacity; allowlisted selection; bounded failure with clear reason.
    Stop must cancel remaining work and never auto-resume.
14. Extend to one selected room/house only after single-container acceptance.
    Discover a bounded container list through Sarah's accepted observations;
    do not read hidden contents. Skip inaccessible/failed targets without loops;
    return to a selected drop point using admitted transfer.
15. Add explainable equipment improvement among a small supported set of owned
    weapons/garments only after manual equip acceptance. Condition/compatibility/
    protection and drawbacks matter; hysteresis prevents repeated swaps.

Gate D: real item conservation, inaccessible rooms, changed/removed containers,
full inventory, Stop and restart. Do not silently resume serialized stale tasks.

## Batch E: defense and one construction action

16. Inspect and implement one-target native melee defense only after sight and
    manual weapon gates. Use real native collision/hit/cooldown machinery, never
    scripted damage. Start explicitly commanded, not autonomous. Lost sight,
    obstacles, exhaustion and Stop must end or safely refuse the action.
17. Add a bounded supported retreat response and explicit work interruption.
    Autonomous defense policy needs an agreed Stop contract; current Stop may
    not be reinterpreted. No interrupted task resumes without a new order.
18. Implement one selected native barricade/recipe only if NPC action admission,
    tools/materials/skills and completion are established. Consume actual resources
    once and verify resulting object. Cancellation/partial placement must be
    truthful. If unavailable, report the blocker instead of free construction.

Gate E: separate isolated combat and construction batches; real hit/health,
animation/cooldown, obstacle/lost-sight behavior, resource consumption and Stop.

## Finish and review

Use the repository's current verification-workflow.md and test runner rather than
inventing a harness or hardcoding the historical 690 count. New suites must emit
RESULT <count> ... passed and be included in runner defaults/preflight evidence.
Maintain STATUS/ROADMAP/HANDOFF/CLAUDE-RESUME for the actual current batch.
Mark native acceptance pending until Codex records live evidence. Hand ownership
back explicitly. Codex alone reviews, commits/pushes and deploys.
