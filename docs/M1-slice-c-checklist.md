# M1 slice C native acceptance checklist

Updated: 2026-10-05 (Europe/Helsinki).
Status: IMPLEMENTED and HARDENED offline (123 automated checks: 29 foundation, 15 engine adapter, 8 checkpoint, 52 command, 19 console). Native acceptance PENDING Codex live check.

## Scope and purpose

This checklist governs the native gameplay acceptance of:
1. **M1 Slice C**: Bounded "walk here" movement, distance/floor validation, already-at-target detection, true arrival verification, and context-menu routing.
2. **M1 Slice B**: Live in-motion action cancellation (stopping a walking NPC mid-path), verifying engine action queue clearing and dispatch history transitions together.

## Safeguards and pre-flight rules

1. **Game closed before changes**: Ensure Project Zomboid is closed (`javaw.exe` / `java.exe` absent) before any backup, restore, setting edit, or mod deployment.
2. **Strict isolation**: Use only `runtime/isolated` and `SarahConsoleNativeCase` under `runtime/isolated/Saves/Rising`. Normal player profiles and installed game files (`G:\Games\ProjectZomboid`) remain read-only and untouched.
3. **Backup procedure**: Before executing tests, copy `SarahConsoleNativeCase`, isolated `keysB42.ini`, `options.ini`, and `latestSave.ini` to a new timestamped backup directory under `runtime/backups/`.
4. **Deploy production mod**: Deploy updated `foundation/SarahFoundation` to `runtime/isolated/mods/SarahFoundation`. Verify no temporary diagnostic probes are in the mod directory (`runtime/disabled-probes`).
5. **Ownership**: Codex handles all game launches and live gameplay tests. Gemini handles offline coding, reviews, and documentation only.
6. **External AI**: The external AI layer remains strictly **ON HOLD**.

---

## Ordered acceptance checklist

- [ ] **1. Normal walk and arrival tracking**
  - **Action**: Open game in `SarahConsoleNativeCase`. Position the player 3–5 tiles away from Sarah on the same floor with a clear path. Press `F9` to open Sarah Console. Type `walk here` and press `Enter`.
  - **Expected result**:
    - Console outputs `Walking to (<tx>, <ty>, <tz>).` and `#<id> running`.
    - Type `status` + `Enter` while Sarah is walking: displays `Action: #<id> walk here (running)`.
    - Sarah visibly navigates to the player's square.
    - Upon arrival, type `status` + `Enter`: displays `Action: idle (last: #<id> completed)`.
    - Type `history` + `Enter`: displays `#<id> walk here: completed (Reached target (<tx>, <ty>, <tz>).)`.
  - **Evidence to record**: Console output text, status before and after arrival, Sarah's observed position matching player square.

- [ ] **2. Already-at-target detection**
  - **Action**: While the player and Sarah are standing on the exact same tile (or adjacent sub-tile in the same square), open console, type `walk here` and press `Enter`.
  - **Expected result**:
    - Console outputs `Already at target (<tx>, <ty>, <tz>).` and `#<id> completed`.
    - Sarah does not start a redundant timed action or change position.
    - Type `status` + `Enter`: displays `Action: idle (last: #<id> completed)`.
  - **Evidence to record**: Output confirming `Already at target` with no movement delay.

- [ ] **3. Distance and target refusal**
  - **Action**: Move the player more than 8 tiles away from Sarah (e.g., 10–12 tiles away on the same floor). Type `walk here` and press `Enter`.
  - **Expected result**:
    - Console outputs `Target is too far (maximum 8 tiles).` and `#<id> rejected`.
    - Sarah does not move or enter a running action state.
    - Type `status` + `Enter`: displays `Action: idle`.
  - **Evidence to record**: Console rejection text; Sarah remains idle.

- [ ] **4. Live movement cancellation via `stop` command (Slice B + C combined)**
  - **Action**: Position player 5–7 tiles away from Sarah. Type `walk here` + `Enter`. Once Sarah is actively walking in motion toward the player, immediately type `stop` and press `Enter`.
  - **Expected result**:
    - Sarah immediately halts movement and pathfinding.
    - Console outputs `Cancelled #<id> (walk here).` and `Sarah stopped.` with `#<id+1> completed`.
    - Type `status` + `Enter`: displays `Action: idle (last: #<id> cancelled)`.
    - Type `history` + `Enter`: displays `#<id> walk here: cancelled (stopped by user)`.
    - No unhandled engine exceptions in console or log.
  - **Evidence to record**: Confirmation that Sarah halted mid-walk, cancelled action ID/name, and idle status.

- [ ] **5. Immediate walk resumption after cancellation**
  - **Action**: Following the mid-walk cancellation in Gate 4, type `walk here` and press `Enter`.
  - **Expected result**:
    - Sarah immediately accepts the new walk request, displaying `Walking to (<tx>, <ty>, <tz>).` and `#<id> running`.
    - Action queue is clean; no stuck or lingering state from the cancelled action.
    - Sarah completes the walk to the player; arrival reports `completed`.
  - **Evidence to record**: Successful second walk and arrival confirmation.

- [ ] **6. Context menu "Sarah: walk here" routing and visible feedback**
  - **Action**: Stand 3–4 tiles away from Sarah. Close the console (`Escape`). Right-click Sarah in the game world to open the context menu. Select `Sarah: walk here`.
  - **Expected result**:
    - Player receives visible onscreen feedback (Halo text / Say): `Walking to player.`
    - Sarah visibly walks to the player's square.
    - Open console (`F9`), type `status`: confirms the menu-initiated walk was tracked through dispatch (`Action: #<id> walk here (running)` or `completed`).
    - Type `history`: confirms the menu walk is recorded with request ID and outcome.
    - Test refusal feedback: Walk > 8 tiles away, right-click Sarah -> `Sarah: walk here`: player receives visible bad/red text: `Target is too far (maximum 8 tiles).` and Sarah remains stationary.
  - **Evidence to record**: Visible onscreen feedback confirmation, console tracking of context-menu walk, and refusal feedback.

- [ ] **7. Session reset and clean reload**
  - **Action**: In `SarahConsoleNativeCase`, open pause menu -> `Exit to Main Menu`. Return to main menu, then select `Continue`.
  - **Expected result**:
    - Log shows `SESSION_RESET` and clean world reload.
    - Open console (`F9`): type `history` -> outputs `No command history.`
    - Type `help` -> output begins at request `#1 help: completed` (sequence counter reset).
    - Sarah and player are intact, one Sarah present, movement functional.
  - **Evidence to record**: Clean log excerpt (`SESSION_RESET`, `RESTORED`), reset history and sequence `#1`.

---

## Post-test cleanup and settings restoration

1. Close game cleanly; verify GameThread exit and save completion (`SAVED a` or `b`).
2. Verify isolated `keysB42.ini` has `Sarah Console=key:67` (F9) and movement intact.
3. Verify all temporary test/diagnostic probes remain disabled outside the mod (`runtime/disabled-probes`).
4. Preserve final test case into `runtime/backups/`.
5. Update `docs/STATUS.md`, `docs/ROADMAP.md`, `docs/HANDOFF.md`, and `docs/M1-console-test.md` with captured evidence.
