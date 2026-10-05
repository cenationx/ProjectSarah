# Native perception adapter: bounded offline investigation

2026-10-05 (Europe/Helsinki). Codex owns checkout. Research only: no adapter
integration, deployment, game launch, saves/settings changes or native acceptance.
External/model AI remains ON HOLD.

## Findings and decision

The installed Lua registration path supports the main geometry candidates:
character facing, loaded square lookup, moving-object lists and static lineClear.
This establishes inspected exposure machinery, not successful in-game invocation.
Coverage must include diagonal side squares; checking only line endpoints or the
centerline is insufficient. A conservative bounded rectangle is a simple first
coverage implementation, with unknown on any missing square or exhausted budget.

No trustworthy Sarah-independent light query was established. getLightLevel(-1)
and getLightLevel2 exist, but their inspected implementation reads a shared JNI
result buffer without fetching it on the -1 branch. Treat this candidate as
unsafe/unverified, not as a darkness detector. Keep lighting unknown and sensory
memory unrefreshed by geometric-only observations. No production change justified.

## Provenance and evidence boundary

Installed read-only source: G:\Games\ProjectZomboid\projectzomboid.jar.
SHA256: E1A69EB743EDE60B213A0FE7F8B83D4FCAB773036D256CC4543A336F3B058A33
(matches the previous inspected jar). Selected class entries extracted with
Python zipfile and freshly decompiled using existing CFR 0.152 and the installed
Java runtime. Running CFR is offline tooling, not starting the game.

Evidence paths below are project-relative ignored local files. A =
runtime/research-adapter-20261005/fresh; E =
runtime/research-engine-20261005/fresh. Decompiled source and class files are
not committed. CFR reports unresolved dependencies in some classes; results
remain static inspection, with no native invocation or JNI implementation proof.

## Exposure and enumeration

| Candidate | Inspected evidence | Boundary |
|---|---|---|
| Facing | E/zombie/characters/IsoGameCharacter.java:2574-2580, public forward X/Y getters; A/zombie/Lua/LuaManager.java:2623 registers IsoGameCharacter | Turning/off-camera correctness and actual Lua calls pending |
| Square lookup | A/zombie/Lua/LuaManager.java:2987 registers IsoCell; A/zombie/iso/IsoCell.java:2864,2927,2931 supplies numeric overloads | Explicit floor integers; Lua overload resolution pending |
| Moving objects | A/zombie/Lua/LuaManager.java:2991 registers IsoGridSquare; A/zombie/iso/IsoGridSquare.java:7959 getter; LuaManager:2515 registers ArrayList | Live list, not snapshot; bound list reads as well as square scans |
| Obstruction | A/zombie/Lua/LuaManager.java:3010 registers LosUtil; E/zombie/iso/LosUtil.java:28-32 public static lineClear overloads | Uncached path; Lua return representation/overloads pending |
| Light candidates | A/zombie/iso/IsoGridSquare.java:6951,9101-9113 | Registered public methods, but no verified independent light semantics |

LuaManager.java:3518-3535 iterates registered classes through
exposeLikeJavaRecursively and restricts shouldExpose to its registered set.
A/se/krka/kahlua/integration/expose/LuaJavaClassExposer.java:300-328 exposes
public static methods/fields and public instance methods except HiddenFromLua.
Registration plus public signature is stronger than a signature alone, but
annotation/overload/marshalling behavior still needs a controlled Lua probe.
LosUtil.TestResults was not explicitly registered in the inspected LuaManager;
its Java enum has Clear, ClearThroughOpenDoor, ClearThroughWindow, Blocked and
ClearThroughClosedDoor (A/zombie/iso/LosUtil$TestResults.java:7-12). Do not assume
LosUtil.TestResults constants, enum name() or tostring are callable/normalized in
Lua. Unknown representations must remain unknown until probe evidence exists.

Enumeration proposal: scan a bounded same-floor region around Sarah, with both
square-lookup and object-entry budgets; stop before traversing an entire crowd.
Copy only player/zombie positions and session IDs into dense plain records,
exclude Sarah, deduplicate objects, and cap 32 emitted candidates. Rotate scan
and list cursors to avoid permanent first-32 starvation; revalidate live lists
and clear cursors/identity registry on replacement/session/unload/death. Weak
object identity/session counters are a design candidate, not a persisted ID.
Neither enumeration nor a remembered ID grants sight/current hidden position.
Exact work budgets require later measurement; no collector implemented here.

## Coverage: why and smallest conservative proposal

E/zombie/iso/LosUtil.java:32-169 samples integer coordinates with float slopes,
0.5 offsets, dominant-axis stepping and fastfloor. It tests adjacency only when
both consecutive squares exist; missing squares skip obstruction checks.
IsoGridSquare.testVisionAdjacent (A:6628-6769) with specialDiag=true invokes
DoDiagnalCheck at both ends in single-player. DoDiagnalCheck (A:7811-7823)
queries both orthogonal side squares before the diagonal destination.
IsoCell.getGridSquare(int,int,int) (A:2931 onward) returns an existing square
from loaded chunk maps or null; it does not promise distant world coverage.
Do not call EnsureSurroundNotNull/createNewGridSquare to satisfy coverage.

First helper proposal (offline fixture implementation next, not implemented):

1. Validate finite x/y/z values, same integer floor and configured range <=64;
   reject extreme coordinates outside a conservative exact-integer bound before
   arithmetic. Apply math.floor explicitly, including negative fractions. Keep
   different-floor sight blocked in Perception; invalid values unknown.
2. Compute the inclusive x/y bounding rectangle between floored endpoints and
   extend it one tile on every side, on the same z. This deliberately overchecks
   squares outside the ray, covering side dependencies and avoiding Lua-double
   versus Java-float traversal disagreement. It is not an exact visibility ray.
