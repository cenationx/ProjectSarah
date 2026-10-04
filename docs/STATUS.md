# Current project state

Updated: 2026-10-04 (Europe/Helsinki).
State: M0 feasibility demonstrated; foundation hardening remains in progress.
External AI: ON HOLD by explicit user instruction.
Active agent: none after the main-script reload checkpoint. Antigravity resume prompt
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
  their behavior is covered with simulated events, not live world switching.
- Two independent disposable worlds passed the new live session probe across
  full process restarts: alive case restored exactly one Sarah and saved;
  death case retained its tombstone and zero live Sarahs. Player instance was
  preserved in both. See `M0-session-test.md` for the narrower test boundary.
- Live main-script reload passed twice: same controller/NPC, one tagged Sarah,
  one current tick per frame, one real OnSave adapter call and player preserved.
  Earlier counter-based probe FAILs were false positives caused by B42 forwarding
  old state tables. No production code change was needed. See `M0-reload-test.md`.

Evidence and boundaries: `M0-PZNS-compatibility.md`, `M0-live-test.md`,
`M0-foundation-live-test.md`, and `../evidence/foundation-policy-tests.txt`.

## Next task: live session transitions

1. Inspect files/processes and back up both worlds described in HANDOFF.
2. The alive copy already exists as `SarahSessionAlive`; the original dated
   world remains the independent death case. Do not overwrite either case.
3. Verify quitting to the main menu and continuing the same world leaves exactly
   one Sarah, correct metadata, and the original player character.
4. Verify switching between two independently disposable worlds does not transfer
   Sarah's state or death flag. If unsupported or blocked, record the exact cause.
5. Main-script reload is verified. Test broader module reload and retention of
   references from actual incomplete cleanup separately if needed; do not infer
   these from the normal alive-controller reload result.
6. Record observations, update milestones, run the automated suite if code
   changes, and commit/push the checkpoint.

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
live/death/tombstone/session/reload probe scripts moved out of the mod into
`runtime/disabled-probes`. Continue selects the alive `SarahSessionAlive` world;
`SarahSessionAlive` is a separate alive copy. Automated Escape input did not
open the pause menu, so same-process menu/world-switch checks remain open.
Main-script reload passed in the alive world; the dated world remains dead.
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
