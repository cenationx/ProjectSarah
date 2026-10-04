# Project Sarah — M0

Started: 2026-10-04. Requested target: Project Zomboid 42.21.
Project folder: `G:\Codex\Project Sarah`.

**Continuing with another agent?** Read [current status](docs/STATUS.md),
[roadmap](docs/ROADMAP.md), [handoff/setup](docs/HANDOFF.md) and [agent instructions](AGENTS.md).
These files are the shared checkpoints and must be updated as work progresses.

M0 is the NPC framework compatibility gate. The AI layer has not been created or started. No model, AI service, dialogue system, or integration has been installed.

## Current decision

**Minimal NPC foundation demonstrated on 42.21.0.** An isolated prototype passed spawn, an explicit walking action, inventory transfer, death/removal, and restoration after a full game restart. See [live results](docs/M0-live-test.md).

**Unmodified upstream PZNS still fails compatibility.** Its full framework was not ported or live-tested. A separate unverified mechanical candidate is preserved for further evaluation. See [the baseline report](docs/M0-PZNS-compatibility.md).

## Contents

- `vendor/PZNS`: unmodified upstream source, pinned by its checked-out commit; MIT license retained.
- `tools`: reproducible source/binary inspection and headless JVM API probe.
- `evidence`: test results from the installed game.
- `docs`: findings and M0 acceptance criteria.
- `foundation/SarahFoundation`: experimental hardened NPC lifecycle candidate; 19 automated checks pass, plus isolated spawn, duplicate prevention, unload/restore, full restart and corrupted-checkpoint recovery checks. See [candidate status](foundation/SarahFoundation/README.md).

## License

Project Sarah's original code and documentation are offered under the [PolyForm Noncommercial License 1.0.0](LICENSE), with the [required copyright notice](NOTICE). Noncommercial use, modification and redistribution are permitted under its terms; commercial uses outside those permissions require separate permission from cenationx. This project is source available.

This licensing change applies from the commit introducing it. The earlier published MIT versions, including commit `e70019c2cf9aedfa007d4a312626a1dd72a92be6`, retain their MIT permissions. Changing this repository's license does not revoke those permissions or prevent commercial reuse of those earlier versions.

Third-party material retains its own license. PZNS by shadowhunter100 remains MIT licensed; its original notice is preserved in [the PZNS license copy](docs/PZNS-MIT-LICENSE.txt) and in the local upstream checkout. Project Sarah's noncommercial terms do not restrict rights independently granted for PZNS. Project Zomboid game files are not covered by this license and are not distributed here.

## M0 acceptance criteria

1. Confirm game version from a launch log or UI. PASS: 42.21.0, revision 4a0e9546ec, confirmed from the normal profile's version/log and isolated game UI.
2. Resolve mod discovery and essential NPC API incompatibilities in an isolated candidate.
3. Load the candidate in a separate cache/profile with a new disposable single-player save.
4. Spawn one human NPC; verify movement, inventory, death/despawn, and save/reload behavior without errors.
5. Record observed results and a pass/fail decision before implementing the AI layer.

Current M0 result: the narrow single-player NPC feasibility gate passes with the independent prototype. Full PZNS compatibility, longer-term stability, production persistence and multiplayer remain unresolved. All live tests used a disposable world under this project; normal game saves and settings were not changed. The test game was closed afterward.
