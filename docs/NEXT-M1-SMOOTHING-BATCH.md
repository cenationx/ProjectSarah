# Next bounded M1 batch: continuous-motion smoothness and window visibility

Read AGENTS.md, CLAUDE.md, current resume/status/roadmap/handoff, then
 evidence/m1-retest-20261017.md and follow-transition-trace-20261017.csv.
Verify Git and sole-editor handoff. Codex has closed the game and preserved the
latest isolated state. This task is OFFLINE; do not deploy/launch or alter saves.

## A. Continuous-motion follow stutter

User observes repeated run-start/stop animation, particularly after releasing
run while continuing movement. Stationary-target catch-up previously passed.
Trace proves catchUp=true/pace=run at gaps above6 and while closing; one sample
at5.51tiles has native npcRun=false despite pace=run/catch=true. Most catch-up
samples run. At gaps below6 outside catch-up, ordinary walking matches current
policy; distinguish policy comfort from native animation/movement continuity.
The30tick sampling cannot prove exact root cause. Do not assume every false
native-running sample is a bug independent of update ordering.

Inspect Commands Follow retarget, Engine action lifecycle, native path/animation
ordering and cleanup. Current retarget invokes full stop/queue/path cancellation
and running reset before replacement; evaluate it as a candidate cause of
repeated restarts, not a confirmed diagnosis. Prefer the smallest supported way
to preserve continuous owned locomotion across moving-target retargets if native
API evidence permits. Otherwise return the precise blocker and one bounded
native experiment. No speculative locomotion framework.

Never weaken explicit Stop, cancellation/failure cleanup, single ownership or
retired-callback isolation. Do not simply stop resetting running globally, invoke
stale base callbacks, teleport, force sprint, multiply speed, suppress failures,
or expand the8tile leash. Preserve WalkHere walking and native physiology.
If supported, address persistent walk gaps after run-to-walk with a documented
bounded pace policy; do not confuse unmeasured gaps with threshold failures.

Add actual-Lua regressions for continuous moving targets across repeated retargets,
run-to-walk with held movement, catch-up entry/exit, reentry/late completion, Stop,
leash, failure and subsequent explicit restart. Model native shared mutations only
where installed evidence supports them; fixtures are not gameplay proof.

## B. Window-distance limitation

Open-road look-away passed; one solid-wall/closed-door case hid Sarah and clear
sight restored her. User reports Sarah must be about2-3tiles from a window to be
visible through it. Exact window/curtain/open state and geometry are unrecorded.
Investigate isCanSee/isCouldSee, current square/head exposure, alpha and depth/
cutaway handling. Keep rendering independent of Sarah's sensory confirmation.
Do not bypass opaque walls, floors, unloaded data or force all alpha visible.
If evidence supports a narrow correction, implement and fixture-test it. Otherwise
prepare a small comparative native probe and clearly mark the issue unresolved;
do not claim a native window rule from this one report.

## Finish

Keep independent lighting unknown, source snapshot inert and external AI ON HOLD.
Preserve prior native evidence; do not mark full M1 complete. Update shared notes
with exact corrected/candidate/blocked states and native retest checklist.
Run aggregate suites plus runner/preflight self-tests after any code changes.
No deployment, launch, saves/settings changes, commit or push. Return sole editing
ownership to Codex with changed files, evidence and tests.
