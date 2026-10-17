# Isolated native acceptance: 2026-10-17

Deployed gameplay checkpoint: 914333b. Operator: Codex with user-operated movement
and Lua diagnostic entry. World: isolated Sandbox/2026-10-05_19-04-21.
No normal saves/settings used. No live gameplay source edits.

Preparation: game closed confirmed; fresh backup live-acceptance-20261016-234628-UTC
contains475 hash-verified files, including451 world files and selected mod/profile.
All17 production files deployed and hash-matched. Preflight at914333b READY.
Backup manifests, raw logs and operational journal remain ignored under runtime.

## Results and evidence limits

- Restore: Codex observed ACTIVE npc=true worn=3 localPlayerPreserved=true and
  RESTORED b. Panel status#1 showed active/idle. No new full reload acceptance.
- Follow start: Codex invoked Follow#2 and observed Sarah move toward stationary
  player. User reports she runs when player runs and walks when player walks.
  Accepted for this user case, not measured speed or all-condition movement.
- Catch-up limitation: user reports walking approach despite larger separation
  when player walks. Source policy derives pace from playerRunning only. Requested
  distance-based catch-up is not implemented; plan a bounded separate correction.
- Stop: user confirms mid-stride Stop and no automatic resumption when walking
  again. Panel corroborated Stop#3 completed / Cancelled Follow#2, then explicit
  Follow#4. Codex Stop#5 cancelled#4 and completed while paused, no stop error shown.
  Latency not measured; native queue/path/running fields not directly inspected.
- Nearby rendering independence FAIL: user reports Sarah visible only when facing
  her on open road. Engine.lua manual FBO draw requires square.isCanSee(playerIndex).
  Wall/floor/occlusion tests not accepted. Do not remove guard without safe replacement.
- Clock: existing helpers executed in the native game successfully. First paused
  t137.9991227942519, dt0, reason paused, errors nil at frame8264. Repeated paused
  reading retained exactly the same t and frame. After user normal-speed interval,
  paused t146.71578948339447 at8787. After user first fast-forward interval,
  paused t171.29912138869986 at9082. Increases8.71666668914257 over523 frames and
  24.58333190530539 over295 frames are consistent with approximate0.016667 vs
  0.083333 engine seconds per update (about5x). Intervals were manually timed;
  not exact wall-clock rate proof. Reload continuity/new-session reset not tested.
- LightSourceSnapshot not invoked or wired. Independent lighting remains OPEN;
  visual unknown and external/model AI ON HOLD.

## Outstanding native gates

Correct nearby look-away rendering, then retest wall/floor/depth boundaries.
Retest Follow after bounded catch-up change, including deceleration, leash,
retarget, Stop and no automatic resume. Clock reload/reset and native queue/path
cleanup inspection remain pending. Source-access/lamp calibration is separate.

## Exit and preservation

User confirmed normal quit. Codex confirmed no game/Java process; log reports SAVED a at frame9083 followed by GameThread exited. Post-test backup runtime/backups/post-live-20261016-235932-UTC contains527 hash-verified files, including495 current world files and deployed mod/profile. Latest test state preserved separately from pre-test backup. No restoration performed.
