# M1 read-only console slice A: 2026-10-04

IN PROGRESS: slice A native acceptance PASSED; slice B (stop, cancellation, history)
REVISED and automated suite increased to 94 passing checks (31 command, 15 console).
Native acceptance of slice B pending Codex live check. Commands/Observations/Console implement
help, status, inventory, stop, and history. No external AI or movement commands (slice C deferred).
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
