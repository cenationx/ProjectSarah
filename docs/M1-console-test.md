# M1 read-only console slice A: 2026-10-04

IN PROGRESS: slice A native acceptance PASSED; slice B native idle-stop/history/session-reset smoke checks PASSED; active movement cancellation tested natively alongside slice C.
Slice C (bounded "walk here", completion tracking, stop cancellation, timeout, and lifecycle invalidation) IMPLEMENTED and hardened offline (146 automated checks across 6 suites plus 11 runner self-tests).
Sarah Console equipped with dedicated mouse-operated command shortcut buttons ([Help], [Status], [Inventory], [History], [Walk Here], [Stop], [Close]).
Native UI source inspected read-only against PZ 42.21.0 ISUI (callback signatures, hit areas, focus behavior, auto-scrolling, and stop accessibility verified; no code defects).
Native acceptance prepared in docs/M1-slice-c-checklist.md using console mouse buttons and human observation.
Commands/Observations/Console implement help, status, inventory, walk here, stop, and history. External AI remains strictly on hold.
Automated tests do not establish native input.

Game-closed SarahModuleCleanupCase, selections and keysB42.ini backed up to
`runtime/backups/console-before-20261004`. Separate SarahConsoleCase is the test
target. Preserve current state before any game-closed restore into a new case.
Installed files and normal profile are untouched. Console only opens in exact
isolated single-player profile. F9 named binding and context-menu fallback;
conflicting runtime bindings refuse keyboard open. No normal key file changes.

## Direct native evidence

- Menu fallback opened the panel, native input field focused and mouse Close
  removed it. Opening did not change normal game speed.
- Individual native letter presses entered `status`, `help` and `inventory`.
  Enter submitted status/inventory; Run submitted help. Bulk Unicode typing did
  not enter text in this game, so individual presses were used and visually checked.
- Status reported active Sarah, player 10768/10271/0 and NPC 10770.47/10271.15/0.
  Inventory reported four items: Bandage and three equipped clothing items.
- Observational samples throughout showed one tagged Sarah, preserved local
  player, focused entry while open and unchanged player position while typing
  `status` (including movement-bound S/A). Focus cleared after mouse close.
- F9 was registered as runtime key 67 and visible in the game's key settings.
  Initial settings exposed untranslated labels; added English UI translations.
- Automated F9/Escape did not close the first panel. Installed engine inspection
  showed ordinary key callbacks are bypassed during native text entry. Final code
  uses raw game-thread key edges, consumes the closing release and checks runtime
  primary/alternate conflicts. Eight simulated checks cover hold-repeat, focused
  Escape, rebind, collisions, text-entry exclusion, reset, reload and output bounds.
- Automated F7 was also missed by the vanilla rebind dialog. Physical key delivery
  and native rebind persistence cannot be declared passed from those attempts.

The initial large list font/fixed row height clipped the final result. Final code
uses native font metrics and scroll padding. After full restart, inventory harness
submission returned four items with the same NPC/player and unchanged position.
Actual typed help/Enter then produced scrolling output with the final completion
row fully visible (`console-final-scroll-live.png`).
First live state/log preserved locally as First-live-before-repair and
runtime/console-first-console.txt. Screenshots show that initial native status and
inventory; they are historical evidence, not final-font acceptance.

## Remaining gate

The user completed the requested physical F9 open, status/Enter, F9 close check.
Probe samples corroborated panel=true/focused=true followed by panel=false/focused=false,
with one Sarah and unchanged local player/position. This is a user-operated check;
no screenshot of the user's status submission was captured. Full restart restored
one Sarah from a, and the console started closed before that check.

Physical Escape fix has since passed native retesting (first Escape closes console without menu; subsequent Escape opens menu; see below). Still open: native hold-repeat, rebind/conflict persistence, English labels in Options, restored movement input, and same-process menu/world teardown. See ordered checklist in docs/M1-native-checklist.md. These
have simulated coverage where applicable, not complete native acceptance.
Do not add stop/walk or claim M1 complete before this gate is resolved. AI stays
on hold. Temporary probe's `Console test: inventory` is explicitly a harness
submission for final rendering checks, not evidence of physical typing.

