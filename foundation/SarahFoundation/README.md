# Sarah NPC foundation candidate

Experimental single-player foundation for installed Project Zomboid 42.21.0.
No external AI or custom console implementation. Keep SarahM0 disabled; use only
the exact isolated profile under this project. See the current
[M0 scope review](../../docs/M0-supported-scope.md) and its linked reports.

The lifecycle prevents duplicate/partial adoption, alternates checkpoints,
promotes recovered fallbacks, refuses fresh replacement after failed recovery,
retains unfinished references and records death tombstones. Fresh UUID binary
readback validates saves and checks verifier cleanup; this is not atomic
replacement or full-file integrity validation.

Travel attempts save/unload beyond 32 tiles or another floor, then defers saved-
location restoration until the player is within 16 tiles on that floor and the
square is loaded/free. Manual unload stays dormant until explicit restore in
that session. Failed unattended recovery blocks retries; do not erase references
or metadata to bypass it. See [travel limits](../../docs/M0-travel-test.md).

The adapter preserves the local player instance. Three clothing items survived
unload/restart and actual model/world inspection. B42 FBO rendering uses a bounded
world event for the resident, visible same-floor NPC; broader cutaway, cursor and
floor behavior remains unverified.

48 actual-Lua automated checks use fake engine objects/events: 27 foundation,
13 adapter and 8 checkpoint readback. Run `tools/test_foundation.py`,
`tools/test_render.py` and `tools/test_checkpoint.py` with project-local Lupa.
They verify policies, not general gameplay compatibility.

Native live evidence includes save/restart, corrupted-slot recovery, saved death,
menu/world transitions, unchanged-source module reloads, locked-file failure/retry
and a six-minute repeated-save session. Injected interruption after native removal
preserved the real reference through reload and refused unsafe replacement/save;
full restart recovered the good checkpoint. Spontaneous native cleanup failures
and complete resource reclamation remain unproven.

The read-only console adds 12 command and 8 simulated UI/key/session checks.
Menu opening, actual typed status/help/inventory, Enter/Run and mouse close
passed in the isolated game. Physical F9 passed the user check; native
rebind/Escape/menu acceptance remains open;
see [console evidence](../../docs/M1-console-test.md). Next, finish that gate
before stop or walk here. Broad M0 hardening/release acceptance remains open.
All existing safeguards stay in force;
AI integration requires a separate explicit instruction.
