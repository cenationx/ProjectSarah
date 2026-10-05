# Sarah: small native survivor core

Date: 2026-10-05. Status: researched initial plan, not implemented or natively verified.
Owner: Codex. Live testing currently deferred by user.

## User requirements and boundaries

Sarah must eventually defend herself, loot a house on request, build something
specified by the player, trade, and equip useful weapons/protective clothing.
Independent sight is a core requirement, not optional future polish. Her
decisions must depend on her own observations rather than the player's visible
tiles or omniscient world queries. Rendering and perception are separate:
nearby Sarah should not disappear solely because the player faces away; no
highlight was requested. Preserve walls, floors and loaded-world limits.

External/model AI belongs near the end, after useful native mechanics work.
No model, service or dialogue integration is authorized. This task authorizes
research/planning, not implementing all proposed behaviors at once. Existing
M1 and responsive-Follow native gates remain open.

## Reference findings

These are inspected primary sources, accessed 2026-10-05. CDDA master and online
documentation are moving references; pin a revision before detailed code study.
Study design patterns; do not copy another game's implementation wholesale.

| Reference | Evidence and useful pattern | Transfer limits |
|---|---|---|
| Cataclysm: Dark Days Ahead | NPC movement source separates danger assessment, action selection and execution. Pickup can be cancelled when conditions change; weapon evaluation selects a preferred weapon. | Turn-based C++, different inventory/combat rules. Its broad feature set is not our minimum scope. |
| CDDA NPC documentation | Documents follower rules, item transfer with capacity refusal, weapon acceptance and trade. | Public gameplay/data contracts do not prove complete autonomy or bug-free execution. |
| CDDA map generation documentation | Describes faction work/retreat/investigation zones. | Borrow bounded work areas and retreat destinations, not its whole zone system. |
| Project Zomboid developer NPC notes (2022) | Describes local characters and separate distant narrative/meta activity. | Historical work-in-progress design; not shipped API evidence. Defer distant task execution. |
| Project Zomboid API documentation | Lists character CanSee overloads and facing APIs. | Signatures do not prove independent vision works for our Build 42.21 IsoPlayer NPC. Inspect installed implementation and test it. |

