# Codex assessment of Gemini Pro review

2026-10-08. Reviewed main e9300b5. Gemini supplied FINDINGS-2026-10-08.md;
it created that file despite the read-only request. Preserve it as an external
review, not accepted project authority. No gameplay source was changed by this
assessment. Git confirmed no tracked modifications before assessment; the report
was untracked. Quota interruptions limit the original review's completeness.

| Original finding | Disposition | Evidence and action |
|---|---|---|
| Queue-wide Follow cancellation, high | Compatibility limitation; no demonstrated current defect | Engine.stop clears Sarah's queue under the single-action-owner contract. Concurrent foreign-mod actions are outside current support. Keep explicit Stop semantics. Revisit scoped interruption before adding admitted multi-action tasks; do not remove blanket cancellation without a complete replacement. |
| Retired callbacks omit base teardown, high | Claimed leak not established; proposed fix rejected | Installed queue clear performs native StopAllActionQueue in the ordinary branch, then clears Lua queue. Engine.stop also cancels pathfinding and clears path2. Base walk stop/perform act on character-global queue/path; calling them from a stale callback can disrupt the new owner. Keep guard and verify native queue cleanup. |
| Unverified pause clears memory, medium | Correct fail-closed policy and valid native API gate | Unavailable time must not retain records with unknown elapsed age. Native exposure/pause/speed/reload needs read-only diagnostic verification. Do not replace unavailable timing with wall time or a fabricated pause state. |
| Inert lighting prototype complexity, low | Valid prioritization concern; no new fix required | Module is deliberately unused and diagnostic-only. Keep inert through M1 acceptance; require concrete native source-access evidence before expansion. |

## Installed-code checks

Read-only installed Lua under G:/Games/ProjectZomboid/media/lua:
- client/TimedActions/ISTimedActionQueue.lua:236-242: clear obtains queue,
  calls character.StopAllActionQueue unless the current action is adding others,
  then clearQueue. clearQueue at46-58 has a special added-actions branch; ordinary
  branch cancels unstarted queued actions and wipes the queue. Actual branch use
  and cleanup must be observed, not inferred from policy fixtures.
- shared/TimedActions/ISBaseTimedAction.lua:63-71: base stop resets character queue;
  base perform calls queue.onCompleted and changes farming state. The report
  incorrectly attributes StopAllActionQueue specifically to base walk teardown.
- client/TimedActions/WalkToTimedAction.lua: stop/perform cancel character path
  and clear path2; these mutate shared character state, not only retired action.
- Sarah Engine.lua: ownership guard at75-91 and perform/stop at110-147 protect
  newer action ownership. stop at301 onward retires the token, clears native/Lua
  queue, attempts running reset/path cancel/path2 cleanup and propagates failures.
- tools/test_render.py: retired-base-method and stale-adapter tests exercise
  preservation of the newer path/queue owner. They do not prove native cleanup.

## Verification and interpretation

Codex reran 29 engine adapter, 71 Follow and45 console checks, all PASS. Existing
aggregate baseline remains784/17 +11 runner +42 preflight; no code changed and
no fresh aggregate or new native acceptance is claimed by this documentation pass.
Fixtures execute actual project Lua with injected engine objects, not merely
Python implementations. They establish policy behavior, not Java/Kahlua/native
compatibility. The original review is right about that boundary, but its broad
claim that mocks perfectly mimic expectations is not established by coverage.

## Highest-value next actions

1. Fresh verified isolated world/mod/profile backup, reviewed deployment, then
   Follow running/turning/retarget/deadzone/leash and mid-stride Stop/no-resume.
   Observe that old callbacks cannot cancel a replacement; inspect native/Lua
   queue/path/running state after Stop and reload. Include actual native action
   completion rather than assuming base-method call counts establish cleanup.
2. Verify pause API callable semantics and clock progression at ordinary speed,
   pause/resume and changed speed; reload/session reset and unavailable-source
   handling remain gates. Missing timing must preserve fail-closed behavior.
3. Finish nearby rendering/wall/floor cases before source access/calibration.
   Lighting remains OPEN. Existing plan allows bounded offline lighting research;
   it does not hold all independent-light investigation until M1 passes.

No deployment, game launch, save/settings changes or external/model AI integration.
