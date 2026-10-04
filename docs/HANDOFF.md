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

Latest runtime state: game closed, only SarahFoundation enabled in the isolated
default. Continue selects `Rising/SarahAppearanceFresh`, a separate copy of the
new mod-free control `Rising/2026-10-04_06-16-14`; that original world's mods.txt
remains empty. Older alive/dead cases are preserved. Appearance model viewer
passed before/after restart; ordinary world visibility is the next check.
All temporary drivers, including appearance, are disabled outside the mod.
Backup `runtime/backups/appearance-before-20261004` preserves both older worlds,
original default/key/latest-save files, `FreshControl-before-reload`,
`FreshControl-after-reload`, `Appearance-before-restart` and `Appearance-final`.
Restore only game-closed after preserving the current case into a new directory.
See `M0-appearance-control-test.md`; metadata errors reproduced with no mods.

- Installed game: `G:\Games\ProjectZomboid`, read-only.
- Isolated profile: `runtime/isolated` under the canonical project.
- Test world: `runtime/isolated/Saves/Rising/2026-10-04_04-21-54`.
- Separate alive case: `runtime/isolated/Saves/Rising/SarahSessionAlive`, copied
  from the pre-recovery backup and live-tested on 2026-10-04. The original dated
  world remains dead. Continue now selects the newer appearance case above.
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
  independent and is currently selected by Continue. Before restoration, close
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
prove gameplay compatibility. Expected latest result: 19 total checks passed.

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

## Antigravity setup verified on 2026-10-04

Project Sarah was added in the Antigravity desktop app from the canonical folder.
The project customization breakdown explicitly listed
`g:\Codex\Project Sarah\AGENTS.md` as a loaded rule. The new-conversation screen
showed local execution and Claude Sonnet 5.5 Medium selected. A resume prompt was
prepared in the composer but not submitted; no Antigravity agent was started.
Re-check selection and draft availability when returning to the app.

Security and plan-review presets were inherited from global settings; they were
inspected without changes. No permission rules or GitHub app authentication were
configured or tested. Git uses the existing local repository and remote.
The app warned that its bundled customization/skills token budget was exceeded;
Sarah's AGENTS.md was nevertheless shown in the loaded rules breakdown. Unrelated
global skills/settings were left unchanged.
