# Sarah NPC foundation candidate

Experimental single-player candidate for Project Zomboid 42.21. No external AI.
Not yet deployed or tested in the game. Keep SarahM0 disabled when testing this
candidate; use only the disposable isolated profile under this project.

The lifecycle policy prevents duplicate creation, alternates two checkpoint
files, retains the previous checkpoint, refuses silent replacement when recovery
fails, retains references after cleanup failure, and records a death tombstone.
A saved square that is unavailable defers restoration; use the context menu's
spawn/restore option once the location is loaded. Automatic offscreen unloading
and travelling NPC recovery are not implemented.

The engine adapter preserves the local-player instance during construction and
requires the exact isolated profile before creating an NPC. Clothing identifiers
were checked against the installed game's scripts; rendering and wearing remain
unverified. Save-event timing and ModData persistence require a live test.

Run `tools/test_foundation.py` with the project-local Lupa dependency to check the
actual Lua lifecycle module using simulated engine failures. Those tests verify
policy, not Project Zomboid gameplay compatibility.
