# Agent handoff and checkpoint workflow

## Start here

Open `G:\Codex\Project Sarah` in Codex or Antigravity. Read root `AGENTS.md`,
then STATUS and ROADMAP. Git is standard and tool-independent. Repository:
https://github.com/cenationx/ProjectSarah, branch `main`, author `cenationx` using
a GitHub noreply address. Do not assume a separate app inherits authentication
or this conversation; check its Git access without displaying credentials.

Read Git status before fetching/pulling. Never discard another agent's work.
Only one agent should modify this checkout at a time. For a remote clone, choose
a directory under `G:\Codex`; runtime/dependencies are not included in GitHub.
The existing canonical checkout is the easiest handoff on this computer.

## What exists only on this computer

Current runtime: game closed (SAVED a, GameThread exited, no native window).
Continue selects Rising/SarahConsoleNativeCase; only SarahFoundation enabled.
One Sarah restored from a; local player preserved. Production source with Escape
guard and English key labels deployed. All temporary probes disabled outside mod;
no temporary driver active. User completed physical F9 open/close and physical
Escape checks (first Escape closes console without menu; second Escape opens menu),
corroborated by probe samples.

Read `M1-console-test.md`, `STATUS.md`, `M1-native-checklist.md`, and `M1-slice-c-checklist.md` for current checks.
146 automated checks passed across 6 suites (29 foundation, 15 engine adapter, 8 checkpoint readback, 54 command,
26 console, 14 acceptance driver) plus 11 runner self-tests. Slice A native acceptance passed (all 6 gates). Slice B idle-stop, history retention,
and session-reset smoke checks passed natively; active moving-action cancellation remains native testing pending.
Slice C (walk here, completion tracking, stop cancellation, timeout, lifecycle invalidation, dual controller+NPC identity
scoping, production controller contract, safe context menu routing, and temporary acceptance driver with sustained halt verification)
implemented and hardened offline (146 automated checks); native acceptance of walking, arrival, and live cancellation pending Codex live check
per `docs/M1-slice-c-checklist.md`.
Automated special-key delivery remains limited by Computer Use; physical keys need the user. Keep external AI on hold.

Latest backup group runtime/backups/console-before-20261004 preserves original
module-cleanup case/selections/keys, First-live-before-repair and Final-console.
Raw logs are runtime/console-first-console.txt and runtime/console-final-console.txt. Prior module-cleanup/long-session/write-fault/
travel/rendering/appearance and alive/dead backup cases remain intact. Restore
only game-closed after preserving the current case into a new directory.
All completed fault drivers stay disabled; never rerun them against stale markers.
See earlier dated M0 reports for their evidence and recovery boundaries.

- Installed game: `G:\Games\ProjectZomboid`, read-only.
- Isolated profile: `runtime/isolated` under the canonical project.
- Test world: `runtime/isolated/Saves/Rising/2026-10-04_04-21-54`.
- Separate alive case: `runtime/isolated/Saves/Rising/SarahSessionAlive`, copied
  from the pre-recovery backup and live-tested on 2026-10-04. The original dated
  world remains dead. Continue now selects SarahConsoleCase above.
- Live reload backup: `runtime/backups/reload-before-20261004`, both worlds
  before the reload investigation. Main-script reload passed; use
  `tools/FoundationReloadProbe.lua` for that exact test. It triggers a real save
  event and does not verify broader module reload or same-process world switching.
- Menu-transition backup: `runtime/backups/menu-before-20261004`, both worlds
  plus isolated key file and latest-save selection before that live test.
  Menu return, same-world Continue and alive/dead/alive switching passed in one
  process. See `M0-menu-transition-test.md`; both temporary drivers are disabled.
- Session-test backup: `runtime/backups/sessions-before-20261004` contains the
  original death world before these runs. Restore only with the game closed:
  first preserve the current target, then copy the desired backup into a new
  disposable case under the isolated Saves/Rising directory.
- Backups: `runtime/backups/foundation-before-20261004-045750` and
  `runtime/backups/recovery-before-20261004-050552`, each containing the world
  directory. Verify contents before using them.
- The original dated world has Sarah dead by design; the alive copy remains
  independent; Continue selects SarahConsoleCase. Before restoration, close
  the game, copy current world to a new backup/case directory, then restore a
  separate copy of the alive backup. Never delete the last copy of a case.
