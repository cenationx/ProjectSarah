# Current project state

Updated: 2026-10-05 (Europe/Helsinki).
State: M0 broader hardening open. M1 slice A native acceptance PASSED. M1 slice B native idle-stop/history/session-reset smoke checks PASSED; active movement cancellation tested natively alongside slice C. M1 slice C bounded movement ("walk here"), tracking, and stop/cancellation integration implemented and hardened offline. Mouse-operated shortcut toolbar expanded to 7 buttons ([Help], [Status], [Inventory], [History], [Walk Here], [Follow], [Stop], [Close]). Movable console panel implemented via title-bar mouse dragging with bounds clamping, small-screen layout adaptation (dynamic panel and history height scaling, non-negative title bar clamp minY=0, full control access), control click isolation, in-session position retention across close/open, session-reset to centered default on leaving world, and OnResolutionChange dynamic re-clamping. Bounded native walk, cancellation with sustained halt, and same-process reload reset PASSED in Codex live session. Consolidated M1 native acceptance session plan authored (docs/M1-batched-acceptance.md) and read-only preflight tool hardened against false-ready conditions (tools/preflight.py). Bounded manual follow-player command implemented offline and hardened against Codex review findings (safe player death observation, tick/activation enforcement, completed-step callback retirement, symmetrical identity/lifecycle callback guards). User-facing follow status distinctions (walking, waiting in range vs before next walk during cooldown, disengaged with reason, engine stop failure warning with blocked recovery) and asynchronous one-time failure feedback (unified disengagement + stop failure notice, console panel append, in-world halo notifications, no duplicate/replayed notices) implemented and verified offline (202 automated checks across 7 suites: 29 foundation + 15 engine adapter + 8 checkpoint readback + 54 command + 36 console + 14 acceptance driver + 46 follow, plus 11 runner self-tests and 19 preflight tests). All native acceptance claims strictly pending Codex live verification.
External AI: ON HOLD by explicit user instruction.
Ownership: Released to Codex. All launches/live tests stay in Codex; Gemini handles bounded offline coding and analysis tasks only.
Do not have two agents edit this checkout concurrently.

## Current local runtime state

- Game is CLOSED (SAVED a, GameThread exited, no native window).
- Continue selects `SarahConsoleNativeCase` under `runtime/isolated/Saves/Rising/`. Only `SarahFoundation` enabled.
- Reviewed slice C source deployed to `runtime/isolated/mods/SarahFoundation/` by Codex (pending Console.lua deployment for small-screen fix). Final native case/settings/log preserved at `runtime/backups/slice-c-native-20261005-143139/Final-native`.
- All temporary diagnostic probes (`ZZSarahEscapeProbe`, `FoundationInputProbe`) disabled outside mod in `runtime/disabled-probes`.
- Backups: Latest final case/settings/logs: `runtime/backups/slice-c-native-20261005-143139/Final-native`. Key settings F9; Forward W.
- Automated tests: 202 automated checks passing across 7 suites (29 foundation + 15 engine adapter + 8 checkpoint readback + 54 command + 36 console + 14 acceptance driver + 46 follow) executed via unified runner `tools/run_tests.py`, plus 11 runner self-tests in `tools/test_runner.py` and 19 preflight tests in `tools/test_preflight.py`.
- Desktop automation limitation: Computer Use `press_key` has no hold-duration controls and special-key attempts (F9/Escape) have not produced reliable observed delivery; native keyboard checks require physical user assistance. See `docs/desktop-input-diagnostic.md`.

## Summary of verified outcomes

- **Automated policy checks**: 202 automated checks pass (29 foundation lifecycle, 15 engine adapter/render, 8 checkpoint readback/cleanup, 54 command parser/dispatch/cancellation, 36 simulated console UI/key/shortcut/dragging/bounds/session/feedback cases, 14 acceptance driver sequencing/movement/stability/timeout/teardown cases, 46 follow companion navigation/status/notice cases) plus 11 runner self-tests and 19 preflight tests. Single-entry runner `tools/run_tests.py`, hardened preflight tool `tools/preflight.py`, and documentation `docs/verification-workflow.md` verified.
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

## Single-entry offline verification workflow (2026-10-05)

Gemini built and verified a dependable, single-entry offline verification workflow in `tools/run_tests.py` and `tools/test_runner.py` (offline only; no game launches, desktop automation, or runtime deployment):
- **Unified test runner (`tools/run_tests.py`)**:
  - Single command executes all 6 offline test suites from any working directory (`& "<python.exe>" tools/run_tests.py`).
  - Resolves suite and report paths relative to repository root; runs child processes in repository root.
  - Resolves Python interpreter via CLI `--python`, environment variable `SARAH_PYTHON`, documented cache runtime `C:\Users\rudol\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe`, or `sys.executable`. No packages installed automatically.
  - Resolves Git metadata (commit, branch, dirty status) gracefully via `SARAH_GIT`, PATH, or cache git; degrades safely if Git is unavailable.
  - Preserves child exit status and output. Verifies exit code 0, positive check count, and valid `RESULT <count>` summary (using `re.findall` to correctly capture final cumulative summaries when intermediate progress lines exist).
  - Enforces per-suite bounded timeout (`--timeout 60`, default 60s) and cleans up hung child processes.
  - Generates human-readable Markdown (`tools/reports/test-report.md`) and machine-readable JSON (`tools/reports/test-report.json`) under ignored `/tools/reports/` with explicit fixture disclaimer and sanitized paths.
- **Runner test suite (`tools/test_runner.py`)**:
  - 9 automated unit tests using standard library only (`unittest`, `subprocess`, `tempfile`, `json`).
  - Tests runner against controlled child fixtures without running the full suite:
    1. Valid suite success and check count extraction.
    2. Non-zero exit code failure reporting.
    3. Missing `RESULT` summary detection and failure reporting.
    4. Child process unhandled exception/crash capture.
    5. Timeout enforcement and process cleanup.
    6. Paths and directories containing spaces.
    7. Invocation from foreign working directories.
    8. Graceful handling of unavailable Git.
    9. Multiple RESULT lines taking the final cumulative summary.
  - All 9 runner tests pass (`OK`).
- **Full suite execution verification**:
  - Executed all 6 production suites through `tools/run_tests.py`:
    - `tools/test_foundation.py`: 29 checks pass
    - `tools/test_render.py`: 15 checks pass
    - `tools/test_checkpoint.py`: 8 checks pass
    - `tools/test_commands.py`: 54 checks pass
    - `tools/test_console.py`: 19 checks pass
    - `tools/test_driver.py`: 14 checks pass
    - Overall: **PASSED (139 checks across 6 suites in ~0.30s)**.
  - Inspected generated Markdown and JSON reports in `tools/reports/`.
- **Workflow documentation (`docs/verification-workflow.md`)**:
  - Documents exact operating command, interpreter resolution and overrides, report formats, troubleshooting, and the explicit distinction between offline fixture checks and native gameplay acceptance.

Checkout ownership is RELEASED to Codex. External AI remains strictly ON HOLD.


### Codex verification runner correction (2026-10-05)
- Git dirty reporting now includes untracked files as well as tracked modifications.
- Runner self-test temporary files are created and cleaned under tools/reports/self-test-tmp, independent of system TEMP settings.
- Verified: 139 project checks and 11 runner self-tests pass. Two regressions cover project-local temporary files and clean/tracked/untracked Git status.
- Offline only; runtime and saves untouched. Native slice C remains pending. Ownership: Codex.

