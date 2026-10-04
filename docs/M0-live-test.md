# M0 live test — minimal NPC foundation demonstrated

2026-10-04. Installed game confirmed as 42.21.0, revision 4a0e9546ec.

The replacement public method is `IsoPlayer.setNpc(boolean)`, and `isNpc()` is inherited. Name setters are `SurvivorDesc.setForename(String)` and `setSurname(String)`. Confirmed against actual installed classes by `NpcApiInventory`, with vanilla descriptor usage as corroboration.

The minimal probe uses these replacements independently of PZNS's jobs, combat and persistence. It does not establish full PZNS compatibility.

Profile: `G:\Codex\Project Sarah\runtime\isolated`.
Disposable world: `2026-10-04 04-21-54`, Rising preset, Rosewood.
Only mod: `SarahM0`. Versioned `42/mod.info` plus an empty `common` directory was discovered, enabled and loaded successfully in the game UI.

The game uses `-cachedir` pointing to the project profile. All test saves and autosaves belong there. No normal-profile save is being used. No restoration is necessary for normal saves because they are not copied or opened. Keep the disposable profile as evidence; never use its world for normal play.

AI layer: deferred. The probe contains no external AI or autonomous jobs.

## Executed results

| Check | Result and evidence |
|---|---|
| Version | PASS: 42.21.0 / 4a0e9546ec in normal profile files, isolated launch logs and UI |
| Mod discovery/load | PASS: versioned probe shown enabled in the game UI; `LOADED` in console |
| Human NPC spawn | PASS: `SPAWN npc=true name=Sarah`; local player instance preserved |
| Inventory | PASS: a Bandage added; the same object transferred to player and back, both `contains=true` |
| Movement | PASS: a single engine walking action moved from x=7978.5 to x=7976.541015625 (second run), and x=7976.50390625 (third run), y=11402.5 |
| Death | PASS in second run: body health set to zero; `dead=true` on later checks; visible corpse in the game |
| Removal | Calls completed without a probe exception and runtime reference cleared; no extended unloading/cleanup stress test |
| Checkpoint save | PASS in third run: 2,999-byte file exists, named token saved, file preserved after NPC removal |
| Full restart restoration | PASS in fourth run: `RESTORED name=Sarah inventory=1 dead=false`, `RESTORED_TOKEN Sarah M0 persistence token`, saved position restored, `npc=true`, local player preserved |

On the fourth run, the walking action reports `moved=false` because the restored NPC is already at the target player's square. Movement success is established separately by runs two and three; this no-op is not treated as another movement pass.

The restart test altered the initial descriptor name to `Unloaded` before loading and did not add an item on the restoration path. The restored `Sarah` name and custom item token therefore establish actual serialized restoration rather than a newly spawned lookalike. The source checkpoint was copied to evidence before restarting; SHA-256 `3bec6e3211b67cd2a00304d43e0167af8c103a253afc14b1d57b81c565b77736`.

## Save/death finding

In this exact build, `IsoPlayer.save(String)` writes an absolute-file checkpoint and records its filename. On NPC death the engine's `removeSaveFile()` deletes that associated file. This was observed in run two and corroborated by inspecting the installed class locally. Death and restart tests must use separate checkpoints/objects. The final probe sequence preserves the checkpoint, and the earlier death result remains in a separate log.

`setNpc(true)` attaches the engine's built-in NPC component. This is engine configuration needed for the foundation test; Sarah's external AI layer has not been implemented or started.

## Evidence and limitations

- `evidence/live-spawn-first.txt`: first spawn and repeated alive checks.
- `evidence/live-sequence-second.txt`: movement, inventory and death/removal.
- `evidence/live-checkpoint-third.txt`: movement and persistent checkpoint verification.
- `evidence/live-reload-fourth.txt` and `live-reload-summary.txt`: full restart restoration.
- `evidence/npc-api-inventory.txt`: installed API inventory.
- `evidence/installed-version.txt`: normal-profile version file.
- `prototype/SarahM0`: final independent probe source; `tools/launch-isolated.ps1` reopens its disposable profile.

The runs contained game texture/font, map and vanilla Lua dependency warnings/errors. Their locations indicate game asset/core paths, but a separate no-mod control run was not performed, so this is not a claim of an error-free installation or proven causal attribution. No Sarah probe failure or Lua exception was found in the completed sequences.

Alive NPC rendering/clothing, combat, off-screen unloading, crowded environments, duplicate prevention, robust production save recovery, multiplayer and extended play remain unverified. The observed runtime state and corpse support feasibility; they do not establish a finished companion.

The normal profile console retained its pre-test modification time, 2026-10-04 04:03:05. The project profile alone received the test saves. The game was closed after the fourth run.

## Decision

Proceed with a narrow engine-based Sarah foundation rather than relying on unmodified PZNS. Treat the single-player feasibility gate as demonstrated, keep the AI layer deferred, and harden rendering, lifecycle and persistence before a normal-play companion. The separate `candidates/PZNS_B42_M0` contains only mechanical API/layout replacements and remains unverified; it was not enabled in these tests.