- Upstream PZNS: `vendor/PZNS`, commit
  `20a30212f98aa891aec9cb070bb96164be27c12a`, from
  https://github.com/Project-Zomboid-Community-Modding/PZNS.
- Mechanically patched PZNS candidate: `candidates/PZNS_B42_M0`, unverified.
- Dependencies: `tools/dependencies`; generated/decompiled classes and raw
  machine logs are ignored. Do not upload them.

If these files are absent, reconstruct the isolated setup before running game
tests. Do not substitute the normal game profile. Consult the existing reports
and scripts; the current engine adapter deliberately rejects other profile paths.

## Automated checks

From the project directory in PowerShell, the single-entry verification workflow runs all 6 offline test suites (146 checks total) and generates detailed reports:

```powershell
& 'C:\Users\rudol\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe' tools\run_tests.py
```

See `docs/verification-workflow.md` for full documentation (CLI flags, `--python` overrides, per-suite options, JSON/Markdown reports under `tools/reports/`, and runner self-tests).

To test the runner itself (11 unit tests using standard library only):
```powershell
& 'C:\Users\rudol\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe' tools\test_runner.py
```

Individual suites can also still be executed directly:
- `tools/test_foundation.py`: 29 foundation lifecycle checks.
- `tools/test_render.py`: 15 engine adapter/render checks.
- `tools/test_checkpoint.py`: 8 checkpoint readback/cleanup checks.
- `tools/test_commands.py`: 54 command parser/dispatch/cancellation checks.
- `tools/test_console.py`: 26 simulated console UI/key/shortcut/session checks.
- `tools/test_driver.py`: 14 acceptance driver sequencing/movement/stability/timeout/teardown checks.
146 automated checks total (across 6 suites) plus 11 runner self-tests. Simulated checks do not prove exceptional native cleanup.

API inspection: `tools/inspect_compatibility.py`, `tools/run-api-probe.ps1` and
the Java probes. The legacy PZNS compatibility probe is expected to fail missing
APIs; that failure is not a regression in SarahFoundation. ECJ 3.43.0 is needed
locally for compilation; CFR 0.152 was used only for local engine inspection.

## Live tests

### Temporary native acceptance driver for walk/stop testing
To run native walk and stop testing without manual typing:
1. Ensure the game is CLOSED.
2. Deploy driver: copy `tools/FoundationWalkStopDriver.lua` to `runtime/isolated/mods/SarahFoundation/42/media/lua/client/ZZSarahWalkStopDriver.lua`.
3. Launch game with isolated profile and `SarahConsoleNativeCase`.
4. The driver UI panel appears at (20, 200). It never starts any test automatically.
5. Move the player 4–6 tiles away from Sarah on the same floor with a clear path.
6. Click `Walk then Stop`:
   - Driver dispatches `walk here`, monitors observable movement (>= 0.2 tiles), and issues `stop`.
   - Verifies Sarah halts before target square and marks mid-walk cancellation `PASS`.
   - If Sarah reaches target square too early, driver marks `INVALID: Arrived too soon` (not labelled mid-walk cancellation).
7. Click `Walk to Player`: verifies clean resumption after cancellation.
8. Click `Status & History`: logs status and history to verify dispatch record.
9. Close game cleanly.
10. Remove driver: delete `runtime/isolated/mods/SarahFoundation/42/media/lua/client/ZZSarahWalkStopDriver.lua`.

1. Read STATUS and the applicable test report. Confirm game process is closed.
   Sandboxed process queries may not see a game launched outside that sandbox;
   use native window inventory or an authorized process query before trusting
   process absence. Verify process ID/start time when claiming no restart.
2. Back up the disposable world and mod selection; record the backup path and
   restoration procedure before mutations or destructive fault tests.
3. Deploy `foundation/SarahFoundation` to `runtime/isolated/mods`. Keep its
   `common` directory. Enable only SarahFoundation, with SarahM0 disabled, in
   isolated profile and save mod selections. Never edit the normal selections.
