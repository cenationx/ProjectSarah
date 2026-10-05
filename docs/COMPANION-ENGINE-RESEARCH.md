# Companion engine research

2026-10-05. Codex owns checkout. Offline investigation only; no gameplay changes,
deployment, game launch or native acceptance. External/model AI remains on hold.

## What the game actually supplies

Sarah is an IsoPlayer with an NPC control component, not a finished autonomous
survivor. The engine supplies a body, inventory, animation/state machinery and
pathfinding. Sarah's Lua supplies lifecycle, orders and cancellation. We must
build observation and task policy around supported engine actions.

The installed `projectzomboid.jar` SHA256 inspected in this session is
`E1A69EB743EDE60B213A0FE7F8B83D4FCAB773036D256CC4543A336F3B058A33`.
Selected classes were freshly decompiled with existing CFR 0.152 into ignored
`runtime/research-engine-20261005/fresh/`. Decompiled code is inspection evidence,
not a supported API guarantee; it is not included in this checkpoint.

## Execution loop in plain language

1. The game updates the character's movement, body and animation states.
2. SarahFoundation's OnTick callback periodically checks residency/lifecycle;
   the command dispatcher independently advances active movement/follow orders.
3. An order validates a loaded target and starts a character timed action.
4. The engine performs that action over subsequent updates. Completion/failure
   callbacks settle the order; Stop clears queued actions and cancels pathfinding.
5. Rendering is another path, with player lighting/visibility. Save/reload is
   another boundary, using Sarah's existing verified checkpoint mechanism.

Perception and decision policy must feed this loop without starting a competing
action or changing the local player's control slot. Current Follow is explicit
tracking of the player order target; it is not evidence of independent sight.

## Installed-code evidence and limits

Paths below are relative to the project unless prefixed `GAME`, meaning
`G:\Games\ProjectZomboid` (read-only). Java methods refer to fresh inspection.

| Area | Inspected evidence | Implication and remaining boundary |
|---|---|---|
| NPC switch | IsoPlayer.setNpc adds/removes AIComponent; IsoGameCharacter.isNpc tests component presence | This selects a control path; it does not install survivor planning |
| Native control | component/AIComponent.update is empty; doUpdatePlayerControls copies melee/bannedAttacking; postUpdatePlayer applies initiateAttack/running/justMoved | Potential native control hooks, not proof Lua can safely drive combat; exposure and state transitions still need tracing |
| Sight | IsoGameCharacter.CanSee delegates to LosUtil.lineClear and accepts anything except Blocked | Not full FOV: no explicit facing cone, sight-distance or light test in this method |
| Obstructions | LosUtil.lineClear samples adjacent grid-square vision tests; returns window/open-door/closed-door distinctions; missing squares skip adjacency checks | Preserve result distinctions. Missing world data cannot safely mean visible; preflight loaded coverage separately |
| Player sight | IsoPlayer.updateLOS uses playerIndex and square visibility | Do not borrow this whole update for an independent NPC; it also updates player threat/music statistics |
| Rendering | Engine.lua:68-84 uses square:isCanSee(playerIndex), same floor, residency and light information | Explains a player-facing visibility dependency. Removing one guard alone does not establish correct alpha/occlusion rendering |
| Movement | Engine.lua:98-147 validates same floor, loaded/free square and 8-tile bound, then ISWalkToTimedAction; stop clears queue, cancels path and clears path2 | Existing bounded executor is reusable; far/unloaded travel remains separate work |
| Creation/equipment | Engine.lua construct creates descriptor/IsoPlayer, marks partial construction, adds actual clothing and calls setWornItem, resets model | Current appearance proves only this creation path, not general timed equip/upgrade handling |
| Inventory/equip | GAME media/lua/shared/TimedActions/ISEquipWeaponAction.lua validates item ID in character inventory, changes hands, invokes player inventory/hotbar paths; ISWearClothing.lua also invokes player inventory UI | Character arguments alone do not guarantee NPC safety. Audit UI-dependent branches and item identity before reuse |
| Transfer | GAME media/lua/client/TimedActions/ISInventoryTransferAction.lua revalidates capacity and uses player loot UI; client transactions have another completion path | Transfer must conserve item identity/count and handle partial/cancelled operations; direct reuse unproven |
| Building | GAME media/lua/shared/TimedActions/ISBarricadeAction.lua validates target existence/equipped tools/materials, turns character, separates perform and complete | Wood requires hammer, plank and two nails. Trace completion and resource consumption before adapting; a visible animation is not completion evidence |
| Queue | GAME media/lua/client/TimedActions/ISTimedActionQueue.lua starts first action and advances queue; shared ISBaseTimedAction perform notifies completion, stop resets queue | Keep one owner of action queue. Audit action-specific complete/perform/stop behavior rather than assuming identical lifecycle |
| Persistence | Lifecycle.lua and Engine.lua manage alternating checkpoints and restore validation | Reuse established boundary. Do not serialize live Java references, queued actions or stale callbacks |

This pass did not fully trace melee collision/damage, door interaction, native
lighting for NPC perception, or all construction/transfer completion branches.
They remain research tasks, not capabilities established by this report.

## Comparable survival games

