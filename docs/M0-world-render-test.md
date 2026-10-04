# M0 ordinary world rendering: 2026-10-04

Installed Build 42.21.0, single player, exact isolated profile. External AI stays
on hold. This is a narrow SarahFoundation fix, not PZNS compatibility.

## Cause and bounded fix

The baseline NPC had a current square, square/object registration, active model,
model-manager registration, render enabled, opacity 1, no scene culling and a
visible square. It still did not appear in the ordinary world scene.

Local inspection of the installed FBO renderer explains the omission:
`FBORenderCell.renderMovingObject` skips objects whose exact class is `IsoPlayer`;
the single-player `renderPlayers` pass draws only local player slots. Sarah is
an NPC IsoPlayer outside those slots. No opacity override was justified.

A temporary `RenderOpaqueObjectsInWorld` hook drew the actual NPC model, visibly
separated from the red-haired local player in the same room. The foundation now
uses that event through its engine adapter. It leaves local player slots,
identity, model, opacity and culling alone. The callback is replaced on main
script reload and stops retrying after an exception until session reset.

The adapter draws only tagged, complete, alive NPCs present in the object list
and not pending removal. It requires single player, FBO rendering, view 0, an
onscreen NPC on the player's floor, a visible square and square lighting.
It draws the actual model and shadow. The legacy renderer gets no extra draw.

## Evidence

- [Baseline state](../evidence/world-render-baseline-summary.txt) and
  [scene](../evidence/world-render-baseline.png).
- [Experimental hook](../evidence/world-render-experimental-summary.txt) and
  [separated characters](../evidence/world-render-experimental.png).
- Production full-process restart restored the existing NPC checkpoint. Exactly
  one tagged Sarah, three clothing items, local player preserved and positive
  production draw counts at ticks 240/600. Experimental drawing was disabled;
  the diagnostic probe only observed and counted the adapter's successful draws.
  [Result](../evidence/world-render-production-restore-summary.txt),
  [ordinary scene](../evidence/world-render-production-restore.png).
- Fresh-spawn verification passed in `SarahWorldRenderFresh`, a separate copy
  of the no-mod control with SarahFoundation enabled and no Sarah checkpoints
  before launch. Exactly one newly constructed Sarah and player preserved at
  probe samples. Her initial square was hidden, opacity 0, and zero draws were
  recorded through tick 1800. The normal Sarah walking command brought her into
  the room, visibly wearing the fresh T-shirt/trousers/trainers. That happened
  after the last probe sample; the screenshot establishes later visibility,
  not a post-walk coordinate/count assertion. Exit saved slot a.
  [Spawn samples](../evidence/world-render-production-spawn-summary.txt),
  [visible fresh NPC](../evidence/world-render-production-spawn.png).
- 20 foundation checks and 9 rendering checks passed against actual Lua source
  with fake engine objects/events. These include callback replacement, failure
  suppression, local-player exclusion, registration, lighting, visibility,
  floor and multiplayer guards. They do not prove engine behavior beyond the
  live cases. [Foundation](../evidence/foundation-policy-tests.txt),
  [rendering](../evidence/foundation-render-tests.txt).

## Limits and recovery

Only the tested room and same-floor visible squares are established. One hidden
square was correctly skipped before walking into view. Broader hidden-room
behavior, stairs, multi-floor cutaways, travel/unloaded squares, long sessions,
controllers and multiplayer are not live-verified. The native world event
depends on a valid picked tile (or joypad camera tile); availability in every
cursor/window state is not established. The actual engine still controls model
alpha and depth. Do not claim complete occlusion correctness or broad release
readiness from these screenshots. Debug shadow disabling is not mirrored by
the experimental adapter.

Existing font/map/room metadata errors remain; prior all-mods-off control
reproduced them. No new Sarah render error was observed in the restore test.
Normal profile console timestamp stayed 04:03:05; installed files were read-only.

Game-closed backup group: `runtime/backups/world-render-before-20261004`:
original appearance world/selections, `Appearance-before-hook`,
`Appearance-before-production`, `Appearance-production-final`, `Fresh-spawn-final`. Preserve the
current case before restoring, close the game and copy a backup into a new
disposable isolated save directory. Raw logs, saves and inspected game classes
remain local and excluded from Git.

Final state: game closed (native window inventory), only foundation selected,
Continue selects `SarahWorldRenderFresh`. Production engine/main are deployed.
The world probe is disabled outside the mod; its experimentalDraw defaults to
false. Never enable experimental drawing together with the production hook.
