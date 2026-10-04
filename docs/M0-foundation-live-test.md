# Hardened NPC foundation live test

Date: 2026-10-04. Installed game: 42.21.0. Single-player modded test only.
Profile: `G:\Codex\Project Sarah\runtime\isolated`.
Disposable world: `Rising/2026-10-04_04-21-54`.
Only SarahFoundation enabled; SarahM0 disabled. No external AI.

Before deployment, the whole disposable world and profile mod selection were
copied to `runtime/backups/foundation-before-20261004-045750`. Earlier test data
can be restored from that backup with the game closed. Normal saves were never
used. The normal profile console timestamp remained 04:03:05 throughout.

The first launch exposed a Build 42 API incompatibility: IsoCell object/add lists
are Java sets, so indexed `get(i)` fails. The adapter now uses their iterators.
The two subsequent runs completed without Sarah Lua failures.

## Observed results

- Spawn: NPC flag true, name Sarah, three equipped clothing items, local player
  instance preserved.
- Repeated ensure: existing NPC retained, exactly one tagged Sarah in the cell.
- Checkpoints: two alternating files written, both present at 3413 bytes after
  the first successful run. Metadata retains current and previous records.
- Unload and restore: save succeeds before removal; restoration on a later tick
  returns exactly one tagged NPC with three equipped items.
- Full process restart: automatically restored checkpoint `a` at tick 120,
  before test writes. Name Sarah and equipped items preserved. This confirms
  recovery metadata persisted through the game's GlobalModData save/load.
- Shutdown: save callback logged a checkpoint write before Saving GlobalModData.
- Automated policy checks: all 15 still pass after the adapter correction.

Evidence: [first successful run](../evidence/foundation-live-summary.txt),
[full restart](../evidence/foundation-restart-summary.txt). The reproducible
test driver is `tools/FoundationLiveProbe.lua`; deploy it only to the isolated
candidate's client directory. It performs save/unload and restore automatically
at ticks 240 and 360. It is not included in the mod's production source.

## Limits and remaining gates

The engine emitted duplicate room and invalid map metadata errors during world
loading. Their relationship to this existing disposable world's state has not
been diagnosed; the session is not classified as error-free.

Equipped clothing is verified by the engine count, not a clear visual inspection.
Live corrupted-file recovery, disk-write failures, death tombstone persistence,
Lua reload, returning to the menu and switching worlds, offscreen unloading,
combat and multiplayer remain unverified. Failure scenarios have simulated
policy tests only. The candidate is experimental and restricted to the isolated
profile. This does not establish full PZNS compatibility. Game closed afterward.
