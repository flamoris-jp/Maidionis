# Runtime adapter and shared-state boundary

Status: **proposed integration; no Runtime files changed and no adapter exists**.
The [design index](README.md) pins the inspected public Runtime revision.

## Actual current seams

| Runtime source | Implemented surface | Consequence for Maidionis |
|---|---|---|
| `include/flamoris/runtime/native.hpp` | concrete `TinyModel`/`NativeSession`, byte tokenizer, causal KV state and native controls | not a generic LibTorch encoder/classifier loader |
| `include/flamoris/runtime/inference.hpp` | `NativeWorkerConfig` bound to `TinyModel`, worker commands/observations and `InferenceMachine` | cannot plug Decision archives into it by renaming a profile |
| `include/flamoris/runtime/compiler.hpp` | `CapabilityContract`, bounded `ValueSchema`, fingerprints, effects and limits | register exact task-specific schema/profile in trusted composition |
| `include/flamoris/runtime/registered_adapter.hpp` | `RegisteredProviderPort`, `AdapterAuthority`, `RegisteredCapabilityAdapter`, bounded sink | usable future bounded call seam; transport/job grants remain Runtime-owned |
| `include/flamoris/runtime/adapter_binding.hpp` and `src/adapters/adapter_binding.cpp` | persistent provider binding and serialized invocation | model worker runs outside control actor; no second scheduler |
| `include/flamoris/runtime/runtime.hpp` and `include/flamoris/runtime/runtime_residency.hpp` | provider registration is possible; immutable residency pool holds concrete `TinyModel` pointers | provider call seam exists, but generic LibTorch residency/load ownership needs an explicit Runtime extension |
| `src/adapters/registered_adapter.cpp` | one-use grant, input pin/digest, output schema/byte validation and outcome bookkeeping | model verdict cannot construct grants or retry evidence |
| `docs/phase-c/STATUS.md` | limited native fixture and CPU/OpenCL evidence | no Maidionis/LibTorch/GPU qualification inherited |

