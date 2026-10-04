# M0 existing-checkpoint write failure: 2026-10-04

Bounded test PASS after fixing a demonstrated failure: Build 42.21.0, single player, exact isolated profile. AI on hold.
Separate SarahWriteFailureCase copied from returned travel case. Original travel
case and selections backed up game-closed to
`runtime/backups/write-failure-before-20261004`. Preserve current state before
restoring a backup into a new disposable case with the game closed.

Installed `IsoPlayer.save(String)` reports IOException from file opening/writing
and closing; it does not return a success flag. The baseline adapter delegated
that call, and lifecycle published metadata after it appeared to return successfully.
Existence alone could be misleading if Lua swallowed the exception and an old
target already existed, so this live test deliberately keeps that old file.

The project-local helper holds slot a with an exclusive Windows file handle.
It changes no bytes, attributes or permissions; it releases on a cache-local
probe signal or after five minutes. Slot b is the latest restored checkpoint
and remains available. Hash comparison checks that the old a file is unchanged
before the successful retry. Runtime dependency files, raw logs and saves stay
local and excluded from Git.

Temporary FoundationWriteFailureProbe attempts save/unload while a is locked,
asserts NPC and checkpoint metadata are retained despite the old a file still
existing, signals release, retries unload and restores the new a checkpoint.
A new NPC token distinguishes a real new write from loading stale a contents.
Then a full-process restart checks that new contents persist. Probe is guarded
to this disposable case and does not inject a fake adapter exception.

The baseline FAILED: native FileNotFoundException reported the Windows sharing
violation, but Lua continued, logged SAVED a and unloaded the NPC. The old a
file remained unchanged (helper hash comparison). This proves the native error
was swallowed at the Lua boundary and existence could falsely validate a save.
[Baseline failure](../evidence/write-failure-baseline-summary.txt).
The failed case is preserved as Failed-baseline; no original case was repaired
or overwritten. A fresh SarahWriteFailureFixed was copied from the travel case.

The adapter now inserts getRandomUUID() into the NPC's checkpoint data and
reads the binary back into a temporary non-player NPC. Only the current UUID,
Sarah identity and alive state validate the write. The verifier is removed in
success/failure paths, local player instance is restored, and unsuccessful
verification restores the in-memory prior marker. Cleanup failure pins the
temporary reference and blocks further saves. Lifecycle then retains its real
NPC/checkpoint metadata on failure instead of publishing stale contents.
The verifier is not the controller NPC and no game tick runs between its
creation and cleanup. It is not drawn by Sarah's world callback.

48 automated checks pass: 27 foundation, 13 adapter and 8 new checkpoint checks.
The new checks execute the actual adapter with fake engine objects and cover
silent stale/missing writes, explicit write/read errors, fresh markers, player
preservation and thrown/silent cleanup failure. Cleanup checks actual square and
world-list removal (including pending removal), not just a returned void call.
[Readback tests](../evidence/checkpoint-readback-tests.txt).

The first fixed run correctly retained Sarah, but the test's release writer
rejected an unsupported .release extension. That harness failure was preserved
as Harness-failure; the helper was manually released without file changes.
[Harness result](../evidence/write-failure-harness-summary.txt).

Fresh SarahWriteFailureRetest with an allowed .txt release signal passed:
failed unload at tick 240 retained the same NPC and checkpoint table while old
slot a still existed; helper verified its hash unchanged and released on the
probe signal. Retry at tick 600 saved/restored a; tick 840 confirmed one Sarah,
new token contents, three worn items, preserved local player and another save.
[Fixed sequence](../evidence/write-failure-fixed-summary.txt),
[lock results](../evidence/write-lock-results.txt).
Full-process restart passed: slot a restored, exactly one Sarah retained the new
token, three worn items and local player instance. Sarah was visible in the
ordinary scene. Exit saved slot b successfully with the final cleanup-confirmation
guard deployed. The fault/retry sequence used the readback fix before that final
guard; exceptional cleanup failure paths have simulated coverage only.
[Restart result](../evidence/write-failure-restart-summary.txt),
[scene](../evidence/write-failure-restart-scene.png).

Game closed, confirmed by native window inventory; all lock helpers finished and
released. Final-restart backup preserves the completed retest case. Temporary
driver is disabled outside the mod. Continue selects SarahWriteFailureRetest;
its completed marker and existing release signal make this a finished one-shot
case. Do not repeat the fault helper without a new backed-up case, slot/marker
inspection and updated matching guards. Normal profile console remained unchanged
(18675 bytes, 04:03:05); installed game files were read-only. Existing game
font/map warnings remain outside this fix.

This adds live Windows write-lock coverage, not disk-full, process-crash or
arbitrary partial writes. Readback is stronger than existence, but is not an
atomic file replacement or full-file checksum; broader corruption guarantees
and temporary verifier behavior during exceptional engine cleanup remain open.
