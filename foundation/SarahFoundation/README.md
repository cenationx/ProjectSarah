# Sarah NPC foundation candidate

Experimental single-player candidate for Project Zomboid 42.21. No external AI.
Live-tested in the isolated game on 2026-10-04; see [results](../../docs/M0-foundation-live-test.md). Keep SarahM0 disabled when testing this
candidate; use only the disposable isolated profile under this project.

The lifecycle policy prevents duplicate creation, alternates two checkpoint
files, retains the previous checkpoint, refuses silent replacement when recovery
fails, retains references after cleanup failure, and records a death tombstone.
A saved square that is unavailable defers restoration; use the context menu's
spawn/restore option once the location is loaded. Automatic offscreen unloading
and travelling NPC recovery are not implemented.

The engine adapter preserves the local-player instance during construction and
requires the exact isolated profile before creating an NPC. Clothing identifiers
were checked against the installed game's scripts; three equipped items survived
unload/restore and a full restart. Visual appearance remains unverified. The save
callback ran before GlobalModData saving, and recovery metadata survived restart.

Run `tools/test_foundation.py` with the project-local Lupa dependency to check the
actual Lua lifecycle module using simulated engine failures. Those tests verify
policy, not Project Zomboid gameplay compatibility.

The automated suite also executes the mod's callback registration with simulated
events to check reload and session reset behavior (19 checks total). These
callback checks are not a live game/world-switch test.
