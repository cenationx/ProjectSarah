# Current project state

Updated: 2026-10-04 (Europe/Helsinki).
State: M0 broader hardening open. M1 read-only console implemented; F9 check passed; broader keyboard acceptance open.
External AI: ON HOLD by explicit user instruction.
Ownership: Codex took over on 2026-10-04 after the user confirmed Claude idle.
Do not have both agents edit this checkout concurrently.

Claude session 2026-10-04 17:10 (verification only, no code changes):
- Git: clean tree, `main` == `origin/main` at `705cec2`; `git push --dry-run origin main`
  succeeded (GitHub access OK). `git` is not on PATH in Antigravity's shell; use
  `C:\Users\rudol\.cache\codex-runtimes\codex-primary-runtime\dependencies\native\git\cmd`.
- Automated (simulated Lua, not native input): 68/68 pass (27+13+8+12+8).
- No Project Zomboid process running. No live test, backup or save change this session.
- STILL UNVERIFIED (need physical keyboard by the user; the game cannot fake them):
  hold-repeat, Escape, rebind/conflict persistence, English Options labels,
  movement input restored after close, same-process menu/world teardown.
  Physical F9 open/close remains the only native keyboard evidence.
- Desktop-control check (17:15): Claude/Antigravity has no desktop-control tool
  (no screenshot, no verified key injection). PowerShell reports an interactive
  session but `CopyFromScreen` fails with "The handle is invalid", so the agent
  cannot see the game. Blind SendKeys could not be verified, and earlier notes
  show function-key injection was missed even by the vanilla rebind dialog.
  Missing capability: screen capture/observation of the user's desktop plus
  reliable key delivery. Native checks therefore stay PENDING (not simulated).
- Next: back up a new disposable case game-closed, then the user runs these
  checks; slice A can be accepted only after they pass.

## Last verified work

Latest verified implementation checkpoint: `8f4f882` on `main`, pushed to
https://github.com/cenationx/ProjectSarah.
This implements the read-only console and records its test boundaries. The next
documentation checkpoint prepares Claude's handoff; identify it using Git history.

- Unmodified PZNS is incompatible with the installed Build 42.21.0 APIs.
- Independent SarahM0 probe demonstrated NPC spawn, walking, inventory transfer,
  death/removal and full process restart restoration.
- SarahFoundation demonstrated spawn, duplicate prevention, three equipped
  clothing items, two-slot saves, unload/restore, full restart restoration,
  recovery from a deliberately truncated latest checkpoint, and saved death
  preventing resurrection after restart.
- 68 automated checks pass: 27 foundation, 13 engine adapter, 8 checkpoint
  readback, 12 read-only command and 8 simulated console UI/key/session cases.
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
- Engine/Lifecycle/main reload twice passed retained controller/NPC, one tick
  and real OnSave callback. A deliberate Lua interruption after native Sarah
  removeFromWorld retained the unfinished real-object reference across another
  module reload and later ticks. Replacement and nonresident writes were refused;
  full restart restored the last good checkpoint with current contents/one Sarah,
  then saved successfully. No production changes. This tests unchanged-source
  reload and an injected fault, not hot upgrades or spontaneous native failures.
  See `M0-module-cleanup-test.md`.

Evidence and boundaries: `M0-PZNS-compatibility.md`, `M0-live-test.md`,
`M0-foundation-live-test.md`, and `../evidence/foundation-policy-tests.txt`.

## Next task: finish M1 slice A keyboard/UI acceptance

Commands/Observations/Console and English binding labels are implemented.
Twelve read-only command and eight simulated UI/key/session checks passed;
all 48 existing foundation checks were rerun successfully (68 total).
Live menu open, typed status/help/inventory, Enter/Run and mouse close passed.
See `M1-console-test.md` for exact evidence and pending checks.

Physical F9 open/close check completed by user and corroborated by probe samples.
Final inventory/font/scroll output and full restart passed; one Sarah/player preserved.

1. Finish native hold repeat, Escape, rebind/conflicts and gameplay
   input restoration. Automated function-key delivery is unreliable even in the
   vanilla rebind dialog; do not substitute simulation or menu use for keyboard pass.
2. Verify English key labels in Options and same-process menu/world cleanup.
3. Back up a new disposable case game-closed before continuing live checks.
4. Only after slice A acceptance, add stop/cancellation, then bounded walk here.
   No external AI, arbitrary Lua or bypass of lifecycle guards.

Broad M0 hardening/release acceptance remains open; no limitations accepted on
user's behalf. Controlled model-free development stays inside the tested envelope.

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
- Reload tests used unchanged source; schema/function hot upgrades and spontaneous
  or silent native cleanup failures remain unverified. Interrupted cleanup needs
  full restart in the tested recovery; no automatic in-session repair is promised.

## Local runtime state at handoff

Game closed; native window inventory confirmed no Project Zomboid window.
Continue selects SarahConsoleCase, only SarahFoundation enabled; no AI.
Final production source/English UI.json deployed. ZZSarahConsoleProbe disabled
outside the mod; no temporary driver remains active. Final case saved b on exit,
one Sarah restored from a before the user's F9 check and final native output check.
Physical F9 open/close completed; native hold/rebind/Escape/menu checks remain open.

Game-closed original SarahModuleCleanupCase, latestSave/default/key files backed
up to runtime/backups/console-before-20261004. First-live-before-repair preserves
initial test state; Final-console preserves final game-closed state. Raw logs
are runtime/console-first-console.txt and runtime/console-final-console.txt.
Older backup groups/cases remain preserved; do not rerun completed fault probes.
Normal profile console remains 18675 bytes, last modified 2026-10-04 04:03:05.
Installed game files read-only. Preserve current case before any restoration,
always game-closed, into a new disposable directory. Runtime excluded from Git.

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

## Codex native acceptance session (IN PROGRESS)

User confirmed Claude idle; Codex owns this checkout for live checks.
Git clean at 0534e61 before takeover. Windows Computer Use initialized; no game window.
Game-closed backup: runtime/backups/console-native-20261004 (SarahConsoleCase,
latestSave/options/key settings). New disposable copy: SarahConsoleNativeCase.
Restore only game-closed after preserving this new case: copy backed-up settings
back to their original isolated paths; original SarahConsoleCase stays preserved.
Next: launch isolated profile; check native input/Options/teardown. Hold duration
is not exposed by the supported desktop API; no hold-repeat pass claimed.


Session progress: isolated Java process 40024 launched outside sandbox; Continue
entered SarahConsoleNativeCase. Mouse/screenshot capture work. Injected F9 did
not open console; injected Escape did not open vanilla pause menu. This is a
key-delivery limitation, not evidence of a Sarah defect. User-assisted hold/Escape
check requested; result pending. No production code changed. All 68 automated
checks rerun successfully. Live log reports ACTIVE/RESTORED b, worn=3 and local
player preserved. Game running while awaiting physical checks; no teardown pass.