4. Temporary probe drivers are in `tools`: FoundationLiveProbe, FoundationDeathProbe
   and FoundationTombstoneProbe; FoundationSessionProbe checks the two named
   alive/dead worlds and marks world-specific metadata. Deploy only the driver(s) required by the test
   before game launch. The death probe kills Sarah; the tombstone probe assumes
   she was already killed and saved. They are not production mod features.
   FoundationMenuProbe adds a temporary mouse entrypoint into the game's real
   pause menu for transition testing; pair it with FoundationSessionProbe.
   This does not verify physical Escape input. Disable both after testing.
   FoundationAppearanceProbe binds a temporary model viewer to the actual NPC
   and logs worn items/position/opacity/culling. Model output is distinct from
   ordinary world rendering. Deploy only in the backed-up appearance case and
   disable after use.
   FoundationWorldRenderProbe observes actual NPC registration/lighting/flags
   and counts production adapter draws. Experimental drawing defaults off;
   never enable it together with the production rendering callback.
   FoundationTravelProbe is one-shot and guarded to SarahTravelCase. It uses
   controlled player debug travel and a full away-world restart to test real
   streaming. Never redeploy into the completed marker=done case; prepare a new
   independent case and adjust the driver guard before repeating the test.
   FoundationWriteFailureProbe and hold-checkpoint-lock.ps1 are a matching
   one-shot fault pair guarded to SarahWriteFailureRetest. The helper refuses a
   stale signal and releases its exclusive handle within five minutes. Do not
   rerun against the completed case: make a backed-up new case, inspect latest
   slot and update both guards/signal together. Done mode only checks restart.
   FoundationLongSessionProbe is guarded to SarahLongSessionCase: six-minute
   one-shot 12-cycle run and completed-marker restart mode. It temporarily wraps
   adapter.remove only to observe objects, then checks and releases references
   after ticks. Do not redeploy to repeat cycles in the completed case; prepare
   a separate backed-up matching case and inspect/reset only its probe metadata.
   FoundationModuleCleanupProbe is guarded to SarahModuleCleanupCase. It reloads
   Engine/Lifecycle/main, interrupts real removal with an injected Lua exception,
   restores the wrapper and requires full process restart for recovery checks.
   Done mode only checks the recovered checkpoint; prepare another backed-up
   matching case/marker to repeat. Do not clear pinned controller references
   manually to bypass safeguards.
5. Launch `tools/launch-isolated.ps1` (optionally `-NoDebug` for intentional
   failures). Inspect the game UI, continue the disposable world, dismiss the
   survival guide, and verify outcomes against logs and game state.
6. Preserve raw logs locally under runtime; publish only sanitized result
   excerpts. Record failures and engine/map warnings as well as passes.
7. Close the game, preserve the final test case, and move temporary test drivers
   out of the mod (currently `runtime/disabled-probes`). Record final state.

For every restoration/move, verify absolute source/destination paths stay under
this project. Keep normal saves and installed game files untouched.

## Checkpoint routine

Update STATUS whenever a bounded task finishes and before stopping. Update the
roadmap only when evidence meets the milestone, and HANDOFF when setup changes.
Commit related code, notes and sanitized evidence together; push and verify.
Checkpoints should be small enough that a usage limit leaves useful saved state.

An interruption note must explain how to continue from partial work. Do not
leave the next agent guessing whether a game is running, which save was changed,
or whether a pass came from fake engine tests or live gameplay.

GitHub stores shared files, not chats, local saves, backups or tool permissions.
No automatic agent switching or background quota monitor is configured. The user
can switch tools/models and ask the next agent to continue using these files.

## Antigravity / Claude handoff verified on 2026-10-04

Project Sarah was added in the Antigravity desktop app from the canonical folder.
The project customization breakdown explicitly listed
`g:\Codex\Project Sarah\AGENTS.md` as a loaded rule. The new-conversation screen
showed local execution and Claude Sonnet 5.5 Medium selected. Use
`CLAUDE.md` and `docs/CLAUDE-RESUME.md` for the current resume instructions.
The user will submit the prompt; Codex has not started an Antigravity agent.
Re-check selection and draft availability when returning to the app.

Project Sarah's Local Permissions now contain Allow `G:\` for File Reads and
File Writes, and Allow `*` for Terminal Commands, as requested by the user.
Saved file rows were reopened and visually verified; terminal wildcard saved
row and project counts (2 file rules, 1 command rule) were visually verified.
This command wildcard covers all terminal commands, including PowerShell/native
tools; it does not constrain arbitrary shell execution to G:\. No Claude run has
tested whether inherited policies produce additional approvals. Security and
plan-review presets remain inherited, and unrelated global/network/MCP settings
were unchanged. App permissions are local and are not distributed through Git.
GitHub app authentication remains untested; Git uses the existing repository/remote.
The app warned that its bundled customization/skills token budget was exceeded;
Sarah's AGENTS.md was nevertheless shown in the loaded rules breakdown. Unrelated
global skills/settings were left unchanged.