These paths belong to [AI Runtime](https://github.com/flamoris-jp/flamoris-ai-runtime/tree/3e8b04137b7510023cb1799aaacfbe3e9cf73771).
The initial integration target is a **registered bounded Workflow capability**
calling a local immutable-model provider. It is not a native causal InferenceJob.
`CapabilityContract.inference=false`, `cancellable=false`, `pausable=false`,
`retry_permitted=false`, `max_attempts=1` are the initial baseline declarations.
Exact capability naming is chosen in the Runtime PR after rechecking current
main; this design does not invent an existing `model.maidionis` API.

That path is sufficient for a single bounded classifier call. If later features
need layer/token control or retained native state, design a Runtime-owned native
model/worker extension with its own accounting and safe points. Do not present
an opaque external call as providing those controls.

## Proposed registration and invocation

Trusted host configuration maps the capability pin/task to an approved artifact
digest and prepared provider. It verifies the bundle under its own residency
admission, loads once, fixes eval/no-grad and serializes calls. Resource registration
must account model storage, allocator/framework/context overhead and peak
transient buffers; no hidden model cache outside Runtime accounting. Changing
artifact, descriptor, adapter/profile or resource contract changes the capability
fingerprint. A stale plan fails pin validation before dispatch.

The current `RuntimeResidencyPool` cannot hold a Maidionis model. R1 must add a
Runtime-owned immutable provider-model holder/accounting seam: reserve capacity
before loading, let a bounded loader worker produce the validated holder and
allocation receipt, transfer it to the Runtime owner, and attach it to provider
calls only under the current lease/pins. Shared storage is counted once while
per-call buffers/execution are charged separately. Admission closes before
retirement, active references drain, and actual allocation release is acknowledged
before clearing residency. Framework allocations that persist after holder
destruction remain explicitly charged until reconciled or process teardown.
An eagerly constructed provider holding unaccounted weights is not an allowed
shortcut. This extension needs its own tests in Runtime; the registered call
interface alone does not demonstrate production-compatible model lifecycle.

Invocation input is the bounded Maidionis request, without artifact paths or
credentials. Runtime's compiler `ValueSchema` is not arbitrary JSON Schema:
the adapter must construct supported closed schema types, validate all task
constraints separately, and test equivalence on shared fixtures. Integral
features must respect Runtime `JsonValue` number precision/provenance; counters
outside exact binary64 range use bounded string IDs, not rounded numbers.

Sequence:

1. Runtime checks present authorization, resource limits, exact pins and input
   digest, then creates its one-use `AdapterGrant` at dispatch.
2. Provider worker validates task/envelope/codec and computes bounded output
   against the pinned immutable model. Core has no access to grant creation.
3. Provider checks numerical/semantic result and every echoed identity, then
   writes into `BoundedProviderSink` under the smaller of result and Runtime caps.
4. A fully delivered valid model result, including `abstain` or a structured
   model `error`, is a **confirmed successful provider exchange**. Runtime's
   `ExternalOutcome` describes delivery/effects, not Decision labels or readiness.
   An exception, lost response or malformed delivery uses Runtime error/outcome
   semantics; never infer confirmed delivery from an unobserved model result.
5. Runtime accepts the fenced result for the same Job. A Workflow explicitly
   handles the model status; action dispatch remains a separate authorization.

For preloaded local immutable evaluation over declared inputs only, a registered
`pure` effect may be justified and tested. If an invocation reads mutable ambient
state/storage or calls another service, declare the applicable `read`/`external`
effects and qualify that profile separately. Model readiness does not imply
permission. Pure must remain exclusive with other effects under Runtime rules.

## Deadline, cancellation and ownership

The current provider call is synchronous and LibTorch forward has no proven
interrupt/rollback safe point. Check deadline before invocation and after return;
these checks do **not** bound time spent inside a hung forward. Runtime may stop
admission or reject a late result, but resources remain owned until the worker
actually stops and cleanup is acknowledged. No pause/resume/injection/native
rewind is advertised for this profile. If a hard deadline is required, implement
and qualify an isolated worker termination/cleanup boundary before deployment.
An in-process call may only be admitted under a profile allowing this limitation.

Use one Runtime Job identity. Core may expose batch size/memory estimates and
model stage timings; it cannot create Jobs, retry a call, move GPUs or mutate
Continuation state. Unknown outcomes follow existing Runtime reconciliation;
student retry labels never become `ProviderRetryEvidence`. Losing a race is not
proof the model worker stopped. Retirement must drain active worker references
before declaring model allocations released.

## Shared-state snapshot

Caller/state owner projects an allowlisted bounded immutable snapshot into model
payload. It chooses redaction, source/version, timestamp and freshness policy;
the envelope's `context_ref` binds digest and projection identity. No live object
handles, ambient state reads, credentials or mutable references enter the model.
Unavailable/unrepresentable evidence uses the task's documented semantics or
input rejection; Core does not invent missing facts.

After an advisory result, caller compares current state version/freshness and
checks deterministic constraints before acting. A stale result may be discarded
or cause a new authorized request. It cannot silently authorize a retry/fallback,
product edit or shared-state write. Agent memory/Oblivionis/product document
ownership stays outside Maidionis. Network/MCP adapters wrap this boundary
elsewhere and are not model dependencies.

## Integration gate

The Runtime PR must cover approved/rejected digest, unsupported descriptor,
revoked authorization/stale capability pin, malformed/nonfinite output, wrong
echoed identity, byte overflow, concurrency, late/cancelled/race-losing completion,
retained-memory drain and state-changed-after-request. Test `ok`, `abstain` and
model `error` as distinct values, plus actual provider failure. A fake action
executor receives only a fresh, policy-approved `ok`; it receives no abstention
diagnostics. Model math remains native and runs with education/teacher services
absent. Passing protocol fakes does not certify production host enforcement.
