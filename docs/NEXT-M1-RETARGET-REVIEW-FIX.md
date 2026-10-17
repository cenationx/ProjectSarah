# Argon follow-up: retarget admission and evidence accuracy

Codex review of the uncommitted smoothing/window batch based on f929580.
Codex independently verified 802 suite checks, 11 runner and 44 preflight tests PASS.
Review remains IN PROGRESS. No deployment or game launch is authorized by this task.

Read AGENTS.md and current shared notes. Verify sole-editor ownership before editing.
Preserve the existing candidate changes; make one bounded correction batch:

1. Engine.lua SarahWalkAction:retarget currently rejects queue membership only
   when pcall succeeds and has == false. Missing hasAction, thrown errors and nil
   therefore proceed to pathToLocation and setRunning. Require positively verified
   membership (successful call, literal true) before in-place native mutation;
   otherwise return false for the existing full-stop/replacement fallback.
   Add actual-Lua coverage for false, nil, exception and unavailable hasAction,
   proving no retarget path/running mutation on rejection. Verify fallback and Stop.

2. Commands.lua currently accepts any retarget result except false, including nil.
   Require explicit true from this optional optimization; add a nil-result fixture
   proving it follows the safe replacement path rather than inventing success.

3. Correct shared notes: the trace does not prove the exact stutter root cause.
   Mark queue churn/startup timing as a supported candidate explanation. Native
   pathToLocation itself resets startedMoving=false and calls setData, so reduced
   Lua queue churn does not establish uninterrupted native locomotion. Remove the
   nonexistent act.stepRetired[prevGen] claim; retirement uses closure-local state.
   Keep smoothing, window visibility and full M1 acceptance OPEN pending retest.
   Preserve the prior native results and independent-lighting unknown status.

Run all suites plus runner/preflight self-tests. Report exact counts and changed
files. No deployment, launch, save/settings edits, commit or push. Return sole
editing ownership to Codex for review. User sends this task manually to Argon.
