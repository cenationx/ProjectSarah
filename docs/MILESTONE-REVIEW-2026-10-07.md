# Project Sarah milestone review

2026-10-07. Codex review against ROADMAP, SURVIVOR-CORE-PLAN,
GEMINI-CODING-QUEUE and shared handoff state at eee1122.
User accepted this milestone review for integration after Gemini handoff. It does not constitute gameplay acceptance or new AI authorization.
Gemini returned ownership; Codex integrated this review into the shared plan.
Native and offline acceptance remain separate; the current prototype needs correction.

## Assessment

The project direction remains appropriate: dependable native mechanics before
external AI. The current roadmap mixes chronological updates, implementation
checkboxes and native acceptance, and still labels M2 research/planning despite
implemented observation candidates. Old suite totals and current ownership
statements appear together. Do not treat each checked research slice as a
completed gameplay feature, or use test counts as completion percentages.

Replace the current milestone overview with the table below, preserving existing
historical evidence in dated sections. Use one current-state overview; historical
notes must not override current status.

| Milestone | Concrete outcome | Current position | Exit evidence |
|---|---|---|---|
| M0 Foundation | One persistent NPC with safe death/unload/recovery | Narrow native evidence accepted; broader limits documented | No duplicate/resurrection; safe failed save/removal; supported-scope record |
| M1 First playable companion | Console, Walk Here, smooth Follow, reliable Stop and nearby rendering | Implemented; prior partial live evidence; current pace/render candidate pending | Reviewed deployment passes movement/Stop, reload, look-away and wall/floor checks |
| M2a Independent observations | Sarah-relative geometry, admitted lighting, bounded observation memory | Offline candidates and diagnostic wiring; lighting OPEN | Native exposure, loaded coverage, darkness/light calibration, age/reset behavior |
| M2b Manual equipment and exchange | Supported melee equip, one garment and give/take | Dormant policy/proposals; native adapters not accepted | Exact item identity/count conservation, hands/model, capacity, cancellation and restart |
| M2c Useful commanded work | Loot one known container, then one selected room/house; supported equipment improvement | Planned | Reachability, discovery rules, partial results, capacity, Stop and lifecycle interruption |
| M2d Defense and construction | One-threat defense/retreat and one selected real build action | Planned | Real hit/cooldown and resource consumption; safe interruption; no implicit resumption |
| M3 External AI | One bounded model-to-accepted-command loop | ON HOLD | Explicit approval after useful native core; no bypass of command/Stop/knowledge guards |
| M4 Continuity/personality | Selected dialogue and longer continuity | Proposed | Define scope only after demonstrated needs; no automatic persistent-memory expansion |
| M5 Release | Installable, recoverable, version-scoped mod | Proposed | Reproducible installation, backup/restore, limited regression and licensing checklist |

M1 is the first-playable checkpoint, not the whole native survivor core. M2b
explicit player-directed operations can proceed without independent sight only
where exact target/ownership and action safety are independently established;
this is not permission for omniscient discovery or autonomous work.

## Reporting completion

For each capability record: owner; code checkpoint; implementation state;
offline evidence; deployed checkpoint; native case/evidence; remaining limitation;
next action. Use not started / implemented / offline verified / native accepted /
blocked. A milestone closes on its exit evidence, not number of helper modules.
A percentage may be a rough planning estimate only; do not report precise effort
remaining from checkbox totals. Historical tests on old revisions are not current
native acceptance of subsequently changed code.

## Sequence from the present checkpoint

1. Finish and review Gemini's inert light-source snapshot batch; no production
   lighting admission. Preserve unknown lighting and confirmed-memory restrictions.
2. Run a small Codex isolated acceptance batch for the current Follow/Stop/render
   candidate and memory clock, with a fresh verified backup before deployment.
   Record exact deployed revision and observed versus unobserved cases.
3. Conduct one explicit lamp calibration experiment. Test source access/on-off,
   power, distance, wall/door/curtain, unload and fixed-position player-facing
   changes. A source snapshot is not target illumination. Include daylight,
   room/window transitions and unsupported source types in the limitation record.
4. Decide lighting route from evidence: native admissible query, explicitly
   authored and calibrated conservative model, or still blocked. Do not add more
   generic scaffolding or repeatedly audit the same rejected methods. A partial
   artificial-light model must report its unsupported cases unknown and must not
   be presented as full independent sight.
5. Review the existing manual equip proposal and implement the smallest supported
   native adapter; then garment and one-item exchange. Accept those before loot.
6. Build single-container loot before room/house discovery. Independently inspect
   combat/build admission, but enable sight-driven work only after perception gates.

## Missing acceptance requirements to add

### A. Stop and interruptions

Document current Stop as cancellation of requested work with no silent restart.
Keep a single action owner across movement, inventory, combat and construction.
Specify what is committed when Stop arrives during item transfer or build
completion. Do not redefine Stop to leave self-defense running without explicit
user agreement. New tasks must demonstrate interruption at start, mid-action,
completion boundary and lifecycle replacement as relevant to their mutation.

### B. Persistence boundaries

Extend the existing recovery contract when real inventory/appearance mutations
arrive. Verify confirmed held/worn/item changes survive restart, and unfinished
tasks do not resume from stale handles. Observation memory stays bounded and
session-local unless persistent memory is separately designed and authorized.
Never claim atomic rollback for irreversible or partially completed native actions.

### C. Performance and ordinary travel

Measure scan/read budgets and frame impact in sparse and crowded loaded scenes;
choose a practical measured acceptance threshold rather than inventing one.
Exercise ordinary walking/driving unload and return, plus floor transitions, once
movement is accepted. Run a sustained normal session for duplicate/callback/memory
leak symptoms; the existing six-minute case is not long-session proof.
Keep native diagnostics bounded and disabled outside the supported isolated setup
until production eligibility is deliberately reviewed.

### D. Useful failure reporting

For every admitted action give a concrete completed / cancelled / refused /
partial-failure result. Missing world data is unknown, not empty or safe. A full
inventory, unreachable target, removed object or unavailable API must terminate
bounded work with a useful reason. Preserve previous committed changes truthfully.

### E. Version and release boundary

Retain the inspected Build 42.21 baseline and supported single-player scope.
Before release, define a cheap compatibility check and refusal/degraded behavior
for unsupported builds. Document backup/restore and uninstall behavior without
promising removal restores world changes. Do not expand to multiplayer or distant
simulation as an accidental consequence of refactoring.

## Scope discipline

Do not add hunger/thirst automation, hearing, relationships, barter economy,
long-range travel, broad crafting, multiplayer or general AI planning now.
These are optional later proposals, not missing blockers for the current native
slices. Trade/give-take and one build action remain existing user goals; the
small first-playable checkpoint does not delete them.

## Handoff integration

When Gemini returns ownership, review its actual changes and tests first, then
update the current ROADMAP milestone table and shared next-step notes using this
review. Keep research-completed and feature-accepted labels separate. Commit/push
reviewed docs with the relevant checkpoint. Do not edit concurrently or interrupt
Gemini's current bounded coding task solely to reorganize planning documents.
