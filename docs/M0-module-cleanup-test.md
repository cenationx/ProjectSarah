# M0 broader module reload and interrupted cleanup: 2026-10-04

Bounded live test PASS. Exact isolated single-player Build 42.21.0; AI on hold.
Game-closed SarahLongSessionCase and selections backed up to
`runtime/backups/module-cleanup-before-20261004`. New SarahModuleCleanupCase is
the only target; restore only game-closed after preserving current state into a
separate disposable directory. Normal profile and installed files untouched.

Temporary driver reloads Engine, Lifecycle and main twice using reloadLuaFile,
then checks the same controller/NPC, tick rate and real OnSave adapter count.
It next injects a Lua exception after the real Sarah removeFromWorld call but
before removeFromSquare. This deliberately leaves cleanup unfinished around a
real game object; it does not demonstrate a spontaneous native cleanup failure.
The wrapper is restored immediately after the attempted unload.

Expected behavior: retained reference, released transaction lock, refusal to
create/restore a replacement, retention through another full module reload and
later ticks, and no write over the last good checkpoint from a nonresident NPC.
Full process restart is the planned recovery; the test does not manually clear
the retained reference. The completion marker selects read-only restart checks.

First run PASS: both module reload passes returned Engine/Lifecycle constructors
and retained the controller/NPC. At tick600 the current callback had advanced
exactly 360 ticks, and one real OnSave invoked the adapter exactly once.
The injected partial removal then failed as intended; the reference and released
transaction lock survived a third full module reload and 360 more ticks.
Replacement remained refused. A subsequent real OnSave invoked no binary write
and left checkpoint metadata unchanged. Travel became blocked safely because
the pinned object was no longer resident. Exit also refused an unsafe write.
[First run](../evidence/module-cleanup-summary.txt).

Expected foundation FAIL and TRAVEL_BLOCKED entries reflect the injected fault
and protective refusals; they are not omitted from the evidence. Interrupted-before-restart
backup preserves this state. Full restart recovery passed: slot a restored with
the new ModuleCleanup token, exactly one Sarah, three worn items, preserved local
player and ordinary world visibility. Exit saved slot b successfully.
[Recovery evidence](../evidence/module-cleanup-restart-summary.txt),
[scene](../evidence/module-cleanup-restart-scene.png).

No production changes needed; existing automated suite remains 48 checks, not
rerun for this temporary live-only probe. Game closed, native inventory confirmed;
driver disabled outside the mod. Continue selects SarahModuleCleanupCase with
ModuleCleanupDone=true. Backup group includes Original-long-session,
Interrupted-before-restart, Recovered-final and original selections. Normal
profile console stayed unchanged (18675 bytes, 04:03:05). Previously documented
font/map metadata warnings remain. Do not rerun the fault in this completed case;
prepare a separate backed-up case and matching guard/marker first.

Reloaded files contained the current unchanged production source. This tests
reload/reference/callback safety, not hot upgrades to changed schemas or function
bodies. Verifier cleanup failures remain covered separately by simulated tests;
this interruption targeted Sarah removal, not the verifier. Native resource
reclamation, arbitrary silent cleanup failures and automatic in-session recovery
from the pinned partial object are not established here.
