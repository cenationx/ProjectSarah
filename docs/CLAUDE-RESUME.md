## Latest checkpoint: offline candidate collector (2026-10-06)

Codex owns checkout. CandidateCollector.lua is implemented OFFLINE and inert,
with injected read-only queries, private state, fixed call/candidate/cursor limits,
round-robin list cursors and transactional lifecycle discard. See COLLECTOR-OFFLINE.md.
Gemini 3.8 Flash HIGH authored code/base fixtures via NO-TOOLS drafts/structured
CLI exports; Codex applied/reviewed, fixed a budget-boundary starvation bug,
corrected fixture assumptions and added review regressions. Gemini did not edit
checkout. User explicitly prefers coding delegated to Gemini, Codex review/tests.
All 401 suite checks across 10 suites +11 runner +19 preflight self-tests PASS.
No native imports/production wiring/deployment/game launches or saves/settings
changes. Latest deployed baseline remains 5fa6b9c; disposable world/backups unchanged.
Tokens are caller-issued strings only; native identity/exposure and independent
lighting remain unresolved. Follow/rendering native gates pending, live tests
deferred, external/model AI ON HOLD. Next offline task: adapter identity/token and
exact-enum boundary investigation/fixtures, not gameplay or tick integration.
Temporary Remote Control session remains available in empty Admin visibility-test;
visible drafts were followed by structured CLI source exports for reproducibility.
Older state/counts below are historical and superseded by this block.

## Latest checkpoint: reviewed adapter diagnostic design (2026-10-06)

Codex owns the checkout. NATIVE-ADAPTER-DIAGNOSTIC-SPEC.md is a reviewed design,
not an implemented collector or native probe. Gemini 3.8 Flash HIGH drafted with
NO TOOLS through the user-visible temporary interactive Remote Control session;
Codex corrected hidden-position leakage, unsupported generation/identity claims,
enumeration fairness and explicit budget/lifecycle boundaries. Gemini did not edit
this checkout. No production changes, deployment, game launches or saves/settings
changes. Independent lighting and native Follow/rendering remain unresolved.
The verified code baseline remains aa7595f: 332 suite checks +11 runner +19 preflight
self-tests passed there. This docs-only checkpoint validates text/diff consistency;
those suites were not rerun. Latest deployed baseline remains 5fa6b9c.
Next: pure injected CandidateCollector policy and actual-Lua budget/fairness/reset
fixtures; resolve identity tokens offline before any native registry. No native
wiring. Live testing deferred; external/model AI ON HOLD. Temporary Gemini session
remains available for visible NO-TOOLS drafts, in the empty Admin visibility-test
workspace. It grants no Sarah checkout editing ownership or gameplay permissions.
Earlier state blocks and counts below are historical.

# Current Codex resume: offline coverage helper (2026-10-06)

Codex owns G:\Codex\Project Sarah. Read AGENTS, STATUS, ROADMAP, HANDOFF,
PERCEPTION-V1, COVERAGE-OFFLINE and NATIVE-PERCEPTION-ADAPTER-RESEARCH before editing.
Verify clean Git main/origin and ownership. Coverage helper is implemented offline
with injected queries/private budgets/no cross-call cache and 64 actual-Lua checks.
All 332 suite +11 runner +19 preflight self-tests PASS. No production integration,
deployment, game launch, saves/settings changes. Independent light unresolved:
-1 light path refresh bypass/shared-buffer read/square write confirmed in bytecode.
Next offline task: inert native adapter diagnostic specification for exposure,
enums, bounded enumeration/fairness, session IDs and lifecycle reset boundaries.
Live Follow/rendering tests remain pending and deferred; external/model AI ON HOLD.
Gemini HIGH authentication works outside sandbox but headless command permission
was denied. No bypass used; source-in-prompt NO-TOOLS proposals worked. Codex
applies/reviews/tests and alone edits/commits/pushes. Historical guidance follows.

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
To test the preflight tool itself (19 unit tests):
```powershell
& $sarahPython tools/test_preflight.py
```

Expected totals across 6 offline suites: 29 + 15 + 8 + 54 + 33 + 14 = 153 checks, plus 11 runner self-tests and 19 preflight tests. These execute actual Lua with simulated
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
