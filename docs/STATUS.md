# Current project state

Updated: 2026-10-04 (Europe/Helsinki).
State: M0 broader hardening open. M1 read-only console slice A in progress. Physical F9 open/close, read-only commands (help, status, inventory), and physical Escape (first-close console, second-open menu) PASSED. Remaining native slice A acceptance OPEN (see `docs/M1-native-checklist.md`).
External AI: ON HOLD by explicit user instruction.
Ownership: Codex owns the checkout after reviewing Gemini documentation checkpoint f22ce71.
Do not have two agents edit this checkout concurrently.

## Current local runtime state

- Game is CLOSED (SAVED a, GameThread exited, no native window).
- Continue selects `SarahConsoleNativeCase` under `runtime/isolated/Saves/Rising/`. Only `SarahFoundation` enabled.
- Production mod deployed at `runtime/isolated/mods/SarahFoundation/` with verified `Console.lua` (Escape pause-menu guard included) and English `UI.json`.
- All temporary diagnostic probes (`ZZSarahEscapeProbe`, `FoundationInputProbe`) disabled outside mod in `runtime/disabled-probes`.
- Backups: Latest backup is `runtime/backups/input-comparison-20261004/After-comparison`. Earlier baseline, appearance, travel, module-cleanup, and native escape backups remain intact.
- Automated tests: 71 automated checks passing (27 foundation + 13 engine adapter + 8 checkpoint readback + 12 command + 11 console).
- Desktop automation limitation: Computer Use `press_key` has no hold-duration controls and special-key attempts (F9/Escape) have not produced reliable observed delivery; native keyboard checks require physical user assistance. See `docs/desktop-input-diagnostic.md`.

## Summary of verified outcomes

- **Automated policy checks**: 71 automated checks pass (27 foundation lifecycle, 13 engine adapter/render, 8 checkpoint readback/cleanup, 12 read-only command parser/dispatch, 11 simulated console UI/key/session cases).
- **M0 NPC lifecycle and recovery**: Demonstrated minimal NPC spawn, duplicate prevention, three equipped clothes, two-slot saves, unload/restore, full restart restoration, corrupt slot recovery, and saved death tombstone without resurrection.
- **M0 live sessions**: Verified in isolated disposable worlds across restarts, main-script reloads, pause menu return and Continue, ordinary same-floor world rendering, bounded travel suspension, locked-write recovery, and idle session cleanup.
- **M1 slice A read-only commands**: Native execution of `help`, `status`, and `inventory` commands passed; local player and NPC preserved; scrolling list box and native font metrics verified.
- **M1 slice A physical F9**: Physical F9 open, command entry, and F9 close verified natively by user; corroborated by probe samples.
- **M1 slice A physical Escape**: Physical Escape fix verified natively by user: first Escape closes console without opening pause menu; subsequent Escape opens vanilla pause menu. Corroborated by probe samples (`guard=true`, swallow armed and expired).
- **Isolation safeguards**: Mod and settings remain strictly isolated to `runtime/isolated`; installed game files and normal profile are read-only and untouched.

## Next task: finish M1 slice A native acceptance

Follow the ordered checklist in `docs/M1-native-checklist.md`:
1. Hold-repeat behavior (F9).
2. Restored movement input after closing.
3. English Options key-binding labels.
4. Key rebinding and persistence across restart.
5. Conflict refusal and context menu fallback.
6. Same-process menu return and world cleanup.

Only after slice A acceptance is complete: proceed to Slice B (stop/cancellation). External AI and stop/walk remain on hold.

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