There is no inspected reference with identical mechanics. Use comparable parts
and explicitly retain engine differences.

**Cataclysm: Dark Days Ahead — technical reference.** Pinned inspected revision:
`09a75ac67df6043f831ca41753f7cc5fe1545244` (GitHub master resolved this session).
In [npcmove.cpp](https://github.com/CleverRaven/Cataclysm-DDA/blob/09a75ac67df6043f831ca41753f7cc5fe1545244/src/npcmove.cpp),
assess_danger starts at line 884; move at 1519 refreshes AI cache, evaluates
danger and selects an action; execute_action starts at 2101. Foraging yields
to danger. pick_up_item at 4509 rechecks permission, changed items/zones and
ownership before proceeding. Weapon evaluation at 2610 avoids repeated full
inventory evaluation per candidate. This supports separating observation,
policy and execution, plus revalidation immediately before mutation. The file
also uses behavior-tree machinery; Sarah need not reproduce it. CDDA is
turn-based with different action costs, inventory and combat, so copy neither
its timing nor its entire system. Armor selection was not established here.

**State of Decay 2 — behavior reference only.** Official developer
[Update 17 notes](https://support.stateofdecay.com/hc/en-us/articles/360043803611-Update-17-Patch-Notes-Updated-for-17-1)
state followers prioritize entering a vehicle during retreat over continuing
combat. [Update 7 notes](https://support.stateofdecay.com/hc/en-us/articles/360025827271-Update-7-0-Choose-Your-Own-Apocalypse?sort_by=votes)
describe preserving followers through population management. Search-index
extracts were accessible; full support pages failed to open, so this is limited
evidence. Borrow retreat overriding optional fighting, and explicit companion
residency. Internal algorithms, inventory architecture and world simulation
were not inspected. Third-person combat/base mechanics differ from Zomboid.

**Zomboid itself — design context.** Its
[2022 NPC developer notes](https://projectzomboid.com/blog/news/2022/04/lone-survivor/)
discuss local characters and distant meta activity. These are historical
work-in-progress plans, not proof of shipped autonomous survivor APIs. They
reinforce keeping loaded-world actions separate from future distant simulation.

Kenshi was searched, but no sufficient primary technical account of its job
arbitration was established. It is not architecture evidence in this report.

## Small Sarah design

Keep current lifecycle, dispatcher, engine adapter and Stop. Add:

- A perception adapter: bounded loaded candidates, Sarah's position/facing,
  range policy and obstruction checks. Results are visible, blocked or unknown
  with a reason. No player-facing visibility dependency; unknown never grants sight.
- Small memory: last observed position/time, with bounded entries and expiry.
  Seeing a target stop behind a wall does not grant its current hidden position.
- Explicit policy: lifecycle invalidation/Stop first; later opt-in defense,
  current task, optional equipment improvement, idle. No general planner needed.
- Task state: validate, approach, interact, verify, finish/fail/cancel. Keep one
  active action, bounded retry and a reason for refusal. Threat interruption
  initially requires a fresh order to resume.
- Staggered observation updates with bounded candidate work. Measure costs
  before selecting budgets. Retain fast cancellation handling.

Persist only appropriate durable state/observations after lifecycle review;
initially discard sensory memory across reload to avoid stale knowledge.
Never persist action handles. Current Stop must not silently resume tasks;
whether defense remains enabled after Stop needs an explicit policy decision.

Player rendering, Sarah's sight and remembered knowledge are three separate
contracts. A visible Sarah need not see the player; remembered targets need not
be currently visible; a hidden target must not receive fresh position updates.

## Minimal next work and experiments

First offline package: a perception policy module using injected engine queries,
fixture tests, and a native probe specification. Implement only after this
bounded package is selected; this report changes no production source.

Policy tests: front/behind, range boundary, different floor, wall, window/door
result distinctions, missing endpoints/intermediate coverage, failed query,
occluded target memory expiry and independence from player facing. Use actual
fixture outcomes rather than assuming engine light behavior.

Before deployment, finish tracing Lua exposure and NPC-relative lighting.
If light cannot be evaluated independently, label initial sight geometric-only
and do not claim darkness-aware vision. Native batch must compare Sarah facing
and player facing independently, walls/doors/windows, day/night, unloaded
coverage, Stop and reload. Rendering gets its own look-away/wall/floor tests.

Then audit one equip action and one transfer end-to-end; later one actual melee
attack and one wood barricade. Each experiment needs success/cancel/failure and
real inventory/health/object evidence. Keep the existing responsive-Follow
native regression pending and batch tests when the user resumes gameplay.

## Subsequent offline adapter investigation (2026-10-05)

See [NATIVE-PERCEPTION-ADAPTER-RESEARCH.md](NATIVE-PERCEPTION-ADAPTER-RESEARCH.md)
for fresh Lua registration, diagonal coverage dependencies and the unverified
getLightLevel(-1) shared-buffer path. It supersedes earlier exposure/coverage/light
candidate summaries without establishing native capability. Coverage helper is
proposed only; lighting remains unknown. No integration/deployment/live tests.
All 268 suite +11 runner +19 preflight self-tests passed; Codex owns checkout.