Sources:
- [CDDA npcmove.cpp](https://github.com/CleverRaven/Cataclysm-DDA/blob/master/src/npcmove.cpp): inspect assess_danger, move/action dispatch, pick_up_item and wield_better_weapon.
- [CDDA NPC contracts](https://docs.cataclysmdda.org/JSON/NPCs.html).
- [CDDA faction zones](https://docs.cataclysmdda.org/JSON/MAPGEN.html).
- [Zomboid Lone Survivor developer notes](https://projectzomboid.com/blog/news/2022/04/lone-survivor/).
- [Zomboid IsoGameCharacter API](https://projectzomboid.com/modding/zombie/characters/IsoGameCharacter.html).

Kenshi and State of Decay remain possible behavior comparisons. This first pass
did not establish their internal algorithms from sufficient primary technical
material, so they are not architecture evidence here. CDDA and Zomboid are the
initial technical references.

## Small architecture proposal

Reuse current lifecycle, engine adapter, dispatcher, cancellation and history.
Add only the pieces required by each accepted slice:

1. **Perception:** bounded local candidate scan followed by Sarah-relative
   facing/range and verified line-of-sight checks. World enumeration supplies
   candidates, not knowledge. Sarah's perception never calls player visibility
   as its authority. Unknown/failed queries remain unknown.
2. **Short observation memory:** last seen position and observation time;
   lose live tracking when occluded. Limit entry count/lifetime. Hearing, when
   available, provides an uncertain location cue, not exact hidden identity.
3. **Decision policy:** explicit ordered priorities, not a general planner:
   lifecycle invalidation/Stop, immediate danger response, urgent supported
   needs, current player task, optional equipment improvement, idle/follow.
4. **Task executor:** one task consists of a few validated actions. Each action
   has start conditions, completion evidence, cancellation and a bounded retry
   policy. Recheck relevant world/item conditions immediately before mutation.

Manual Stop cancels the requested task and must not silently restart it. Future
autonomous self-defense needs a separately defined enabled/disabled policy;
do not reinterpret current Stop semantics during implementation. Threat handling
must interrupt work safely, report the reason, and initially require a new order
to resume. No invisible looting, free building materials or artificial damage.

Performance: restrict scans to loaded nearby candidates, cap work per update,
cache bounded observations and use staggered sensory updates. Avoid scanning
every container or entity each frame. Choose budgets from measurements; no
unverified milliseconds or zero-cost claims.

## Delivery sequence and acceptance

Each row is a separate slice with offline checks plus a batched isolated native
check. A plan checkbox is not feature acceptance. Do not build a general-purpose
behavior framework before these small slices work.

| Slice | Small meaningful outcome | Native acceptance needed |
|---|---|---|
| 0. Close foundation gaps | Responsive Follow and rendering visibility requirements resolved | Turns, Stop, stall behavior, reload, look away near Sarah; wall/floor occlusion retained |
| 1. Own sight | Sarah reports whether she sees one known target independently of player facing | Front/behind, player looking elsewhere, opaque wall, door opening/closing, darkness, unloaded square; failed queries |
| 2. Carry and equip | Give/take one actual item; wield one supported melee weapon; wear one supported garment | Inventory counts conserved, carry limit, visible held/worn item, persistence and no duplication |
| 3. Self-defense | Detect one zombie, face it, execute supported melee defense or retreat | Actual hit/health/animation/cooldown, obstacle and lost-sight behavior, interrupted task cancellation; expand only after one-threat case |
| 4. Loot one container | On request, approach a known reachable container and take allowed items up to capacity | Real transfer, closed/blocked/removed container, changed items, full inventory, threat interruption and Stop |
| 5. Loot one selected room/house | Visit a bounded list of discovered containers, return to a chosen drop point | No knowledge of hidden contents; inaccessible rooms skipped with reason, no repeated failed targets, item conservation |
| 6. Improve equipment | Choose among a small supported set of owned weapons/garments | Condition, slot compatibility and protection considered; no endless swapping or arbitrary “best item” claim |
| 7. Exchange/trade | Player-Sarah item exchange first, then a small explicit barter rule if desired | Both inventories validated, cancellation causes no loss, no duplicates or half-completed exchange |
| 8. One construction request | Perform one verified native recipe/action at a player-selected location | Tool/material/skill checks, actual timed action and resulting object, consumes real resources exactly once, interrupted placement handled |

Suggested first build target: barricade one selected window if Build 42.21 NPC
timed-action support is verified; otherwise select one simpler supported recipe.
This is a proposal, not a promise that the NPC can use the player build system.
General house building, vehicles, firearms, group tactics, autonomous economy,
large needs simulation and distant offline work are later expansions.

Initial equipment improvement should use an allowlist with explainable scores:
usable condition and supported weapon behavior; compatible clothing coverage and
protection with relevant drawbacks. Do not treat every higher protection number
as an unconditional upgrade. Start manual equipment before automatic selection.

## Research questions before implementation

- Does installed CanSee depend on a local-player sight slot/cache? Does it handle
  NPC facing, light and occlusion correctly? If not, identify supported line of
  sight plus Sarah-relative cone/range checks. A cone alone cannot see walls.
- What supported sounds can Sarah observe without reusing player-only hearing?
- Which native melee actions and attack state transitions work for setNpc(true),
  and do they apply actual collision/hit checks rather than scripted damage?
- Which item-transfer/equip timed actions accept this NPC, and how are item
  identity, weight and save/reload handled?
- Which one building action works with NPC tools/materials and cancellation?
- What does “trade” mean here: exchanging with Sarah or autonomous negotiation
  with other survivors? Default first scope is player-Sarah exchange; no other
  survivor population is assumed.

Record installed-code/API inspection separately from live evidence. Initial
local inspection found Engine.lua currently gates rendering through
square:isCanSee(playerIndex); wearing clothing is already used during creation.
These facts do not establish general perception, combat or equipment support.

## First follow-up work package

Offline research only: inspect installed B42.21 vision/render APIs and relevant
Lua paths; produce a minimal perception adapter contract and test matrix, with
explicit engine uncertainties. Do not deploy or implement combat/looting yet.
Keep rendering independence and Sarah's own vision as two separate tasks.

Then implement the smallest approved sight slice with fixtures, followed by
isolated native checks. Reuse the existing single-writer Gemini/Codex workflow:
Gemini can take bounded offline work; Codex alone deploys and launches tests.
