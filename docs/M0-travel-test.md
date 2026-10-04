# M0 travel policy: 2026-10-04

Bounded live checks PASSED: installed Build 42.21.0, single player, isolated SarahTravelCase.
External AI remains on hold. Original cases preserved under
`runtime/backups/travel-before-20261004`; this test is a separate copy.
Restore only game-closed after preserving current state into a new disposable
case. Installed files and normal saves/settings are not modified.

## Policy

Installed chunk cleanup removes moving objects from world and square. Keeping
an active NPC reference across that engine cleanup is unsafe. The foundation
now checks travel every 120 ticks. Beyond 32 tiles (Euclidean distance), or when
the player leaves Sarah's floor, it saves and unloads her. It restores the latest
checkpoint at its own saved location only when the player returns within 16
tiles on that floor and the square is loaded/free. It does not move Sarah to
the player or create a fresh NPC when restoration is unavailable.

The two distances avoid repeated boundary unload/restore. Pending additions are
accepted as resident; pending removals and missing current squares are not.
An already removed NPC cannot overwrite a good checkpoint. Save, cleanup or
restore failures stop unattended travel retries for that controller, retain
recovery state and log TRAVEL_BLOCKED. They require investigation/session restart;
there is no automatic destructive repair. Manual unload stays dormant for the
current session until an explicit spawn/restore request. Session restart still
restores living checkpoints when eligible.

This is preventive suspension, not offline NPC simulation. Abrupt movement may
outrun the polling interval: that path fails closed if the engine already removed
Sarah. A restart can use the last checkpoint, losing any unsaved later changes.
The thresholds are a narrow test policy, not a guarantee for every chunk setting,
vehicle speed, floor transition or teleport. Multiplayer remains unsupported.

## Checks

40 checks passed against actual Lua with fake engine objects/events: 27
foundation and 13 adapter. Seven new lifecycle cases cover delayed restoration,
manual dormancy, failed writes, removed references, duplicate refusal, corrupt
current-slot recovery with a deferred older fallback, and death.
Four adapter cases cover thresholds, floors, pending add/remove residency and
loaded/free saved-square eligibility.
These are policy checks, not live disk or streaming proof.

Outbound live stage passed: checkpoint slot b at 10770.4951,10271.4395,0;
automatic suspension at tick 360; zero tagged NPCs at tick 480; saved square
actually absent at tick 1440, zero NPCs and player instance preserved. Game
saved/closed and the away case was backed up as Away-before-restart.
[Outbound evidence](../evidence/travel-outbound-summary.txt).

Full-process away restart passed: zero Sarah objects, slot b retained, restoration
deferred. After the player returned, the normal foundation poll restored Sarah
at tick 720; tick 840 confirmed one NPC, persisted token, three worn items,
four inventory items, preserved local player and successful save to slot a.
Returned coordinates were 10770.4902,10271.4258,0, within the probe's 0.25-tile
tolerance of the saved location. She was also visible in the ordinary scene.
[Return evidence](../evidence/travel-return-summary.txt),
[scene](../evidence/travel-return-scene.png).

Temporary FoundationTravelProbe uses the game's debug
PLAYER teleport API to move within loaded terrain, then farther away, exercise
real map streaming, restart while away and return. Sarah is never teleported.
The disposable player temporarily gets god mode to protect the test while away;
the original setting was stored and restored through the game API on return.
This does not establish ordinary walking
or driving across the boundary.

Final game exit saved slot b. Native inventory confirmed game closure. The
returned case was preserved as Returned-final in the backup group; the temporary
driver is disabled outside the mod. Only foundation is enabled; Continue selects
SarahTravelCase. The test marker is done, so do not rerun the driver against this
completed case. Use a separate backed-up copy and adjust the driver world guard
when repeating the scenario. All older alive/dead/control cases remain intact.

No Sarah FAIL/TRAVEL_BLOCKED/RENDER_DISABLED appeared in either live run. Existing
font/map/invalid-room errors remain as reproduced by the no-mod control; these
runs were not entirely error-free. Normal profile console remained timestamped
04:03:05. Raw logs and inspected classes remain local and ignored. Broader floor,
cursor/cutaway, fast travel and live write/cleanup-failure behavior remain open.
