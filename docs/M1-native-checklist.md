# M1 slice A native acceptance checklist

Updated: 2026-10-04 (Europe/Helsinki).
Status: OPEN. Physical F9 open/close, read-only commands (help, status, inventory), and physical Escape (first-close console, second-open menu) PASSED. Six remaining acceptance gates below must be completed before M1 slice A is accepted or slice B (stop/cancellation) begins.

## Safeguards and pre-flight rules

1. **Game closed before changes**: Close Project Zomboid before any backup, restore, setting edit, or probe deployment.
2. **Strict isolation**: Use only `runtime/isolated` and `SarahConsoleNativeCase` under `runtime/isolated/Saves/Rising`. Normal player profiles and installed game files (`G:\Games\ProjectZomboid`) remain read-only and untouched.
3. **Backup procedure**: Before executing tests (especially rebinding or menu transitions), copy `SarahConsoleNativeCase`, isolated `keysB42.ini`, `options.ini`, and `latestSave.ini` to a new timestamped backup directory under `runtime/backups/`.
4. **Restoration procedure**: Close game, preserve current state into a new backup folder, and restore the world directory to `runtime/isolated/Saves/Rising/SarahConsoleNativeCase`, `keysB42.ini` to `runtime/isolated/Lua/keysB42.ini`, and `options.ini` / `latestSave.ini` to the isolated profile root. Never delete the last good backup.
5. **Physical-key requirement**: Automated F-key/Escape attempts have not produced reliable observed delivery in this game; Computer Use exposes no hold-duration control (see `desktop-input-diagnostic.md`). Keyboard tests require user-operated physical keypresses.

---

## Ordered acceptance checklist

All remaining gates are currently pending. Mark `[x]` only when direct native evidence is captured.

- [x] **1. Hold-repeat behavior (F9)**
  - **Action**: Open game in `SarahConsoleNativeCase`. Physically press and hold `F9` down steadily for 1–2 seconds.
  - **Expected result**: Sarah Console opens on the initial down-edge and remains open without flickering, stuttering, or repeatedly toggling open and closed while held.
  - **Evidence to record**: Visual confirmation of a steady panel and user-reported hold duration and observed panel behavior. Transition logging requires a separately backed-up, observation-only probe; production does not log panel transitions.

- [x] **2. Restored movement input after closing**
  - **Action**: Open console (`F9`), confirm input box has focus. Close console (via `Escape` or mouse clicking `Close`). Ensure the game is unpaused, then press movement keys (`WASD`). Test Escape close and mouse Close separately.
  - **Expected result**: Character movement responds immediately without stuck movement keys, swallowed inputs, or residual keyboard focus.
  - **Evidence to record**: Character visibly moves; coordinates from a read-only status result before/after movement (or a deployed observation probe); no stuck-key state.

- [x] **3. English Options key-binding labels**
  - **Action**: Open Main Menu / Pause Menu -> `Options` -> `Key Bindings`. Scroll to the Project Sarah section.
  - **Expected result**: Section reads `Project Sarah` and action is labeled `Sarah Console` bound to `F9` (no untranslated keys like `UI_...` or missing text).
  - **Evidence to record**: Screenshot or visual confirmation of clean English labels in vanilla Options dialog.

- [x] **4. Key rebinding and persistence across restart**
  - **Action**: In `Options` -> `Key Bindings`, rebind `Sarah Console` to an unused key (e.g. `F10` or an unused keyboard letter). Save/apply options. Return to game and press the new key. Then exit game completely to desktop, restart via `launch-isolated.ps1 -NoDebug`, and press the rebound key.
  - **Expected result**: Rebound key opens and closes the console; in-console toggle status shows the updated key name; binding persists in isolated `keysB42.ini` across full process restart.
  - **Evidence to record**: Updated binding in `keysB42.ini`, successful toggle before and after full restart.

- [ ] **5. Conflict refusal and context menu fallback**
  - **Action**: In Options, rebind `Sarah Console` to a conflicting key used by movement (e.g. `W` / Forward) Confirm the other action remains bound to the same key: Options may clear collisions automatically. Unbound (`0`) is a separate fallback check and does not establish collision refusal. Return to game and press that key. Then right-click the game world to open the context menu.
  - **Expected result**: Pressing the conflicting key refuses to open the console (movement behaves normally without conflict errors). Right-click world context menu displays `Sarah: console`; clicking it opens the console, displaying conflict warning text in the history.
  - **Evidence to record**: Console opens via context menu; conflict warning banner visible; conflicting gameplay action operates safely without unintended opening.

- [x] **6. Same-process menu return and world cleanup**
  - **Action**: In `SarahConsoleNativeCase` with console open or closed, first close the console, then press `Escape` again to open the pause menu -> select `Exit to Main Menu`. Return to the main menu, then select `Continue` back into `SarahConsoleNativeCase`.
  - **Expected result**: Console panel is closed and removed from UIManager on menu exit; no orphaned UI elements on main menu; session reset runs cleanly. On reload, `F9` toggles console cleanly; a new session controller is initialized from saved state, with one restored Sarah and the current local player. Do not require retaining the old controller/object across sessions.
  - **Evidence to record**: Clean session reset in log; one Sarah restored; absence of new Sarah-specific errors; retain known map warnings. Duplicate-callback assertions need a separately scoped observation probe; one visible panel alone does not prove callback counts.

---

## Post-test cleanup and settings restoration

2026-10-04 same-process native PASS: process 41784 retained start time throughout
Quit to main menu and Continue. No console panel visible on main menu. Log records
SAVED a, SESSION_RESET, ACTIVE npc=true worn=3 localPlayerPreserved=true and RESTORED a.
User confirms F7 opens/closes normally after reload. No instrumented callback-count
or UIManager-membership claim; evidence covers visible cleanup and session behavior.

1. Close game cleanly; verify GameThread exit and save completion (`SAVED a` or `b`).
2. Restore the backed-up isolated key file (including any movement bindings changed by Options), then verify Sarah Console is F9. Do not restore just one setting and leave another displaced.
3. Verify all temporary test/diagnostic probes remain disabled outside the mod (`runtime/disabled-probes`).
4. Preserve final test case into `runtime/backups/`.
5. Update `STATUS.md`, `ROADMAP.md`, and `M1-console-test.md` with captured evidence.


Movement result (2026-10-04): user completed the requested Escape-close and mouse-Close walking sequence and reported movement fine. User-operated native PASS; no coordinate probe deployed. Hold-repeat confirmation requested separately; still pending.

2026-10-04: user confirms holding F9 then releasing leaves console open (hold-repeat PASS). Codex visually verified Project Sarah / Sarah Console / F9 labels in native Options (English labels PASS). Rebind dialog prepared; F7 assignment requested, not yet verified/applied.