### Sarah Console mouse shortcuts for commands (2026-10-05)
- **Mouse shortcut toolbar added to Sarah Console**:
  - Purpose: Avoids unreliable automated desktop keyboard input in PZ; allows Codex to open the console via mouse context menu (`Sarah: console`) and submit all core commands by clicking dedicated buttons, while the user controls movement and gameplay.
  - Buttons: Dedicated, clearly labelled buttons for `Help`, `Status`, `Inventory`, `History`, `Walk Here`, and `Stop`.
  - Exact command path: Every button routes directly through the existing validated dispatcher (`self.dispatch:execute()`) and the unified display path (`executeCommand()`), identical to typed entry. No duplicated logic or secondary dispatchers.
  - `Walk Here`: Captures the player's position at click time via `self.observe(false)`, validating proximity (<= 8 tiles, same floor), alive/active status, and busy state.
  - `Stop`: Remains accessible and clickable while a walk is running, halting Sarah and cancelling the active timed action.
  - Rejection & failure visibility: Rejected requests (e.g. distant target, busy state) and failure reasons are displayed in the history box with request IDs.
  - Layout & geometry: Compact toolbar at `y = height - 74` (height 26) with balanced proportional button widths (Help: 72, Status: 80, Inventory: 96, History: 82, Walk Here: 102, Stop: 72). Clean margins (12px left/right), no overlap with history (y: 42..288), entry (y: 330..356), Run (x: 484..548), or Close (x: 480..548, y: 10..34). Fits cleanly inside 1280x720.
  - Translation integration: Added translation keys `UI_SarahConsole_Help`, `UI_SarahConsole_Status`, `UI_SarahConsole_Inventory`, `UI_SarahConsole_History`, `UI_SarahConsole_WalkHere`, `UI_SarahConsole_Stop`, `UI_SarahConsole_Run`, and `UI_SarahConsole_Close` to `Translate/EN/UI.json`. Safe `tr()` helper checks `getText()`.
  - Preserved controls: Typed command entry in `entry` and Enter/Run button remain fully functional. Reopening/redrawing never executes commands.
- **Offline regression suite (`tools/test_console.py`)**:
  - 7 new automated tests (26 checks total in suite):
    1. All 6 shortcut buttons created with valid labels and non-overlapping geometry.
    2. Each shortcut button invokes its command once through normal output path with refocused entry.
    3. Stop shortcut button remains accessible and halts active walk mid-stride.
    4. Rejected walk shortcut feedback displays rejection reason and request ID.
    5. Reopening/redrawing does not execute commands or advance sequence.
    6. Translation helper uses `getText` when available and falls back gracefully.
    7. Typed command entry and session reset remain fully operational alongside shortcuts.
- **Verification status**:
  - 146 checks across 6 suites pass in `tools/run_tests.py` (0.31s).
  - 11 runner self-tests pass in `tools/test_runner.py` (2.77s).
  - Offline tooling and mod source updated. Native UI verification and Slice C native acceptance remain PENDING live testing by Codex.
  - Temporary driver in `tools/FoundationWalkStopDriver.lua` retained for Codex evaluation.

Checkout ownership is RELEASED to Codex. External AI remains strictly ON HOLD.

