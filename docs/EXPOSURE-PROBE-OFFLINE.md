# Project Sarah: Native Exposure Probe Specification & Boundary Document

**Artifact:** `tools/NativeExposureProbe.lua`
**Baseline:** `40bc5aa`
**Status:** INERT OFFLINE DIAGNOSTIC PROBE (No Native Engine Calls, No Deployment, No Game Launch)
**Review Authority:** Codex

---

## 1. Architectural Scope & Purpose

`NativeExposureProbe.lua` is a standalone, inert diagnostic tool designed exclusively to prepare a future, manually invoked native symbol exposure check for Project Sarah. It does **not** implement or constitute a runtime adapter, does **not** grant native compatibility acceptance, and does **not** perform any game operations.

### Key Invariants:
1. **Zero Registration / Zero Imports:** The module contains no `require`, no imports, and binds no global listeners, events, ticks, actions, or logging hooks.
2. **No Value Invocation:** Any function references, native pointers, or enum objects returned by `api.readSymbol` are strictly inspected for Lua type and exact reference identity via `rawequal`. **Probe never invokes returned functions, calls methods on returned userdata, or accesses metamethods (`__index`, `__eq`, `__tostring`).**
3. **Fixed Allowlist Only:** Exactly 13 fixed symbol keys are probed in an immutable sequence. Caller overrides (`api.keys`) are strictly ignored.
4. **Paired Read Protocol:** On a completed pass each symbol is queried twice to check only that adjacent supplied references match; an aborted pass can stop earlier. This does not establish cross-tick or native object identity stability.
5. **Forced Unknown Lighting & Non-Acceptance:** The return structure explicitly sets `lighting = "unknown"` and `nativeAcceptance = false`. It performs zero lighting queries.
6. **Strict Sanitization:** Public results contain only scalar strings (`key`, `status`, `valueType`). No coordinates, handles, raw error messages, or callback-derived strings are returned.

---

## 2. Fixed Allowlist & Expected Typings

| Index | Key Name | Expected Lua Type | Category | Engine Purpose |
| :--- | :--- | :--- | :--- | :--- |
| 1 | `forward_x` | `function` | Character Vector | Facing direction X accessor |
| 2 | `forward_y` | `function` | Character Vector | Facing direction Y accessor |
| 3 | `cell_get_square` | `function` | Grid Spatial | Coordinate to square lookup |
| 4 | `square_get_moving_objects` | `function` | Spatial Entity | Square moving object list getter |
| 5 | `list_size` | `function` | List Container | Engine ArrayList size getter |
| 6 | `list_get` | `function` | List Container | Engine ArrayList indexed element getter |
| 7 | `los_line_clear` | `function` | Geometric LOS | Raycast line of sight utility |
| 8 | `get_cell` | `function` | World Context | Active IsoCell instance accessor |
| 9 | `enum_clear` | `table` or `userdata` | TestResults Enum | Unobstructed line-of-sight token |
| 10 | `enum_open_door` | `table` or `userdata` | TestResults Enum | Open door aperture token |
| 11 | `enum_window` | `table` or `userdata` | TestResults Enum | Window aperture token |
| 12 | `enum_blocked` | `table` or `userdata` | TestResults Enum | Geometric obstruction token |
| 13 | `enum_closed_door` | `table` or `userdata` | TestResults Enum | Closed-door result token (policy remains unknown) |

---

## 3. Paired Read Evaluation Logic

For each key, `readSymbol(key)` is invoked twice. The pair `(r1, r2)` is evaluated according to a strict deterministic priority order:

1. **`query_error`**: If either read throws an exception.
2. **`missing`**: If either read returns `nil`.
3. **`type_mismatch`**: If either read returns a Lua type different from the expected category (`function` vs `table`/`userdata`).
4. **`unstable_reference`**: If both reads return non-nil expected types, but `not rawequal(r1.val, r2.val)`.
5. **`exposed`**: If both reads succeed, match expected types, and satisfy `rawequal(r1.val, r2.val)`.

`enumBindings` is marked `"distinct_references"` if and only if all 5 enum keys evaluate to `"exposed"` and their 5 references are pairwise distinct under `rawequal`. Otherwise, `enumBindings = "unknown"`.

---

## 4. Truthful Boundary Limitations

