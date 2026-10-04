# M0 evidence and development handoff

Reviewed 2026-10-04 against source and recorded reports through `8884306`.

The narrow NPC feasibility gate passes. The hardened foundation has enough
bounded evidence to plan a manual command console in the isolated test profile.
It is an experimental development foundation, not a normal-play companion or
a complete PZNS port. Broader hardening remains open; this review does not accept
untested limitations on the user's behalf or mark release readiness complete.
External AI remains on hold.

## Tested envelope

Installed Project Zomboid 42.21.0, revision 4a0e9546ec; single player, one Sarah,
exact cache `G:/Codex/Project Sarah/runtime/isolated`. Installed game files remain
read-only. Tests used independent disposable worlds with game-closed backups.
The production rendering addition is restricted to FBO view 0, visible same-floor
squares and a resident, complete, alive tagged NPC. No multiplayer support.

Earlier reports preserve what was known at their test date. Later evidence below
resolves some earlier open checks; historical test counts are not current totals.

## Evidence matrix

| Capability | Evidence type and observed result | Boundary / source |
|---|---|---|
| Unmodified PZNS | Installed binary/source inspection and headless JVM resolution: essential APIs absent | FAIL; no complete framework port or live compatibility claim. [Baseline](M0-PZNS-compatibility.md) |
| Independent NPC feasibility | Native live prototype: spawn, one explicit walking action, Bandage transfer, death/removal and token restoration after full restart | These basic actions were demonstrated in the prototype, not a tested general command interface. [Prototype](M0-live-test.md) |
| Foundation lifecycle | Native live spawn/ensure/unload/restore/restart; one tagged Sarah, clothing and local player preserved | Controlled cases; no broad combat or crowds. [Foundation](M0-foundation-live-test.md) |
| Corrupt latest slot | Live deliberate two-byte truncation: latest rejected, older good checkpoint restored and promoted | One corruption form; arbitrary partial binary integrity is unproven. [Recovery](M0-foundation-live-test.md) |
| Death tombstone | Native live death and full restart: zero living Sarahs, no resurrection | Death world independent of alive cases. [Death](M0-foundation-live-test.md), [sessions](M0-session-test.md) |
| Menu/world transitions | Native live same-process Continue and alive/dead/alive switching; state reset and player preserved | Temporary mouse entrypoint used the real menu handler; physical Escape input remains unverified. [Transitions](M0-menu-transition-test.md) |
| Lua reload and incomplete removal | Live unchanged-source Engine/Lifecycle/main reload, single tick/save callback; injected Lua interruption after native removal pinned the real reference, refused replacement/unsafe save, recovered on full restart | Injected adapter fault, not spontaneous native failure; no hot schema upgrade claim. [Reload/cleanup](M0-module-cleanup-test.md), [main reload](M0-reload-test.md) |
| Clothing and world appearance | Actual-NPC model viewer and ordinary fresh/restored world scenes passed | Tested room/same floor; broader cutaways, cursor states and event availability open. [Appearance/control](M0-appearance-control-test.md), [rendering](M0-world-render-test.md) |
| Travel suspension/recovery | Controlled player debug travel caused real square unloading; away restart deferred, return restored saved position/token/inventory | Player teleported for the test; Sarah was not. Ordinary walking/driving, abrupt movement and floors unverified. [Travel](M0-travel-test.md) |
| Failed existing-file write | Real Windows exclusive lock exposed swallowed native error; fresh UUID readback fix retained Sarah/metadata, old hash unchanged, retry/restart passed | Final cleanup guard passed later healthy restart/save; disk-full, mid-write and crash not covered. [Write failure](M0-write-failure-test.md) |
| Repeated healthy cleanup | Six-minute idle-room live run: 12 unload/restores, 25 verified saves and verifier removals; later world-list checks and full restart passed | Not hours-long play or proof of all JVM/native resource reclamation. [Long session](M0-long-session-test.md) |
| Defensive policies | 48 automated actual-Lua checks with fake engine objects/events: 27 foundation, 13 adapter, 8 checkpoint | Simulation evidence, including thrown/silent verifier cleanup failures. [Foundation checks](../evidence/foundation-policy-tests.txt), [adapter checks](../evidence/foundation-render-tests.txt), [readback checks](../evidence/checkpoint-readback-tests.txt) |
| Installation warnings | New no-mod world reproduced duplicate/invalid room metadata errors | Sarah not required to trigger them; cause unknown. Font/map warnings persist; no entirely error-free claim. [Control](M0-appearance-control-test.md) |

## Persistence and stop conditions

Binary saves alternate a/b and retain the prior metadata record. The adapter
reads a fresh UUID back from a temporary NPC before accepting a write; it restores
the local player instance and checks verifier cleanup. This is not atomic file
replacement, a checksum of the whole file or a guarantee against every corruption.
Death may remove the engine-associated NPC file; the saved tombstone prevents
fresh resurrection. A checkpoint restores only its saved location when eligible.

Travel polls every 120 ticks: beyond 32 tiles or a different floor it attempts
save/unload, and within 16 tiles of the saved square/floor it can restore when
loaded and free. It performs no offline simulation or teleport-to-player action.
Manual unload stays dormant in-session until an explicit restore request.

For a failed write, remove only the known test fault and retry when the object is
still resident and cleanup is healthy. For an incomplete object/verifier cleanup,
duplicate, failed recovery or TRAVEL_BLOCKED condition, stop issuing mutations,
preserve the log/case and investigate. Never clear a pinned reference or erase
metadata to force a replacement. Full process restart from the last good
checkpoint is the demonstrated interrupted-removal recovery; unsaved changes
can be lost. An unavailable saved square should defer, not spawn a substitute.

Back up before a new live test with the game closed. Before restoring a backup,
preserve current state, then copy into another disposable directory. Do not
restore over the only copy. Normal profiles, installed game files and global
settings are outside this development scope. See [handoff](HANDOFF.md).

## Handoff decision and remaining work

Proceed with planning the model-free M1 console and validated action boundary.
The next implementation slice should be read-only UI/commands in the isolated
profile, followed by stop/walk tests with their own evidence. Carry every M0
guard and limit into M1; do not bypass them through a debug console.

Before broader use or release, resolve or explicitly review: normal walking and
driving travel boundaries, floors/cutaways/cursor delivery, combat/crowds, long
play sessions, native cleanup/resource failures, disk-full/crash/partial writes,
changed-schema reloads and safe installation outside the exact isolated path.
Multiplayer and full PZNS modernization remain outside the initial scope.

No new gameplay or automated runs were needed for this documentation review.
The latest live evidence is the completed module/cleanup checkpoint. M0's scope
review is complete; broad hardening acceptance remains open. No AI/model service,
dialogue or provider integration is authorized by the console plan.