## Coding and native-test ownership (2026-10-04)

The user confirmed Claude idle and authorized Codex to take over the canonical
checkout. Codex owns the current native M1 slice A test session. Claude receives
coding/automated-test tasks only when the user sends the prepared handoff prompt.
Codex handles desktop observation, isolated game setup and native acceptance.
Do not edit concurrently. Each owner commits/pushes its checkpoint and states
whether the game is running, the active case, backups, evidence and next task.
No automatic agent messaging/switching is configured; the user forwards prompts.

Current case: runtime/isolated/Saves/Rising/SarahConsoleNativeCase, copied from
SarahConsoleCase with game closed. Backup: runtime/backups/console-native-20261004.
Original case, latestSave.ini, options.ini and Lua/keysB42.ini preserved there.
For restoration, close game, preserve latest NativeCase into a new backup first,
then copy saved settings to their original isolated paths. Do not erase cases.
Codex Windows Computer Use captures this game and clicks successfully; F9 and
Escape injection had no observed effect. Physical key checks remain user-assisted.

Latest handoff: native Escape gate FAILED by user's precise report (first Escape
opens pause menu, second closes Sarah Console). Codex released checkout for
user-started Claude coding work, with game CLOSED, SAVED a and no native window.
Final NativeCase backup: console-native-20261004/After-escape-check under runtime/backups.
Claude should fix/automatically test input handling, without launching the game,
then commit/push and release checkout to Codex for native retesting. No gate pass
or stop/walk/AI authorization. See STATUS and updated CLAUDE-RESUME first.

## Escape fix released to Codex (2026-10-04)

Claude edited only `Console.lua`, `tools/test_console.py` and docs. The fix is native-
unverified and not deployed to the isolated mod. Codex owns the checkout again: back up
game-closed, deploy production source, retest physical Escape. Antigravity has no
desktop-control tool and no `git` on PATH (use the Codex runtime git `cmd` directory).
Stop/walk and external AI remain on hold. See STATUS and `M1-console-test.md`.

## Updated sustained-work policy (2026-10-04)

User changed the workflow after Claude's Escape checkpoint 88fbafc: Codex now
handles sustained coding and testing. Gemini can assist when the user starts a
bounded task, respecting one-writer ownership. Do not automatically hand coding
to Claude; reserve it for explicit user requests. Codex owns the current checkout.
Claude's fix is native-unverified and not deployed; next task remains isolated
Escape retest, following game-closed backups. External in-game AI stays on hold.

Latest local runtime after input comparison: game CLOSED and SAVED a; production
Escape fix deployed, all temporary input/Escape probes disabled outside mod.
Continue selects SarahConsoleNativeCase. Final backup is
runtime/backups/input-comparison-20261004/After-comparison. Diagnostic/evidence
in docs/desktop-input-diagnostic.md and evidence/input-comparison-summary.txt.
No tool repair established; use physical special-key/hold checks where required.
Codex owns coding/testing; do not start Claude. Remaining slice A gate unchanged
except successful physical Escape acceptance recorded in M1-console-test.md.

## Gemini bounded documentation handoff (2026-10-04)

Codex released this clean checkout for a user-started Gemini task. Scope: reconcile
current summaries/ownership and prepare one concise remaining slice A native
checklist from existing evidence. Allowed edits: docs/STATUS.md, docs/HANDOFF.md,
docs/CLAUDE-RESUME.md, docs/ROADMAP.md, docs/M1-console-test.md and a new
 docs/M1-native-checklist.md. Preserve historical evidence and all limitations.
No source/tests/runtime/save/settings changes, no game launch or desktop control.
Escape retest PASS is already documented; the top STATUS summary is stale.
71 automated checks last passed in Codex. All other native gates remain pending.
Gemini commits/pushes documentation and releases ownership to Codex. User forwards
prompt/results; no external agent was started by Codex. AI remains on hold.

## Documentation cleanup and checklist handoff to Codex (2026-10-04)

Gemini completed documentation reconciliation and created `docs/M1-native-checklist.md`.
Status summary, roadmap, handoff, and resume notes were updated to reflect the verified physical
Escape fix PASS (first Escape closes console without menu; subsequent Escape opens menu)
and 71 passing automated checks. No code, tests, saves, or settings were modified.
Checkout ownership is RELEASED to Codex for native slice A acceptance following the
ordered checklist. External in-game AI remains on hold.
## Gemini assisted native-acceptance handoff (2026-10-04)