Final state: game closed, saved b; final world backed up as Final-console. Probe
disabled outside the mod; production modules deployed. Raw final log retained
locally; sanitized Sarah-only summary in evidence/console-live-summary.txt. Normal
profile console still 18675 bytes / 2026-10-04 04:03:05; installed game untouched.

## Native follow-up: Codex session 2026-10-04

User reports physical F9 shows the console and Escape works in the isolated
SarahConsoleNativeCase. Record this as user-operated F9 open / Escape close
confirmation. Hold duration/repeat and absence of a pause menu after closing
were not explicitly reported, so those details remain pending. Rebind/conflict
persistence, English Options labels, movement restoration and same-process
console teardown remain open. No production code changes from this result.

### Correction: native Escape failure

The user's subsequent precise report supersedes "Escape works" above: first
Escape opens the game menu; second Escape closes the console. Slice A Escape
acceptance FAILS. Expected first Escape close without pause-menu activation.
Underlying cause is unverified. Existing simulated test does not cover the native
ordering/state that produced this result. Codex observed console absent afterward,
then closed game normally: SAVED a / GameThread exited. NativeCase preserved in
runtime/backups/console-native-20261004/After-escape-check. No teardown acceptance
is inferred from closing the whole process. Rebind/conflict/labels/movement,
hold-repeat and same-process world/menu cleanup remain pending.

## Escape fix attempt: Claude session 2026-10-04 (NATIVE-UNVERIFIED)

Code, engine/API inspection and automated tests only; the game was not launched and no
save, backup, setting or deployed mod was touched. Inspection: the pause menu is the
vanilla global `ToggleEscapeMenu` (installed MainScreen.lua) on `OnKeyPressed`, which
the engine raises on key release unless `eatKeyPress`, a consuming UI element or native
text entry stops it. The earlier `eatKeyPress`-only fix did not hold natively; the exact
engine ordering is not established. `Console.lua` now also arms a one-shot swallow when
Escape closes the console and routes `OnKeyPressed` through `SarahConsole.guard`, which
drops that single Escape release and otherwise calls the original handler. Expiry is 5
ticks after Escape is up; reload restores the original handler; nothing is wrapped if it
is missing. Automated: 71 checks (27+13+8+12+11) pass; 3 new simulated console cases.
These do NOT prove native behavior. Native retest by Codex/user is required: deploy
production source game-closed after backup, press Escape once with the console open, and
confirm the console closes and the pause menu does not appear. If it fails, capture raw
ESC state, OnKeyPressed calls and tick order with a temporary probe.

## Escape fix native retest PASS (user-operated, 2026-10-04)

User confirmed both requested results: physical F9 then Escape closes console
without game menu; later Escape opens normal menu. Probe records panel true then
raw Escape/panel false/swallow true, expiry back to false and guard=true.
This establishes bounded Escape behavior, not all remaining slice A acceptance.
Physical Escape stopped Computer Use in the prior turn; result is still valid.
See desktop-input-diagnostic.md for separate automated special-key limitation.

## Movement restoration PASS (user-operated, 2026-10-04)
User completed requested walking checks after Escape close and mouse Close and
reported movement fine. No stuck focus/movement reported. Screenshot afterward
shows changed world framing/player location; no coordinate probe deployed.
Hold-repeat remains pending explicit confirmation; no additional gate inferred.


## Hold-repeat and English labels PASS (2026-10-04)
User confirms holding F9 then releasing leaves console open, following the two-second instruction. Codex visually verified native Options displays Project Sarah, Sarah Console and F9 without untranslated labels. No probe used. F7 rebinding dialog prepared; assignment/apply/runtime/persistence checks still pending.


F7 rebind follow-up: user reports F7 works. Native rebound-key functionality confirmed; old F9 inactivity, full-restart persistence and updated console key text remain pending. Game closed normally and saved b before Gemini handoff.

# Native restart acceptance (2026-10-04)

Same-process native PASS: PID 41784 retained identity/start time through menu exit
and Continue; no orphaned console visible on main menu. SAVED a, SESSION_RESET,
ACTIVE npc=true worn=3 localPlayerPreserved=true / RESTORED a. User confirms F7
opens/closes after reload. Callback counts/UIManager membership not instrumented.

