# M1 slice C native acceptance checklist

Updated: 2026-10-05 (Europe/Helsinki).
Status: IMPLEMENTED, HARDENED offline, and PREPARED for native acceptance (146 automated checks across 6 suites plus 11 runner self-tests). Native UI inspection completed read-only against PZ 42.21.0 ISUI source. Native acceptance PENDING Codex live check using console mouse buttons and human observation.

## Scope and purpose

This checklist governs the native gameplay acceptance of:
1. **M1 Slice C**: Bounded "walk here" movement, distance/floor validation, already-at-target detection, true arrival verification, context-menu routing, and onscreen feedback.
2. **M1 Slice B**: Live in-motion action cancellation (stopping a walking NPC mid-path via the console `Stop` button), verifying engine action queue clearing and dispatch history transitions together.
3. **Console mouse shortcuts**: Operating Sarah Console via mouse context menu (`Sarah: console`) and the 7 buttons (`Help`, `Status`, `Inventory`, `History`, `Walk Here`, `Stop`, and `Close`) to avoid unreliable desktop keyboard injection in Project Zomboid.

## Division of responsibilities

- **User**: Controls player character movement/positioning with physical keys/mouse; visually observes and confirms physical NPC movement, arrival, and halting.
- **Codex**: Opens Sarah Console via mouse context menu (`Sarah: console`) or key; operates the console mouse buttons (`Help`, `Status`, `Inventory`, `History`, `Walk Here`, `Stop`, `Close`); inspects and logs console text output and status lines. (Typed keyboard commands remain fully functional as a fallback).
- **Physical keyboard gates already passed**: Special-key handling from slice A (F9 hold-repeat, Escape pause-menu swallow, F7 rebinding, W conflict refusal) was accepted natively in slice A and does NOT need repeating unless investigating a suspected regression.
- **Temporary acceptance driver**: `tools/FoundationWalkStopDriver.lua` is completely optional. Native acceptance proceeds via the production console buttons and human observation.

---

## Deployment and recovery protocol for Codex

### Production source files to deploy
Before starting the test, the following reviewed production source files must be deployed from `foundation/SarahFoundation/` to `runtime/isolated/mods/SarahFoundation/`:
- `foundation/SarahFoundation/42/media/lua/client/SarahFoundation.lua` (context menu dispatch routing and onscreen feedback)
- `foundation/SarahFoundation/42/media/lua/client/Sarah/Commands.lua` (slice C walk dispatch, cancellation, dual-identity scoping, session-reset token counter)
- `foundation/SarahFoundation/42/media/lua/client/Sarah/Console.lua` (mouse shortcut toolbar, unified `executeCommand`, `tr()` translation helper)
- `foundation/SarahFoundation/42/media/lua/client/Sarah/Engine.lua` (`SarahWalkAction` class, `adapter.validateTarget`, `adapter.walk`)
- `foundation/SarahFoundation/42/media/lua/shared/Translate/EN/UI.json` (new button label translations)
- `foundation/SarahFoundation/README.md` (updated mod documentation)

*(Note: `Lifecycle.lua`, `Observations.lua`, `mod.info`, and `common/.gitkeep` are unchanged).*

### Baseline vs pending changes
- **Baseline currently deployed in `runtime/isolated/mods/SarahFoundation/`**: Slice B code (from checkpoint `70eee10`), backed up in `runtime/backups/slice-b-20261005-014102/Final-native`.
- **Pending changes**:
  1. `Commands.lua`: Bounded `walk here`, target validation (8 tiles, same floor, free square), already-at-target detection, true arrival verification, path failure propagation, timeout tracking (600 ticks), stop cancellation, dual controller+NPC identity scoping, session-reset token counter, synchronous callback safety.
  2. `Console.lua`: Mouse shortcut toolbar (`Help`, `Status`, `Inventory`, `History`, `Walk Here`, `Stop`), `Close` and `Run` buttons, translation lookup `tr()`, `executeCommand` unified display, `walkSarah` callback with controller verification, `state.getDispatch` export.
  3. `Engine.lua`: `SarahWalkAction` class derived from `ISWalkToTimedAction`, `adapter.validateTarget`, `adapter.walk`.
  4. `SarahFoundation.lua`: Rerouted context menu option `"Sarah: walk here"` through `SarahConsole.getDispatch():execute('walk here')` with visible feedback halo/say.
  5. `UI.json`: Translation keys for console button labels (`UI_SarahConsole_Help`, etc.).

