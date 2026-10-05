# Project Sarah: CallerEpoch & CaptureAccounting Specification

## 1. Scope & Architectural Boundaries
- **Baseline:** Main branch checkpoint `dac6c1f`. Both tools (`tools/CallerEpoch.lua` and `tools/CaptureAccounting.lua`) are standalone, inert, modules using Lua 5.1-compatible syntax (tested through Lupa Lua55; native Kahlua acceptance remains separate).
- **Zero Native Invocations:** These modules introduce no engine imports, globals, game events, or native calls. They execute purely as offline caller policies.
- **Ownership:** Codex retains exclusive repository editing, checkout review, and test execution ownership. Gemini authored the source/base fixtures with NO TOOLS; Codex applied/reviewed and ran the checks described below.

---

## 2. `CallerEpoch.lua` Specification
- **Constructor:** `CallerEpoch.new(namespace)`
  - `namespace`: String matching `^[%w_%-]+$` with length 1..32. Copied as an immutable scalar.
  - *Caller Obligation:* The caller must supply a unique namespace per instance/session. This module does **not** maintain a global registry and cannot prevent collisions if identical namespaces are reused across reloads.
- **Lifecycle Observation:** `:observe(state)`
  - Requires a plain table with 5 raw string fields (`1..96` characters): `framework`, `controller`, `npc`, `cell`, `worldRevision`.
  - `framework`: Caller-issued session token marking the top-level `SarahFoundation` instance. Must change across script reloads.
  - `worldRevision`: Caller-issued epoch token. *Not* a native engine generation or world-freeze guarantee.
  - State transitions:
    - First valid observe binds state at `epoch = 1` and returns `{ status = 'ready', changed = true, epoch = 1, generation = namespace .. ':1' }`.
    - Identical tokens return `{ status = 'ready', changed = false, epoch = ..., generation = ... }`.
    - Any token change while active increments `epoch` and binds new tokens.
    - Invalid observe while active clears state, increments `epoch`, and returns `{ status = 'invalid', changed = true, epoch = ..., generation = nil }`.
    - Repeated invalid observe does *not* increment `epoch` (`changed = false`).
    - Valid observe after invalid or reset binds the *current* epoch without an extra increment.
- **Reset & Overflow:**
  - `:reset()` increments `epoch`, clears state, and returns `{ status = 'reset', changed = true, epoch = ..., generation = nil }`.
  - Maximum epoch is clamped at `MAX_EPOCH = 2147483647`. Any increment past MAX permanently marks the module `exhausted`. Observe and reset calls on an exhausted instance return `{ status = 'exhausted', changed = false, epoch = MAX_EPOCH, generation = nil }`.
  - `:snapshot()` returns scalar copies: `{ epoch = ..., active = ..., exhausted = ... }`.

---

## 3. `CaptureAccounting.lua` Specification
- **Constructor:** `CaptureAccounting.new(config)`
  - Optional table with optional positive integer limits: `captureLimit` (default 54, hard limit 512) and `operationLimit` (default 1024, hard limit 16384).
  - One ledger per pass: instances cannot be reset or refilled.
- **Budget Consumption:**
  - `:beginCapture()` grants `true` and advances `captures` until `captureLimit` is reached. Refusal sets sticky invalidation reason `capture_budget`.
  - `:charge(kind)` consumes from `operationLimit` across 4 fixed groups: `"world"`, `"membership"`, `"state"`, `"symbol"`.
    - Unrecognized kinds trigger immediate sticky invalidation `invalid_kind` with zero operation charge.
    - Operation limit exhaustion sets sticky invalidation `operation_budget`.
  - `:invalidate()` sets sticky reason `cancelled`.
  - Once invalid, all further grants are refused, counter advances cease, and the first invalidation reason is strictly preserved.
- **Accounting Truthfulness:**
  - The ledger counts declared call expressions instrumented by the caller *prior* to attempting native lookups.
  - It does *not* measure or prove underlying Java JNI execution time, garbage collection impact, or semantic read-only guarantees.
  - Methods that materialize whole collections (e.g. `IsoCell.getObjectListForLua`) must be explicitly excluded from bounded caller paths.

---

