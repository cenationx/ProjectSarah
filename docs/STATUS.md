# Current project state

Updated: 2026-10-04 (Europe/Helsinki).
State: M0 broader hardening open. M1 read-only console implemented; F9 check passed; Escape fix awaiting native retest; broader keyboard acceptance open.
External AI: ON HOLD by explicit user instruction.
Ownership: Codex owns coding and native testing after Claude released checkpoint 88fbafc.
Do not have two agents edit this checkout concurrently.

Escape fix (Claude, 2026-10-04; code + API inspection + automated tests only; game NOT launched):
- Bug (user-reported, native): with Sarah Console open, first Escape opened the pause
  menu; second Escape closed the console. Expected: first Escape closes the console only.
- Inspection of the local decompiled engine and installed game Lua: the pause menu is the
  global `ToggleEscapeMenu` (MainScreen.lua), registered on `OnKeyPressed`. The engine
  raises `OnKeyPressed` on key RELEASE, and skips it only if `GameKeyboard.eatKeyPress`
  marked the key, a UI element consumes the release, or native text entry is active.
  The previous fix relied only on `eatKeyPress` from `OnTick`. The exact native ordering
  that defeated it is UNVERIFIED (no probe ran in Codex's failed run, so there is no log).
- Change (`Console.lua`): an Escape edge with the panel open still eats the key and closes,
  and now also arms a one-shot `swallow`. `ToggleEscapeMenu` is replaced on `OnKeyPressed`
  by `SarahConsole.guard`, which drops exactly that one Escape release and otherwise calls
  the original. The swallow expires 5 ticks after Escape is up. Reload restores the vanilla
  handler before re-wrapping; if the handler is not found nothing is wrapped.
- Automated: all five suites pass, 71 total = 27 foundation + 13 adapter + 8 checkpoint
  + 12 command + 11 console (3 new simulated cases: swallow once then a real Escape works,
  expiry/pass-through, reload without stacking/missing handler). Simulation only.
- NATIVE-UNVERIFIED. The fixed file is in `foundation/` and is NOT yet deployed to
  `runtime/isolated/mods` (deployment left to Codex with its game-closed backup routine).
- Next (Codex, native): back up game-closed, deploy production source, retest physical
  Escape; also record whether `ToggleEscapeMenu` was wrapped (`SarahConsole.guard~=nil`).
  If it still fails, add a temporary probe logging raw ESC state, `OnKeyPressed` calls and
  tick order. Still pending: hold-repeat, rebind/conflict persistence, English Options
  labels, movement restoration, same-process teardown. Stop/walk and AI stay on hold.
- Git helper: `git` is not on PATH in Antigravity; use
  `C:\Users\rudol\.cache\codex-runtimes\codex-primary-runtime\dependencies\native\git\cmd`.
- Antigravity has no desktop-control/screenshot tool (`CopyFromScreen` fails), so native
  checks need Codex or the user.

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
- 71 automated checks pass (after the Escape fix): 27 foundation, 13 engine adapter, 8 checkpoint\n  readback, 12 read-only command and 11 simulated console UI/key/session cases.
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

User follow-up: physical F9 opens the console and Escape works. User-operated
open/close confirmed; no held-key duration or pause-menu release detail reported.
Hold-repeat, rebind/conflicts, English Options labels, movement restoration and
same-process teardown remain pending. Codex retains checkout ownership.

## Latest result and coding handoff: Escape gate FAILED

The user's more precise report supersedes the earlier broad "Escape works"
confirmation: with console open, first Escape opens the game menu, second Escape
closes the console. Expected: first Escape closes console with no pause menu.
Physical F9 opens; hold-repeat still not independently established. This is
user-operated native failure evidence, not an automated reproduction. No root
cause confirmed; inspect native input ordering, focus and paused tick behavior.
All other remaining slice A gates stay open; do not proceed to stop/walk or AI.

Game now CLOSED via normal window Close; native window inventory confirms absent.
Log records SAVED a and GameThread exited. New disposable case preserved at
runtime/backups/console-native-20261004/After-escape-check; original console case
and pre-test isolated settings remain in the same backup group. Raw log retained
as runtime/console-native-escape-20261004.txt. Continue selects SarahConsoleNativeCase.
No production edits or temporary probe deployments. 68 automated checks passed
before the manual report; existing simulated Escape pass misses this native issue.
Codex stops editing after this documentation checkpoint. Next owner: Claude,
started by the user, coding/automated tests only. Read docs/CLAUDE-RESUME.md.

## Ongoing agent workflow (user decision, 2026-10-04)

Codex handles sustained coding, automated checks and native game testing. Gemini
may assist with bounded coding/review work when the user starts it, with explicit
checkout ownership or a separate authorized workspace. Claude is no longer the
routine coding handoff target because of the user's weekly usage budget; only
use Claude when explicitly requested. The user forwards any external-agent prompt.
Codex has read Claude's completed Escape fix report and checked a clean checkout
at 88fbafc. The reported 71 passing checks are Claude's verification; Codex has not
rerun them yet. Fix remains native-unverified and not deployed. Next: review fix,
back up game-closed, deploy and retest in isolated NativeCase. AI remains on hold.