Codex released checkout. Game CLOSED, SAVED b; F7 binding remains in isolated key file. Backup: runtime/backups/acceptance-20261004-183708/Before-Gemini plus F7-before-Gemini.ini; original F9 baseline at group root. User reports F7 works.

## Workflow boundary update: Codex handles launches & live tests (latest, 2026-10-04)

Per user directive:
- **Codex handles all game launches and live gameplay tests.**
- **Gemini handles coding, reviews, documentation, and offline analysis only.**
- Gemini has ceased all game launching and desktop troubleshooting.
- Game confirmed CLOSED (no `javaw.exe` or `java.exe` processes running).
- No saves, settings, launchers, probes, or source files were modified.
- Diagnostic note for Codex: `tools/launch-isolated.ps1` line 8 contains `-WindowStyle Hidden` (inherited from M0 headless probe runs) which forces `SW_HIDE` on GLFW, keeping the game window invisible while audio plays. Background agent sessions also execute in an isolated virtual desktop (`WinSta0\exebox-...`). Codex can adjust the launcher or launch interactively as needed.
- M1 slice A acceptance gates 4 (rebind persistence across restart), 5 (conflict refusal & context menu fallback), and 6 (same-process teardown) remain strictly PENDING in `docs/M1-native-checklist.md`.
- Active case: `runtime/isolated/Saves/Rising/SarahConsoleNativeCase`; key file retains `Sarah Console=key:65`. Full baseline backups preserved in `runtime/backups/acceptance-20261004-183708`.
- Checkout ownership is RELEASED to Codex.

Codex resumed at 8224446; game-closed backup runtime/backups/codex-resume-20261004-234837.
Native F7 full-restart persistence, updated label and old F9 inactivity PASS per user.
Same-process Quit/Continue PASS: PID 41784 unchanged, SAVED a and SESSION_RESET,
RESTORED a / ACTIVE npc=true worn=3 localPlayerPreserved=true. User confirms F7
toggle after reload. No orphaned console visible on main menu; callback counts not
instrumented. Game running; conflict/fallback remaining, full F9 baseline restoration
still due at game-closed cleanup. Codex owns all live tests; Gemini offline only.
Existing hidden-style launcher produced a usable visible game through Codex; the
blanket hidden-window diagnosis above is not established for GLFW across runners.



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
## M1 slice B stop, cancellation, and history handoff (2026-10-05)

Gemini completed M1 slice B implementation and automated validation (offline only; no game launches or desktop control).
- Changed source files:
  - `foundation/SarahFoundation/42/media/lua/client/Sarah/Commands.lua` (stop command, lifecycle tokens, stale completion rejection, bounded history buffer capped at 30, history query command).
  - `foundation/SarahFoundation/42/media/lua/client/Sarah/Console.lua` (dispatch preservation across open/close via `getDispatch()`, game thread `stopSarah` callback, session reset cleanup, prompt update).
  - `tools/test_commands.py` (added 10 unit checks: idle stop, repeat stop, dead/unloaded stop, active action registration, busy rejection, cancellation by stop, late-completion prevention, successful completion, stale token rejection, session reset cancellation, unload/death observation cancellation, history query and immutability).
  - `tools/test_console.py` (added 3 console checks: panel stop submission, history display, session reset dispatch cleanup).
- Automated test results: 84 passing checks (27 foundation + 13 engine adapter + 8 checkpoint readback + 22 command + 14 console).
- Live gameplay testing: Handed off to Codex.
  - Game is CLOSED.
  - Step 1: Deploy `foundation/SarahFoundation` to `runtime/isolated/mods/SarahFoundation` while game is closed.
  - Step 2: Launch `SarahConsoleNativeCase`.
  - Step 3: Open console (F9) and test commands: `help`, `status`, `inventory`, `stop`, `history`.
  - Step 4: Verify character movement restored after closing console (Escape / mouse Close).
  - Step 5: Clean shutdown and save.
- External AI remains strictly ON HOLD. Checkout ownership is RELEASED to Codex.
## M1 slice B revision handoff (2026-10-05)