User-operated PASS after full-process restart: F7 opens/closes, console toggle
label displays F7, old F9 inactive. Persisted isolated binding key:65. NativeCase
RESTORED b in process 41784; ACTIVE npc=true worn=3 localPlayerPreserved=true.
Prelaunch backup: runtime/backups/codex-resume-20261004-234837.

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
## M1 slice B automated validation (2026-10-05)

Gemini implemented and validated slice B cancellation and bounded history:
- `Commands.lua` additions:
  - `stop`: Cancels active action (`cancelActive`), clears active tracking, invokes `stopCallback` safely on game thread (`SarahFoundation.controller.adapter.stop`), reports cancelled action ID/name, and is harmless on repeated calls when idle (`Sarah stopped; nothing active.`). Clean status on dead/unloaded states.
  - Action lifecycle & tokens: `beginAction(name, details)` assigns a unique incrementing request `id` and generation `token`. `cancelActive(reason)` transitions state to `'cancelled'`. `completeAction(id, token, success, message)` verifies active existence, matching ID, and matching token. Stale completions from cancelled, timed out, or reset actions are rejected with `'stale or cancelled'`.
  - Request & result history: Bounded ring buffer `self.history` capped at `maxHistory = 30`. `getHistory()` returns shallow copies of records (`id`, `command`, `state`, `summary`) without exposing mutable engine handles.
  - `history` query command: Formats the last 10 commands with IDs, outcomes, and short summaries.
  - `status` command: Reflects active action (`Action: #<id> <command> (running)`), idle state with last action summary (`Action: idle (last: #<id> <state>)`), or idle.
  - `help` command: Documents `stop` and `history`.
- `Console.lua` additions:
  - Preserves dispatch instance across open/close cycles via `state.dispatch` / `getDispatch()`, avoiding sequence or history wipes when the UI panel closes.
  - Connected `stopSarah` callback to call `SarahFoundation.controller.adapter.stop(npc)` on the game thread.
  - Connected `state.reset` on session reset (`OnGameStart`, `OnMainMenuEnter`) to call `state.dispatch:reset()`, ensuring no active requests survive session boundaries.
  - Updated initial prompt banner to `Commands: help, status, inventory, stop, history. Enter submits.`
- Automated test coverage: 84 total passing checks (up from 71):
  - `tools/test_foundation.py`: 27 passing lifecycle/reload/event checks.
  - `tools/test_render.py`: 13 passing engine adapter/hysteresis checks.
  - `tools/test_checkpoint.py`: 8 passing readback token/cleanup checks.
  - `tools/test_commands.py`: 22 passing checks (10 new slice B tests: idle stop, repeat stop, dead/unloaded stop, active action registration, busy rejection, cancellation by stop, late-completion rejection, successful completion, stale token rejection, session reset cancellation, unload/death observation cancellation, history query and immutability).
  - `tools/test_console.py`: 14 passing checks (3 new slice B tests: panel stop execution, history command output formatting, session reset dispatch cleanup).

Native acceptance remains pending Codex live verification following the checklist in `docs/STATUS.md`.
## M1 slice B revision automated validation (2026-10-05)

Gemini addressed the review blockers and review corrections in slice B:
- Stop failure propagation: `invokeStop` checks exceptions and `false, reason` return values from the adapter stop callback. Invalidation of the request is preserved, while the stop command outcome accurately reflects `failed` when the engine stop fails.
- Independent lifecycle invalidation: `completeAction` revalidates Sarah's state and controller match before accepting completion. Rejects completion without requiring prior status queries if Sarah died or unloaded.
- Closed-console lifecycle monitoring: `Console.tick()` calls `dispatch:tick()` on every frame even when the UI panel is closed.
- Handle-free public observations: `Observations.read()` exposes strictly copied data (`state`, `player`, `npc`, `reason`, `inventory`) without exposing mutable engine handles (`controller`, `adapter`, `npc`).
- Decoupled action ownership & identity provider: `Commands.new(observe, stopCallback, identityProvider)` accepts a private identity provider closure or token. `Console.lua` supplies `function() return SarahFoundation and SarahFoundation.controller end` as identity provider and checks `action.owner` in `stopSarah` to reject stops targeting stale controllers.
- Action record snapshot protection: Action records returned by `beginAction`, `cancelActive`, and `getHistory` are shallow-copied snapshots that protect internal dispatch state (`self.active`, `self.history`) from caller mutation.
- Automated tests: Increased from 84 to 94 passing checks:
  - `tools/test_foundation.py`: 27 checks
  - `tools/test_render.py`: 13 checks
  - `tools/test_checkpoint.py`: 8 checks
  - `tools/test_commands.py`: 31 checks (was 22, then 29; added regression tests for handle-free observations and controller identity stop scoping)
  - `tools/test_console.py`: 15 checks (was 14)

