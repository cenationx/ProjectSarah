# M0 appearance and fresh control: 2026-10-04

IN PROGRESS. Installed Build 42.21.0, exact isolated profile. No AI work.
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
Raw logs remain local under runtime. A full-restart reload of this no-mod world
is pending; it will check whether saved invalid-room metadata errors reproduce.
The restarted game (PID 41052) was minimized at its main menu. The UI helper
reported `user input was detected in this window; call get_window_state before
continuing`; refreshing reported `window is minimized`, and the attempted
activation was rejected with the user-input message again. UI actions stopped;
a question about bringing the game forward remains pending. Reobserve before
resuming and do not reuse old coordinates or window snapshots.

## Appearance

`tools/FoundationAppearanceProbe.lua` is prepared but not deployed/tested yet.
It logs the actual NPC identity and worn items, verifies one NPC/player identity,
then binds the installed game's ISUI3DModel viewer directly to that same NPC.
It does not assign a separate display outfit or change NPC appearance.
Visual inspection will remain distinct from engine worn-item counts and world
rendering. No production source change has been made.
The prepared probe passes Lua syntax compilation only; no live pass is claimed.
