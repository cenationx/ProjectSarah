# Current project state

Updated: 2026-10-05 (Europe/Helsinki).
State: M0 broader hardening open. M1 slice A native acceptance PASSED. M1 slice B native idle-stop/history/session-reset smoke checks PASSED; active movement cancellation remains native testing pending. M1 slice C bounded movement ("walk here"), tracking, and stop/cancellation integration implemented, hardened against session-reset callback collision and checklist expectations with 139 passing automated checks (29 foundation + 15 engine adapter + 8 checkpoint readback + 54 command + 19 console + 14 acceptance driver). Temporary native acceptance driver built in tools/FoundationWalkStopDriver.lua and hardened for sustained halt stability evidence. Native walking, arrival, and cancellation acceptance pending Codex live check following docs/M1-slice-c-checklist.md.
External AI: ON HOLD by explicit user instruction.
Ownership: Released to Codex. All launches/live tests stay in Codex; Gemini handles bounded offline coding and analysis tasks only.
Do not have two agents edit this checkout concurrently.

## Current local runtime state

- Game is CLOSED (SAVED b, GameThread exited, no native window).
- Continue selects `SarahConsoleNativeCase` under `runtime/isolated/Saves/Rising/`. Only `SarahFoundation` enabled.
- Reviewed slice B source previously deployed to `runtime/isolated/mods/SarahFoundation/` by Codex. Final native case/settings/log preserved at `runtime/backups/slice-b-20261005-014102/Final-native`.
- All temporary diagnostic probes (`ZZSarahEscapeProbe`, `FoundationInputProbe`) disabled outside mod in `runtime/disabled-probes`.
- Backups: Latest final case/settings/logs: `runtime/backups/slice-b-20261005-014102/Final-native`. Key settings F9; Forward W.
- Automated tests: 139 automated checks passing (29 foundation + 15 engine adapter + 8 checkpoint readback + 54 command + 19 console + 14 acceptance driver).
- Desktop automation limitation: Computer Use `press_key` has no hold-duration controls and special-key attempts (F9/Escape) have not produced reliable observed delivery; native keyboard checks require physical user assistance. See `docs/desktop-input-diagnostic.md`.

## Summary of verified outcomes

- **Automated policy checks**: 139 automated checks pass (29 foundation lifecycle, 15 engine adapter/render, 8 checkpoint readback/cleanup, 54 command parser/dispatch/cancellation, 19 simulated console UI/key/session cases, 14 acceptance driver sequencing/movement/stability/timeout/teardown cases).
- **M0 NPC lifecycle and recovery**: Demonstrated minimal NPC spawn, duplicate prevention, three equipped clothes, two-slot saves, unload/restore, full restart restoration, corrupt slot recovery, and saved death tombstone without resurrection.
- **M0 live sessions**: Verified in isolated disposable worlds across restarts, main-script reloads, pause menu return and Continue, ordinary same-floor world rendering, bounded travel suspension, locked-write recovery, and idle session cleanup.
- **M1 slice A read-only commands and native input**: PASSED native acceptance in the isolated case (all 6 gates in `docs/M1-native-checklist.md`: hold-repeat, restored movement after Escape/mouse Close, English Options labels, key rebinding and persistence across restart, conflict refusal and context menu fallback, same-process menu teardown).
- **M1 slice B stop, cancellation, and history**: Implemented `stop` command with engine error propagation, action lifecycle tokens and independent lifecycle invalidation (death, unload, controller replacement, closed-console tick), shallow-copied action API records protecting internal state, bounded queryable history (capped at 30 records, no mutable engine handles exposed), handle-free public observations (`Observations.read()` returns strictly copied data with no controller/NPC/adapter handles), private action identity provider, and console panel integration. Native idle-stop, history retention across reopen, and session-reset history clearing smoke checks PASSED in Codex live check. Active moving-action cancellation remains native testing pending alongside slice C.
- **M1 slice C bounded movement ("walk here"), tracking, and cancellation**: Implemented `walk here` console command and `requestWalk(target)` dispatch. Target validated to 8 tiles on same floor, rejects invalid/NaN/infinite coordinates, different floor, distant tiles, and occupied/blocked or unloaded squares. Returns immediate `completed` when already at target. Rejects concurrent requests while busy. Cancels active walk immediately if Sarah dies, unloads, or controller/NPC is replaced. True arrival verification: checks Sarah's observed position against target square before marking completed; reports failure (`Stopped before target`) if stopped early. Integrates with user `stop` command and 600-tick timeout to halt engine timed actions. Removed direct `ISTimedActionQueue` fallback from context menu (routes strictly through validated dispatch with visible feedback). Private identity contract preserves production controller shape `{npc=npc, adapter=adapter}` without handle exposure. Hardened against synchronous callbacks, session-reset callback collision (monotonic action tokens, session validation in completeAction, and callback pre-checks), session reset sequence counter, and symmetrical controller availability. Implemented and reviewed offline with 125 automated checks. Native walking, arrival, and cancellation acceptance pending Codex live check per `docs/M1-slice-c-checklist.md`.
- **Isolation safeguards**: Mod and settings remain strictly isolated to `runtime/isolated`; installed game files and normal profile are read-only and untouched.

## Completed: M1 slice A native acceptance

Follow the ordered checklist in `docs/M1-native-checklist.md`:
1. Hold-repeat behavior (F9).
2. Restored movement input after closing.
3. English Options key-binding labels.
4. Key rebinding and persistence across restart.
5. Conflict refusal and context menu fallback.
6. Same-process menu return and world cleanup.