- **Symbol Presence != Semantic Correctness:** A symbol returning `status = "exposed"` means only that the injected resolver supplied two identical expected-type references in this pass. Offline fixture values do not prove any engine binding. Even eventual native references would establish only the resolver's observation, not native compatibility. It does **not** prove argument count, overload dispatch, return types, or native thread safety.
- **No Sandboxing of Caller:** The injected `api.readSymbol` callback is trusted to execute cleanly; Probe protects itself from exceptions via `pcall`, but cannot prevent external native crashes if the caller's native bridge is flawed.
- **Deferred Overload Evaluation:** Verification of Java method overloads (such as `cell:getGridSquare(int,int,int)` vs `(double,double,double)`) remains a separate, deferred gate.
- **Test Isolation:** The attached test suite validates the Lua state machine against mock callbacks and verifies that 48 fixture cases and their boundary sweeps hold without accessing the game engine.

## API, lifecycle and evidence

`NativeExposureProbe.new():run({capture=fn,readSymbol=fn})`, `:reset()`,
`:snapshot()`. These callbacks are frozen with rawget before initial capture.
No engine bridge is included. The names in the allowlist are diagnostic aliases,
not actual Java/Lua binding paths. Expected function versus table/userdata is an
offline convention: unexpected native callable wrappers remain type_mismatch,
not proof a method is absent or unusable.

Resolver callbacks must be audited separately for side effects before native
use. Reading a userdata property can execute bridge code even when this probe
never invokes the resolved value. pcall cannot undo such effects or contain
a native crash. No live use is authorized by this artifact.

Capture uses raw scalar fields controller/npc/cell/generation strings1..96,
alive/resident=true,cancelled=false, finite bounded x/y/z/fx/fy (abs<=1e6),
nonzero facing. Captures are copied and all fields compared. Caller generation
and token provenance are still unverified native contracts. Captures bracket
each lookup and final publication. Max26 symbol attempts and54 captures; failed
attempts count, no extra retries. Reset during either callback, invalid capture
or detected drift aborts with empty results and no later original callbacks.
A synchronous native read cannot be interrupted mid-call; no Stop path is changed.

No comparisons of enum names/methods/ordinals/metatables and no method return
values are observed. enumBindings=distinct_references means five supplied
expected-type refs are individually stable and pairwise distinct by rawequal.
It is not permission to feed those values into ObstructionNormalizer or claim
real LosUtil.TestResults identity. Actual enum exposure/marshalling remains open.

Return status completed means the fixed diagnostic plan finished, even with
missing/query_error/type_mismatch/unstable_reference rows. Reason is
plan_completed on success; abort/reentrancy reasons are fixed strings. Outputs
contain scalar key/status/valueType rows, counts, lighting=unknown,
nativeAcceptance=false and enumBindings status. No values or capture locators.
Snapshot contains numeric attempts/completed/aborted for runs admitted with
valid callback configuration; invalid API and reentry reject before those counters.
Reset invalidates the active revision without clearing lifetime counters.

Gemini 3.8 Flash HIGH authored source/base38 fixtures via NO-TOOLS structured CLI
export. Codex owns edits: explicit completion reason, tightened weak/vacuous
fixture assertions and10 review regressions including actual-stage sweeps,
opaque userdata, hostile metadata, guarded global environment and Lua weak-ref
collection. The latter is Lua fixture evidence, not native Java GC guarantees.
Full555 checks across13 suites +11 runner +19 preflight PASS;48 probe checks.
Actual modules execute through Lupa Lua55; native Kahlua acceptance is separate.
No runtime module/Stop/Knowledge changes, no deployment/game launch, normal or
isolated saves/settings untouched. Probe is under tools, never imported by
production. Exports remain ignored under runtime/exposure-gemini-20261006/.

## Next bounded offline step

Review a concrete caller/resolver binding plan against inspected Lua exposure
paths and this allowlist, including how to obtain scalar lifecycle tokens
without guessing wrapper identity. Prepare explicit deferred native acceptance
cases for overloads, enums and resets. Do not automatically resolve globals,
create a runtime adapter, query illumination or invoke native methods during
this preparation. Gemini drafts further coding; Codex reviews/applies/tests.
Live execution/deployment remains deferred until the user resumes it. Existing
Follow/rendering gates and Sarah-independent light remain open; model AI ON HOLD.