Native acceptance remains pending Codex live verification.

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

## M1 slice C automated validation and review revision (2026-10-05)

Gemini implemented, revised per Codex review, and validated slice C bounded movement ("walk here"), completion tracking, and cancellation:
- `Commands.lua`:
  - `walk here`: Parses command, validates observation state, resolves player or specified target coordinates, verifies finite numbers, same floor, max 8-tile distance, and free square.
  - Already-at-target: If Sarah is already at target, returns immediate `completed` without starting a redundant action.
  - Busy check: Refuses second action if an action is currently active.
  - Active tracking: Registers action with request ID, session token, and dual controller+NPC identity (`owner` and `npc`). Status command reflects `Action: #<id> walk here (running)`.
  - True arrival verification: `onComplete` verifies Sarah's observed position against target square before marking completed; reports failure (`Stopped before target`) if stopped early.
  - Dual-identity scoping & unambiguous private identity contract: Actions are scoped to both the originating controller and NPC. `Commands:getIdentity()` directly unpacks `(controller, npc)` from `identityProvider()` without treating `{npc=npc, adapter=adapter}` as a wrapper table or querying `ctrl.controller` (which yielded nil). Preserves exact controller and NPC references privately without exposing handles through public observations. Replacement of the NPC or controller immediately invalidates active work (`'npc replaced'` or `'controller replaced'`). Late completion callbacks check identity before inspecting positions and reject without evaluating arrival against replacement entities.
  - Stop integration: `stop` command cancels active walking and invokes engine stop (`adapter.stop(npc)`) on game thread. Stale callbacks from cancelled actions or mismatched identities are safely rejected; replacement controllers and NPCs are left untouched.
  - Timeout: 600-tick timeout cancels active walk and invokes engine stop.
  - Lifecycle invalidation: Background unload, death, controller replacement, or NPC replacement invalidates active walk immediately.
  - `requestWalk(target)`: Exposes direct programmatic dispatch.
- `Console.lua`:
  - `walkSarah` and `stopSarah` callbacks scope to both controller and NPC identity (`action.npc` and `action.owner`), refusing with `stale npc` or `stale controller` and leaving replacement controllers and NPCs untouched.
  - Identity provider contract: returns `controller, controller and controller.npc` directly.
  - Exposes `state.getDispatch = getDispatch`.
  - Updated prompt line to include `walk here`.
- `SarahFoundation.lua`:
  - World context menu `"Sarah: walk here"` strictly routes through `SarahConsole.getDispatch():execute('walk here')`.
  - Removed direct `ISTimedActionQueue` fallback entirely: untracked walks are never queued.
  - Added visible feedback via `state.notify(player, message, isBad)` (logging to console, HaloTextHelper/Say, and recording `state.lastFeedback`) when console/dispatch is unavailable or when walk is rejected/failed/running/completed.
- `Engine.lua`:
  - `SarahWalkAction` derived from `ISWalkToTimedAction` via `getWalkActionClass()`, hooking `perform()` and `stop()`.
  - `adapter.validateTarget(npc, target)` and `adapter.walk(npc, square, onSuccess, onFail)`.