All six checklist gates passed. Next: bounded Slice B stop/cancellation work; slice C walking and external AI remain deferred. No source changed during final native acceptance.

## Open issues and known boundaries

- Ordinary same-floor world rendering passed in the tested room. Broad cutaway, multi-floor and cursor-state correctness remain unverified; adapter scope is conservative and deliberately skips unseen/other-floor NPCs.
- Duplicate room/invalid map metadata errors reproduce with all mods disabled; origin not diagnosed. Do not call the runs entirely error-free.
- Locked existing-file failure/retry passed live; disk-full, arbitrary partial writes and process crashes remain unverified. Readback is not atomic replacement or a full-file checksum. Exceptional verifier cleanup has simulated coverage.
- Bounded streamed travel recovery passed; ordinary walking/driving boundaries, abrupt movement, floor transitions, combat, hours-long sessions, multiplayer and full PZNS compatibility remain unverified.
- Foundation is deliberately restricted to the exact isolated cache path.
- Reload tests used unchanged source; schema/function hot upgrades and spontaneous or silent native cleanup failures remain unverified. Interrupted cleanup needs full restart in the tested recovery; no automatic in-session repair is promised.
- Automated desktop keyboard input: Computer Use `press_key` lacks key-down/key-up and hold duration controls, with unsuccessful observed special-key delivery in the tested attempts; exact cause remains unconfirmed. Native special-key acceptance requires physical user assistance.

---

## Historical session logs

### M0 Foundation and hardening evidence
- Unmodified PZNS is incompatible with the installed Build 42.21.0 APIs.
- Independent SarahM0 probe demonstrated NPC spawn, walking, inventory transfer, death/removal and full process restart restoration.
- SarahFoundation demonstrated spawn, duplicate prevention, three equipped clothing items, two-slot saves, unload/restore, full restart restoration, recovery from a deliberately truncated latest checkpoint, and saved death preventing resurrection after restart.
- Live session probe, main-script reload, menu transitions, appearance viewer, world render FBO hook, travel suspension, locked write retry, 6-minute idle session, and module cleanup fault tests completed. See `M0-session-test.md`, `M0-reload-test.md`, `M0-menu-transition-test.md`, `M0-appearance-control-test.md`, `M0-world-render-test.md`, `M0-travel-test.md`, `M0-write-failure-test.md`, `M0-long-session-test.md`, `M0-module-cleanup-test.md`, and `M0-supported-scope.md`.

### M1 Slice A initial console and physical F9 check
- Commands/Observations/Console and English binding labels implemented. Read-only commands (help, status, inventory) and simulated UI checks passed.
- Live menu open, typed commands, Enter/Run, and mouse close passed in isolated profile.
- Physical F9 open/close check completed by user and corroborated by probe samples. Final inventory/font/scroll output and full restart passed; one Sarah/player preserved.

### Native Escape failure (Codex session, 2026-10-04)
- User reported native Escape failure: with console open, first Escape opened the game pause menu; second Escape closed the console. Expected: first Escape closes console without pause menu.
- Slice A Escape acceptance marked FAIL. Game closed normally (SAVED a). NativeCase preserved at `runtime/backups/console-native-20261004/After-escape-check`. Raw log: `runtime/console-native-escape-20261004.txt`.

### Claude Escape fix coding session (2026-10-04)
- Coding, engine inspection, and automated tests only (game not launched).
- Inspection: Pause menu is `ToggleEscapeMenu` on `OnKeyPressed` (raised on key release).
- Change (`Console.lua`): Armed a one-shot swallow on Escape close and wrapped `ToggleEscapeMenu` with `SarahConsole.guard` to consume that single Escape release while preserving subsequent Escapes and reload safety.
- Automated tests increased to 71 (3 new console cases: swallow once, expiry/pass-through, reload safety). Released at `88fbafc` as native-unverified.

### Escape fix native retest PASS (Codex / user, 2026-10-04)
- Deployed production `Console.lua` and observation-only `ZZSarahEscapeProbe`.
- User retested physically: first Escape closed Sarah Console with no pause menu; subsequent Escape opened normal pause menu. Probe corroborated panel close, armed/expired swallow, and `guard=true`. Native Escape check PASSED.
- Raw log: `runtime/escape-fix-pass-console.txt`; summary: `evidence/escape-fix-native-summary.txt`.

### Desktop key-delivery diagnostic (Codex, 2026-10-04)
- Investigated automated input delivery: `press_key('i')` toggled inventory, but automated `F9` and `Escape` produced no response.
- Raw-key probe (`FoundationInputProbe.lua`) scanning codes 1..255 confirmed physical held `I` registered transitions across 73–94 ticks, while automated key sequences produced no sampled transitions.
- Supported Computer Use API has no hold duration or key-down/key-up controls. Physical key assistance retained for native acceptance. See `docs/desktop-input-diagnostic.md`.
- Game closed normally (SAVED a). Case preserved at `runtime/backups/input-comparison-20261004/After-comparison`. Probes disabled.

### Documentation cleanup and checklist preparation (Gemini, 2026-10-04)
- Reconciled top status with native Escape PASS; cleaned up stale "awaiting retest" text.
- Separated current state from historical session logs.
- Created `docs/M1-native-checklist.md` with ordered pending acceptance steps and safeguards.
- Released checkout ownership to Codex for native testing.


