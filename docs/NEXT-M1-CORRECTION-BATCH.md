# Next M1 correction batch: rendering and Follow catch-up

Read AGENTS.md, CLAUDE.md and current resume/status/roadmap/handoff, then
 evidence/native-acceptance-20261017.md. Verify Git and sole-editor ownership.
The game is closed. Codex preserved the latest isolated state after clean save.
No deployment, launch or changes to saves/settings are authorized for this batch.

## 1. Nearby look-away rendering (native failure)

User sees Sarah only when facing her on open road. Engine.render currently
requires square:isCanSee(playerIndex). Inspect the installed Build42.21 rendering,
alpha/depth and visibility paths and propose the smallest supported draw route
that preserves a nearby resident same-floor NPC when the player turns away.
Keep walls/floors, cutaways, depth ordering, loaded/on-screen checks and valid
local camera context. Do not simply remove isCanSee or substitute a permissive
flag. Any alternative visibility/obstruction predicate needs exact static evidence
and focused regressions for open-ground look-away versus occluded/unloaded cases.
If no safe route is established, return the precise blocker and minimal native
probe; do not invent renderer hooks or call arbitrary JNI functions.
Player camera rendering/color context is not Sarah perception authority: keep
rendering and independent sight separate. Never enable x-ray or highlights.

## 2. Distance-based Follow catch-up

User confirms run/walk pace matching works, but Sarah walks to close larger gaps
when player walks. Add a bounded run-to-catch-up policy with hysteresis so a large
gap triggers running even if the player walks or stands, then returns to ordinary
pace near the player. Choose and document modest thresholds inside the existing
8-tile leash (e.g. start6, leave3); preserve deadzone2 and native physiology.
No speed multipliers, teleportation, leash expansion or sprint forcing.
Apply policy at initial step and during an existing step; prevent rapid pace
oscillation. Preserve current player-running behavior, WalkHere walking, single
owner, retired-callback guards, Stop/failure cleanup and no automatic resumption.

## Verification and handoff

Add meaningful actual-Lua regressions for catch-up transitions/hysteresis,
stationary/moving targets, deceleration, retarget, deadzone, leash, Stop and stale
callbacks. Rendering fixtures demonstrate policy only, not native acceptance.
Run aggregate suites and runner/preflight self-tests. Update shared notes with
exact implemented/candidate/blocked/native-pending states and changed files.
No unrelated refactors, autonomous work, perception-light admission or external AI.
No deployment, game launch, save/settings changes, commit or push.
Hand sole ownership back to Codex for review, checkpoint and backed-up retest.