## 4. Next Deferred Native Gate
Prior to introducing any native adapter or in-game staging:
1. Verify operator resume consent, clean git status, and confirmation that the game process is closed.
2. Audit userdata property getters on candidate objects to ensure property indexing triggers no unintended native mutations.
3. Verify that native call accounting boundaries are preserved without relying on synthetic mocks or uninspected chunk APIs.

## 5. Reviewed API and caller obligations

CallerEpoch state contains only copied scalar tokens. It does not derive the
framework token from a Lua table or manufacture controller/NPC/cell identity.
The future caller must truthfully change framework token when the top-level
SarahFoundation table is replaced, even when its controller is preserved.
worldRevision is also supplied externally; changing it advances the ticket but
does not establish an authoritative engine/chunk generation or frozen world.
No raw handles, input tables or token registry are retained by these tools.

The first overflow transition reports changed=true, clears all active state
and keeps epoch at2147483647; further observe/reset calls report changed=false
and never emit a generation. Valid observation after an ordinary invalidation/
reset binds the current epoch, preserving non-reuse of previously active tickets.
Namespace uniqueness across instances/reloads is an explicit caller obligation;
same namespace can alias generation tickets. Capture token lengths do not
impose the namespace pattern. Generation length is at most43 characters.

Epoch reset does not itself call NativeExposureProbe.reset, change the user
Stop handler or abort a native method in progress. Caller orchestration must
propagate invalidation and supply fresh generation to every lifecycle capture.
Observe ready means valid supplied token state, not verified native residency.

CaptureAccounting snapshots contain copied captures/operations, limits, remaining
budgets, valid/reason and four group counts. charge consumes an irrevocable
authorization before an attempted operation; charges remain consumed if the
operation throws, returns nil, or is cancelled before completion. A dishonest
or uninstrumented caller can bypass accounting; this is not a native sandbox.
The ledger does not execute callbacks or automatically invalidate on errors it
cannot observe. Callers must stop on any denied grant, close/invalidate the ledger
on pass completion/abort, and create a fresh ledger for the next pass. There is
no reset/refill method. Limits are policy choices, not measured native costs.

World/membership/state/symbol groups classify declared call expressions, not
full nested Java/JNI work. Additional death, coordinates, facing and native
property access require their own instrumentation. Existing Engine.isResident
has up to10 explicit API call expressions, using Set/HashSet membership. Neither
cached currentSquare nor a chunk shortcut substitutes for residency proof;
whole-collection getObjectListForLua materialization remains excluded.

## 6. Verification and scope

Gemini3.8 Flash HIGH authored both tools and39 base fixtures; Codex corrected a
nil-hole namespace fixture, standardized the summary, removed redundant string
conversion and added14 review cases. Tests include raw-input/copy isolation,
opaque-handle rejection, every role change, framework-only reload marker changes,
mandatory debug reflection for all overflow paths, hard512/16384 boundaries,
failed-call charge retention and guarded global environments.

Actual NativeExposureProbe composition uses54 captures,26 symbol resolutions
and a declared10-operation capture model:566 charges complete,565 abort at the
final capture with empty output. This models source call sites, not execution
of Engine.isResident/native methods. Additional real-Lua callback tests verify
precharge denial prevents those callbacks and retains failed-attempt charges.
Both policy and probe reset/drift abort paths are exercised. No game functions
are invoked. Forced lighting remains unknown/nativeAcceptance=false in probe.

All608 suite checks across14 suites +11 runner +19 preflight PASS; this new suite
contains53 cases. No production imports, native caller, runtime event changes,
deployment/game launches, saves/settings changes, new Knowledge observations
or Stop modifications. Deployed isolated baseline remains5fa6b9c. Gemini exports
remain ignored under runtime/caller-gemini-20261006/. See sanitized
evidence/caller-context-offline-20261006.txt.

## 7. Next bounded offline step

Review a dormant one-shot caller/bridge design that uses these tickets and
precharge ledgers with the existing exposure probe. Specify exact token provenance,
reset propagation, per-operation accounting and fail-closed native prerequisites.
Do not bind globals, create event hooks or invoke native methods during design.
No additional residency simulation or lighting substitute is justified. Actual
Lua binding/types/overloads, enum access, native identity and loaded-world gates
still require explicit deferred acceptance; Follow/rendering remains pending.
Gemini handles further coding drafts; Codex alone applies/reviews/tests and later
deploys/launches after user resumption. External/model AI stays ON HOLD.
