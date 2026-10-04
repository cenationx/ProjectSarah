# M0 menu/world transitions: 2026-10-04

Build 42.21.0, only SarahFoundation enabled in the exact isolated profile. Both
disposable worlds, isolated key file and latest-save selection were backed up
with the game closed to `runtime/backups/menu-before-20261004`. Restore only with
the game closed and after preserving the current case; copy into a new isolated
disposable directory. Normal saves/settings and installed files were untouched.

`FoundationMenuProbe.lua` temporarily adds a mouse button calling the installed
game's `ToggleEscapeMenu` with its configured menu key. The actual pause menu
Quit option and main-menu Continue/Load/Play controls handle all transitions.
It logs main-menu controller state. `FoundationSessionProbe.lua` checks world
marker, death state, tagged NPC count and local-player instance; alive cases also
repeat ensure and save. Production foundation source is unchanged.

Automated Escape input remains unreliable. The profile key file was empty and
the installed default binding was Escape; no binding was changed. The test
button validates the menu handler and subsequent transitions, not physical
Escape-key delivery. The sandbox cannot see the separately launched GUI process;
its identity is checked outside that sandbox when verifying process continuity.

## Observations

- Initial alive world: one living Sarah restored and saved; player preserved.
- Quit returned to main menu; controller nil. Same process/start time confirmed.
- Continue reopened the alive world: one living Sarah restored, no death flag,
  saved world marker matched, repeated ensure/save passed, player preserved.
- Quit returned to main menu with controller nil before selecting the dated
  death case through Load/Play.

- Death world selected through Load/Play: saved death flag true, no controller
  NPC, zero tagged live Sarahs, ensure did not resurrect her, player preserved.
- Quit returned to main menu with controller nil again. Load/Play selected the
  alive world: checkpoint a restored, one living tagged Sarah, death flag absent,
  correct saved world marker, repeated ensure/save passed, player preserved.
- Java process ID 18188 and start time 06:02:27 remained unchanged through the
  initial alive load, same-world Continue, death load and final alive load.
  Lua/main-menu reinitialization occurred inside that same process.
- Alt+F4 closed the game and saved checkpoint a. Native window inventory then
  confirmed the game window was absent. Both temporary drivers were moved to
  `runtime/disabled-probes`; Continue selects `SarahSessionAlive`.

Evidence: [complete sanitized sequence](../evidence/foundation-menu-transition-summary.txt).

Result: menu return, same-world Continue and alive-to-dead-to-alive switching
passed in the isolated single-player setup. No production fix was necessary.
The existing 19 automated checks cover unchanged foundation source; this task
adds direct live evidence rather than another simulated test.

Map/engine load errors remain unresolved; no entirely error-free claim.
Appearance, broader module reload, incomplete-cleanup references, offscreen
travel, write failures and longer sessions remain separate checks. No AI.