Gemini completed offline revision and review correction of slice B:
- Propagated engine stop failures (exceptions and `false, reason` returns) into structured `failed` outcomes and history, while cleanly invalidating the command.
- Added independent lifecycle invalidation: `completeAction` revalidates state and controller before accepting success, and `Console.lua` game-thread tick runs lifecycle checks while console is closed.
- Decoupled internal action ownership from public observations: `Observations.read()` exposes strictly copied data (`state`, `player`, `npc`, `reason`, `inventory`) with no mutable engine handles (`controller`, `adapter`, `npc`).
- Private identity provider: `Commands.new(observe, stopCallback, identityProvider)` accepts a private identity provider closure/token. `Console.lua` passes `function() return SarahFoundation and SarahFoundation.controller end`.
- Scoped actions and stop callback to controller identity: `checkLifecycle` invalidates active work on controller replacement (`'controller replaced'`), stale callbacks targeting replaced controllers are rejected, and `stopSarah` verifies `action.owner` to reject stale stops.
- Record snapshot protection: Action records returned by `beginAction`, `cancelActive`, and `getHistory` are shallow-copied snapshots protecting internal dispatch state (`self.active`, `self.history`) from caller mutation.
- Automated tests: 94 passing checks across all 5 test suites (27 foundation + 13 engine adapter + 8 checkpoint readback + 31 command + 15 console).
- Live gameplay testing: Handed off to Codex. Game is CLOSED.
  - Step 1: Deploy `foundation/SarahFoundation` to `runtime/isolated/mods/SarahFoundation`.
  - Step 2: Launch `SarahConsoleNativeCase`.
  - Step 3: Test console commands (`help`, `status`, `inventory`, `stop`, `history`) and character movement.
  - Step 4: Clean shutdown and save.
- External AI remains strictly ON HOLD. Checkout ownership is RELEASED to Codex.

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

## M1 slice C bounded movement ("walk here") handoff (2026-10-05)

Gemini completed M1 slice C implementation and automated validation (offline only; no game launches or desktop control).
- Changed source files:
  - `foundation/SarahFoundation/42/media/lua/client/Sarah/Commands.lua` (walk here command, requestWalk, target validation, already-at-target detection, true arrival verification, path failure propagation, timeout tracking, busy check, help update).
  - `foundation/SarahFoundation/42/media/lua/client/Sarah/Console.lua` (walkSarah callback verifying controller owner, state.getDispatch export, prompt line update).
  - `foundation/SarahFoundation/42/media/lua/client/Sarah/Engine.lua` (SarahWalkAction derivation via getWalkActionClass, adapter.validateTarget for finite coordinates/floor/distance/square-status, adapter.walk).
  - `foundation/SarahFoundation/42/media/lua/client/SarahFoundation.lua` (rerouted context menu option "Sarah: walk here" through SarahConsole.getDispatch():execute('walk here')).
  - `tools/test_render.py` (2 new unit tests, 15 total: validateTarget and adapter.walk).
  - `tools/test_commands.py` (14 new unit tests, 45 total: start, already-at-target, busy, non-active, invalid coords, floor, distance, start failure, arrival verification, stopped-short failure, path failure, stop cancellation, timeout, replacement, requestWalk).
  - `tools/test_console.py` (2 new unit tests, 17 total: console panel walk here submission and getDispatch context menu routing).
- Automated test results: 112 passing checks across all 5 test suites (27 foundation + 15 engine adapter + 8 checkpoint readback + 45 command + 17 console).
- Live gameplay testing: Handed off to Codex following the checklist in `docs/STATUS.md`.
  - Game is CLOSED.
  - Step 1: Deploy `foundation/SarahFoundation` to `runtime/isolated/mods/SarahFoundation`.
  - Step 2: Launch `SarahConsoleNativeCase`.
  - Step 3: Open console (F9) and test commands: `help`, `status`, `walk here`, `stop`, `history`.
  - Step 4: Verify Sarah walks to player square, reports arrival in status and history, halts cleanly on `stop`, rejects movement when busy or already at target, and context menu routes cleanly.
  - Step 5: Clean shutdown and save.
- External AI remains strictly ON HOLD. Checkout ownership is RELEASED to Codex.

## M1 slice C lifecycle audit, hardening, and native checklist handoff (2026-10-05)

Gemini completed the lifecycle audit and hardening of M1 command and action boundaries (offline only; no game launches or desktop control):
- **Lifecycle audit findings**:
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
- **Live testing handoff to Codex**:
  - Game is CLOSED.
  - Follow `docs/M1-slice-c-checklist.md` in `SarahConsoleNativeCase`.
  - Checkout ownership is RELEASED to Codex. External AI remains strictly ON HOLD.

## Temporary acceptance driver & halt evidence hardening (latest, 2026-10-05)

Gemini built and verified a temporary acceptance driver in `tools/FoundationWalkStopDriver.lua` and hardened halt verification evidence offline (no game launches, runtime deployment, or desktop automation):
- **WAIT_HALT evidence verification**:
  - Requires fresh, valid observations of the same controller and NPC on every tick; missing observations immediately invalidate the run (`INVALIDATED`), never substituting old/cached coordinates.
  - Captures `walkToken`, `walkSession`, controller identity, and NPC identity privately from the dispatched action.
  - Controller or NPC replacement or an unrelated/newer active action immediately invalidates monitoring (`INVALIDATED`) without stopping the replacement entity or new action.
  - Movement timeout cleanup strictly checks action ID, token, session, and identity, ensuring it never stops an unrelated newer action.
  - Position is sampled over a bounded observation window (`MAX_HALT_TICKS = 30`).
  - Requires sustained positional stability: `REQUIRED_STABLE_TICKS = 5` consecutive tick observations with positional delta `<= HALT_TOLERANCE = 0.05` tiles.
  - Continued physical movement resets stability counter and fails after the observation window (`FAILED: Continued movement`).
- **Driver offline unit tests (`tools/test_driver.py`)**:
  - 14 automated unit tests pass, covering profile gating, panel initialization, status/history execution, walk dispatch & monitor, observable movement verification, mid-walk cancellation, invalid early arrival handling, tick timeout, overlapping run refusal, post-cancellation resumption, session teardown, and 4 new regression tests (continued movement failure, missing observation invalidation, identity replacement/newer action protection, and sustained positional stability PASS).
  - Total project suite: 139 checks passing (29 foundation + 15 engine adapter + 8 checkpoint readback + 54 command + 19 console + 14 driver).
- **Deployment & operation instructions for Codex**:
  1. *Deploy*: Copy `tools/FoundationWalkStopDriver.lua` to `runtime/isolated/mods/SarahFoundation/42/media/lua/client/ZZSarahWalkStopDriver.lua`.
  2. *Launch*: Launch isolated game with `SarahConsoleNativeCase`. The driver panel appears at `(20, 200)`.
  3. *Reposition player*: Move player 4–6 tiles away from Sarah on the same floor with a clear path.
  4. *Run Walk then Stop*: Click `Walk then Stop`. Watch console output for `[SarahDriver] WALK_THEN_STOP PASS: Mid-walk cancellation verified with sustained halt stability`.
  5. *Test resumption*: Click `Walk to Player`. Verify Sarah walks to the player's new position and arrives.
  6. *Verify history*: Click `Status & History`. Verify recent outcomes recorded.
  7. *Remove*: Close game cleanly. Delete `ZZSarahWalkStopDriver.lua` from `runtime/isolated/mods/SarahFoundation/42/media/lua/client/`.

Checkout ownership is RELEASED to Codex. External AI remains strictly ON HOLD.

## Single-entry offline verification workflow handoff (latest, 2026-10-05)

Gemini built and verified a dependable, single-entry offline verification workflow in `tools/run_tests.py` and `tools/test_runner.py` (offline tooling only; no game launches, desktop automation, or runtime deployment):
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
- **Slice C native acceptance status**:
  - Offline tooling complete. Native walking, arrival, and live cancellation acceptance remain **PENDING** live check per `docs/M1-slice-c-checklist.md`.

Checkout ownership is RELEASED to Codex. External AI remains strictly ON HOLD.

### Verification runner correction (2026-10-05)
Runner dirty status includes untracked files. Self-tests use ignored tools/reports/self-test-tmp and clean their temporary directories. Verified 139 project checks plus 11 runner self-tests; native acceptance remains pending.

## Sarah Console mouse shortcuts for commands (latest, 2026-10-05)

Gemini added mouse-operated command shortcut buttons to `SarahConsole.lua` and added full regression coverage in `tools/test_console.py` (offline tooling only; no game launches, desktop automation, or runtime deployment):
- **Mouse shortcut toolbar in Sarah Console**:
  - Purpose: Overcomes unreliable automated keyboard input in PZ; allows Codex to open the console via mouse context menu (`Sarah: console`) and submit all core commands by clicking dedicated buttons, while the user controls movement and gameplay.
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
