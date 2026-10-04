# Current project state

Updated: 2026-10-04 (Europe/Helsinki).
State: M0 feasibility demonstrated; foundation hardening remains in progress.
External AI: ON HOLD by explicit user instruction.
Active agent: none; appearance/control checkpoint completed. Antigravity resume prompt
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
- A newly generated no-mod Rising control reproduced duplicate RoomDef metadata
  during generation and the same four invalid room IDs on full-restart reload.
  Sarah is not required to trigger these errors on this installation; root cause
  remains unknown. Both no-mod and foundation-enabled copies reached gameplay.
- Actual Sarah model viewer visually confirmed T-shirt, trousers and trainers
  before/after full restart, one NPC and player preserved. World opacity=1,
  target opacity=1 and culling=false at ticks 600/1800, but ordinary world-scene
  visibility was not confirmed. See `M0-appearance-control-test.md`.

Evidence and boundaries: `M0-PZNS-compatibility.md`, `M0-live-test.md`,
`M0-foundation-live-test.md`, and `../evidence/foundation-policy-tests.txt`.

## Next task: ordinary world-scene visibility

1. Inspect Git/runtime state and back up `SarahAppearanceFresh` and selections
   with game closed. Preserve all independent alive/dead/no-mod cases.
2. Use a temporary narrow probe to inspect actual NPC square/object registration,
   world model, player-view visibility and rendering flags. Compare with the
   local player and installed engine paths. No forced opacity/visibility fix
   without a demonstrated cause; do not conflate model viewer and scene output.
3. Arrange separated player/NPC positions in unobstructed space and directly
   observe Sarah in the world scene. Use screenshots plus matching coordinates.
4. If a production fix is justified, make the smallest adapter change and verify
   live spawn/restore/player preservation plus automated lifecycle checks.
5. Record limitations, close game, disable probes and commit/push. Keep AI on hold.

## Open issues

- Actual-NPC clothing/model viewer passed; ordinary world-scene visibility still
  needs direct verification and diagnosis.
- Duplicate room/invalid map metadata errors reproduce with all mods disabled;
  origin not diagnosed. Do not call the runs entirely error-free.
- Disk-write failures have simulated policy coverage only.
- Offscreen unloading/travel recovery, combat, longer sessions, multiplayer and
  full PZNS compatibility remain unverified.
- Foundation is deliberately restricted to the exact isolated cache path.

## Local runtime state at handoff

Game closed; native window inventory confirmed no Project Zomboid window.
Only SarahFoundation selected. Continue selects `SarahAppearanceFresh`, the
foundation-enabled copy of fresh mod-free `2026-10-04_06-16-14`. Original control
has an empty world mod list; older alive/dead cases remain preserved.
All temporary live/death/tombstone/session/reload/menu/appearance drivers are
outside the mod in `runtime/disabled-probes`. Appearance case final state saved
slot b and backed up as `appearance-before-20261004/Appearance-final`.
`SarahSessionAlive` is a separate alive copy. Menu/world switching passed using
the temporary mouse menu entrypoint; automated Escape input remains unresolved.
Main-script reload passed in the alive world; the dated world remains dead.
Latest backup group: `runtime/backups/appearance-before-20261004`: both older
worlds, original selections, fresh control before/after reload, appearance case
before restart and final state. Restore only game-closed,
after preserving the current case, into a new disposable directory.
Runtime files and backups exist locally but are excluded from Git.
No production code changes or unfinished tracked edits. Check Git status and
fresh native window inventory before resuming UI work.

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
