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

Current runtime: game closed after M1 read-only console checks. Continue selects
Rising/SarahConsoleCase; only SarahFoundation enabled. One Sarah restored from a
on full restart, local player preserved; final exit saved b. Production source
and English key labels deployed. ZZSarahConsoleProbe is disabled outside the mod;
no temporary driver active. User completed physical F9 open/status/close check,
with probe corroboration of opening/focus/closing and player preservation.

Read `M1-console-test.md` and STATUS for current checks. Twelve command and eight
simulated UI/key/session checks passed; all 48 M0 checks were rerun successfully.
Live menu open, typed commands, Enter/Run and mouse Close passed in the first build.
Final inventory/scroll display passed, including typed help/Enter after restart.
Physical F9 passed the user check; native hold/rebind/Escape/menu teardown and
English Options labels still need acceptance. Automated function keys were missed
even by vanilla rebind UI.
Keep external AI on hold and finish slice A before stop/walk.

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
Also run `tools/test_render.py` with the same Python: 13 engine adapter checks.
Run `tools/test_checkpoint.py`: 8 actual-adapter readback/cleanup checks;
48 automated checks total. Simulated checks do not prove exceptional native cleanup.

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
