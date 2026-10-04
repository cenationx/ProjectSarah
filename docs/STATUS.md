# Current project state

Updated: 2026-10-04 (Europe/Helsinki).
State: M0 feasibility demonstrated; foundation hardening remains in progress.
External AI: ON HOLD by explicit user instruction.
Active agent: none; menu/world transition checkpoint completed. Antigravity resume prompt
remains unsent; no second agent is authorized to edit this checkout concurrently.

## Last verified work

Latest gameplay/source checkpoint: `8b17b21` on `main`, pushed to
https://github.com/cenationx/ProjectSarah.
The handoff documentation is published in a subsequent commit; use Git history
and remote refs to identify the newest checkpoint instead of this historical ID.

- Unmodified PZNS is incompatible with the installed Build 42.21.0 APIs.
- Independent SarahM0 probe demonstrated NPC spawn, walking, inventory transfer,
  death/removal and full process restart restoration.
- SarahFoundation demonstrated spawn, duplicate prevention, three equipped
  clothing items, two-slot saves, unload/restore, full restart restoration,
  recovery from a deliberately truncated latest checkpoint, and saved death
  preventing resurrection after restart.
- 19 automated checks pass: 16 lifecycle cases plus 3 simulated callback cases.
- Latest fix promotes the good fallback slot before subsequent saves and refuses
  adoption of partial constructions. Session callbacks reset controller state;
  their behavior is covered by simulated events and the live transitions below.
- Two independent disposable worlds passed the new live session probe across
  full process restarts: alive case restored exactly one Sarah and saved;
  death case retained its tombstone and zero live Sarahs. Player instance was
  preserved in both. See `M0-session-test.md` for the narrower test boundary.
- Live main-script reload passed twice: same controller/NPC, one tagged Sarah,
  one current tick per frame, one real OnSave adapter call and player preserved.
  Earlier counter-based probe FAILs were false positives caused by B42 forwarding
  old state tables. No production code change was needed. See `M0-reload-test.md`.
- Live menu return, same-world Continue and alive/dead/alive switching passed
  within one unchanged Java process. Each menu reset left controller nil;
  alive cases had exactly one Sarah, death case zero, and player preserved.
  Temporary mouse entrypoint used the real menu handler; physical Escape input
  remains unverified. See `M0-menu-transition-test.md` and its sanitized evidence.

Evidence and boundaries: `M0-PZNS-compatibility.md`, `M0-live-test.md`,
`M0-foundation-live-test.md`, and `../evidence/foundation-policy-tests.txt`.

## Next task: appearance and fresh-world control

1. Inspect Git/runtime state and, with game closed, back up both existing cases
   and isolated selections. Preserve the independent alive and death worlds.
2. Create a fresh disposable world in the isolated profile without copying old
   map metadata; record its creation and restoration procedure.
3. Compare map-load errors with the existing worlds. Use a foundation-disabled
   fresh control if needed to distinguish engine/map issues from Sarah behavior.
4. In a backed-up foundation-enabled case, bring Sarah into a clear view and
   inspect clothing/appearance, recording visual evidence and engine counts.
5. Record findings and remaining limits, disable temporary probes, close the
   game, update shared state, and commit/push the checkpoint. Keep AI on hold.

## Open issues

- Visual NPC clothing/appearance still lacks a clear live inspection.
- Existing test world logs duplicate room/invalid map metadata errors on load;
  origin not diagnosed. Do not call the runs entirely error-free.
- Disk-write failures have simulated policy coverage only.
- Offscreen unloading/travel recovery, combat, longer sessions, multiplayer and
  full PZNS compatibility remain unverified.
- Foundation is deliberately restricted to the exact isolated cache path.

## Local runtime state at handoff

Game closed. Only SarahFoundation selected in the isolated profile. Temporary
live/death/tombstone/session/reload/menu probe scripts moved out of the mod into
`runtime/disabled-probes`. Continue selects the alive `SarahSessionAlive` world;
`SarahSessionAlive` is a separate alive copy. Menu/world switching passed using
the temporary mouse menu entrypoint; automated Escape input remains unresolved.
Main-script reload passed in the alive world; the dated world remains dead.
Latest live-test backup: `runtime/backups/menu-before-20261004`, both worlds
plus isolated key file and latest-save selection. Restore only game-closed,
after preserving the current case, into a new disposable directory.
Runtime files and backups exist locally but are excluded from Git.
No known tracked code changes are unfinished. Check Git status before work.

## Interrupted-session note template

Replace this section when needed; remove stale entries after completing them.

- Work item / owner / date:
- State: IN PROGRESS / BLOCKED / VERIFIED
- Modified files and local-only outputs:
- Checks passed, failed or not yet run:
- Running processes and safe stop method:
- Backup and restoration plan:
- Exact next action:
- Latest local commit / remote pushed or pending:
