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

Read `M1-console-test.md`, `STATUS.md`, and `M1-native-checklist.md` for current checks.
84 automated checks passed (27 foundation, 13 engine adapter, 8 checkpoint, 22 command,
14 console). Slice A native acceptance passed. Slice B (stop, cancellation, history)
implemented and unit tested; native acceptance pending Codex live check.
Automated special-key delivery remains limited by Computer Use; physical keys need the user.
Keep external AI on hold; movement commands (slice C) deferred.

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

From the project directory in PowerShell, the tested command is:

```powershell
& 'C:\Users\rudol\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe' tools\test_foundation.py
```

It uses Lupa from `tools/dependencies/python`. The last tested installation was
Lupa 2.8; on a fresh setup install it into that project-local directory using an
available Python, with temporary/output directories under the project. This test
executes actual Lua source with fake engine adapters and events. It does not
prove gameplay compatibility. Expected latest result: 27 foundation checks.
Also run `tools/test_render.py`: 13 engine adapter checks.
Run `tools/test_checkpoint.py`: 8 checkpoint readback/cleanup checks.
Run `tools/test_commands.py`: 22 command parser/cancellation checks.
Run `tools/test_console.py`: 14 simulated console UI/key/session checks.
84 automated checks total. Simulated checks do not prove exceptional native cleanup.

API inspection: `tools/inspect_compatibility.py`, `tools/run-api-probe.ps1` and
the Java probes. The legacy PZNS compatibility probe is expected to fail missing
APIs; that failure is not a regression in SarahFoundation. ECJ 3.43.0 is needed
locally for compilation; CFR 0.152 was used only for local engine inspection.

## Live tests

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