### Pre-test backup checklist
1. Verify Project Zomboid is closed (`javaw.exe` / `java.exe` absent).
2. Create fresh timestamped backup directory (e.g. `runtime/backups/slice-c-<timestamp>`).
3. Copy the following into the backup directory:
   - `runtime/isolated/Saves/Rising/SarahConsoleNativeCase`
   - `runtime/isolated/Lua/keysB42.ini`
   - `runtime/isolated/options.ini`
   - `runtime/isolated/latestSave.ini`
   - Current mod directory `runtime/isolated/mods/SarahFoundation` (or rely on baseline at `runtime/backups/slice-b-20261005-014102/Final-native`).

### Deployment checklist
1. Ensure game is closed.
2. Copy the production files from `foundation/SarahFoundation/` into `runtime/isolated/mods/SarahFoundation/`.
3. Verify no temporary probes exist in `runtime/isolated/mods/SarahFoundation` (disabled probes stay in `runtime/disabled-probes`).
4. Ensure `tools/FoundationWalkStopDriver.lua` is NOT copied into the mod directory (acceptance uses production buttons).

### Removal and recovery checklist
1. Close game cleanly; verify GameThread exit and save completion (`SAVED a` or `b`).
2. If roll-back to Slice B baseline is required: copy files from `runtime/backups/slice-b-20261005-014102/Previous-mod` (or `slice-b-20261005-014102/Final-native` mod files) back into `runtime/isolated/mods/SarahFoundation`.
3. If save world needs restoring: copy backed-up `SarahConsoleNativeCase` back into `runtime/isolated/Saves/Rising/SarahConsoleNativeCase`.
4. If key bindings need restoring: copy backed-up `keysB42.ini` back to `runtime/isolated/Lua/keysB42.ini`.

---

## Ordered acceptance checklist

- [ ] **1. Normal walk and arrival tracking via mouse buttons**
  - **Action**: Launch isolated game with `SarahConsoleNativeCase`. User positions the player 3–5 tiles away from Sarah on the same floor with a clear path. Codex opens console via right-click world -> `Sarah: console` (or F9). Codex clicks `[Walk Here]` button.
  - **Expected result**:
    - Console outputs `> walk here`, `Walking to (<tx>, <ty>, <tz>).`, and `#<id> running`.
    - While Sarah is walking, Codex clicks `[Status]` button: outputs `> status` and `Action: #<id> walk here (running)`.
    - User visually confirms Sarah navigates across the floor toward the player's square.
    - Upon arrival, Codex clicks `[Status]` button: outputs `> status` and `Action: idle (last: #<id> completed)`.
    - Codex clicks `[History]` button: outputs `> history` and `#<id> walk here: completed (Reached target (<tx>, <ty>, <tz>).)`.
  - **Evidence to record**: Console output text, status before and after arrival, confirmation of Sarah's observed position matching player square.

- [ ] **2. Already-at-target detection via mouse buttons**
  - **Action**: User and Sarah stand on the exact same tile (or adjacent sub-tile in the same square). Codex clicks `[Walk Here]` button.
  - **Expected result**:
    - Console outputs `> walk here`, `Already at target (<tx>, <ty>, <tz>).`, and `#<id> completed`.
    - User confirms Sarah does not start a redundant timed action, turn, or change position.
    - Codex clicks `[Status]` button: outputs `> status` and `Action: idle (last: #<id> completed)`.
  - **Evidence to record**: Output confirming `Already at target` with immediate completion and no movement delay.

- [ ] **3. Distance and target refusal via mouse buttons**
  - **Action**: User moves the player more than 8 tiles away from Sarah (e.g. 10–12 tiles away on the same floor). Codex clicks `[Walk Here]` button.
  - **Expected result**:
    - Console outputs `> walk here`, `Target is too far (maximum 8 tiles).`, and `#<id> rejected`.
    - User confirms Sarah remains stationary and does not enter a running action state.
    - Codex clicks `[Status]` button: outputs `> status` and `Action: idle`.
  - **Evidence to record**: Console rejection text and request ID; Sarah remains stationary.

