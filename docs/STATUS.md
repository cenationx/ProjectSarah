# Current project state

Updated: 2026-10-04 (Europe/Helsinki).
State: M0 feasibility demonstrated; foundation hardening remains in progress.
External AI: ON HOLD by explicit user instruction.
Active agent: none after this documentation checkpoint; next agent claims the
next task here before making changes. No background task or game is left running.

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

Evidence and boundaries: `M0-PZNS-compatibility.md`, `M0-live-test.md`,
`M0-foundation-live-test.md`, and `../evidence/foundation-policy-tests.txt`.

## Next task: live session transitions

1. Inspect current files and running processes. Read HANDOFF's disposable-save
   warning: Sarah is intentionally dead in the latest test world.
2. Preserve that death-test world and prepare an alive-NPC test using the
   pre-recovery backup, with the game closed. Retain both cases independently.
3. Verify quitting to the main menu and continuing the same world leaves exactly
   one Sarah, correct metadata, and the original player character.
4. Verify switching between two independently disposable worlds does not transfer
   Sarah's state or death flag. If unsupported or blocked, record the exact cause.
5. Test live Lua reload separately, including callback counts and incomplete
   cleanup references. Fix only problems the test exposes.
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
live/death/tombstone probe scripts moved out of the mod into
`runtime/disabled-probes`. Current disposable save retains Sarah's death flag.
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
