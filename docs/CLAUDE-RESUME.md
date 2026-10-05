# Superseding workflow note (2026-10-04)

The Escape coding fix was completed at `88fbafc`, deployed to the isolated mod,
and verified natively by the user as PASS (first Escape closes console without pause menu;
subsequent Escape opens normal pause menu). Corroborated by probe samples (`guard=true`,
swallow armed and expired).

The user now uses Codex for sustained coding and native testing, with Gemini assisting
on bounded tasks. Claude is reserved only for explicit user requests. Read `docs/STATUS.md`,
`docs/HANDOFF.md`, and `docs/M1-batched-acceptance.md` for current owner and remaining acceptance gates.
External in-game AI remains on hold.

---
# Historical: Escape failure coding handoff (2026-10-04, completed)

*Status: COMPLETED at `88fbafc` and natively verified.*

This task requested a narrow fix for the first-Escape pause menu bug:
Inspect actual Build 42.21.0 input ordering (`ToggleEscapeMenu` on `OnKeyPressed`).
`Console.lua` was modified to arm a one-shot swallow on Escape close and wrap
`ToggleEscapeMenu` with `SarahConsole.guard` to consume that single release.
All 71 automated checks passed (3 new console cases). Natively verified by user.

---
# Historical: Claude initial resume guide (2026-10-04)

Open the existing Antigravity Project Sarah project, local execution, canonical
folder `G:\Codex\Project Sarah`. Claude Sonnet 5.5 Medium was visible in the model
selector during setup; recheck your chosen model before sending the prompt.
The user will start Claude; no second coding agent has been started by Codex.

## Resume prompt

Continue Project Sarah in this existing checkout. Read AGENTS.md, CLAUDE.md,
docs/STATUS.md, docs/ROADMAP.md and docs/HANDOFF.md first. The latest implementation
checkpoint is 8f4f882; read docs/M1-console-test.md for the precise evidence.
Finish M1 slice A acceptance: native hold-repeat, Escape, rebind/conflict
persistence, English labels in Options, restored movement input and same-process
menu/world teardown. Physical F9 open/status/close already passed a user-operated
check. Back up a new disposable case game-closed before more live tests; preserve
the completed SarahConsoleCase and its Final-console backup. Do not rerun old
one-shot fault drivers or use normal saves. Keep installed game files read-only.
After each bounded task, update shared notes, commit source/evidence together,
push main and verify the remote. Keep external AI on hold. Add stop/cancellation
and bounded walk here only after slice A's remaining gate passes. Work autonomously
within this scope and ask only for missing information or actions that need it.

## Immediate local state

- Game closed at the previous checkpoint; recheck native window/process state.
- Continue selects isolated `Rising/SarahConsoleNativeCase`, only SarahFoundation enabled.
- Final exit saved a; one Sarah restored before checks.
- Temporary console probe disabled under runtime/disabled-probes; production
  console/modules/English UI.json deployed to the isolated mod.
- Latest backup group: runtime/backups/input-comparison-20261004/After-comparison.
- GitHub: https://github.com/cenationx/ProjectSarah, branch main. Git author already
  configured. Authentication in this separate app still needs a harmless check.
- Saves/logs/backups/dependencies are local and ignored, not included in GitHub.

## Automated checks

Working directory: `G:\Codex\Project Sarah`. Local Python:
`C:\Users\rudol\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe`.
Each suite imports Lupa from tools/dependencies/python; no install is required.

Run all 6 suites via the single-entry verification runner (153 checks total):
```powershell
$sarahPython = 'C:\Users\rudol\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe'
& $sarahPython tools/run_tests.py
```
See `docs/verification-workflow.md` for runner options, interpreter resolution, and generated Markdown/JSON reports in `tools/reports/`.
To test the runner itself (11 unit tests):
```powershell
& $sarahPython tools/test_runner.py
```

Run acceptance preflight tool before native testing (read-only inspection):
```powershell
& $sarahPython tools/preflight.py
```
To test the preflight tool itself (14 unit tests):
```powershell
& $sarahPython tools/test_preflight.py
```

Expected totals across 6 offline suites: 29 + 15 + 8 + 54 + 33 + 14 = 153 checks, plus 11 runner self-tests and 14 preflight tests. These execute actual Lua with simulated
engine/UI fixtures. They do not establish native game compatibility or input.
For consolidated native acceptance, follow `docs/M1-batched-acceptance.md`. Bulk Unicode typing and automated function keys were
unreliable in this game; physical/user checks and real observations must be labelled.

## Permissions and scope

The user authorized broad G-drive file access and PowerShell commands for
Antigravity Project Sarah to reduce routine prompts. Local app permission settings
are separate from Git and project instructions. File Allow rules for G:\ reads
and writes, plus a Terminal Commands Allow * rule were saved and visually checked.
The terminal wildcard covers all terminal commands, including PowerShell/native
tools; it is not a shell-only or G-drive-only execution boundary. Global/inherited
policies and other tool categories may still prompt. No command execution was
started through Claude to test approval behavior.

Broad capability does not change Sarah's work scope: keep project outputs under
the canonical checkout, preserve normal saves and installed game files, and do
not start the external AI layer. App permissions do not travel with this repo.
