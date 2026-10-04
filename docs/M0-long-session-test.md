# M0 bounded longer session: 2026-10-04

Bounded live test PASS. Six-minute idle-room test, 12 cycles approximately 30 seconds apart,
two verified saves and one unload/restore per cycle. Final completion save and
full-process restart also passed. This does not test hours of play, combat, movement
or JVM heap reclamation. External AI remains on hold.

Game-closed source case SarahWriteFailureRetest and selections are backed up at
`runtime/backups/long-session-before-20261004`. A separate SarahLongSessionCase
is the only target. Original cases are preserved. Restore only game-closed after
preserving the current case, into a new disposable directory.

Temporary FoundationLongSessionProbe wraps the current adapter's remove method
to observe real removed NPCs/verifiers without changing removal behavior. Every
60 ticks it requires previously removed objects to have no square and be absent
from object/add/remove lists, then releases its observation references. It also
scans these lists for any CheckpointVerifier. Each cycle checks fresh write UUID,
persisted cycle marker, one Sarah, clothing and local-player preservation. These
are registration/reference checks, not proof of model/descriptor memory cleanup.

Local engine inspection shows removed IsoPlayers are intentionally kept briefly
for emitter cleanup (a private recently-removed collection). This probe does not
inspect that private collection or force garbage collection. Passing world-list
checks must not be described as proving that every native resource is reclaimed.

All 12 cycles passed, completion after 365000 ms (6 minutes 5 seconds): 25
verified saves and 25 temporary verifiers removed. Previously removed Sarahs and
verifiers cleared object/add/remove lists on subsequent checks, and the adapter
released its verifier reference. Each restore retained its current cycle marker;
one Sarah, three worn items and local player preserved. Exit saved slot b.
[Cycle evidence](../evidence/long-session-summary.txt),
[completed scene](../evidence/long-session-complete-scene.png).

Full restart restored slot b with cycle 12, exactly one Sarah, three worn items
and original local player instance. Ordinary scene visibility passed. Exit saved
slot a successfully. No foundation/probe FAIL was logged in either run.
[Restart evidence](../evidence/long-session-restart-summary.txt),
[restart scene](../evidence/long-session-restart-scene.png).

No production changes were needed. Game closed, confirmed by native inventory;
temporary driver disabled outside the mod. Continue selects SarahLongSessionCase
with LongSessionDone=true. Do not repeat the cycles against this completed case;
new matching guarded case/marker preparation is required. Backup group includes
Original-retest, Completed-before-restart and Final-restart plus selections.
Existing automated suite remains 48 checks; this live probe is additional evidence.
Normal profile console stayed unchanged (18675 bytes, 04:03:05); installed game
files were read-only. Previously documented font/map metadata warnings remain.

Remaining boundaries: hours-long play, combat/travel/floor transitions, complete
native resource reclamation and broader module reload are not established by
this test. Healthy cleanup passed; exceptional cleanup is a separate gate.