- [ ] **4. Live movement cancellation via `[Stop]` button (Slice B + C combined)**
  - **Action**: User positions player 5–7 tiles away from Sarah. Codex clicks `[Walk Here]`. Once Sarah is actively walking mid-stride toward the player, Codex clicks `[Stop]` button.
  - **Expected result**:
    - Console outputs `> stop`, `Cancelled #<id> (walk here).`, `Sarah stopped.`, and `#<id+1> completed`.
    - User confirms Sarah immediately halts movement and pathfinding before reaching the player's square.
    - Codex clicks `[Status]` button: outputs `> status` and `Action: idle (last: #<id> cancelled)`.
    - Codex clicks `[History]` button: outputs `> history` and `#<id> walk here: cancelled (stopped by user)`.
    - No unhandled engine exceptions in console or log.
  - **Evidence to record**: Confirmation that Sarah halted mid-stride, cancelled action ID/name, idle status, and clean history record.

- [ ] **5. Immediate walk resumption after cancellation via mouse buttons**
  - **Action**: Following the mid-walk cancellation in Gate 4, user moves player 3–4 tiles in another direction. Codex clicks `[Walk Here]` button.
  - **Expected result**:
    - Console outputs `> walk here`, `Walking to (<tx>, <ty>, <tz>).`, and `#<id> running`.
    - Action queue is clean; no stuck or lingering state from the cancelled action.
    - User confirms Sarah completes the walk to the player's new position and arrives.
    - Codex clicks `[Status]` button: outputs `> status` and `Action: idle (last: #<id> completed)`.
  - **Evidence to record**: Successful second walk and arrival confirmation.

- [ ] **6. Context menu "Sarah: walk here" routing, onscreen feedback, and console `[Close]` button**
  - **Action**: User positions player 3–4 tiles away from Sarah. Codex clicks `[Close]` button on top-right of Sarah Console. User right-clicks Sarah in the game world to open the context menu and selects `Sarah: walk here`.
  - **Expected result**:
    - Clicking `[Close]` closes Sarah Console cleanly without opening the game pause menu.
    - Selecting `Sarah: walk here` gives visible onscreen feedback (Halo text / Say): `Walking to (<tx>, <ty>, <tz>).`.
    - User confirms Sarah visibly walks to the player's square.
    - Codex reopens console via right-click world -> `Sarah: console` (or F9).
    - Codex clicks `[Status]`: confirms menu-initiated walk was tracked through dispatch (`Action: #<id> walk here (running)` or `completed`).
    - Codex clicks `[History]`: confirms menu walk recorded with request ID and outcome.
    - Refusal feedback test: User moves player > 8 tiles away; user right-clicks Sarah -> `Sarah: walk here`. Player receives visible bad/red text: `Target is too far (maximum 8 tiles).` and Sarah remains stationary.
  - **Evidence to record**: Clean console close, visible onscreen feedback confirmation, console tracking of context-menu walk, and refusal feedback.

- [ ] **7. Session reset and clean reload via mouse buttons**
  - **Action**: In `SarahConsoleNativeCase`, open pause menu -> `Exit to Main Menu`. Return to main menu, then select `Continue`.
  - **Expected result**:
    - Log shows `SESSION_RESET` and clean world reload (`RESTORED a` or `b`).
    - Codex opens console via right-click world -> `Sarah: console` (or F9).
    - Codex clicks `[Help]` button: output begins at request `#1 help: completed` (sequence counter reset).
    - Codex clicks `[History]` button: lists only `#1 help: completed`, then reports request `#2 completed` (confirming pre-reset history cleared and sequence numbering restarts at #1).
    - User confirms player and Sarah are intact, one Sarah present, and movement functional.
  - **Evidence to record**: Clean log excerpt (`SESSION_RESET`, `RESTORED`), reset history and sequence `#1`.

---

## Post-test cleanup and settings restoration

1. Close game cleanly; verify GameThread exit and save completion (`SAVED a` or `b`).
2. Verify isolated `keysB42.ini` has `Sarah Console=key:67` (F9) and movement intact.
3. Verify all temporary test/diagnostic probes remain disabled outside the mod (`runtime/disabled-probes`).
4. Preserve final test case into `runtime/backups/`.
5. Update `docs/STATUS.md`, `docs/ROADMAP.md`, `docs/HANDOFF.md`, and `docs/M1-console-test.md` with captured evidence.


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
