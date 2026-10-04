# Current project state

Updated: 2026-10-04 (Europe/Helsinki).
State: M0 feasibility demonstrated; foundation hardening remains in progress.
External AI: ON HOLD by explicit user instruction.
Active agent: none; bounded longer session completed. Antigravity resume prompt
remains unsent; no second agent is authorized to edit this checkout concurrently.

## Last verified work

Previous published checkpoint: `1d42d78` on `main`, pushed to
https://github.com/cenationx/ProjectSarah.
The accompanying checkpoint adds repeated-session evidence below;
use Git history and remote refs to identify its commit rather than this parent ID.

- Unmodified PZNS is incompatible with the installed Build 42.21.0 APIs.
- Independent SarahM0 probe demonstrated NPC spawn, walking, inventory transfer,
  death/removal and full process restart restoration.
- SarahFoundation demonstrated spawn, duplicate prevention, three equipped
  clothing items, two-slot saves, unload/restore, full restart restoration,
  recovery from a deliberately truncated latest checkpoint, and saved death
  preventing resurrection after restart.
- 48 automated checks pass: 27 foundation, 13 engine adapter and 8 checkpoint readback cases.
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
- Preventive travel suspension now saves/unloads beyond 32 tiles or another
  floor; return within 16 tiles on the saved floor restores at the saved square
  when loaded/free. Controlled player travel passed real square unloading,
  full-process away restart and return: one Sarah, persisted token, clothes and
  inventory, preserved player, save and ordinary visibility. NPC was not
  teleported. Manual unload remains dormant in-session; failures retain state
  and block unattended retries. See `M0-travel-test.md` for remaining limits.
- Real locked existing-file write exposed swallowed native I/O errors and false
  save success. Adapter now reads a fresh UUID back before accepting a checkpoint.
  Fixed fault/retry retained the NPC and metadata on failure, unchanged old-file
  hash, and new contents on successful retry. Full restart restored one Sarah
  and exit saved successfully with the cleanup-confirmation guard. Temporary
  verifier cleanup failure is pinned/blocked and covered by simulated tests.
  See `M0-write-failure-test.md`; disk-full/partial writes remain unverified.
- Six-minute idle-room session passed 12 unload/restores and 25 verified saves.
  All 25 save verifiers released the adapter reference and cleared world lists
  after subsequent ticks; removed Sarah objects also cleared those lists. One
  Sarah, current cycle contents, clothes and player instance were retained.
  Full restart loaded cycle 12 and exit saved successfully. No production changes
  needed. This does not prove JVM/native resource reclamation or hours of play.
  See `M0-long-session-test.md`.

Evidence and boundaries: `M0-PZNS-compatibility.md`, `M0-live-test.md`,
`M0-foundation-live-test.md`, and `../evidence/foundation-policy-tests.txt`.

## Next task: broader module reload and incomplete-cleanup references

1. Inspect Git/runtime state; with game closed, back up and create a separate
   disposable copy of the completed long-session case plus selections.
2. Inspect module reload behavior; reload Engine/Lifecycle/main through actual
   game Lua reload and verify controller/NPC retention, one tick and save callback.
3. Use a bounded reversible adapter cleanup fault around a real test NPC to
   verify its retained reference survives reload and prevents replacement.
   Label injected adapter failures separately from native engine failures.
4. Preserve failures before fixing any demonstrated gap; then retest/restart.
5. Close game, disable temporary probes, update docs and commit/push. Keep AI on hold.

## Open issues

- Ordinary same-floor world rendering passed in the tested room. Broad cutaway,
  multi-floor and cursor-state correctness remain unverified; adapter scope is
  conservative and deliberately skips unseen/other-floor NPCs.
- Duplicate room/invalid map metadata errors reproduce with all mods disabled;
  origin not diagnosed. Do not call the runs entirely error-free.
- Locked existing-file failure/retry passed live; disk-full, arbitrary partial
  writes and process crashes remain unverified. Readback is not atomic replacement
  or a full-file checksum. Exceptional verifier cleanup has simulated coverage.
- Bounded streamed travel recovery passed; ordinary walking/driving boundaries,
  abrupt movement, floor transitions, combat, hours-long sessions, multiplayer and
  full PZNS compatibility remain unverified.
- Foundation is deliberately restricted to the exact isolated cache path.

## Local runtime state at handoff

Game closed; native window inventory confirmed no Project Zomboid window.
Only SarahFoundation selected. Continue selects `SarahLongSessionCase`, a separate
copy of SarahWriteFailureRetest; original retest/travel/fresh/control cases remain intact. Original control
has an empty world mod list; older alive/dead cases remain preserved.
All temporary drivers, including long-session, travel and write failure, are outside the mod in
`runtime/disabled-probes`. Production Engine/Lifecycle/main deployed to isolated mod.
Long-session case saved slot a on final exit; LongSessionDone=true, cycle=12.
Original retest saved b; write probe marker done. All exclusive file
handles released; local .txt release signal remains. Do not rerun the one-shot
fault helper against this completed case/stale signal. Fresh matching guards,
latest-slot inspection and a backed-up separate case are required.
`SarahSessionAlive` is a separate alive copy. Menu/world switching passed using
the temporary mouse menu entrypoint; automated Escape input remains unresolved.
Main-script reload passed in the alive world; the dated world remains dead.
Latest backup group: `runtime/backups/long-session-before-20261004`: Original-retest,
Completed-before-restart, Final-restart and selections. Prior write-failure group
retains Failed-baseline, Harness-failure and fixed results. Prior travel backup
retains Away-before-restart and Returned-final. Older rendering, appearance and
alive/dead backups remain preserved. Restore only game-closed,
after preserving the current case, into a new disposable directory.
Runtime files and backups exist locally but are excluded from Git.
Long-session probe, evidence and handoff updates are included in this checkpoint.
No unfinished work remains for this bounded task; M0 hardening is still open.
Check Git status and fresh native window inventory before resuming UI work.

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
