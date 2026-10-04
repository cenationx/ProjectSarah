# Project Sarah — M0

Started: 2026-10-04. Requested target: Project Zomboid 42.21.
Project folder: `G:\Codex\Project Sarah`.

M0 is the NPC framework compatibility gate. The AI layer has not been created or started. No model, AI service, dialogue system, or integration has been installed.

## Current decision

**Minimal NPC foundation demonstrated on 42.21.0.** An isolated prototype passed spawn, an explicit walking action, inventory transfer, death/removal, and restoration after a full game restart. See [live results](docs/M0-live-test.md).

**Unmodified upstream PZNS still fails compatibility.** Its full framework was not ported or live-tested. A separate unverified mechanical candidate is preserved for further evaluation. See [the baseline report](docs/M0-PZNS-compatibility.md).

## Contents

- `vendor/PZNS`: unmodified upstream source, pinned by its checked-out commit; MIT license retained.
- `tools`: reproducible source/binary inspection and headless JVM API probe.
- `evidence`: test results from the installed game.
- `docs`: findings and M0 acceptance criteria.

## M0 acceptance criteria

1. Confirm game version from a launch log or UI. PASS: 42.21.0, revision 4a0e9546ec, confirmed from the normal profile's version/log and isolated game UI.
2. Resolve mod discovery and essential NPC API incompatibilities in an isolated candidate.
3. Load the candidate in a separate cache/profile with a new disposable single-player save.
4. Spawn one human NPC; verify movement, inventory, death/despawn, and save/reload behavior without errors.
5. Record observed results and a pass/fail decision before implementing the AI layer.

Current M0 result: the narrow single-player NPC feasibility gate passes with the independent prototype. Full PZNS compatibility, longer-term stability, production persistence and multiplayer remain unresolved. All live tests used a disposable world under this project; normal game saves and settings were not changed. The test game was closed afterward.
