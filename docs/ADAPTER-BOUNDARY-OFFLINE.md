# Identity and obstruction boundaries (offline only)

2026-10-06. Two inert policies implemented and fixture-tested. No game Lua
exposure, native identity, independent lighting or native acceptance is established.
Nothing in production imports these modules. No collector/tick/action wiring,
deployment, game launch, saves/settings changes or external/model AI integration.

Gemini 3.8 Flash HIGH authored both modules and base fixtures with NO TOOLS.
Codex retained sole checkout editing ownership, applied/reviewed code and repaired
false-positive fixtures: nil holes in ipairs lists, optional overflow checks and
a simulated memory flag instead of real Perception/Knowledge calls. Added review
regressions for binding copies, toxic equality and bounded maximum IDs. Structured
CLI exports remain ignored under runtime/identity-gemini-20261006.

## Caller-token registry

`SessionIdentity.new(namespace)` takes a caller-issued unique namespace, 1..32
characters matching `^[%w_-]+$`. Invalid namespaces raise an error. The namespace
must be unique across instances/reloads whose IDs might coexist: two instances
with the same namespace can issue identical IDs. No global namespace allocator
or persistence is implemented. Future lifecycle code must reset stale Knowledge.

`registry:resolve(token, kind)` accepts only caller-issued stable object-token
strings, nonempty and <=96 characters; kind is player/zombie. It returns a fresh
plain record with id/kind/reason=new or existing. Invalid token/kind or conflicting
kind returns a reason with no ID and no allocation. A retained token with another
kind is a conflict; an evicted token has no remembered kind/history.

Native wrapper stability and token provenance are caller obligations, not facts
validated by this registry. Do not derive tokens from names, coordinates or
tostring; userdata/table/numeric tokens are rejected. Reusing a string for a
different object can alias that object while the token is retained. No automatic
registry integration with CandidateCollector has been added.

At most 64 records survive, with FIFO eviction; lookups do not renew FIFO order.
IDs are namespace:epoch:sequence, epoch starts at 1, sequence at 0. Evicted tokens
seen again get a new sequence ID. Within a unique namespace, IDs are not reused
by eviction/reset. Reset clears records, increments epoch and resets sequence.
Both counters stop at 2,147,483,647; an allocation beyond sequence limit or reset
beyond epoch limit clears records and permanently exhausts the instance. It never
wraps; future resolves return exhausted and reset cannot revive it. Create a new
unique namespace only through a reviewed caller lifecycle.

`registry:snapshot()` copies epoch/issued/retained/exhausted scalars. Public field
assignments or result/snapshot mutation cannot change private state. Maximum ID
length is 54 characters with the permitted namespace/counters. Internal records
contain only strings/numbers and bounded plain tables, no native object handles.
Private closures are encapsulation for cooperative code, not a security sandbox
against Lua debug access.

## Exact-reference obstruction policy

`ObstructionNormalizer.new(bindings)` copies five references via rawget:
Clear, ClearThroughOpenDoor, ClearThroughWindow, Blocked, ClearThroughClosedDoor.
Every reference must be a table or userdata and all must be distinct by rawequal.
Any missing, primitive, function or duplicate invalidates the complete binding
configuration. The normalizer retains at most five private references, not the
caller bindings table. No name, field, ordinal, tostring, __index or __eq query
is used to interpret a result.

Binding correctness/freshness must be established by the future adapter. Accepting
an opaque reference does not prove it is an engine enum. In particular, multiple
Lua wrappers for one Java value could fail rawequal and conservatively remain
unknown; these fixtures do not establish Kahlua/Java canonical wrapper identity.
Installed enum evidence is in NATIVE-PERCEPTION-ADAPTER-RESEARCH.md; actual enum
exposure remains pending.

`normalizer:normalize(rawResult, covered)` returns plain status/reason:

| Exact bound reference | Status | Reason |
|---|---|---|
| Clear | clear | clear |
| ClearThroughOpenDoor | clear | open_door |
| ClearThroughWindow | clear | window |
| Blocked | blocked | blocked |
| ClearThroughClosedDoor | unknown | closed_door |
| Unrecognized result, including nil/string/ordinal/clone | unknown | unknown_result |

Coverage must be exactly true for clear OR blocked classification. Any other
value returns unknown/coverage_unknown. Invalid bindings take precedence and
return unknown/invalid_bindings. No door material semantics are inferred.
Clear obstruction is not visual detection. Lighting remains unknown unless a
separate certified Sarah-independent query exists; none is currently available.

`normalizer:invalidate()` clears all five references and permanently invalidates
that instance; repeating it is safe. `snapshot()` copies valid/bound only. No raw
reference escapes in normalization output. Future callers must invalidate on
session/world replacement or loss of binding freshness; no lifecycle hooks exist
in this module. Mutating binding-table fields does not reconfigure an instance.

## Verification and continuation

49 actual-Lua boundary checks PASS. Full runner: 450 checks across 11 suites;
11 runner and 19 preflight self-tests PASS. Tests use Lua table references and
Python opaque userdata through Lupa; these are not Java enums or game execution.
Overflow fixtures require debug.getupvalue/setupvalue to place private counters
at boundaries, and fail if that technique is unavailable. Production provides
no counter override or debug hook. These tests do not claim Kahlua debug support.

Real pure-module composition verifies that unknown obstruction or unknown light
produces no confirmed position or new Knowledge record. No production pipeline
integration is implied. Existing Stop tests remain passing; neither new module
can initiate an action itself.

Next bounded offline task: a one-shot injected sampling coordinator contract with
shared budgets and lifecycle invalidation, plus further independent-light evidence
audit before any native wiring. Avoid rolling back issued IDs into reuse when
discarding a sample; registry and Knowledge reset ownership needs explicit design.
Native Follow/rendering and actual adapter exposure/identity/light gates remain
pending. Live testing stays in this chat and is deferred until explicitly resumed.