### Preparation for native acceptance using console mouse buttons (Gemini, 2026-10-05)
- **Native UI source inspection (PZ 42.21.0 ISUI)**:
  - Inspected `ISButton.lua`, `ISScrollingListBox.lua`, `ISUIElement.lua`, and `ISTextEntryBox.lua` read-only under `G:\Games\ProjectZomboid\media\lua\client\ISUI\`.
  - Callback signatures: `ISButton:onMouseUp` invokes `self.onclick(self.target, self, ...)`. In `Console.lua`, buttons pass `target = self` (the `Panel`), so `Panel.onShortcut*` receives `Panel` as `self`, executing `Panel:executeCommand(...)` correctly. The `Close` button passes `state.close` as `onclick` with `nil` target, which cleanly cleans up `state.panel`. Signatures match native PZ UI exactly.
  - Button hit areas and geometry: Toolbar is positioned at `y = height - 74` (`y = 296`, `height = 26`) with button widths 72, 80, 96, 82, 102, 72 and 6-7px horizontal gaps. Clearance is 8px below list box (`y: 42..288`) and 8px above text input (`y: 330..356`). No overlaps.
  - Title string auto-expansion check: Native `ISButton:new` expands button width if `width < getTextManager():MeasureStringX(UIFont.Small, title) + 10`. In our layout, all button titles ("Help", "Status", "Inventory", "History", "Walk Here", "Stop") measure 15-30px smaller than assigned widths, preventing unintended button width expansion.
  - Focus behavior: `Panel:executeCommand` resets entry text (`self.entry:setText('')`) and refocuses (`self.entry:focus()`), ensuring immediate keyboard input readiness without extra clicks.
  - Output scrolling: `Panel:append` calls `self.history:setYScroll(-math.max(0, #self.history.items * self.history.itemheight - self.history.height + 8))` after each added line, keeping newest entries scrolled into view.
  - Stop accessibility during walk: `btnStop.enable = true` is never toggled off. Panel remains active in `UIManager` throughout timed action execution, ensuring `Stop` is clickable at any time during a walk.
  - Boundary: Design verified; no code defects identified. Per rule, native UI acceptance is not claimed from code inspection alone.
- **Checklist update (`docs/M1-slice-c-checklist.md`)**:
  - Re-oriented all 7 acceptance gates to use the mouse context menu (`Sarah: console`) and the 7 buttons (`[Help]`, `[Status]`, `[Inventory]`, `[History]`, `[Walk Here]`, `[Stop]`, `[Close]`).
  - Clear division of responsibilities: User moves player and visually verifies NPC movement/arrival/halt; Codex operates UI buttons and inspects console output.
  - Omitted repeating accepted slice A physical keyboard gates unless investigating a regression.
  - Clarified that `tools/FoundationWalkStopDriver.lua` is optional; native acceptance proceeds via production console buttons.
- **Deployment and recovery protocol documented for Codex**:
  - Documented exact production source files (`SarahFoundation.lua`, `Commands.lua`, `Console.lua`, `Engine.lua`, `UI.json`, `README.md`).
  - Documented baseline (Slice B at `runtime/isolated/mods/SarahFoundation/` and `runtime/backups/slice-b-20261005-014102/Final-native`) vs pending Slice C & UI changes.
  - Documented pre-test backup, deployment, and recovery/rollback checklists (without executing deployment).
- **Single next task**:
  - Native M1 slice C and console-button acceptance by Codex following `docs/M1-slice-c-checklist.md`.
  - External AI remains strictly ON HOLD.
  - Checkout ownership is RELEASED to Codex.

### Native slice C session IN PROGRESS (2026-10-05)
Codex owns checkout. Gamepad-disconnected automated F9/A/I had no visible effect. Prior game closed cleanly (SAVED a; GameThread exited). Backup: runtime\backups\slice-c-native-20261005-143139 (world, Previous-mod, keys, options, selection, raw log). Reviewed production files deployed; no temporary driver. Restore only game-closed after preserving latest state. Native UI/walking/cancellation checks remain pending.

Native progress: Help #1, Status #2, Inventory #3 and History shortcuts displayed correctly. Walk #4 reached (10768,10270,0); longer walk #8 reached (10769,10275,0) before Codex stop #9. User submitted walk #11 and stop #12: cancelled before target (10769,10271,0). Status #13/#14 observed NPC (10769.47,10274.26,0) unchanged across unpaused interval. Follow-up walk #15 completed at target; #17 immediately reported Already at target. Remaining: user visual confirmation of mid-walk halt, distance refusal, context-menu feedback and session reset. Game remains running; no final acceptance claim.

User confirmed native visual mid-walk halt after making game fullscreen: Walk Here followed by Stop visibly stopped Sarah. This completes visual cancellation confirmation; distance refusal, context-menu feedback and session reset remain pending.

Context-menu walk #23 reached (10768,10272,0), confirmed by History #24 and visible travel/green feedback. Native distance refusal deferred because indoor space is insufficient. Next: same-process menu/reload reset. Game still running; Codex owns checkout.

### Native slice C bounded results (Codex, 2026-10-05)
Production mouse shortcuts passed help/status/inventory/history, nearby walk arrival,
already-at-target, active cancellation with sustained halt, and subsequent walk.
User visually confirmed walk #18 halted by stop #19. Context-menu walk #23 displayed
green feedback and completed at (10768,10272,0), confirmed by history #24.
Same-process Quit -> Continue passed: Help restarted at #1; History #2 listed only
new Help, with no previous-session requests. Status #3 showed Sarah active/idle,
player (10768.86,10272.74,0), NPC (10768.47,10272.42,0). Log showed SESSION_RESET,
ACTIVE npc=true localPlayerPreserved=true, RESTORED b. Post-reload user movement
was not separately retested. Native distance refusal and red context-menu refusal
feedback remain pending: house too small; user did not go outside. No full slice C
acceptance claim. Offline baseline remains 146 project checks plus 11 runner tests.
Game closed cleanly: SAVED a; GameThread exited; no java/javaw processes remained.
Final world/settings/raw log preserved at
runtime/backups/slice-c-native-20261005-143139/Final-native.
F9 key:67 and Forward key:17 retained. No temporary probes deployed.
Codex owns checkout. Next: safe disposable spacious case for native refusal checks,
or bounded offline work while those checks remain explicitly pending. AI ON HOLD.

### Movable Sarah Console panel and window size robustness (Gemini, 2026-10-05)

Gemini implemented title-bar mouse dragging, screen boundary clamping, and in-session position retention for Sarah Console (offline only; no game launches, desktop automation, or runtime modifications):
- **Mouse dragging via title bar (`Console.lua`)**:
  - Implemented `Panel:onMouseDown`, `Panel:onMouseMove`, `Panel:onMouseMoveOutside`, `Panel:onMouseUp`, `Panel:onMouseUpOutside` following native PZ ISUI conventions (`ISModalDialog`, `ISCollapsableWindow`).
  - Title bar drag zone: bounded strictly to `0 <= y < 40 and 0 <= x < self.width` and `x < self.btnClose.x`.
  - Control click isolation: clicks on `btnClose` (`x >= btnClose.x`), toolbar buttons (`Help`, `Status`, `Inventory`, `History`, `Walk Here`, `Stop` at `y = 296`), text entry / `Run` (`y = 330`), history listbox (`y = 42`), or between-control margins never initiate dragging (`self.moving` remains falsy) and never fire duplicate commands.
- **Bounds clamping algorithm across window sizes**:
  - `state.clampPosition(x, y, w, h)` computes:
    - `minX = math.min(0, sw - w); maxX = math.max(0, sw - w)`
    - `minY = math.min(0, sh - h); maxY = math.max(0, sh - h)`
    - `cx = math.max(minX, math.min(maxX, x or minX))`
    - `cy = math.max(minY, math.min(maxY, y or minY))`
  - On standard screens (`sw >= 560, sh >= 370`): clamps strictly to `[0, sw - w]` and `[0, sh - h]`. The console is kept 100% onscreen, controls are never clipped, and the console can be freely moved aside to give an unobstructed view of Sarah.
  - On small screens (`sw < 560` or `sh < 370`): clamps to `[sw - w, 0]` and `[sh - h, 0]`. The panel slides between screen boundaries, allowing access to both left and right controls (Close, Run) without escaping into the void or becoming unrecoverable.
  - Set `self.keepOnScreen = false` on `SarahConsolePanel` to bypass naive native `ISUIElement:setX/setY` clamping which breaks on screens smaller than panel dimensions.
- **In-session position retention & session reset**:
  - In-session retention: chosen position is saved in `state.pos` upon dragging, mouse up, and `state.close()`. Reopening within the same session re-opens at `state.pos` (re-clamped against current screen size).
  - World exit reset: `state.reset()` (hooked to `Events.OnGameStart` and `Events.OnMainMenuEnter`) clears `state.pos = nil`. Reopening after a session reset restores the default centered position.
  - No disk persistence, no new dependencies, no external AI.
- **Resolution change handling**:
  - Registered `Events.OnResolutionChange.Add(state.resolution)`.
  - If screen resolution changes while panel is open, immediately re-clamps `state.panel` to valid onscreen coordinates. If closed, re-clamps `state.pos`.
- **Automated test suite (153 passing checks)**:
  - Added 7 new regression tests in `tools/test_console.py` (33 console checks total):
    1. Title bar mouse dragging moves panel and updates coordinates and `state.pos`.
    2. Dragging bounds clamped on standard screen (`1280x720`) and keeps entire panel onscreen.
    3. Dragging bounds clamped on small screens (`500x300`) and keeps panel accessible without getting lost.
    4. Clicking controls (`btnClose`, shortcut buttons, `entry`, `btnRun`, history) does not start drag, modify coordinates, or duplicate commands.
    5. Position is preserved across close and reopen within same world session.
    6. Session reset clears position and re-centers console on next open.
    7. `OnResolutionChange` immediately re-clamps open panel and closed position.
  - All 6 suites pass: 29 foundation + 15 engine adapter + 8 checkpoint readback + 54 command + 33 console + 14 driver = 153 checks total.
  - All 11 runner self-tests in `tools/test_runner.py` pass.
- **Native verification checklist for Codex**:
  1. Launch isolated game (`SarahConsoleNativeCase`). Open Sarah Console (F9 / context menu).
  2. Drag console aside by grabbing the title bar ("Sarah Console" area); verify Sarah is visible in the game scene.
  3. Verify all controls remain fully functional while moved: click shortcut buttons, enter text, click Run, click Stop.
  4. Close console (Escape / mouse Close) and reopen (F9 / context menu); verify console reopens at the chosen moved position.
  5. Quit to main menu and Continue; verify console resets to default centered position.
- **State and ownership**:
  - Game is CLOSED (SAVED a, GameThread exited, no native window).
  - Runtime and saves untouched.
  - Checkout ownership is RELEASED to Codex.

### Small-screen console layout adaptation and recovery fix (Gemini, 2026-10-05)

Gemini resolved the oversized-panel recovery bug on small window sizes (offline only; no game launches, desktop automation, or runtime modifications):
- **Oversized-panel recovery bug resolution**:
  - *Problem*: At screen size 500x300, the 560x370 panel previously reached `y = -70` under `minY = math.min(0, sh - h)`. Its entire 40px title bar and Close button were pushed offscreen. Once the mouse was released, dragging could not be restarted, and closing/reopening retained the inaccessible offscreen coordinate.
  - *Height adaptation (`state.computeHeight(sh)`)*: Clamps panel height to `math.min(370, math.max(180, sh))`. On standard screens (`sh >= 370`), height remains standard 370px. On small screens (`sh < 370`), height scales down to match available screen height (e.g. 300px at `sh = 300`).
  - *Strict non-negative title bar clamp (`minY = 0`)*: `state.clampPosition` computes `minY = 0` and `maxY = math.max(0, sh - h)`. Because `minY = 0`, the panel `y` coordinate is strictly non-negative under all conditions (`cy >= 0`). The 40px title bar and Close button can never enter negative screen space or be dragged off the top of the screen.
  - *Dynamic component layout (`Panel:setPanelHeight(newH)`)*: Updates `self.history` height to `math.max(40, newH - 124)`, toolbar buttons (`btnHelp`..`btnStop`) to `y = newH - 74`, and input row (`entry`, `btnRun`) to `y = newH - 40`.
  - *Small-screen control accessibility*: On 500x300, horizontal sliding within `[-60, 0]` provides full access: when slid left to `x = -60`, right-side controls (`Close` at screen x=420, `Run` at 424, `Stop` at 416) are completely on screen; when slid right to `x = 0`, left-side controls (`Help`, `Status`, `Inventory`, text entry) are on screen. The top 40px title bar remains visible and grab-able across screen x `[0, 420]`, enabling drag restart at any time.
  - *Dynamic resolution handling*: `Events.OnResolutionChange` dynamically calls `Panel:setPanelHeight(targetH)` on open panel and re-clamps coordinates to `[0, maxY]`; if closed, re-clamps `state.pos`.
  - *Reopening and retention*: Closing and reopening retains adapted height and non-negative position; session reset clears position to center default.
- **Automated test suite (153 passing checks)**:
  - Updated `tools/test_console.py`:
    1. Replaced small-screen test accepting `y = -70` with comprehensive layout adaptation checks (panel height 300, history height 176, toolbar y=226, entry y=260, Close y=10, y=0, non-negative vertical drag clamp, horizontal slide control reachability, drag restart from visible title bar, command execution, Close click, and reopening at adapted size).
    2. Enhanced `OnResolutionChange` test to verify dynamic shrinking to 500x300, component repositioning, expansion back to 1280x720, and closed-panel resolution shrink.
  - All 6 suites pass: 29 foundation + 15 engine adapter + 8 checkpoint readback + 54 command + 33 console + 14 driver = 153 checks total.
  - All 11 runner self-tests in `tools/test_runner.py` pass.
- **State and ownership**:
  - Game is CLOSED (SAVED a, GameThread exited, no native window).
  - Runtime and saves untouched.
  - Checkout ownership is RELEASED to Codex. External AI remains ON HOLD.

### Consolidated M1 native acceptance session plan and acceptance preflight tool (Gemini, 2026-10-05)

Gemini prepared a consolidated M1 native acceptance protocol and implemented a read-only preflight inspection tool to streamline native testing for Codex and the user (offline only; no game launches, desktop automation, or runtime modifications):
- **Consolidated acceptance session plan (`docs/M1-batched-acceptance.md`)**:
  - Reconciled existing evidence against checklists: separated 12 passed native gates (A1–A6 in slice A, B1–B2 in slice B, C1–C6 in slice C) from the 8 remaining native acceptance gates (R1: movable console dragging, R2: control click isolation, R3: in-session position retention, R4: resolution/small-screen adaptation with non-negative title bar clamp, R5: distance refusal via `[Walk Here]` button, R6: red context-menu refusal feedback, R7: post-reload WASD character movement, R8: session reset to centered default).
  - Designed an ordered 6-phase protocol minimizing launches and user keypresses: requires exactly 1 game process launch, exactly 1 in-process reload (`Quit to Main Menu` -> `Continue`), and exactly 2 user movement phases.
  - Partitioned responsibilities: Codex performs mouse operations (preflight inspection, console dragging, control clicks, close/reopen, button commands, menu navigation), while the user provides physical WASD movement and observes on-screen behavior.
  - Addressed small-room limitation: proposed `SarahSpaciousCase` (Rosewood Fire Station vehicle bay or Church nave with >= 10-12 open tiles on floor 0) along with a safe exterior porch fallback in the existing case.
  - Documented strict rollback steps and evidence capture requirements.
- **Native acceptance preflight tool (`tools/preflight.py`)**:
  - Built a strictly read-only inspection script verifying pre-test environment readiness:
    1. *Git State*: Reports clean commit, branch, and dirty tree status.
    2. *Offline Test Report*: Verifies `tools/reports/test-report.json` exists, passed, and matches current HEAD commit (detects stale test reports).
    3. *Isolated Profile*: Confirms directory existence, active save case, mod selection (`SarahFoundation` enabled), and key binding (`Sarah Console=key:67`).
    4. *File Deployment*: Compares SHA-256 hashes of all 9 production source files against deployed copies in `runtime/isolated/mods/SarahFoundation/`. Detects modified or un-deployed files before launch.
    5. *Temporary Probes*: Scans active mod directory to verify absence of temporary test probes or drivers.
    6. *Backup Availability*: Verifies baseline backups exist in `runtime/backups/` and identifies the latest backup.
    7. *Game Processes*: Checks running processes via standard Windows `tasklist` (`javaw.exe`, `java.exe`, `ProjectZomboid64.exe`) to ensure game is closed.
  - Outputs structured reports in Markdown (`tools/reports/preflight-report.md`) and JSON (`tools/reports/preflight-report.json`).
  - Implemented `--no-strict` and `--fix-check` CLI options; fails closed with exit code 1 if blockers are detected.
- **Preflight automated test suite (`tools/test_preflight.py`)**:
  - 14 automated unit tests covering ready environment, missing reports, stale reports, failed reports, mismatched file hashes, missing deployed files, probe detection, active game processes, missing backups, misconfigured mod files, missing saves, read-only file immutability, report formatting, and CLI execution.
  - Uses project-local temporary fixtures under `tools/reports/self-test-tmp/` that are cleanly wiped after test runs.
- **Automated test suite (167 passing checks + 11 runner self-tests)**:
  - `tools/run_tests.py`: 153 checks passing across 6 suites (29 foundation + 15 engine adapter + 8 checkpoint readback + 54 command + 33 console + 14 driver = 153 checks).
  - `tools/test_runner.py`: 11 runner self-tests passing.
  - `tools/test_preflight.py`: 14 preflight tests passing.
- **State and ownership**:
  - Game is CLOSED (SAVED a, GameThread exited, no native window).
  - Runtime and saves untouched.
  - Checkout ownership is RELEASED to Codex. External AI remains strictly ON HOLD.

### Preflight false-ready hardening and batched acceptance corrections (Gemini, 2026-10-05)

Gemini resolved the four preflight false-ready defects discovered by Codex and corrected `docs/M1-batched-acceptance.md` (offline only; no game launches, desktop automation, or runtime modifications):
- **Preflight false-ready hardening (`tools/preflight.py`)**:
  1. *Individual source missing detection (`check_deployed_files`)*: Tracks `source_missing_count` and `source_missing_files`. When any individual required production file is missing from the repository, sets `status = "source_missing"` and blocks readiness in `evaluate_preflight`.
  2. *Failed Git status query handling (`get_git_info`)*: When `git status --porcelain` returns non-zero, sets `status = "unknown"`, `dirty = "unknown"`, and records command failure instead of falsely treating it as clean.
  3. *Explicit UNKNOWN / not-ready result (`evaluate_preflight`)*: When essential checks cannot be verified (e.g. process query unavailable, Git status unknown, or test report commit match unverified), reports `overall = "UNKNOWN"` with `ready = False` and enumerates unverified items, preventing false `READY` results.
  4. *Dirty-run test report rejection (`check_test_report`)*: Inspects `rep_git.dirty` flag in `test-report.json`. A test report generated on a dirty working tree is flagged `status = "dirty_run"` and blocked, ensuring clean HEAD verification.
- **Preflight automated test suite (`tools/test_preflight.py`)**:
  - Added 5 new targeted regression tests covering: missing individual source files blocking readiness, git status query failure reporting unknown, unknown process querying reporting UNKNOWN overall, unverified test-report commit reporting UNKNOWN overall, and dirty-run test reports blocking readiness.
  - All 19 preflight tests pass cleanly (0.66s).
- **Corrections to batched acceptance plan (`docs/M1-batched-acceptance.md`)**:
  - Treated proposed building dimensions (Rosewood Fire Station, Church nave, gymnasium) and interior safety in normal saves as unverified estimates.
  - Removed the outdoor front porch fallback; the user explicitly declined outdoor testing risk due to zombie hazards.
  - Proposed a fresh isolated sandbox save configured with zero zombies (`Zombie Population = None`) for spacious testing, eliminating infection and combat risks.
  - Described completing acceptance in a single game process launch as an operational goal conditional on advance case preparation, rather than an unconditional guarantee.
- **Automated test suite (172 passing checks + 11 runner self-tests)**:
  - `tools/run_tests.py`: 153 checks passing across 6 suites (29 foundation + 15 engine adapter + 8 checkpoint readback + 54 command + 33 console + 14 driver = 153 checks).
  - `tools/test_runner.py`: 11 runner self-tests passing.
  - `tools/test_preflight.py`: 19 preflight tests passing.
- **State and ownership**:
  - Game is CLOSED (SAVED a, GameThread exited, no native window).
  - Runtime and saves untouched.
  - Checkout ownership is RELEASED to Codex. External AI remains strictly ON HOLD.

### Post-M1 bounded gameplay feature proposal: manual follow-player command (Gemini, 2026-10-05)

Gemini authored a concrete technical and operational proposal for the next bounded gameplay feature after M1 native acceptance (`docs/M1-next-feature-proposal.md`). Offline documentation only; no game launches, desktop automation, or runtime modifications:
- **Proposal Summary (`docs/M1-next-feature-proposal.md`)**:
  - *Observable player benefit*: Replaces repetitive micro-management of one-shot `walk here` commands with companion navigation. When activated via typed `follow`, mouse toolbar shortcut, or context menu, Sarah dynamically paths toward the player as they explore a room or base on the same floor, halting when the player stops and settling into an idle stance.
  - *Smallest implementation scope*: Reuses Sarah's minimal command dispatcher (`Commands.lua`) and engine adapter (`Engine.lua`). Avoids all PZNS jobs architecture, behavior trees, vehicle handling, door opening logic, and combat interrupts. Managed as a single active action (`self.active.command == 'follow'`) issuing throttled `adapter.walk` sub-actions.
  - *Geometry & limits*:
    1. *Inner deadzone ($r \le 2.0$ tiles)*: Prevents pathing into the player's occupied square, collision pushing, and animation jitter; Sarah remains idle while close.
    2. *Repath band ($2.0 < r \le 8.0$ tiles)*: Dispatches `adapter.walk` to an open adjacent square when the player moves away.
    3. *Leash limit ($r > 8.0$ tiles)*: Fails closed and disengages with feedback (`Player out of range (>8 tiles); follow disengaged.`) if the player sprints away.
    4. *Floor limit ($sz \neq tz$)*: Disengages immediately if the player changes floors (stairs unverified).
  - *M0 travel suspension interaction*: Disengagement at 8 tiles ensures Sarah is stationary long before reaching the 32-tile boundary where `adapter.shouldUnload` unloads her to checkpoint storage.
  - *Lifecycle & Teardown*: Volatile in-memory state only. Canceled immediately on Sarah death, player death, unload, controller/NPC replacement, or session reset (`Commands:reset()`). Never saved to disk or binary checkpoints; Sarah restores idle upon reload.
  - *Native API analysis*: Grounded in verified APIs (`ISWalkToTimedAction`, `ISTimedActionQueue`, `isFree(false)`, `getGridSquare()`). Strictly excludes unverified APIs (`IsoPlayer:setSneaking()`, `PZNS_JobCompanion`, vehicle boarding, automatic door opening, teleportation).
  - *Dependencies on remaining M1 gates*: Blocked until gates R1–R8 in `docs/M1-batched-acceptance.md` pass natively in Codex (movable console, click isolation, position retention, resolution adaptation, distance refusal, red context-menu refusal, post-reload movement, and session reset).
  - *Verification strategy*: Defines 9 offline unit tests in `tools/test_commands.py` and a 6-step native acceptance protocol in `SarahSpaciousCase`.
  - *Implementation prompt*: Provides a ready-to-copy implementation prompt for Codex review once M1 acceptance is complete and user authorization is granted.
- **Automated test suite (172 passing checks + 11 runner self-tests)**:
  - `tools/run_tests.py`: 153 checks passing across 6 suites (29 foundation + 15 engine adapter + 8 checkpoint readback + 54 command + 33 console + 14 driver = 153 checks).
  - `tools/test_runner.py`: 11 runner self-tests passing.
  - `tools/test_preflight.py`: 19 preflight tests passing.
- **State and ownership**:
  - Game is CLOSED (SAVED a, GameThread exited, no native window).
  - Runtime and saves untouched.
  - Checkout ownership is RELEASED to Codex. External AI remains strictly ON HOLD.

### Bounded manual follow-player implementation and offline verification (Gemini, 2026-10-05)

Gemini implemented bounded manual follow-player behavior offline across `Commands.lua`, `Console.lua`, `SarahFoundation.lua`, and `UI.json`, corrected `docs/M1-next-feature-proposal.md`, added dedicated test suite `tools/test_follow.py` (28 checks), and updated the unified test runner (offline only; no game launches, desktop automation, or runtime modifications):
- **Follow dispatcher architecture (`Commands.lua`)**:
  - *`follow` command*: Executes via existing dispatcher. Registers active follow action with session `token`, `session`, `stepGen` counter, and private controller/NPC ownership.
  - *Inner deadzone ($r \le 2.0$ tiles)*: When Sarah is within 2.0 tiles of the player on the same floor, remains idle in follow mode without dispatching redundant walk actions.
  - *Adjacent candidate targeting ($2.0 < r \le 8.0$ tiles)*: Evaluates all 8 adjacent neighbors to player square. Candidate sorting calculates distance from candidate tile center to Sarah with integer tile-center alignment (`snx, sny`), selecting the closest valid candidate. Fails cleanly if all adjacent squares are blocked.
  - *Step generation guard (`stepGen`)*: Monotonic step counter prevents late callbacks from superseded or cancelled steps from mutating active state.
  - *Sequential steps & cooldown*: Sub-walk steps complete into idle stance with 15-tick cooldown before subsequent step dispatch.
  - *Leash limit ($r > 8.0$ tiles)*: Evaluated every tick independently of throttling; cancels follow immediately with `player out of range (>8 tiles)` and halts engine timed action.
  - *Floor boundary ($nz \neq pz$)*: Cancels follow immediately mid-stride if player changes floors.
  - *Lifecycle invalidation*: Sarah death, player death, unload, controller/NPC replacement, or observation failure cancels follow immediately.
  - *Stop integration & mid-stride cancellation*: User `stop` command immediately cancels follow and halts engine movement.
  - *Stop failure safety*: If engine stop fails, sets `self.stopFailed` and blocks replacement movement until stop recovers or session resets.
  - *Synchronous callback hardening*: Handles immediate step completion and immediate step failure safely without nil indexing or false running states.
  - *Session reset*: Cancels active follow, increments session token, resets visible request sequence counter to 0, and clears history.
- **Console integration (`Console.lua`, `UI.json`)**:
  - Added `[Follow]` shortcut button between `[Walk Here]` and `[Stop]` in Sarah Console panel.
  - Toolbar geometry updated to 7 non-overlapping buttons across 560px width with 6px gaps: `Help` (60px), `Status` (68px), `Inventory` (84px), `History` (72px), `Walk Here` (84px), `Follow` (72px), `Stop` (60px).
  - Small-screen layout and click isolation updated to ensure all 7 buttons remain fully reachable and never initiate accidental dragging.
  - Added `"UI_SarahConsole_Follow": "Follow"` to `Translate/EN/UI.json`.
- **Context menu integration (`SarahFoundation.lua`)**:
  - Added world context menu option `Sarah: follow` routing through `SarahConsole.getDispatch():execute("follow")` with visible notifications.
- **Proposal corrections (`docs/M1-next-feature-proposal.md`)**:
  - Updated status to OFFLINE IMPLEMENTATION AUTHORIZED while keeping native acceptance strictly pending.
  - Corrected Section 4.1: removed claim that player-occupied tiles fail `isFree(false)`; framed adjacent targeting and 2-tile deadzone as an intentional spatial spacing policy.
  - Corrected Sections 2.1 & 7.2: removed unsupported crash/clipping claims, noting unverified status in B42 and out-of-scope boundaries.
- **Follow automated test suite (`tools/test_follow.py`)**:
  - 28 automated offline unit tests covering: help listing, busy rejection against walk and follow, inactive Sarah rejection, missing coordinate rejection, floor difference rejection, initial leash rejection, deadzone idle stance, repath dispatch, candidate sorting with blocked fallback, no-valid-target failure, read-only commands during follow, repath on tick, sequential steps and cooldown, leash break mid-stride, floor change mid-stride, Sarah death/unload invalidation, controller replacement invalidation, stop cancellation mid-stride, idle stop cancellation, stop failure blocking and recovery, path failure callback cancellation, 600-tick step timeout, stale callback defusing, synchronous completion/failure safety, session reset, and `requestFollow` method.
- **Automated test suite (211 total passing checks)**:
  - `tools/run_tests.py`: 181 checks passing across 7 suites (29 foundation + 15 engine adapter + 8 checkpoint readback + 54 command + 33 console + 14 driver + 28 follow = 181 checks in 0.28s).
  - `tools/test_runner.py`: 11 runner self-tests passing.
  - `tools/test_preflight.py`: 19 preflight tests passing.
- **State and ownership**:
  - Game is CLOSED (SAVED a, GameThread exited, no native window).
  - Runtime and saves untouched.
  - Checkout ownership is RELEASED to Codex. External AI remains strictly ON HOLD.

### Follow-player defect hardening: player death observation and step callback retirement (Gemini, 2026-10-05)

Gemini resolved both follow defects identified during Codex review (offline only; no game launches, desktop automation, or runtime modifications):
- **Player death observation (`Observations.lua`)**:
  - Added safe `isCharacterDead(char)` helper inspecting `char:isDead()` via `pcall` as well as boolean flags (`dead`, `isDead`, and `alive`).
  - `Observations.read(controller, player)` now sets `data.playerDead = dead`, `data.playerAlive = not dead`, and attaches `dead`, `isDead`, and `alive` boolean properties to `data.player` alongside `{x, y, z}` coordinates.
  - Fully backward-compatible: preserves existing observation consumers expecting numeric coordinates without leaking engine handles.
- **Player death enforcement (`Commands.lua`)**:
  - Added `isPlayerDead(data)` helper inspecting `data.playerDead`, `data.player.dead`, `data.player.isDead`, and `data.player.alive`.
  - Follow activation in `execute('follow')` rejects immediately with `Player is dead; cannot follow.` (state: `rejected`, summary: `Player dead`).
  - Active follow ticks in `checkLifecycle()` and `tickFollow()` immediately cancel active follow with `player dead` and halt engine timed actions via `invokeStop`.
  - Covers both in-motion walking steps and close-range deadzone idle stances.
- **Completed-step callback retirement & identity enforcement (`Commands.lua`)**:
  - `dispatchFollowStep` now flags each step as retired upon first terminal callback (`stepRetired = true`) and increments `self.active.stepGen = self.active.stepGen + 1` upon retirement.
  - Symmetrical controller/NPC identity checks (`currentOwner == nil` -> `controller unavailable`, `currentOwner ~= self.active.owner` -> `controller replaced`, `currentNpc == nil` -> `npc unavailable`, `currentNpc ~= self.active.npc` -> `npc replaced`) and `checkLifecycle()` enforced identically on both `onStepComplete` and `onStepFail`.
  - Step retirement defuses late failures during idle/cooldown intervals (`cb_fail` during cooldown is ignored, follow remains active in cooldown).
  - Step retirement defuses duplicate completion callbacks during cooldown (`cb_complete` during cooldown is ignored and does not reset cooldown).
  - Stale callbacks from earlier actions (after user `stop` or restarted `follow`) or previous sessions (after `reset()`) cannot mutate active follow state or cancel replacement actions.
  - Synchronous walk callback failures increment `stepGen` and retire the step immediately.
- **Follow regression suite expanded (`tools/test_follow.py`)**:
  - Added 8 new regression tests (suite now 36 tests):
    1. Test 29: Follow activation rejected when player is dead.
    2. Test 30: Player death during walking step cancels follow and halts engine.
    3. Test 31: Player death during close-range waiting (deadzone) cancels follow.
    4. Test 32: Step completion followed by late failure during cooldown is defused.
    5. Test 33: Duplicate step completion during cooldown does not reset cooldown.
    6. Test 34: Callback identity disappearance and replacement cancel follow consistently on both callbacks (controller replacement, controller disappearance, NPC replacement, NPC disappearance).
    7. Test 35: Stale callbacks after stop/restart and session reset cannot affect new actions.
    8. Test 36: `Observations.read` extracts player liveness safely for alive and dead player.
- **Automated test suite (219 total passing checks)**:
  - `tools/run_tests.py`: 189 checks passing across 7 suites (29 foundation + 15 engine adapter + 8 checkpoint readback + 54 command + 33 console + 14 driver + 36 follow = 189 checks).
  - `tools/test_runner.py`: 11 runner self-tests passing.
  - `tools/test_preflight.py`: 19 preflight tests passing.
- **State and ownership**:
  - Game is CLOSED (SAVED a, GameThread exited, no native window).
  - Runtime and saves untouched.
  - Checkout ownership is RELEASED to Codex. External AI remains strictly ON HOLD.

### Follow-player status distinctions and asynchronous feedback (Gemini, 2026-10-05)

Gemini completed offline implementation and automated verification of user-facing follow status distinctions and asynchronous failure feedback across `Commands.lua`, `Console.lua`, and `Observations.lua` (offline only; no game launches, desktop automation, or runtime modifications):
- **Follow status distinctions (`Commands.lua`)**:
  - *Following while walking*: While Sarah is executing a sub-walk step toward the player, `status` command reports `Action: #<id> follow (running)` followed by `Follow: following while walking to (x, y, z)`.
  - *Follow engaged but waiting within range*: Within 2 tiles of the player on the same floor, `status` command reports `Action: #<id> follow (running)` followed by `Follow: follow engaged but waiting within range`.
  - *Follow disengaged with reason*: After leash break (>8 tiles), floor change, player death, path failure, or lifecycle invalidation, `status` reports `Action: idle (last: #<id> cancelled)` followed by `Follow: disengaged (<reason>)`.
  - *Engine stop failure warning*: If an engine stop fails (`self.stopFailed`), `status` appends `Warning: engine stop failed (<reason>); movement blocked pending recovery.`. Subsequent movement commands (`follow`, `walk here`) are rejected until a successful stop recovers engine state. Upon recovery, output explicitly confirms `Prior engine stop failure cleared; movement recovered.` and never falsely claims "Sarah stopped" while a failure persists.
- **Asynchronous one-time failure feedback (`Commands.lua`, `Console.lua`)**:
  - *Notice queueing*: Out-of-band follow terminations (leash break >8 tiles, player death, path failure, lifecycle invalidation) enqueue structured notices `{id, command, state, message, isBad}` via `self.noticeQueue` in `Commands.lua`. Manual user stops do not enqueue notices.
  - *Immediate delivery on tick*: `Console.lua` drains notices via `state.dispatch:consumeNotices()` during `state.tick()`.
    - If console panel is open: appends notification message and `#<id> cancelled` to history without requiring user polling via `status` or `history`.
    - Regardless of panel visibility: triggers in-world halo text via `SarahFoundation.notify(player, notice.message, notice.isBad)` if available.
  - *Single reporting & no replay*: Notice queue is emptied upon consumption. Closed console delivers in-world halo feedback; reopening the panel later starts clean without replaying notifications or executing commands.
  - *Session reset cleanup*: Quitting to main menu or session reset clears `self.noticeQueue = {}`, preventing notification leakage into new sessions.
  - *Safe query commands*: `status` and `history` remain strictly read-only and free of gameplay side effects.
- **Defensive safety & coordinate validation (`Observations.lua`, `Commands.lua`)**:
  - *Player liveness query safety*: `checkCharacterLiveness(char)` inspects `isDead()` via `pcall` and safely checks boolean properties; returns `'unknown'` if queries fail or throw. Follow activation and ticks require confirmed `isPlayerAlive(data)`; unconfirmed liveness rejects activation and cancels active follow with `player liveness unknown`.
  - *Non-finite & invalid coordinate rejection*: `isValidNumber(n)` and `isValidCoord(x, y, z)` validate finite numbers (`n == n and n ~= math.huge and n ~= -math.huge`), safely rejecting `NaN`, infinite, missing, or non-numeric coordinates without arithmetic runtime errors.
- **Automated test suite (227 total passing checks)**:
  - `tools/test_follow.py` (expanded to 41 checks): added tests 37–41 covering status line distinctions, unknown player liveness rejection, non-finite/NaN coordinate rejection without arithmetic errors, engine stop failure warning and recovery, and one-time notice queue consumption.
  - `tools/test_console.py` (expanded to 36 checks): added tests 34–36 covering open-panel asynchronous notice append and in-world feedback, closed-console in-world notification with clean non-replaying reopen, and session reset notice queue clearing.
  - `tools/run_tests.py`: 197 checks passing across 7 suites (29 foundation + 15 engine adapter + 8 checkpoint readback + 54 command + 36 console + 14 driver + 41 follow = 197 checks in 0.28s).
  - `tools/test_runner.py`: 11 runner self-tests passing.
  - `tools/test_preflight.py`: 19 preflight tests passing.
- **Batched acceptance plan updated (`docs/M1-batched-acceptance.md`)**:
  - Documented Gates F1–F6 in Section 2.3 and execution steps in Phase 6 as optional post-M1 companion smoke checks without altering M1 baseline gates R1–R8.
- **State and ownership**:
  - Game is CLOSED (SAVED a, GameThread exited, no native window).
  - Runtime and saves untouched.
  - Checkout ownership is RELEASED to Codex. External AI remains strictly ON HOLD.

### Follow status cooldown accuracy and asynchronous stop failure reporting (Gemini, 2026-10-05)

Gemini completed offline hardening of follow status reporting during cooldown and asynchronous stop-failure notification handling across `Commands.lua` and `tools/test_follow.py` (offline only; no game launches, desktop automation, or runtime modifications):
- **Follow status cooldown accuracy (`Commands.lua`)**:
  - `status` command evaluates observed NPC and player coordinates during follow cooldown / idle:
    - Reports `Follow: follow engaged but waiting within range` only when verified on the same floor (`nz == pz`) and within the 2-tile inner deadzone (`dx*dx + dy*dy <= 4.0`).
    - Reports `Follow: follow engaged but waiting before next walk` when the player is outside the deadzone during cooldown, on a different floor, or coordinates are unavailable.
  - `status` command remains strictly read-only: no queue changes, no state or cooldown advancement, and no notification consumption.
- **Asynchronous stop failure handling (`Commands.lua`)**:
  - `cancelActive(reason, isUserStop)` captures `invokeStop` return values (`stopOk, stopErr`) before formatting asynchronous notifications.
  - If engine stop fails (`not stopOk`), sets `self.stopFailed = stopErr`, `action.stopFailed = self.stopFailed`, and `self.lastAction.stopFailed = self.stopFailed`.
  - Enqueues exactly one notice in `self.noticeQueue` carrying original action ID, command, state, reason, and unified message: `Follow disengaged: <reason>. Warning: engine stop failed (<stopErr>); movement blocked pending recovery.`
  - Physical halt is never falsely reported as successful while an engine stop failure persists.
  - Movement commands (`follow`, `walk here`) remain blocked until a later successful `stop` command clears `self.stopFailed` and explicitly reports: `Prior engine stop failure cleared; movement recovered.` and `Sarah stopped; nothing active.`
  - Defuses stale step callbacks: `checkStepCallback` sets `stepRetired = true` immediately upon detecting stale action ID/token, mismatched session, or stale step generation, defusing subsequent callbacks before lifecycle checks.
- **Automated test suite (232 total passing checks)**:
  - `tools/test_follow.py` (expanded to 46 checks): added tests 42–46:
    1. Test 42: Follow status during cooldown distinguishes inside vs outside deadzone, floor change, and disengagement on missing player.
    2. Test 43: Repeated status calls leave follow state, cooldown, step ticks/gen, and queues completely untouched.
    3. Test 44: Asynchronous leash break combined with failed engine stop enqueues one unified notice carrying reason, request ID, stop failure, and blocked movement warning.
    45. Test 45: Asynchronous path failure combined with failed engine stop enqueues one unified notice carrying path failure reason, request ID, and stop failure warning.
    46. Test 46: Successful recovery clears failure and stale callbacks after recovery are ignored.
  - `tools/run_tests.py`: 202 checks passing across 7 suites (29 foundation + 15 engine adapter + 8 checkpoint readback + 54 command + 36 console + 14 driver + 46 follow = 202 checks in 0.28s).
  - `tools/test_runner.py`: 11 runner self-tests passing.
  - `tools/test_preflight.py`: 19 preflight tests passing.
- **State and ownership**:
  - Game is CLOSED (SAVED a, GameThread exited, no native window).
  - Runtime and saves untouched.
  - Checkout ownership is RELEASED to Codex. External AI remains strictly ON HOLD.




Batched follow native session IN PROGRESS: Codex owns checkout. Game confirmed closed before backup/deployment. Backup: runtime\backups\batched-follow-20261005-190349 (existing world, Previous-mod, keys/options/selection). Reviewed five changed production files deployed from 5fa6b9c. Next: prepare fresh isolated zero-zombie case through native sandbox UI. No native acceptance claimed. Restore only game-closed after preserving latest state.

Fresh isolated Sandbox/2026-10-05_19-04-21 created through native UI; Zombie Count None and Respawn None visually confirmed. Game running, player inside starting house; Sarah not yet spawned. Next user positions player on clear flat space, then clean exit/backup of prepared case before acceptance.

Prepared Sandbox/2026-10-05_19-04-21 saved a and GameThread exited. Sarah ACTIVE npc=true localPlayerPreserved=true logged after manual spawn, but not visibly rendered before exit. Prepared-spacious backup preserved game-closed at runtime/backups/batched-follow-20261005-190349. Next reload/inspect visibility then UI gates.

Reloaded prepared case: Status #1 Sarah active/idle, player (8314.66,11690.41,0), NPC (8305.50,11689.50,0). Sarah was already spawned nearer the house, explaining absence from current view; no rendering failure established. Walk Here #2 correctly rejected target beyond 8 tiles. Automated title drag did not move panel; user drag needed to distinguish input limitation from UI defect.

Native batch progress: physical title drag passed (user); moved panel close/reopen retained position approximately (53,187). Context-menu distance refusal visibly displayed red Target is too far (maximum 8 tiles). Game running; next bring player nearer Sarah for follow activation. Future longer-range catch-up is desired by user, not implemented in this batch.

Native follow progress (Codex, 2026-10-05): Follow #5 accepted; Status #6 showed active follow waiting within range after Sarah moved from (8305.50,11689.50,0) to (8310.50,11689.50,0), near player (8311.31,11690.81,0). User subsequently walked and confirmed Sarah followed, with noticeable tracking delay. Implementation waits beyond 2 tiles, completes each current walk target before retargeting, and waits 15 eligible ticks between steps. Responsiveness concern recorded; no timing measurement or source adjustment. Follow remains engaged in running isolated sandbox; next verify Stop and no automatic resumption. Full native acceptance pending. Codex retains checkout ownership.

Native Stop #8 cancelled follow #7 and reported Sarah stopped. Status #9 confirmed Action idle (last #7 cancelled), Follow disengaged (stopped by user), player (8301.84,11678.75,0), NPC (8302.50,11679.50,0). Game was paused at initial capture; resumed via normal play before console/Stop. Sarah had reached player before Stop, so mid-stride cancellation is NOT established by this attempt. Console closed; next user movement checks no automatic follow resumption. Game remains running, Codex owns checkout.

Native batch update (Codex, 2026-10-05): user confirmed Sarah stayed put after manual Stop while player moved away; no automatic resumption observed. User then restarted Follow and moved beyond leash. Console visually inspected: Status #11 reports Sarah active, Action idle (last #10 cancelled), Follow disengaged (player out of range (>8 tiles)); player (8281.83,11679.61,0), NPC (8291.88,11679.50,0), approximately 10.05 tiles apart. Native leash cancellation/status PASS. Automatic notice timing, one-time delivery and no-replay are not established by this status screenshot. Game remains running PAUSED, console open at (53,187), Follow inactive. Mid-stride Stop and remaining batched gates pending; Codex retains ownership. No source or normal-save changes.

Native mid-stride Stop (user-operated, 2026-10-05): user followed the requested sequence: return near Sarah, activate Follow, move 3-4 tiles within the leash, press Stop while Sarah visibly walks, then move again. User reports it works like a charm. Recorded as user-observed PASS for mid-stride follow cancellation and sustained halt/no automatic resumption; no independent screenshot of the moving-to-stopped transition. Remaining batched acceptance and automatic notice/replay checks remain pending. Source unchanged; Codex retains checkout ownership. Last independently inspected game state was paused with console open; current pause/UI state not re-inspected.

Native F6 PASS (Codex visual inspection, 2026-10-05): after user ran beyond leash with console closed, screenshot showed red in-world Follow disengaged: player out of range (>8 tiles). Game paused with message visible. Resumed normally; halo expired. Context-menu console reopen displayed only initial command/binding headers, no replayed notice or automatic command. Moved panel position retained. Game running, console open; Follow cancelled. F5 open-panel delivery remains pending, F6 closed-panel feedback/no-replay accepted.

Same-process reload native check (Codex, 2026-10-05): Quit to main menu then Continue reloaded isolated sandbox; SESSION_RESET seen in local log. Console reopened centered at approximately (361,206), instead of retained (53,187): R8 PASS. Clean headers with no stale notice; Status restarted at #1 and reported Sarah active / Action idle, player (8268.49,11680.46,0), NPC (8279.50,11679.50,0). No follow restored. Console closed for user WASD check; R7 pending user reply. Game running; Codex owns checkout.

R7 PASS (user-operated, 2026-10-05): user confirmed WASD works after same-process Quit/Continue and mouse console Close. R8 centered reset and idle follow state independently observed before this reply. Remaining batch gates: R2 full control isolation coverage, R4 resolution adaptation, F1 walking status, F2 out-of-range cooldown wording, F5 open-console automatic notice; F4 stop failure remains offline-only unless naturally encountered. F6 accepted. Game remains running, no source changes; Codex retains ownership. Final game-closed snapshot still pending.

Native control coverage (Codex, 2026-10-05): centered console remained at (361,206) through Help #2 completed, Inventory #3 completed (4 items), History #4 completed (one entry each for #1-#3), input-field click, and empty Run #5 rejected Unknown command. Bulk automated type_text(status) produced no visible text, so typed Run acceptance remains pending. Attempted native window-corner drag did not resize the 1282x752 capture and instead delivered input at endpoint over Follow: #6 rejected Player is too far (maximum 8 tiles). No action started; no resizing acceptance claimed. Do not repeat automated corner drag. User physical resize or in-game Options needed for R4. Game running, console open centered; Codex owns checkout.

User typed status then clicked Run: visually verified one Status #7 completed, Sarah active / Action idle; console position unchanged at (361,206), entry cleared. Combined toolbar/input/Run/Close coverage now establishes R2 PASS for exercised controls without drag/duplicate requests. User resized native game capture from 1282x752 to 1080x636; console remained fully visible with title, output, all toolbar buttons, input and Run reachable. R4 partial PASS for this size; very-short-window height adaptation/top-edge recovery still unverified. Current game paused, console open, Sarah idle. Source unchanged, Codex owns checkout.

Compact native layout (Codex, 2026-10-05): user reduced game capture to 1264x270 (approximately 1248x238 client). Console shortened to available client height, top edge at client y=0; title/Close, scrolling output, all seven toolbar buttons, input and Run fully visible. Pending user-entered status was present; resumed game and clicked Run: #8 completed once, Sarah active / Action idle; entry cleared, panel unchanged. Confirms typed Run and compact layout/top clamp. R4 PASS for live shrink/height adaptation/control reachability; physical drag-away/recovery at this size still not separately exercised. Earlier #7 output was an already-completed status, not proof that a later pending input had run; this #8 is direct typed-Run evidence. Game running, console compact/open, Codex owns checkout.

Native batch checkpoint (Codex, 2026-10-05): open-console automatic cancellation output PASS: following #9, prior Status #10, then Follow disengaged: player out of range (>8 tiles). and #9 cancelled appended without any subsequent request. Halo on this particular open-panel event not captured; closed-panel halo previously verified. F5 panel-delivery accepted, exact latency/this-event halo unverified. F1 walking-status capture missed arrival; F2 outside-deadzone cooldown wording remains unverified; F4 engine-stop failure/recovery remains offline-only, no fault induced.

Game CLOSED via native window close; SAVED a and GameThread exited verified, no java/javaw processes. Final world, log, latestSave, options and key bindings preserved game-closed under runtime/backups/batched-follow-20261005-190349/Final-native. Existing survival case and normal profile untouched. Continue selects Sandbox/2026-10-05_19-04-21; Sarah last follow cancelled, session reset verified earlier. Codex retains ownership; no source changes. External AI ON HOLD.

Next: bounded offline Follow responsiveness proposal/implementation for Gemini, preserving 2-tile deadzone, 8-tile leash, single movement action, true completion, callback/session guards and reliable Stop. Remaining native wording and drag recovery checks must stay explicit; do not claim full acceptance. Current 202 suite checks +11 runner +19 preflight were verified before live deployment; docs-only checkpoint did not rerun them.

Gemini offline responsiveness handoff (2026-10-05): user authorized next coding task. Checkout ownership RELEASED to Gemini for bounded Follow responsiveness work; Codex will review after Gemini releases it. Game CLOSED; Final-native backup preserved. Starting implementation/evidence checkpoint 9a675d5. Scope: diagnose stale-target tracking and eligible-tick cooldown, implement a justified small improvement with offline regression tests, preserve all existing movement/Stop/lifecycle/leash safety. No launches, desktop automation, deployed runtime/save/settings changes, external AI, longer-distance movement or unrelated refactoring. Native responsiveness remains unverified until Codex tests. Full copyable instructions provided to user. Gemini must update shared notes, commit/push verified offline changes, then explicitly release ownership to Codex.