- Automated test coverage: 120 total passing checks (up from 118, originally 94):
  - `tools/test_foundation.py`: 29 passing checks.
  - `tools/test_render.py`: 15 passing checks (validateTarget and adapter.walk).
  - `tools/test_checkpoint.py`: 8 passing readback token/cleanup checks.
  - `tools/test_commands.py`: 49 passing checks (+1 new: production controller shape `{npc=npc, adapter=adapter}` preserves identity, controller replacement with same NPC cancels old action, rejects late completion, and isolates replacement from stale stop operations).
  - `tools/test_console.py`: 19 passing checks (+1 new: console dispatch rejects controller replacement with same NPC, cancelling action and leaving replacement controller untouched).

Native acceptance remains pending Codex live verification following the checklist in `docs/STATUS.md` and `docs/M1-slice-c-checklist.md`.

## M1 slice C lifecycle audit, hardening, and native checklist (2026-10-05)

Gemini completed the lifecycle audit and hardening of M1 command and action boundaries (offline only; no game launches or desktop control):
- **Lifecycle audit**:
  - Traced Commands.lua, Console.lua, Engine.lua, and SarahFoundation.lua together across request start, adapter rejection, completion, failure, stop, timeout, controller/NPC replacement, and session teardown.
  - Inspected PZ 42.21.0 engine `IsoGridSquare.isFree(false)`: passes `bCountOtherCharacters=false`, verifying that player occupancy does not prevent Sarah from navigating to the player's square.
- **Reproduced defect and hardening: Synchronous callbacks**:
  - Reproduced defect where an adapter or timed action calling `onFail` or `onComplete` synchronously during `invokeWalk()` left `execute('walk here')` reporting `running` and recording a `running` history entry, even though the action had already finished and cleared `self.active`.
  - Fix: Pre-registers `running` history before invoking walk callback; updates history to `failed` if `walkOk` is false; accurately returns `action.state` and `action.summary` in `result` if the action finished synchronously during `invokeWalk()`.
- **Reproduced defect and hardening: Session reset sequence and controller availability**:
  - `Commands:reset()` resets `self.sequence = 0`, ensuring new sessions cleanly begin request numbering at `#1`.
  - Symmetrical controller availability: `currentOwner == nil` triggers `'controller unavailable'` action invalidation in `checkLifecycle()` and `completeAction()`.
- **Automated test suite (123 passing checks)**:
  - Added 3 regression unit tests in `tools/test_commands.py` (52 checks total):
    1. `walk here synchronous failure during start updates history and returns failed outcome`.
    2. `walk here synchronous completion during start updates history and returns completed outcome`.
    3. `session reset resets sequence counter and controller unavailable invalidates active action`.
  - Full suite: 29 foundation + 15 engine adapter + 8 checkpoint + 52 command + 19 console = 123 checks passing.
- **Native acceptance checklist**:
  - Created `docs/M1-slice-c-checklist.md` with ordered 7-gate native testing procedure:
    1. Normal walk arrival and tracking (`walk here` -> running -> arrival -> completed).
    2. Already-at-target detection (`Already at target` immediate completion without movement).
    3. Target refusal (> 8 tiles distance limit rejection).
    4. Live in-motion stop cancellation (`walk here` -> in motion -> `stop` -> halted -> cancelled).
    5. Immediate walk resumption after cancellation.
    6. Context menu "Sarah: walk here" routing and visible onscreen feedback.
    7. Session reset and clean reload (`SESSION_RESET`, history reset, request `#1`).

Checkout ownership is RELEASED to Codex for native testing following `docs/M1-slice-c-checklist.md`. External AI remains strictly ON HOLD.

## M1 slice C session-reset callback collision fix and checklist reconciliation (2026-10-05)

Gemini resolved the session-reset callback collision reproduced by Codex and reconciled native checklist expectations (offline only; no game launches or desktop control):
- **Defect resolution**:
  - `Commands:reset()` preserved `self.sequence = 0` so new sessions cleanly begin request numbering at `#1`, while removing `self.token = 0` so action tokens advance monotonically across session boundaries.
  - `Commands:completeAction(id, token, success, message, owner, npc, session)` validates `session` against `self.active.session`, rejecting stale callbacks across resets.
  - Pre-checked action token and session in `onComplete` and `onFail` before inspecting controller/NPC identities or querying observations.
