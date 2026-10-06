# Installed Kahlua resolver audit and operation manifest

2026-10-06. Read-only offline study from clean main7d7d37d. Codex owns checkout.
No runtime source, resolver, helper or event changes. Live testing is deferred.
Gemini3.8 Flash HIGH reviewed sanitized observations with NO TOOLS requested;
no game source/classes or project documents exported in this dispatch.

## Evidence provenance

Installed projectzomboid.jar SHA256 freshly matches
E1A69EB743EDE60B213A0FE7F8B83D4FCAB773036D256CC4543A336F3B058A33.
Six selected classes were freshly extracted/decompiled with existing CFR0.152;
class exposer uses the same-hash earlier snapshot plus fresh direct class parsing.
Dependencies/anonymous comparator remain unresolved. Selected method Code and
exception-table entries were parsed directly without initializing target classes.
Raw classes/decompilation/exports stay ignored in runtime/resolver-audit-20261006/.
Citations below identify that ignored fresh tree, except exposer under
runtime/research-adapter-20261005/fresh/. This is static evidence, not gameplay.

## Findings that narrow the native unknowns

| Path | Inspected fact | Practical limit |
|---|---|---|
| LuaJavaClassExposer.setupMetaTables, lines245-257 | Stores a KahluaTable as class __index; index table inherits superclass metatable | Actual registration/metatable modifications still need observation |
| exposeMethod/addInvoker, lines184-214 | Stores LuaJavaInvoker; overloaded name can store MultiLuaJavaInvoker | Actual candidate alias/reference not resolved in this study |
| LuaJavaInvoker line32 and MultiLuaJavaInvoker line25; KahluaUtil.type252-274 | Both implement JavaFunction; JavaFunction/LuaClosure maps to function type | Strong static rationale for probe policy, not live availability proof |
| KahluaThread.tableget1104-1134 | rawgets tables, follows __index; callable __index is invoked, table __index is traversed | Standard stored method lookup does not call target method; arbitrary metatables can execute code |
| getClassMetatable1193-1213 | Searches class/interface/superclass registry and caches result, including null | Lookup can allocate/mutate VM caches; no universal purity or time guarantee |
| BaseLib.rawequal167-174 and luaEquals428-441 | Double values compare numerically; other objects use reference equality, no Object.equals/Lua __eq | Returned wrapper reference is not persistent world/entity identity |
| LuaJavaInvoker.prepareCall63 onward | hasSelf requires non-null argument0 satisfying clazz.isInstance | Extracted instance invoker needs receiver at invocation; static/global paths differ |
| MultiLuaJavaInvoker.call28 onward | Several match/prepare fallback passes | Actual overload selection/comparator order not established |

Direct Code corroboration: tableget rawget31, getMetaOp51, conditional callable
call160; getMetaOp uses rawget18. setupMetaTables stores __index at rawset46;
addInvoker stores invoker at rawset100 or multi-invoker65. KahluaUtil.type tests
JavaFunction38/LuaClosure45. These offsets concern the named methods, not files.

This narrows the earlier concern about automatic getter invocation: the inspected
standard registered method lookup retrieves a stored invoker without calling the
target. It does not establish that every live userdata/global lookup takes that
path, that the environment is untouched, or that lookup has no VM side effects.

## Protected calls are not success evidence by themselves

MethodCaller.call lines41-58 invokes Method.invoke at Code18; normal nonvoid
return is pushed at33. Its exception table covers12..37 with handlers40 for
InvocationTargetException and53 for Throwable. Handlers call logException47/57,
then converge on return60 without explicit rethrow. logException invokes the
UIManager default thread stacktrace/debug routines and ExceptionLogger.
Logging itself may throw; not every native error necessarily becomes pcall=true.
But a target failure can be caught/logged without a valid return, so protected
call success alone cannot certify getter success. LuaJavaInvoker's outer wrapper
cannot recover exceptions already consumed in MethodCaller.

Later getter diagnostics must validate expected types/domains and separately
review sanitized logs for that invocation window. Nil can also be a legitimate
optional result, so nil alone cannot universally identify a Java failure. No
native fault injection, logger invocation or Java method call was performed here.

## Declared resolver boundary manifest, not implemented

| Candidate | Minimum precondition | Future source boundary to audit/account |
|---|---|---|
| framework/revision marker | Caller-owned plain Lua state | raw Lua reads can be non-native; arbitrary injected callback work is not assumed pure |
| get_cell | Known plain environment table | Raw global lookup; do not invoke getCell to manufacture cell handle inside a symbol-only pass |
| los_line_clear | Actual LosUtil container type/path established | Global acquisition plus separately audited lineClear indexing; no target invocation |
| forward_x/y | Independently available audited NPC handle | One declared method indexing expression per alias; underlying metatable work separate |
| cell_get_square | Independently available audited cell handle | getGridSquare method indexing; does not choose/call any overload |
| square_get_moving_objects | Independently available square handle | Method indexing only; otherwise pending separately audited square acquisition |
| list_size/get | Independently available moving-list handle | Method indexing only; otherwise pending separately audited list acquisition |
| five enum aliases | Exact lookup path established | No guessed traversal or blind path discovery; unresolved remains unassessed |

One readSymbol callback can contain several boundary operations. Precharge each
potentially bridged acquisition/indexing before attempting it, preserve failed
charges, then check fresh markers/reset before any next operation. Do not infer
an operation/time limit from26 callbacks. VM internal recursion and Java work
are not bounded in elapsed time by the caller ledger. No complete native budget
or resolver has been implemented or certified.

If handles are unavailable, never call unaudited getters or fabricate synthetic
wrappers to satisfy a symbol row. A resolver returning nil produces missing in
the current probe; accompanying evidence must state acquisition/path unassessed,
not claim native API absence. Square/list acquisition usually involves getters
unless a suitable handle already exists; this audit does not prove getters are
the only possible source. LosUtil.TestResults absence from inspected explicit
registration does not prove absence from runtime nested globals.

## Review, verification and next gate

Codex corrected Gemini's universal zero-native marker/raw-global assumptions,
getter-only handle acquisition claim, silent-error wording, inferred complete
static audit, and claim that Lua55 proves Lua5.1 compatibility. Source targets
Lua5.1-compatible syntax; native Kahlua remains a separate gate. The standard
bridge mechanisms are now inspected, not every alias or modified runtime path.
41 symbol fixtures rerun PASS. Prior full649 checks/15 suites +11 runner +19
preflight baseline unchanged; full suite not rerun for this documentation batch.
No new native compatibility, lighting or Follow/rendering evidence.

Stop generic scaffolding. The next meaningful gate is explicit user resumption
of isolated native testing, starting with pending Follow/rendering acceptance;
exposure/getter diagnostics require reviewed audited paths and an exact staging
revision separately. Game closed before staging, fresh disposable-world and
mod backups, recorded restore plan, normal saves/settings untouched. Codex alone
handles deployment/game launches. Stop unchanged, lighting unknown; deployed
baseline5fa6b9c. External/model AI remains ON HOLD.