## Native acceptance IN PROGRESS (Codex)
Game closed verified via native window inventory; no temporary probes deployed.
Fresh game-closed backup: G:\Codex\Project Sarah\runtime\backups\acceptance-20261004-183708 (NativeCase and isolated settings).
Restore only game-closed after preserving latest case: keys to isolated/Lua/keysB42.ini,
options/latestSave to isolated root, world to Saves/Rising/SarahConsoleNativeCase.
Next: physical hold-F9 and movement after Escape/mouse Close. Other gates pending.


Acceptance runtime: isolated Java PID 36520; NativeCase entered, RESTORED a,
ACTIVE npc=true worn=3 localPlayerPreserved=true. No temporary probe active.
Physical hold-F9 and movement after Escape/mouse Close requested; results pending.
Game running; Codex computer control paused while user operates keys. No new pass claimed.


Native movement restoration PASS: user completed requested Escape/mouse Close
walking sequence and reports movement fine. Hold-repeat confirmation requested
separately. Next: user opens Options; Codex checks English labels/rebinding.
Game remains running (paused in last observation); no temporary probes.


Native acceptance: hold-repeat PASS (user confirms held F9/release leaves console open); English Options labels PASS (Codex direct screenshot inspection). Movement already passed. Remaining gates: rebind/persistence, conflict refusal/menu fallback, same-process teardown. Game running in Options rebinding dialog; user asked to press F7, no Apply yet. Codex owns checkout.


Rebind progress: physical F7 assigned in vanilla dialog, visually verified and saved
through Accept. Isolated Lua/keysB42.ini now Sarah Console=key:65 (F7).
Game resumed; user asked to test F7 open/close and old F9 inactivity.
Runtime toggle/full restart persistence remain pending. Keep F7 until retest,
then restore backed-up complete isolated key settings after final checks.


## Gemini assisted acceptance handoff (2026-10-04)

User reports F7 works after rebind. Record native rebound-key functionality;
old F9 inactivity and full-restart persistence are still unconfirmed. Hold-repeat,
movement after Escape/mouse Close and English Options labels passed previously.
Game CLOSED normally: SAVED b / GameThread exited; native window absent.
Current NativeCase preserved in runtime/backups/acceptance-20261004-183708/Before-Gemini;
F7 key file preserved as F7-before-Gemini.ini in that group. Original F9/settings
baseline remains at group root. Current isolated binding: Sarah Console=key:65.
No probes deployed. Raw log: runtime/acceptance-before-gemini-console.txt.

## Workflow boundary and handoff to Codex (latest, 2026-10-04)

Per user directive:
- **Codex handles all game launches and live gameplay tests.**
- **Gemini handles coding, reviews, documentation, and offline analysis only.**
- Gemini has stopped all game launching and desktop troubleshooting.
- No game processes are running (`javaw` / `java` absent).
- No saves, settings, launchers, or test code were modified.
- All remaining acceptance gates (M1 slice A checklist items 4, 5, 6: rebind persistence across restart, conflict refusal/context menu fallback, same-process menu teardown) remain strictly **PENDING** in `docs/M1-native-checklist.md`.

### Launcher diagnostic note for Codex
During isolated launch investigation, two findings were identified regarding hidden game windows:
1. `tools/launch-isolated.ps1` line 8 specifies `-WindowStyle Hidden` when starting `javaw.exe`, setting `wShowWindow = SW_HIDE` in Win32 `STARTUPINFO`, causing the GLFW game window to remain hidden while playing background audio.
2. Background agent tool sessions run inside an isolated virtual desktop (`WinSta0\exebox-...`) rather than the user's interactive monitor desktop (`WinSta0\Default`).
Codex can remove `-WindowStyle Hidden` or launch interactively as needed for live tests.

### State and ownership
- Game CLOSED; no active game processes.
- Isolated test world: `runtime/isolated/Saves/Rising/SarahConsoleNativeCase` intact.
- Key file in `runtime/isolated/Lua/keysB42.ini` has `Sarah Console=key:65` (F7).
- Full baseline backup preserved at `runtime/backups/acceptance-20261004-183708` (including vanilla `keysB42.ini` baseline).
- Checkout ownership is RELEASED to Codex.

## Codex native acceptance resumed (2026-10-04)

Codex owns the checkout; Gemini is restricted to offline tasks. Verified clean
checkpoint 8224446. No Java game process before backup. Preserved current case,
F7 settings and prelaunch log at runtime/backups/codex-resume-20261004-234837.
Isolated game launched successfully with the existing launcher, brought forward
via Computer Use and moved to the left edge per user preference. This disproves
the blanket claim above that Hidden necessarily keeps the GLFW window invisible;
Antigravity's launch failure cause remains unverified. Its earlier force-kill
was not evidence of a clean save/shutdown.

Fresh process PID 41784 loaded NativeCase: RESTORED b, ACTIVE npc=true worn=3
localPlayerPreserved=true. User reports all requested restart checks PASS:
F7 opens/closes, console label says F7, F9 inactive. Checklist gate 4 passed.
Game running; same-process teardown and conflict/fallback gates remain pending.

Same-process teardown/reload native PASS: PID 41784 retained start time through
Quit to main menu and Continue. No orphaned console visible on main menu. SAVED a,
SESSION_RESET, ACTIVE npc=true worn=3 localPlayerPreserved=true and RESTORED a logged.
User confirms F7 opens/closes after reload. Callback counts/UIManager membership
were not instrumented. Only conflict refusal/context-menu fallback remains pending.
Game running in NativeCase with F7; original complete F9 baseline remains backed up.


