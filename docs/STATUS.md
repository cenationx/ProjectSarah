# Current project state

Updated: 2026-10-04 (Europe/Helsinki).
State: M0 feasibility demonstrated; foundation hardening remains in progress.
External AI: ON HOLD by explicit user instruction.
Active agent: none; rendering checkpoint completed by Codex. Antigravity resume prompt
remains unsent; no second agent is authorized to edit this checkout concurrently.

## Last verified work

Previous published checkpoint: `ca76815` on `main`, pushed to
https://github.com/cenationx/ProjectSarah.
The accompanying checkpoint adds the world-render fix and verification below;
use Git history and remote refs to identify its commit rather than this parent ID.

- Unmodified PZNS is incompatible with the installed Build 42.21.0 APIs.
- Independent SarahM0 probe demonstrated NPC spawn, walking, inventory transfer,
  death/removal and full process restart restoration.
- SarahFoundation demonstrated spawn, duplicate prevention, three equipped
  clothing items, two-slot saves, unload/restore, full restart restoration,
  recovery from a deliberately truncated latest checkpoint, and saved death
  preventing resurrection after restart.
- 29 automated checks pass: 20 foundation cases and 9 rendering cases.
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
- Subsequent world-render diagnosis found the B42 FBO player-pass omission.
  Foundation now draws its actual visible same-floor NPC through the world
  event. Ordinary scene screenshots passed for restored and newly spawned
  Sarah; local player preserved in probe samples and exactly one tagged NPC.
  Fresh spawn's hidden square produced zero draws; walking into view showed her.
  See `M0-world-render-test.md` for the tested boundaries and recovery steps.

Evidence and boundaries: `M0-PZNS-compatibility.md`, `M0-live-test.md`,
`M0-foundation-live-test.md`, and `../evidence/foundation-policy-tests.txt`.

## Next task: offscreen and unloaded-square recovery

1. Inspect Git/runtime state and back up the selected fresh rendering case and selections
   with game closed. Preserve all independent alive/dead/no-mod cases.
2. Inspect how the engine removes/culls NPCs as squares unload. Specify whether
   to checkpoint/unload before travel or safely defer restoration at the saved
   square. Preserve identity and never create a fresh replacement or teleport.
3. Exercise the chosen policy with simulated faults, then a bounded disposable
   live case: travel away, return, save/reload, exactly one Sarah and local player
   preserved. Record unloaded-square, object-list and controller observations.
4. Check same-floor visibility and occlusion as travel permits; broader floor
   cutaways and world-event cursor availability remain unverified limitations.
5. Close game, disable temporary probes, update docs and commit/push. Keep AI on hold.

## Open issues

- Ordinary same-floor world rendering passed in the tested room. Broad cutaway,
  multi-floor and cursor-state correctness remain unverified; adapter scope is
  conservative and deliberately skips unseen/other-floor NPCs.
- Duplicate room/invalid map metadata errors reproduce with all mods disabled;
  origin not diagnosed. Do not call the runs entirely error-free.
- Disk-write failures have simulated policy coverage only.
- Offscreen unloading/travel recovery, combat, longer sessions, multiplayer and
  full PZNS compatibility remain unverified.
- Foundation is deliberately restricted to the exact isolated cache path.

## Local runtime state at handoff

Game closed; native window inventory confirmed no Project Zomboid window.
Only SarahFoundation selected. Continue selects `SarahWorldRenderFresh`, a
foundation-enabled separate copy of mod-free `2026-10-04_06-16-14`. Original control
has an empty world mod list; older alive/dead cases remain preserved.
All temporary drivers, including world rendering, are outside the mod in
`runtime/disabled-probes`. Production Engine/main deployed to isolated mod.
Fresh render case saved slot a; appearance restore test saved slot a.
`SarahSessionAlive` is a separate alive copy. Menu/world switching passed using
the temporary mouse menu entrypoint; automated Escape input remains unresolved.
Main-script reload passed in the alive world; the dated world remains dead.
Latest backup group: `runtime/backups/world-render-before-20261004`: appearance
world/selections, Appearance-before-hook, Appearance-before-production,
Appearance-production-final and Fresh-spawn-final. Older appearance and
alive/dead backups remain preserved. Restore only game-closed,
after preserving the current case, into a new disposable directory.
Runtime files and backups exist locally but are excluded from Git.
Production world-render change and evidence are included in this checkpoint.
No unfinished work remains for this bounded task; M0 hardening is still open.
Check Git status and fresh native window inventory before resuming UI work.

## Interrupted-session note template

Replace this section when needed; remove stale entries after completing them.

No interrupted work at this checkpoint.

- Work item / owner / date:
- State: IN PROGRESS / BLOCKED / VERIFIED
- Modified files and local-only outputs:
- Checks passed, failed or not yet run:
- Running processes and safe stop method:
- Backup and restoration plan:
- Exact next action:
- Latest local commit / remote pushed or pending:
