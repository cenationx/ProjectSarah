# M1 read-only console slice A: 2026-10-04

IN PROGRESS: read-only slice A implemented; physical F9 check completed, broader
keyboard acceptance still open. Commands/Observations/Console implement help, status and inventory only;
no external AI or movement commands. Twelve automated actual-Lua command checks,
eight simulated UI/key/session checks and all 48 existing M0 checks passed.
Existing M0 source is unchanged. Automated tests do not establish native input.

Game-closed SarahModuleCleanupCase, selections and keysB42.ini backed up to
`runtime/backups/console-before-20261004`. Separate SarahConsoleCase is the test
target. Preserve current state before any game-closed restore into a new case.
Installed files and normal profile are untouched. Console only opens in exact
isolated single-player profile. F9 named binding and context-menu fallback;
conflicting runtime bindings refuse keyboard open. No normal key file changes.

## Direct native evidence

- Menu fallback opened the panel, native input field focused and mouse Close
  removed it. Opening did not change normal game speed.
- Individual native letter presses entered `status`, `help` and `inventory`.
  Enter submitted status/inventory; Run submitted help. Bulk Unicode typing did
  not enter text in this game, so individual presses were used and visually checked.
- Status reported active Sarah, player 10768/10271/0 and NPC 10770.47/10271.15/0.
  Inventory reported four items: Bandage and three equipped clothing items.
- Observational samples throughout showed one tagged Sarah, preserved local
  player, focused entry while open and unchanged player position while typing
  `status` (including movement-bound S/A). Focus cleared after mouse close.
- F9 was registered as runtime key 67 and visible in the game's key settings.
  Initial settings exposed untranslated labels; added English UI translations.
- Automated F9/Escape did not close the first panel. Installed engine inspection
  showed ordinary key callbacks are bypassed during native text entry. Final code
  uses raw game-thread key edges, consumes the closing release and checks runtime
  primary/alternate conflicts. Eight simulated checks cover hold-repeat, focused
  Escape, rebind, collisions, text-entry exclusion, reset, reload and output bounds.
- Automated F7 was also missed by the vanilla rebind dialog. Physical key delivery
  and native rebind persistence cannot be declared passed from those attempts.

The initial large list font/fixed row height clipped the final result. Final code
uses native font metrics and scroll padding. After full restart, inventory harness
submission returned four items with the same NPC/player and unchanged position.
Actual typed help/Enter then produced scrolling output with the final completion
row fully visible (`console-final-scroll-live.png`).
First live state/log preserved locally as First-live-before-repair and
runtime/console-first-console.txt. Screenshots show that initial native status and
inventory; they are historical evidence, not final-font acceptance.

## Remaining gate

The user completed the requested physical F9 open, status/Enter, F9 close check.
Probe samples corroborated panel=true/focused=true followed by panel=false/focused=false,
with one Sarah and unchanged local player/position. This is a user-operated check;
no screenshot of the user's status submission was captured. Full restart restored
one Sarah from a, and the console started closed before that check.

Still open: native hold-repeat, Escape, rebind/conflict persistence, English labels
in Options, restored movement input and same-process menu/world teardown. These
have simulated coverage where applicable, not complete native acceptance.
Do not add stop/walk or claim M1 complete before this gate is resolved. AI stays
on hold. Temporary probe's `Console test: inventory` is explicitly a harness
submission for final rendering checks, not evidence of physical typing.

Final state: game closed, saved b; final world backed up as Final-console. Probe
disabled outside the mod; production modules deployed. Raw final log retained
locally; sanitized Sarah-only summary in evidence/console-live-summary.txt. Normal
profile console still 18675 bytes / 2026-10-04 04:03:05; installed game untouched.

## Native follow-up: Codex session 2026-10-04

User reports physical F9 shows the console and Escape works in the isolated
SarahConsoleNativeCase. Record this as user-operated F9 open / Escape close
confirmation. Hold duration/repeat and absence of a pause menu after closing
were not explicitly reported, so those details remain pending. Rebind/conflict
persistence, English Options labels, movement restoration and same-process
console teardown remain open. No production code changes from this result.