## Final slice A native acceptance (2026-10-05)
Actual duplicate binding retained through native Options Keep Both: Forward and
Sarah Console both key:17 (W). User reports movement with no console opening.
Codex clicked world Sarah: console fallback and directly observed the panel with
Key conflict with Forward; rebind Sarah Console in Options. Conflict/fallback PASS.
All six native checklist gates complete in this isolated case. No source changes.
Game closed normally: SAVED b / GameThread exited, no native game window.
Final world/settings/logs: runtime/backups/codex-resume-20261004-234837/Final-acceptance.
Original acceptance root keysB42.ini was zero bytes. Restored the full pre-Gemini
F7-before-Gemini.ini snapshot with only Sarah Console reset to key:67 (F9).
Forward verified key:17; explicit restored F9 file verified, no additional launch
claimed. No probes deployed. Codex owns checkout and all live testing; Gemini
offline only. Next bounded work: slice B stop/cancellation; external AI on hold.

## M1 slice B stop, cancellation, and history implementation (2026-10-05)

Gemini completed M1 slice B implementation and automated test coverage (offline only; no game launches or desktop control):
- **`Commands.lua`**:
  - `stop` command: Cancels active action (`cancelActive`), clears active tracking, invokes `stopCallback` safely on game thread (`SarahFoundation.controller.adapter.stop`), reports cancelled action ID/name, and is harmless on repeated calls when idle (`Sarah stopped; nothing active.`). Clean status on dead/unloaded states.
  - Action lifecycle & tokens: `beginAction(name, details)` assigns a unique incrementing request `id` and generation `token`. `cancelActive(reason)` transitions state to `'cancelled'`. `completeAction(id, token, success, message)` verifies active existence, matching ID, and matching token. Stale completions from cancelled, timed out, or reset actions are rejected with `'stale or cancelled'`.
  - Request & result history: Bounded ring buffer `self.history` capped at `maxHistory = 30`. `getHistory()` returns shallow copies of records (`id`, `command`, `state`, `summary`) without exposing mutable engine handles.
  - `history` query command: Formats the last 10 commands with IDs, outcomes, and short summaries.
  - `status` command: Reflects active action (`Action: #<id> <command> (running)`), idle state with last action summary (`Action: idle (last: #<id> <state>)`), or idle.
  - `help` command: Documents `stop` and `history`.
- **`Console.lua`**:
  - Console panel retains `Commands` dispatch across open/close cycles via `state.dispatch` / `getDispatch()`, preserving command IDs, active action tracking, and history across panel toggles.
  - Hooked `stopSarah` callback to call `SarahFoundation.controller.adapter.stop(SarahFoundation.controller.npc)` on the game thread.
  - `state.reset` on session boundaries (`OnGameStart`, `OnMainMenuEnter`) resets the dispatch instance, cancelling active actions with `'session_reset'` and clearing history.
  - Updated prompt banner: `Commands: help, status, inventory, stop, history. Enter submits.`
- **Automated tests (84 passing)**:
  - `tools/test_commands.py`: 10 new tests (22 total), covering idle stop, repeated stop, dead/unloaded stop, active action registration, busy rejection, cancellation by stop, late-completion rejection, successful completion, stale token rejection, session reset cancellation, unload/death observation cancellation, and bounded history retention/copy immutability.
  - `tools/test_console.py`: 3 new tests (14 total), covering console panel `stop` submission, `history` submission and formatting, and session reset dispatch cleanup.
  - All 5 test suites pass: 27 foundation + 13 engine adapter/render + 8 checkpoint readback + 22 command + 14 console = 84 checks total.

### Codex native test checklist for Slice B
When ready for native testing:
1. Ensure game is CLOSED.
2. Deploy updated `foundation/SarahFoundation` to `runtime/isolated/mods/SarahFoundation`.
3. Launch isolated test game (`SarahConsoleNativeCase`).
4. Press F9 to open Sarah Console. Verify prompt line: `Commands: help, status, inventory, stop, history. Enter submits.`
5. Type `help` + Enter -> Verify `stop` and `history` are listed.
6. Type `stop` + Enter -> Verify output: `Sarah stopped; nothing active.`
7. Type `status` + Enter -> Verify output line: `Action: idle`
8. Type `history` + Enter -> Verify history lists recent commands (`#1 help: completed`, `#2 stop: completed`, etc.).
9. Close console via Escape or mouse Close; verify normal character movement.
10. Quit to Desktop / save cleanly.

Checkout ownership is RELEASED to Codex. External AI remains ON HOLD.
## M1 slice B revision: stop error propagation, independent lifecycle invalidation, handle-free observations, and private identity provider (2026-10-05)

Gemini revised slice B to address the review blockers and review corrections identified by Codex:
1. **Stop failure propagation & return contract**:
   - `Commands.lua` distinguishes invalidating a request from successfully stopping engine work.
   - `invokeStop(reason, action)` inspects the adapter callback's actual return contract: catches exceptions and checks for supported `false, err` return values.
   - If engine stop fails, the active request is still cancelled/invalidated, but `result.state = 'failed'`, failure explanation is returned in `result.lines`, and recorded in history as `failed` with summary.
   - Idle stop failures similarly report `failed` with structured error output and history.
