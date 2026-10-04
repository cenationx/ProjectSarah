# Immediate coding handoff: Escape failure (2026-10-04)

This task supersedes the older resume prompt below. Codex has released the
checkout. The user will start Claude; do not assume a background agent exists.
Read AGENTS.md, CLAUDE.md, STATUS, ROADMAP, HANDOFF and M1-console-test first.
Check Git and preserve other work. Game is closed; saves backed up.

Fix M1 slice A Escape handling: user reports first Escape opens the pause menu
while Sarah Console is open; second Escape closes the console. Expected first
Escape closes the focused console without opening the game menu. Inspect actual
Build 42.21.0 input ordering/focus/paused callbacks and use a narrow supported fix.
Do not assume root cause; existing simulated Escape test passes but misses this
native result. Add meaningful regression coverage for the actual ordering found;
run all five suites. Do coding, read-only API inspection and automated tests only.
Do not launch/control the game or modify isolated saves, settings or deployed mod.
Keep external AI on hold and do not add stop/walk until slice A accepted.
Update shared notes, commit/push checkpoint, verify remote and release checkout
for Codex to deploy into a backed-up isolated case and retest native behavior.
Label the fix native-unverified until Codex/user confirms it. Report changed files,
tests, checkpoint and the exact native retest required.

---
# Claude resume guide: 2026-10-04

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
- Continue selects isolated `Rising/SarahConsoleCase`, only SarahFoundation enabled.
- Final exit saved b; one Sarah restored from a before the final checks.
- Temporary console probe disabled under runtime/disabled-probes; production
  console/modules/English UI.json deployed to the isolated mod.
- Latest backup group: runtime/backups/console-before-20261004, including original
  module-cleanup case/selections/keys, First-live-before-repair and Final-console.
- GitHub: https://github.com/cenationx/ProjectSarah, branch main. Git author already
  configured. Authentication in this separate app still needs a harmless check.
- Saves/logs/backups/dependencies are local and ignored, not included in GitHub.

## Automated checks

Working directory: `G:\Codex\Project Sarah`. Local Python:
`C:\Users\rudol\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe`.
Each script imports Lupa from tools/dependencies/python; no install is required.

```powershell
$sarahPython = 'C:\Users\rudol\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe'
& $sarahPython tools/test_foundation.py
& $sarahPython tools/test_render.py
& $sarahPython tools/test_checkpoint.py
& $sarahPython tools/test_commands.py
& $sarahPython tools/test_console.py
```

Expected totals: 27 + 13 + 8 + 12 + 8 = 68. These execute actual Lua with simulated
engine/UI fixtures. They do not establish native game compatibility or input.
For backed-up live tests, use tools/launch-isolated.ps1 -NoDebug and the exact
isolated profile in HANDOFF. Bulk Unicode typing and automated function keys were
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