3. Before querying, compute rectangle area and reserve its budget. Suggested
   initial limits: 1024 unique square reads per candidate, 4096 per sample,
   32 candidate maximum. These are conservative policy limits, not performance
   measurements; long diagonal rays may be unknown even within allowed range.
4. Query each unique square once through an injected read-only getter. Missing,
   exception, identity/session invalidation or exhausted budget returns unknown
   with a reason. Budget exhaustion never means blocked or clear. Never reuse
   coverage across ticks/world changes without fresh revalidation.
5. Only after all squares exist, invoke uncached lineClear with integer endpoints
   and bIgnoreDoors=false. All calls stay synchronous in one sampling pass; do
   not yield between coverage and obstruction. Catch query failures as unknown.

The rectangle proves only existence of required same-floor square data; it does
not prove collision/vision matrices are current or native object geometry sound.
It also conservatively returns unknown for harmless unloaded side squares.
This tradeoff is acceptable for a first diagnostic helper. A tighter exact
corridor walker needs Java-float/traversal equivalence and diagonal dependency
fixtures before replacing it. Coverage budgets and scan budgets are separate.

Required fixtures: both ray directions, axis/tie/steep/shallow rays, zero-length,
negative fractions and exact boundaries, missing endpoint/interior/diagonal side,
NaN/infinity/extreme coordinates, floor mismatch, callback exceptions, exact
budget and one-over budget, repeated square deduplication and sample cap. A
missing diagonal side must stay unknown even if injected LOS says Clear.

## Obstruction normalization proposal

Use explicit verified enum identity/representation, never arbitrary tostring.
Preserve raw diagnostic distinctions separately from normalized policy:

| Verified result | Proposed policy | Meaning/limit |
|---|---|---|
| Blocked | blocked | Engine obstruction, not detection |
| Clear | clear | Only after conservative loaded coverage |
| ClearThroughOpenDoor | clear | Retain open-door diagnostic |
| ClearThroughWindow | clear | Engine permits this material path; retain window diagnostic |
| ClearThroughClosedDoor | unknown initially | This can mean an unblocked/transmitting closed door, not every closed door; await material/native evidence |
| Anything else/exception | unknown | No permissive fallback |

IsoGridSquare.java:6666-6748 assigns door/window distinctions only when each
object's TestVision returns Unblocked; Blocked curtains/windows/barricades and
non-ignored doors can stop sight. Null special-object entries return Clear in
this inspected implementation. Loaded coverage cannot eliminate that separate
object-integrity limitation. A blanket closed-door-to-blocked mapping would
misdescribe transmitting doors; conservative unknown is a proposed Sarah policy.
CanSee alone is still insufficient: range, cone, coverage and lighting belong
in separate read-only contracts. Native material gates remain pending.

## Independent lighting: candidate rejected for now

Square.getLightInfo(int) at A/zombie/iso/IsoGridSquare.java:6951 reads per-player lightInfo;
isCanSee/isCouldSee and dark multipliers also use indexed lighting. LightingJNI
update loop (A/zombie/iso/LightingJNI.java:819-846) iterates player chunk maps,
updates player state and uses player render settings. Borrowing this cache would
make Sarah's senses depend on local-player state.

Square.getLightLevel(-1) delegates to getLightLevel2 at A/zombie/iso/IsoGridSquare.java:
9101-9113. That creates JNILighting(-1,square) and obtains max RGB. In
A/zombie/iso/LightingJNI$JNILighting.java:166-193, playerIndex==-1 short-circuits
the conditional before getSquareDirty/getSquareLighting and then decodes the
static lightInts buffer. The buffer is allocated once at lines 392-394; normal
player queries refresh it. The branch also writes square.lightLevel (line 190),
so the apparent getter is not a strictly read-only implementation. It returns
before player seen-room/meta updates at 250-267, but that does not fix freshness.

This is decompiled control-flow evidence, not a reproduced engine defect. A
bytecode-level confirmation and native controlled freshness/independence test
would be needed before any use. Never treat zero/default/stale RGB as darkness
or confirmed illumination. Do not directly invoke JNI with -1, swap player
slots, run updatePlayer for Sarah or mutate lighting caches as a workaround.

LightingJNI.getSquareLighting is a native method (A/zombie/iso/LightingJNI.java:949);
its implementation was not inspected. ClimateManager provides ambient/global
light/daylight getters (A/zombie/iso/weather/ClimateManager.java:475-515,581),
but weather-wide values do not establish indoor, lamp, torch, wall or target
illumination. No independent query was established within this inspected scope;
this is not proof that no such query can exist elsewhere in the engine.

## Next task and deferred native gates

Smallest next offline step: implement/test the injected conservative coverage
helper without events, live handles, production integration or light queries.
Keep lighting unknown and do not update Knowledge from geometry alone. Consider
a separate offline bytecode check of the -1 lighting path; no JNI workaround.
Then prepare an inert native diagnostic specification for actual Lua exposure,
list filtering, enum representation and sample costs. Live testing stays deferred.

Before any eventual deployment: reviewed revision, new game-closed backup,
exact disposable case and recovery plan; facing/player-independence, loaded
coverage, doors/windows/walls, day/night/interior/torch and lifecycle resets.
Follow/rendering acceptance remains independent and pending. Stop never starts
or resumes action; this research changes no movement or callbacks.

## Delegation outcome

Gemini 3.8 Flash HIGH dispatch was attempted through the documented CLI. Both
sandbox and normal execution requested authentication in this session; cancelled
before task execution, no Gemini edits. No global permission bypass or login.
Codex reclaimed ownership and performed this investigation. Authentication must
be re-established separately before relying on future Gemini dispatch.