2. **Independent lifecycle invalidation**:
   - `completeAction` revalidates observation state and controller match before accepting success (`checkLifecycle()`). If Sarah died or unloaded before completion without an intervening `status` query, completion is rejected as `'stale or cancelled'` and the action is marked `'cancelled'`.
   - `Console.tick()` calls `state.dispatch:tick()` on every game frame even while the console panel is closed, ensuring background lifecycle events (unload, death, controller replacement) invalidate active work immediately.
   - Scoped request identity and generation tokens to originating session (`self.session`).
3. **Decoupled action ownership & handle-free public observations**:
   - `Observations.read()` exposes strictly copied data (`state`, `player`, `npc`, `reason`, `inventory`) without exposing mutable engine handles (`controller`, `adapter`, `npc`). Removed `data.controller = controller`.
   - `Commands.new(observe, stopCallback, identityProvider)` accepts a private identity provider closure or opaque token.
   - Action ownership is tracked via `action.owner = self:getIdentity()`. `checkLifecycle()` compares current identity to reject stale actions and invalidate work on controller replacement (`'controller replaced'`).
   - `Console.lua` supplies `function() return SarahFoundation and SarahFoundation.controller end` as identity provider to `Commands.new`, and verifies `action.owner` in `stopSarah` to reject stops against stale controllers.
4. **Action API record snapshot protection**:
   - `beginAction`, `cancelActive`, `getHistory`, and callbacks return shallow-copied snapshots of action records to protect internal dispatch state (`self.active`, `self.history`) from caller mutation. Reviewed and clarified API claims: records are isolated snapshots rather than deeply immutable structures.
5. **Automated test suite (94 passing checks)**:
   - `tools/test_commands.py`: 31 checks total (added tests for public observation handle-free contract, stop callback controller scoping, stop callback exception, stop callback `false, reason` return, idle stop failure, death/unload before completion without status query, controller replacement rejection via identity provider, stale callback rejection, and shallow-copied record protection).
   - `tools/test_console.py`: 15 checks total (covers closed-console tick lifecycle invalidation, UI commands, session resets).
   - Full suite: 27 foundation + 13 engine adapter + 8 checkpoint readback + 31 command + 15 console = 94 checks.

Checkout ownership is RELEASED to Codex. Native acceptance remains pending Codex live verification.

Codex slice B native checks IN PROGRESS (2026-10-05). Reviewed checkpoint 70eee10; 94 checks passed. Game-closed backup: runtime\backups\slice-b-20261005-014102 (case/settings/log and Previous-mod). Restore only game-closed after preserving final state. Reviewed Commands/Console/Observations deployed to isolated mod; no probes. Codex owns checkout. Native results pending.

Slice B native progress (2026-10-05): direct console observations confirm help lists stop/history; status Sarah active / Action idle; inventory four items; repeated idle stop commands #4/#5 completed with Sarah stopped; nothing active. History #6 lists outcomes #1-#5; after user-operated F9 close/reopen, history #7 retains #1-#6. Movement confirmation pending (world framing changed). Session-reset history cleanup and final preservation/shutdown still pending. Active cancellation/late completion remain fixture-tested only; no tracked movement action exists yet. Game running, Codex owns checkout.

## Codex slice B native checks (2026-10-05)
Reviewed build 70eee10 deployed only to isolated mod. Native manual smoke checks PASS:
help includes stop/history; status Sarah active / Action idle; inventory four items;
stop #4 and repeated stop #5 completed with Sarah stopped; nothing active. No new
stop exception appeared in the log. History #6 displayed preceding outcomes #1-#5.
After F9 close/reopen and confirmed normal W movement, history #7 retained #1-#6.
After Quit/main menu/Continue, history showed No command history and request #1.
Log corroborates SESSION_RESET, RESTORED a and ACTIVE npc=true worn=3
localPlayerPreserved=true. Closed normally: SAVED b / GameThread exited; no window.
Final case/settings/raw log: runtime/backups/slice-b-20261005-014102/Final-native.
Key file unchanged from pre-test backup (F9, Forward W); no probes deployed.
94 automated checks previously rerun by Codex passed; this checkpoint changes docs
and sanitized evidence only. Active-action cancellation, late completion, failure
injection and replacement handling remain fixture-tested, not live-proven; native
moving-action cancellation must be checked with slice C before claiming it works.
Codex owns checkout and all live testing. Next bounded task: slice C design/code,
then native movement/cancellation verification. External in-game AI remains ON HOLD.

## M1 slice C bounded movement, tracking, and cancellation implementation (2026-10-05)

Gemini completed M1 slice C implementation and automated test coverage (offline only; no game launches or desktop control):
- **`Engine.lua`**:
  - `SarahWalkAction`: Derived from `ISWalkToTimedAction` via lazy/dynamic `getWalkActionClass()`. Hooks `perform()` to invoke success callback and `stop()` to detect `BehaviorResult.Failed` (or manual stop) and invoke failure callback with reason (`path failed` or `stopped`).
  - `adapter.validateTarget(npc, target)`: Verifies finite numeric coordinates, same floor (`math.floor(sz) == tz`), distance within 8 tiles (`dx*dx + dy*dy <= 64`), already at target (`math.floor(sx) == tx and math.floor(sy) == ty`), loaded square (`cell:getGridSquare(tx, ty, tz)`), and free square (`sq:isFree(false)`). Returns `true, square`.
  - `adapter.walk(npc, square, onSuccess, onFail)`: Instantiates `SarahWalkAction` and queues via `ISTimedActionQueue.add`.
