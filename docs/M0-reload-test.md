# M0 live main-script reload: 2026-10-04

Only SarahFoundation enabled, installed Build 42.21.0, exact isolated profile.
Both alive/dead worlds were backed up with the game closed to
`runtime/backups/reload-before-20261004`. Tests used `SarahSessionAlive`; normal
saves and installed game files were not modified. Preserve the current target
before restoring a backup into another disposable case with the game closed.

The temporary `tools/FoundationReloadProbe.lua` reloads
`media/lua/client/SarahFoundation.lua` twice with a living restored Sarah.
It checks retained controller/NPC identity, one tagged NPC, original local player,
one controller tick per subsequent frame, and exactly one adapter save invocation
when the real Lua OnSave event is triggered. The adapter is restored after the
save-count measurement, including when event triggering fails.

## Probe correction

The initial probe falsely treated increasing fields read through old state-table
references as proof of old callbacks running. The installed Kahlua table
implementation forwards reads/writes through a reload replacement table. Old
table identities can differ while their field reads reach the current table.
Local inspection also found event registration suppression and filename/name
callback rerouting during reload. Decompiled source is kept locally and ignored.

The corrected acceptance check measures the current tick rate and actual save
invocations. Experimental callback changes were discarded; production foundation
and automated suite remain unchanged from the prior checkpoint. Earlier FAIL
logs are probe failures, not confirmed foundation defects.
Those rejected counter checks are preserved as
[first probe](../evidence/foundation-reload-first-summary.txt) and
[diagnostic probe](../evidence/foundation-reload-diagnostic-summary.txt); they
must not be used as evidence of duplicate callbacks.

## Boundary

The corrected run passed on the original foundation implementation: same
controller and NPC after two reloads, exactly 360 controller ticks over 360
subsequent frames, one tagged NPC, one adapter save call and player preserved.
See [final live evidence](../evidence/foundation-reload-summary.txt). The original
19 automated checks passed again. The game was closed and the driver disabled;
the normal profile console timestamp remained 04:03:05. Continue now selects the
alive copy; the dated death case was not loaded or changed during these runs.

This test concerns the main script only. It does not reload all required engine
and lifecycle modules, inject a real partial-removal failure, count every menu or
death callback, or verify same-process world switching. Those remain separate
checks. Existing map/engine load errors remain unresolved. No external AI.
