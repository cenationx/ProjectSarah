# M0 appearance and fresh control: 2026-10-04

Completed checks with a documented world-visibility limitation. Installed Build
42.21.0, exact isolated profile. No AI work.
Original alive/dead worlds and isolated selections backed up game-closed to
`runtime/backups/appearance-before-20261004`. Restore only game-closed after
preserving the current state, into a new disposable case. Normal profile and
installed files were not modified.

## Fresh control

Both Sarah mods were visibly unchecked in the isolated mod UI and the selection
was applied. The game was fully closed and relaunched before creating a fresh
Rising world through Solo, Muldraugh, custom occupation with no traits and the
default character. Save name: `2026-10-04_06-16-14`. Keyboard name entry did not
change the generated name; the observed name above is authoritative.

No old save or map metadata was copied into this new world. Its `mods.txt` and
the profile default both have empty mods/maps sections. Its first-run log has
no Sarah log entries. The player entered gameplay, then Alt+F4 saved/closed it.
Window inventory confirmed closure. The newly saved world was separately
backed up as `FreshControl-before-reload` beneath the backup directory above.

Initial generation produced the same duplicate RoomDef.metaID error at
10707,9484,0 as the earlier Sarah-enabled cases. This demonstrates Sarah is not
required to reproduce that error on this installation. It does not establish
the root cause or prove every engine/map warning harmless. Font texture and
map-zone errors/warnings also occurred with all mods disabled.

Evidence: [first control run](../evidence/fresh-control-first-summary.txt).
Raw logs remain local under runtime. The full-restart reload subsequently
reproduced one duplicate RoomDef error and the same four invalid room IDs
(231, 327914, 327911, 655594), in cell 25,33 while reading map_meta.bin.
There were zero Sarah log entries; both profile/world mod lists remained empty.
The restored control player reached gameplay. Sarah is not required to trigger
either metadata error on this installation; their root cause is still unknown.
Evidence: [no-mod reload](../evidence/fresh-control-reload-summary.txt).
The restarted game (PID 41052) was minimized at its main menu. The UI helper
reported `user input was detected in this window; call get_window_state before
continuing`; refreshing reported `window is minimized`, and the attempted
activation was rejected with the user-input message again. UI actions stopped;
The user then authorized resuming; a fresh observation/activation succeeded and
the reload check above completed. No old coordinates were reused after recovery.

## Appearance

`SarahAppearanceFresh` is a separate copy of the fresh control after its mod-free
reload, with only SarahFoundation enabled in its own mods.txt. The original
fresh control stays no-mod. `tools/FoundationAppearanceProbe.lua` was deployed
temporarily before launching this case.
It logs the actual NPC identity and worn items, verifies one NPC/player identity,
then binds the installed game's ISUI3DModel viewer directly to that same NPC.
It does not assign a separate display outfit or change NPC appearance.
Visual inspection will remain distinct from engine worn-item counts and world
rendering. No production source change has been made.
The prepared probe passed Lua syntax compilation, then ran in the live game.

- Fresh NPC: exactly one tagged living Sarah; local player preserved. Viewer
  bound directly to that NPC, not a separate outfit/mannequin. Engine worn list:
  Base.Tshirt_WhiteTINT, Base.Trousers_DefaultTEXTURE_TINT, Base.Shoes_TrainerTINT.
  Visual inspection clearly showed teal T-shirt, dark trousers and pink trainers.
- Existing Sarah walk command was selected through the real context menu.
  The world scene still did not provide a clear view of Sarah. No walk success
  assertion was added in this run; the prior walking test remains separate.
- Game closed/saved slot a; appearance case backed up game-closed to
  `Appearance-before-restart` beneath the same backup directory. Full process
  restart restored slot a and exactly one Sarah with the same clothing/model.
  The viewer was rotated to inspect another angle. Player was also moved through
  the vanilla Walk to control to help separate world positions.
- At ticks 600 and 1800, NPC opacity and target opacity were both 1,
  scene-culling false, and local player identity preserved. These engine values
  do not prove world rendering: ordinary scene visibility remains unconfirmed.
  Investigate scene rendering, object registration and visibility separately;
  do not infer the root cause from these counters or force opacity as a fix.

Evidence: [initial log](../evidence/appearance-first-summary.txt),
[initial visual](../evidence/appearance-model-first.png),
[restored log](../evidence/appearance-restored-summary.txt),
[restored visual](../evidence/appearance-model-restored.png).

Clothing/model appearance PASS in the actual-NPC viewer before/after restart.
Ordinary world-scene visibility remains an open check. No production code was
changed; the existing automated foundation suite covers unchanged source.
Local class inspection inputs are ignored explicitly to prevent publishing
game bytecode. Sanitized findings/screenshots are the published evidence.

Final state: game closed and absence verified through native window inventory;
slot b saved, appearance case preserved as `Appearance-final` in the backup
group. Appearance driver moved to `runtime/disabled-probes`; no temporary
driver remains active. Isolated default is restored to only SarahFoundation,
Continue selects `SarahAppearanceFresh`, original control remains no-mod.
Normal console timestamp remained unchanged at 04:03:05 throughout these tests.