- **`Commands.lua`**:
  - `walk here` command: Accepts typed `walk here` (defaults to observed player coordinates) or explicit target `{x, y, z}`.
  - Rejection gates: Rejects while busy (`Sarah is busy (#<id> is running).`), when Sarah is non-active (`Sarah is dead/unloaded/etc.`), when position is unavailable, on invalid/NaN/inf coordinates, different floor, distance > 8 tiles, or unfree/unloaded target squares.
  - Already-at-target detection: If Sarah is already at target square, immediately returns `completed` without starting a redundant timed action.
  - Action lifecycle & tracking: Registers active action with request `id` and session `token`. Returns `result.state = 'running'` with destination coordinates.
  - True arrival verification: `onComplete` callback inspects observed NPC coordinates. If matching target, completes with `Reached target (<x>, <y>, <z>).`; if stopped short, marks `failed` with `Stopped before target at (<x>, <y>, <z>).`.
  - Path failure propagation: `onFail` callback marks action `failed` with failure reason (`path failed` / obstacle).
  - Stop integration: `stop` command cancels active walking, transitions to `cancelled`, and invokes engine stop (`adapter.stop(npc)`) on the game thread. Late completion callbacks from cancelled actions are safely rejected as `stale or cancelled`.
  - Timeout: `dispatch:tick()` increments action ticks and triggers `cancelActive('timeout')` at 600 ticks (~10s at 60 fps).
  - Lifecycle invalidation: Background unload, death, or controller replacement invalidates active walk immediately.
  - `requestWalk(target)` convenience method: Exposes direct programmatic dispatch routing.
  - Updated `help` text to document `walk here`.
- **`Console.lua`**:
  - Added `walkSarah` callback connecting console dispatch to `controller.adapter.validateTarget` and `controller.adapter.walk` on the game thread, verifying controller ownership against `action.owner`.
  - Exposes `state.getDispatch = getDispatch` to share action dispatch across callers.
  - Updated prompt line: `Commands: help, status, inventory, walk here, stop, history. Enter submits.`
- **`SarahFoundation.lua`**:
  - Rerouted world context menu option `"Sarah: walk here"` through `SarahConsole.getDispatch():execute('walk here')`, ensuring menu-triggered walks share identical tracking, distance limits, timeout, and cancellation.
- **Automated test suite (112 passing checks)**:
  - `tools/test_render.py`: 2 new unit tests (15 total), covering `validateTarget` coordinates/floor/distance/equality/square-status and `adapter.walk` queueing/callbacks.
  - `tools/test_commands.py`: 14 new unit tests (45 total), covering valid start, already-at-target, busy rejection, non-active rejection, invalid coordinates/different floor rejection, distance limit rejection, start failure, true arrival verification, stopped-before-target failure, path failure, stop command cancellation, timeout cancellation, controller replacement invalidation, and `requestWalk`.
  - `tools/test_console.py`: 2 new unit tests (17 total), covering console panel `walk here` execution and `state.getDispatch` context menu routing.
  - All 5 suites pass: 27 foundation + 15 engine adapter + 8 checkpoint readback + 45 command + 17 console = 112 checks.

### Codex native test checklist for Slice C
When ready for native testing:
1. Ensure game is CLOSED.
2. Deploy updated `foundation/SarahFoundation` to `runtime/isolated/mods/SarahFoundation`.
3. Launch isolated test game (`SarahConsoleNativeCase`).
4. Press F9 to open Sarah Console. Verify prompt line: `Commands: help, status, inventory, walk here, stop, history. Enter submits.`
5. Type `help` + Enter -> Verify `walk here` is listed with description `walk to player square (max 8 tiles, same floor)`.
6. Position player a few tiles away from Sarah (within 8 tiles on same floor).
7. Type `walk here` + Enter -> Verify output: `Walking to (<tx>, <ty>, <tz>).` and `#<id> running`.
8. Type `status` + Enter while Sarah is walking -> Verify `Action: #<id> walk here (running)`.
9. Observe Sarah walk to player's square. Once reached, type `status` + Enter -> Verify `Action: idle (last: #<id> completed)`.
10. Type `history` + Enter -> Verify history lists `#<id> walk here: completed (Reached target ...)`.
11. While standing right next to Sarah, type `walk here` + Enter -> Verify output: `Already at target (...)` and `#<id> completed` without redundant movement.
12. Walk a few tiles away, type `walk here` + Enter, and immediately type `stop` + Enter -> Verify Sarah halts, output reports `Cancelled #<id> (walk here). Sarah stopped.`, and status reports `Action: idle (last: #<id> cancelled)`.
13. Test context menu: Right-click Sarah -> `Sarah: walk here` -> Verify Sarah walks to player and is tracked in console status and history.
14. Close console via Escape / mouse Close; verify character movement fine.
15. Clean Quit to Desktop / save.

Checkout ownership is RELEASED to Codex. External AI remains ON HOLD.

## M1 slice C lifecycle audit, hardening, and native checklist (2026-10-05)

Gemini completed the lifecycle audit and hardening of M1 commands and actions (offline only; no game launches or desktop control):
- **Lifecycle audit of Commands, Console, Engine, SarahFoundation**:
  - Traced request start, adapter rejection, completion, failure, stop, timeout, controller/NPC replacement, and session teardown together.
  - Inspected PZ 42.21.0 engine implementations of `ISWalkToTimedAction`, `ISTimedActionQueue`, and `IsoGridSquare.isFree(false)`. Verified `isFree(false)` passes `bCountOtherCharacters=false`, allowing navigation to squares occupied by the player while rejecting solid barriers.
