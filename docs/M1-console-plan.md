# M1 manual Sarah console

Planned 2026-10-04 from the user's proposal: an in-game panel opened by an unused,
configurable key, with basic NPC commands before more complex AI work.
Slice A now has a read-only implementation and bounded live command evidence;
keyboard acceptance is still open. See `M1-console-test.md`. External AI remains
on hold, and slices B-D are still proposals.

## First experience

Toggle a compact "Sarah Console" panel, type a command and press Enter. Show
brief help, the current Sarah state and a bounded scrolling result history.
Keep a visible Close button and a fallback entry through the Sarah context menu.
The key should toggle once per press; key repeat must not repeatedly open/close.
When the input has focus, typing must not also move the player or trigger other
game bindings. Closing restores normal game input. Opening the panel does not
silently pause or change game speed.

F9 is a provisional default: it is absent from the inspected installed default
keyBinding.lua and the isolated Lua/keysB42.ini is currently empty. That does not
prove F9 is free in every profile, mod or hardcoded handler. F8 was rejected after
finding its hardcoded WorldMapEditor handler. No KEY_F9 match was found in the
installed Lua scan; engine/runtime checks still remain. Register a named
rebindable action in the game's key settings, inspect runtime conflicts, and
verify actual key delivery in-game before calling the binding complete. If a
conflict exists, expose rebinding and leave the conflicting action untouched.
Do not change the user's normal key file. A mouse fallback does not establish
that the requested keyboard toggle works.

## Commands and staged delivery

| Slice | Command | Intended result |
|---|---|---|
| A: read-only | `help` | List supported commands and short examples |
| A: read-only | `status` | Sarah lifecycle/action state, player/NPC position when available, blocked/deferred reason |
| A: read-only | `inventory` | Small item/count summary, or a clear unavailable/dead/unloaded result |
| B: cancellation | `stop` | Cancel Sarah's current permitted action and queued request; repeated stop is harmless |
| C: bounded movement | `walk here` | Walk to a captured nearby player square on the same floor; report accepted, running, reached, cancelled or failed |
| D: optional developer lifecycle | `restore`, `save`, `unload` | Explicit guarded foundation operations with truthful results; add only after A-C pass |

No free-form dialogue, follow mode, combat, looting, spawning extra NPCs, revival,
teleportation, arbitrary coordinates or arbitrary Lua execution in the first
version. Do not interpret unknown text as an action. Quoted code, command chains
or model responses cannot bypass the command allowlist. Keep lifecycle operations
out of the initial input surface; existing debug menus still require the same
foundation safeguards when later consolidated.

## Shared action boundary

The console should be one caller of a small command/observation module. A future
model can call the same validated commands after explicit approval; it should
not have a separate path to game objects. Parsing, validation/dispatch and UI
are separate responsibilities. All engine work runs on the game thread.

Use stable request IDs and structured outcomes: accepted/running/completed,
cancelled/rejected/failed, plus a short reason. Accepted does not mean movement
completed. Distinguish parser errors, blocked lifecycle state and action failure.
Bound input length, history and inventory output. One movement action at a time;
reject extra movement while busy instead of building an unbounded queue. Stop
has priority. Invalidate pending work on world/session reset, unload, death or
controller replacement; do not carry commands into another save.

Observations should expose copied data, not mutable engine handles: lifecycle
state, alive/resident state, positions, equipment/inventory summary, action state
and a useful blocked reason. Represent unloaded/dead/deferred/blocked separately.
Read-only commands must work without spawning, restoring, saving or repairing
Sarah as a side effect.

Before walk, require exactly one complete living resident Sarah, healthy
controller/verifier, idle action state and local player preserved. Capture and
revalidate a loaded/free same-floor target, initially within 8 tiles of Sarah
(a proposed command limit, not a live-tested guarantee). Reject movement through
unsupported floors/travel boundaries; no automatic restore to satisfy a command.
If already at the target, report already there. Use the engine walking action,
bounded completion timeout and cancellation; never teleport on path failure.

Check both transaction status and returned operation value: lifecycle may return
`true, false` or `true, nil` for an operation that did not actually occur.
For restore, confirm a real NPC; for save/unload, confirm their actual result.
Do not claim success merely because a Lua call returned without an exception.

## Implementation order and acceptance

1. Inspect installed key/UI APIs and current runtime bindings, then add a small
   command schema/parser/observation module and slice A panel. Test invalid input,
   read-only side effects, unavailable states, focus and output bounds.
2. Back up a new disposable case game-closed. Live-test keyboard open/close,
   rebind, conflict handling, typing without player movement, mouse close,
   commands and menu/world transitions. If automated key input is unreliable,
   record it and obtain a narrow manual key check; do not substitute a claimed pass.
3. Add stop and its meaningful cancellation tests; then walk here with one action,
   completion tracking, invalid target, busy rejection, timeout and lifecycle reset.
   Verify visible native movement/cancellation in the isolated game.
4. Verify save/restart, one Sarah and player preservation after command sessions.
   Disable temporary probes, preserve evidence and checkpoint each completed slice.
5. Consider optional lifecycle commands only from demonstrated debugging needs.

All slices inherit [M0's envelope and stop rules](M0-supported-scope.md). The
initial target is the isolated single-player developer profile. M1 is in progress,
with slice A command tests only; it is not a release. M0 broad hardening stays open; the console work
does not imply acceptance of its remaining limits or authorization for M2 AI.
