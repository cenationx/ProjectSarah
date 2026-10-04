# M0: PZNS compatibility gate

Date: 2026-10-04

## Verdict

**FAIL for unmodified PZNS against the installed game at `G:\Games\ProjectZomboid`.** Three essential public methods used by PZNS are absent from IsoPlayer and its inherited public API. The constructor's presence alone does not make the framework compatible.

The installed target was subsequently verified as **42.21.0** from the normal profile's version file and console log, then visually in the isolated game and its launch log. See `M0-live-test.md` for the follow-up prototype tests. The inspected binary is identified by SHA-256 and build revision below.

## Inputs

- Upstream: https://github.com/Project-Zomboid-Community-Modding/PZNS
- Commit: `20a30212f98aa891aec9cb070bb96164be27c12a`
- Installed `projectzomboid.jar` SHA-256: `e1a69eb743ede60b213a0fe7f8b83d4fcab773036d256cc4543a336f3b058a33`
- Installed build revision read at runtime: `4a0e9546ec`
- Runtime: installed Azul Java 25.0.4.1.
- Upstream README marks the project dropped. Workshop advertises Build 41: https://steamcommunity.com/sharedfiles/filedetails/?id=3001908830
- Metadata has `versionMin=41.1`; this minimum is not evidence of Build 42 support. Source uses the legacy root `mod.info`/`media` layout and has no `42/mod.info` folder.

## Executed tests

The Python inspector parsed actual JVM class files, traversed the game's superclass hierarchy and inspected 79 PZNS Lua files. A separately compiled Java probe then used the installed game's JVM and reflection to confirm public constructor/method resolution. It did not initialize game classes to create a world or player; only the small GitVersion class was initialized to read its revision.

| PZNS requirement | Installed API result |
|---|---|
| `IsoPlayer(IsoCell, SurvivorDesc, int, int, int)` | PASS |
| `SurvivorFactory.CreateSurvivor(SurvivorType, boolean)` | PASS |
| `IsoPlayer.setSceneCulled(boolean)` | PASS, inherited |
| `IsoPlayer.setForname(String)` | FAIL, absent |
| `IsoPlayer.setSurname(String)` | FAIL, absent |
| `IsoPlayer.setNPC(boolean)` | FAIL, absent |

The Java probe exits with code 2 when required APIs are missing; this is an expected compatibility failure, not a crash. Compilation succeeded without warnings on the final run.

### Where the failures occur

`PZNS_Framework/media/lua/client/04_data_management/PZNS_NPCsManager.lua`, lines 63–76, creates an IsoPlayer and then invokes all three missing methods. The first missing call, `setForname`, prevents this creation function from completing normally.

`media/lua/client/02_mod_utils/PZNS_UtilsDataNPCs.lua`, lines 133–146, also invokes `setNPC(true)` on the save/load spawn path. Removing the name calls would not fix this second incompatibility.

The installed vanilla Lua uses descriptor methods for surname changes. Whether there is a supported replacement for PZNS's NPC flag and player simulation assumptions remains unresolved; simply deleting `setNPC` is not a verified fix.

### Additional inspection warnings

- The layout needs an actual Build 42 discovery/load check before a candidate can be tested in-game.
- The dependency scan flags `require("PZNS_ISDebugPanelBase")` while that file resides under `09_mod_ui`. This is a path-resolution warning, not a confirmed runtime loader failure; actual engine lookup must decide it.
- Other timed actions, NPC tick processing and persistence have not been exhaustively checked.

## Verification boundary and next work

This is a headless runtime API test plus source inspection, **not** an in-game NPC test. No game UI was launched, no existing save was opened, and no mod was deployed into the game or the user's normal profile. An unmodified gameplay run would encounter already-proven missing API calls; it would not establish a working NPC foundation.

Follow-up work established the replacement NPC flag (`setNpc`) and descriptor name setters and built an independent minimal prototype. The original baseline remains incompatible without changes. A separate mechanically patched candidate exists under `candidates/PZNS_B42_M0`; it has not been deployed or runtime-tested. The unmodified upstream snapshot is preserved. See `M0-live-test.md` for live results. The AI layer remains deferred.

## Reproduce

Run `tools/run-api-probe.ps1`. It uses the installed Java runtime and the project-local Eclipse compiler (ECJ 3.43.0, fetched from Maven Central); no compiler or dependency was installed globally. Raw output: `evidence/runtime-api-probe.txt`. Additional binary/dependency evidence: `evidence/compatibility.json`.