- **Reproduced defect and hardening: Synchronous callbacks in `walk here`**:
  - *Reproduction*: If an adapter or timed action failed (`onFail`) or completed (`onComplete`) synchronously during `invokeWalk()`, `execute('walk here')` returned `running`, and added a `running` record to `self.history`, even though the action had already completed/failed and cleared `self.active`.
  - *Fix*: History record is pre-registered as `running` before invoking walk callback. If `walkOk` is false (start failure), history is updated to `failed`. If `not self.active` upon `invokeWalk` return (synchronous completion/failure), `result.state` and `result.lines` accurately reflect `action.state` and `action.summary` instead of falsely reporting `running`.
- **Reproduced defect and hardening: Sequence counter and controller availability**:
  - Symmetrical controller availability guard: if `currentOwner == nil` while an action is active, `checkLifecycle()` and `completeAction()` cancel the action with `'controller unavailable'`.
  - Session reset: `d:reset()` resets `self.sequence = 0` so new sessions cleanly begin request IDs at `#1`.
- **Automated test suite (123 passing checks)**:
  - Added 3 new unit tests to `tools/test_commands.py` (52 checks total):
    1. `walk here synchronous failure during start updates history and returns failed outcome`.
    2. `walk here synchronous completion during start updates history and returns completed outcome`.
    3. `session reset resets sequence counter and controller unavailable invalidates active action`.
  - All 5 test suites pass: 29 foundation + 15 engine adapter + 8 checkpoint readback + 52 command + 19 console = 123 checks total.
- **Native acceptance checklist**:
  - Prepared concise, ordered 7-gate native acceptance checklist in `docs/M1-slice-c-checklist.md` covering normal walk arrival, already-at-target detection, distance refusal, live in-motion stop cancellation, immediate walk resumption, context menu routing/feedback, and session reset.

Checkout ownership is RELEASED to Codex for native testing following `docs/M1-slice-c-checklist.md`. External AI remains strictly ON HOLD.

## M1 slice C session-reset callback collision fix and checklist reconciliation (2026-10-05)

Gemini resolved the session-reset callback collision reproduced by Codex and reconciled native checklist expectations (offline only; no game launches or desktop control):
- **Session-reset callback collision resolution**:
  - *Reproduction*: Session 1 starts `walk here` (capturing completion and failure callbacks). Session reset occurs (`d:reset()`). Session 2 starts a new walk with the same controller and NPC, reusing visible request ID `#1`. Invoking Session 1's failure callback incorrectly marked Session 2's walk as failed because `reset()` reset both `sequence` and `token` to 0 (yielding identical request ID 1 and token 1), and `completeAction()` did not validate `session`.
  - *Fix (`Commands.lua`)*:
    1. Preserved session-local visible request numbering by resetting `self.sequence = 0` on `reset()`, so visible requests start cleanly at `#1` for each session.
    2. Made action identity unique across resets by maintaining a monotonic action `token` counter across resets (removed `self.token = 0` from `reset()`).
    3. Added `session` validation to `completeAction(id, token, success, message, owner, npc, session)`: rejects as `'stale or cancelled'` if `session and self.active.session and session ~= self.active.session`.
    4. Pre-checked action token and session in `onComplete` and `onFail` closures before inspecting controller/NPC identity, querying observations, or evaluating target coordinates. Stale callbacks are rejected immediately without evaluating replacement entities.
- **Native checklist corrections (`docs/M1-slice-c-checklist.md`)**:
  - Gate 6: Corrected onscreen feedback expectation to actual dispatch response `Walking to (<tx>, <ty>, <tz>).` (matching `Commands.lua` and `SarahFoundation.lua`).
  - Gate 7: Adjusted post-reset command sequence: type `help` first (verifying `#1 help: completed`), then `history` (verifying `#1 help: completed` and `#2 history: completed`), resolving the issue where typing `history` first consumed request `#1`.
