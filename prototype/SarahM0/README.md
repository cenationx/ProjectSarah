# Sarah M0 probe

Disposable single-player test mod for the exact installed 42.21.0 build. It exercises engine NPC construction and a single explicit walking action, inventory transfer, serialization and removal. No external AI layer or autonomous behavior system is implemented.

Use only the isolated profile under this project. The engine's `setNpc` attaches its built-in NPC component; that is necessary to test engine NPC support.

The first runtime sequence separately exercised NPC death. Death deletes an NPC's own save file in this build; the final sequence keeps the persistence checkpoint alive. A corpse may remain after the death test.

The probe automatically begins 180 ticks after the game starts. At 360 ticks it queues one walk to the local player's square. At 900 it checks movement and transfers one item to the player and back, naming it `Sarah M0 persistence token`. At 1200 it writes the NPC checkpoint and records its path in the local player's mod data. At 1800 it checks the file and removes the NPC object. Close/reopen the world to test restoration. Only scalar metadata is stored on the local player.

Do not use this probe as a normal gameplay companion. Production persistence, duplicate prevention, unloading, combat, multiplayer and longer-term stability remain outside these tests.
