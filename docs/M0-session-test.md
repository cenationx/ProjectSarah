# M0 disposable session test: 2026-10-04

Installed game: Build 42.21.0. Only SarahFoundation enabled in the isolated
profile. No external AI. Production foundation source was unchanged.

With the game closed, the dated death-test world was copied to
`runtime/backups/sessions-before-20261004`. A separate `SarahSessionAlive` world
was copied from the untouched pre-recovery backup. Neither case overwrote the
other. Recovery requires preserving the current case before copying a backup
to another disposable directory; normal saves were never used.

`tools/FoundationSessionProbe.lua` was deployed temporarily. It checks the exact
world name, world-specific metadata marker, death state, tagged NPC count and
`IsoPlayer.getInstance()` identity. In the alive case it also repeats ensure and
save. Its metadata marker is published by the game's subsequent save.

- Alive case: checkpoint b restored; exactly one living tagged Sarah; repeated
  ensure succeeded; save a succeeded; player instance preserved.
- After closing and restarting the entire game, the original dated death case:
  death flag true, controller NPC nil, zero tagged live Sarahs; ensure refused
  resurrection; player instance preserved.
- 19 automated foundation checks passed again.

Evidence: [alive](../evidence/foundation-session-alive-summary.txt) and
[dead](../evidence/foundation-session-dead-summary.txt).

This verifies independent cases across full process restarts. It does **not**
verify menu return/continue or world switching within the same game process.
Repeated automated Escape input did not open the pause menu; cause unresolved.
No foundation failure was observed. Live Lua reload also remains untested.
The existing map-load warnings remain unresolved. Appearance was not clearly
verified in the alive view; engine equipment count is still the narrower claim.

Both sessions were closed with Alt+F4, the temporary driver was moved to
`runtime/disabled-probes`, and Continue was left pointing at the death case.
Both disposable worlds and backups remain local and are excluded from Git.

Follow-up: [menu/world transition test](M0-menu-transition-test.md) subsequently
verified same-process menu return, Continue and alive/dead/alive switching.
[Main-script reload](M0-reload-test.md) also passed separately. The limitations
above describe this earlier full-restart test, not the latest project state.