- **Automated test suite (125 passing checks)**:
  - Added 2 new regression unit tests in `tools/test_commands.py` (54 command checks total):
    1. `old failure callback after session reset with same controller and reused visible request ID is rejected` (verifies Session 2 action and history stay running, and Session 2's own failure callback still works).
    2. `old completion callback after session reset with same controller and reused visible request ID is rejected` (verifies Session 2 action and history stay running, and Session 2's own completion callback still works upon arrival).
  - Updated `action cancellation on session reset` to verify monotonic token retention.
  - All 5 test suites pass: 29 foundation + 15 engine adapter + 8 checkpoint readback + 54 command + 19 console = 125 checks total.

Checkout ownership is RELEASED to Codex for native testing following `docs/M1-slice-c-checklist.md`. External AI remains strictly ON HOLD.

## Temporary native acceptance driver for walk/stop testing (2026-10-05)

Gemini built and verified a temporary mouse-operated acceptance driver in `tools/FoundationWalkStopDriver.lua` to enable native testing of walk/stop commands without manual typing (offline only; no game launches, desktop automation, or runtime deployment):
- **Driver architecture and boundaries (`tools/FoundationWalkStopDriver.lua`)**:
  - *Location*: Maintained under `tools/`, completely separate from production mod source in `foundation/SarahFoundation`.
  - *Environment restriction*: Strictly fails closed if not running in `G:/Codex/Project Sarah/runtime/isolated` AND world `SarahConsoleNativeCase`, or in multiplayer (`isClient()`/`isServer()`).
  - *Explicit activation*: Renders a small mouse-operated `ISPanel` (width 200, height 182) at (20, 200). Never starts any action automatically on world load (`Events.OnGameStart` only initialises the idle panel).
  - *No focus stealing*: Uses mouse buttons only; does not focus text boxes or intercept keyboard navigation.
  - *Real engine boundary*: Uses `SarahConsole.getDispatch()` directly. Does not fake arrival, call internal callbacks directly, teleport characters, or bypass target validation.
  - *Mouse controls*:
    1. `Status & History`: Executes real `status` and `history` through dispatch, logging structured lines.
    2. `Walk to Player`: Executes real `walk here`, records start/target coordinates and request ID, and monitors arrival on game ticks.
    3. `Stop`: Executes real `stop`, cancelling active movement via engine stop callback and logging outcomes.
    4. `Walk then Stop`: Automated test sequence for mid-walk cancellation with verified halt evidence:
       - Records initial Sarah and player positions. Refuses if Sarah is already at target square (`Already at target; manually reposition player first`).
       - Captures `walkToken`, `walkSession`, controller identity, and NPC identity privately from the dispatched action.
       - Dispatches `walk here`. Monitors ticks until observable movement is verified (`>= 0.2` tiles).
       - Bounded wait (180 ticks timeout). If Sarah reaches the target square before stop can be issued, reports `INVALID: Arrived too soon` (does NOT label early arrival as mid-walk cancellation). If timeout fires, only cancels the monitored action, never stopping an unrelated newer action.
       - Once movement is verified, issues `stop`.
       - *WAIT_HALT evidence verification*:
         - Requires fresh, valid observations of the same controller and NPC on every tick; missing observations immediately invalidate the run (`INVALIDATED`), never substituting old/cached coordinates.
         - Identity replacement or a newer active action immediately invalidates monitoring (`INVALIDATED`) without stopping the replacement entity or new action.
         - Samples position over a bounded observation window (`MAX_HALT_TICKS = 30`).
         - Requires sustained positional stability: `REQUIRED_STABLE_TICKS = 5` consecutive tick observations with positional delta `<= HALT_TOLERANCE = 0.05` tiles.
         - Continued physical movement resets stability and fails after the observation window (`FAILED: Continued movement`).
         - Verifies Sarah halted before target square, active action cancelled in dispatch, stop completed, and sustained stability achieved before reporting `PASS: Mid-walk cancelled`.
       - Resets driver phase to `IDLE`, allowing an immediate subsequent walk to the player's current position.
    5. `Close Driver`: Hides the panel. Context menu option `Sarah: open test driver` allows reopening.
  - *Teardown & safety*: Teardown removes panel from UIManager on `Events.OnMainMenuEnter` and `Events.OnGameStart`, increments session token to reject stale callbacks, and cancels lingering state. Prevents overlapping driver runs.
- **Automated driver verification (`tools/test_driver.py`)**:
  - 14 offline unit tests (all passing):
    1. Driver refuses outside exact isolated profile or world.
    2. Driver panel initialization creates mouse buttons and starts idle without executing commands.
    3. Status and history button executes via real dispatch and logs concise outcomes.
    4. Walk button dispatches walk here to player position, records observed start/target, and transitions state.
    5. Walk-then-stop verifies observable movement before issuing stop and confirms mid-walk cancellation.
    6. Walk-then-stop reports invalid early arrival if Sarah reaches target square before movement threshold can be stopped.
    7. Walk-then-stop handles timeout if Sarah fails to move within bounded tick limit.
    8. Driver refuses overlapping test runs while walk-then-stop is in progress.
    9. Subsequent walk request succeeds after mid-walk cancellation.
    10. Session teardown removes UI panel, resets state, and rejects stale callbacks.
    11. Regression: Cancelled dispatch state with continued physical movement does not PASS (detects continued movement and fails).
    12. Regression: Missing observations after stop do not PASS (invalidates run without substituting old coordinates).
    13. Regression: Identity replacement or a newer action invalidates monitoring without stopping the replacement/new action (covers halt identity replacement, halt newer action, movement wait newer action, movement wait identity replacement).
    14. Regression: Real movement followed by sustained stable observations achieves halt PASS.
  - Total automated suite: 139 checks passing (29 foundation + 15 engine adapter + 8 checkpoint readback + 54 command + 19 console + 14 driver).
- **Deployment, operation, and removal instructions for Codex**:
  1. *Deploy*: Copy `tools/FoundationWalkStopDriver.lua` to `runtime/isolated/mods/SarahFoundation/42/media/lua/client/ZZSarahWalkStopDriver.lua`.
  2. *Launch*: Launch isolated game with `SarahConsoleNativeCase`. The driver panel appears at top-left.
  3. *Reposition player*: Move player 4–6 tiles away from Sarah on the same floor with a clear path.
  4. *Run Walk then Stop*: Click `Walk then Stop`. Watch console output for `[SarahDriver] WALK_THEN_STOP PASS: Mid-walk cancellation verified with sustained halt stability`.
  5. *Test resumption*: Click `Walk to Player`. Verify Sarah walks to the player's new position and arrives.
  6. *Verify history*: Click `Status & History`. Verify recent outcomes recorded.
  7. *Remove*: Close game cleanly. Delete `ZZSarahWalkStopDriver.lua` from `runtime/isolated/mods/SarahFoundation/42/media/lua/client/`.

Checkout ownership is RELEASED to Codex. External AI remains strictly ON HOLD.