- **Native checklist corrections (`docs/M1-slice-c-checklist.md`)**:
  - Gate 6: Corrected onscreen feedback expectation to actual dispatch response `Walking to (<tx>, <ty>, <tz>).` (matching `Commands.lua` and `SarahFoundation.lua`).
  - Gate 7: Adjusted post-reset command sequence to type `help` first (`#1 help: completed`), then `history` (`#1 help: completed` and `#2 history: completed`), since typing `history` first consumed request `#1`.
- **Automated test suite (125 passing checks)**:
  - Added 2 new regressions in `tools/test_commands.py` (54 command checks total, 125 total across 5 suites):
    1. `old failure callback after session reset with same controller and reused visible request ID is rejected`.
    2. `old completion callback after session reset with same controller and reused visible request ID is rejected`.
  - All 5 test suites pass: 29 foundation + 15 engine adapter + 8 checkpoint readback + 54 command + 19 console = 125 checks total.

Checkout ownership is RELEASED to Codex for native testing following `docs/M1-slice-c-checklist.md`. External AI remains strictly ON HOLD.

## Sarah Console mouse shortcuts and native UI inspection (2026-10-05)

Gemini implemented mouse-operated command buttons directly on the Sarah Console panel and inspected native UI interaction against installed PZ 42.21.0 ISUI source (offline only; no game launches, desktop automation, or runtime deployment):
- **Mouse shortcut toolbar in Sarah Console**:
  - Dedicated buttons for `Help`, `Status`, `Inventory`, `History`, `Walk Here`, and `Stop` along with `Close` and `Run`.
  - Every button executes through `executeCommand(commandText)` routing to `self.dispatch:execute()` and displays through unified history output, identical to typed entry.
  - Avoids unreliable desktop keyboard injection while allowing Codex to trigger commands and inspect results, with the user controlling character movement.
  - English translations added to `Translate/EN/UI.json` (`UI_SarahConsole_Help`, etc.) with `tr()` fallback.
- **Native UI source inspection (PZ 42.21.0 ISUI)**:
  - Inspected `ISButton.lua`, `ISScrollingListBox.lua`, `ISUIElement.lua`, and `ISTextEntryBox.lua` read-only.
  - Verified callback signatures: `ISButton:onMouseUp` invokes `self.onclick(self.target, self, ...)`. In `Console.lua`, buttons pass `target = self` (`Panel`), so `Panel.onShortcut*` receives `Panel` as `self`. The `Close` button passes `state.close` as `onclick` with `nil` target, cleanly cleaning up `state.panel`.
  - Verified hit areas: toolbar `y = 296, h = 26`, widths 72, 80, 96, 82, 102, 72; gaps 6-7px, 12px margins. 8px vertical clearance above and below toolbar; no overlaps with list box (`y: 42..288`) or text entry (`y: 330..356`).
  - Native `ISButton` auto-width check: Measured title widths + 10px are well within allocated button widths (15-30px clearance), preventing unexpected width expansion.
  - Focus behavior: `Panel:executeCommand` resets entry text (`self.entry:setText('')`) and refocuses (`self.entry:focus()`), ensuring keyboard readiness without extra clicks.
  - Output scrolling: `Panel:append` calls `self.history:setYScroll(...)` to keep latest results scrolled into view.
  - Stop accessibility: `btnStop.enable = true` is never disabled. Panel remains active in `UIManager` throughout timed action execution, ensuring `Stop` is clickable at any time during a walk.
  - No concrete code defects found. Per rule, native UI acceptance is not claimed from code inspection alone.
- **Automated test suite (146 passing checks)**:
  - 7 new console tests added in `tools/test_console.py` (26 checks total).
  - All 6 offline suites pass: 29 foundation + 15 engine adapter + 8 checkpoint readback + 54 command + 26 console + 14 driver = 146 checks, plus 11 runner self-tests.
- **Checklist and deployment protocol updated**:
  - `docs/M1-slice-c-checklist.md` updated with mouse-operated acceptance procedure, division of responsibilities, and deployment/recovery protocol.
  - Temporary acceptance driver `tools/FoundationWalkStopDriver.lua` retained as optional.
  - Single next task: native M1 slice C and console-button acceptance by Codex following `docs/M1-slice-c-checklist.md`.
  - External AI remains strictly ON HOLD. Checkout ownership released to Codex.

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
