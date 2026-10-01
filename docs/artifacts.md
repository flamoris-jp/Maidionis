# Checkpoints, artifacts and reproducibility

Status: proposed v1. Source training checkpoints are partially implemented;
the complete serving bundle/loader is not. See the [extraction map](arbitrium-extraction-map.md).

## Identity and compatibility

Use versioned LibTorch-native CPU FP32 archives for the initial registered
profile. SentencePiece is optional, required only by a selected text codec.
No Python pickle/TorchScript program, downloadable plugin, generic `.pt` loader
or cross-framework compatibility is part of v1. Native archives require trusted
provenance and exact tested dependency/ABI profiles. Checksums prove integrity
against a trusted external digest, not authenticity or deserializer safety.

| Identifier | Meaning |
|---|---|
| specialization/task ID and version | immutable semantic contract |
| component/schema/profile ID and version | exact compiled supported implementation contract |
| artifact/checkpoint/dataset logical ID | immutable human-readable registry label |
| manifest digest | integrity of final manifest bytes, supplied externally |
| component/file digests | exact bytes/config/tensor binding |

No semantic compatibility is inferred from matching label count, filename or
semver major alone. New weights/tokenizer/assembly/task/precision invalidate
calibration and evaluation bindings. Compatibility entries name tested LibTorch,
SentencePiece where relevant, compiler ABI, OS/architecture, dtype and registered
codec/component versions. Reject unknown profiles; no implicit device fallback.

## Serving artifact inventory

`maidionis.artifact.v1` manifest requires `schema_version`, `format_version=1`,
`artifact_id`, `created_at`, `descriptor_digest`, `training_run_id`, `status`,
`files`, `compatibility`, `tensor_inventory`, `limits`, `evidence`.
`status` is `research_only` or `release_candidate`; neither grants deployment.
`evidence` binds immutable training, calibration and evaluation report digests,
their evaluated-component digest and exact evaluation registration digest.
Required records may say `not_applicable` only when that evaluation registration
explicitly permits the stage's absence. A release candidate requires complete
passing evidence under the named registration; raw diagnostics remain research-only.
Operator approval under current policy belongs to an external trusted registry.

Required files: specialization descriptor, semantic spec, schema/config members,
resolved model config, weights archive, training metadata, evaluation summary
and model card. Codec-specific artifacts, calibration and diagnostics schema
are required exactly when the descriptor and bound calibration configuration select
them. Diagnostics schema is intrinsic to the descriptor; evaluation/release policy
is a separate evidence record. `files` inventories
all members except manifest and includes regular relative path, SHA-256 and
byte size. No extra/unlisted members. No self-hash in manifest. Model card states
license/provenance, intended use, known failures and actual supported profile.

Tensor inventory enumerates parameter/buffer names, dtype and dimensions. Config
enumerates every backbone/head/codec/normalization/initialization option; no
implicit request-controlled defaults. Initial caps: 512 MiB bundle, 256 MiB
weights, 32 MiB tokenizer, 4 MiB per JSON/schema/config, 30M parameters, 1,000
members and 1,024-byte relative paths. Check count/shape products for overflow
and consistency before allocating. Profiles may reduce these limits.

## Validation, admission and materialization

Core exposes two distinct conceptual operations; names are proposed interfaces,
not shipped C++ APIs. Their host-independent value types contain no Runtime Jobs,
grants or scheduler access.

| Operation | Input and result | Forbidden side effects |
|---|---|---|
| `validate_bundle(source, validation_context)` | caller-selected immutable source and trusted expected digest/compatibility; bounded metadata, complete hash/cross-binding checks; validated description and compiled resource estimate | no tensor/model construction, archive deserialization or device initialization/move |
| `materialize_model(validated_bundle, execution_context)` | validated immutable source, frozen compiled registry and caller-admitted placement/budgets/observer; exact constructed model plus allocation receipt, or failure/cleanup record | no admission decision, fallback placement, unrequested device move, hidden cache or published partial model |

Validation CPU buffers, hashing/I/O and any verified snapshot are charged to the
caller's bounded validation context. Streaming a bundle does not allocate its
entire contents. Keeping a snapshot resident requires a separate accounted byte
budget; an immutable source handle/lock survives both stages to prevent hash/load
races. The validated description binds manifest/descriptor/component digests,
tensor inventory, required numerical compatibility, maximum input/batch shapes,
source identity and registry/build identity. Unknown compatibility or missing
resource estimates fail closed. Sizes from the manifest are not admission grants.

For serving, Runtime reserves CPU RAM and any selected device capacity **before**
the worker calls materialization; it also owns the validation admission. For
offline train/export/tests, an explicit bounded offline host supplies the context
and owns accounting. Core cannot reserve production capacity. `execution_context`
is an in-process trusted host object, never request JSON: admitted operation ID,
exact tested numerical/placement profile, persistent and peak transient budgets,
allocation observation and cleanup hooks. No authority is gained from echoing
its ID. The host checks current admission before entering Core and before transfer.
The initial profile selects CPU FP32 only; no optional automatic GPU move exists.

Order after admission: construct registered CPU model → load trusted CPU archive
→ check exact keys/shapes/dtypes/finiteness → validate codec controls → eval/no-grad
self-check under an admitted transient budget → return immutable holder/receipt.
All constructor parameters, weights, tokenizer storage, archive staging, framework
allocator caches/context overhead and self-check buffers count, including peak
overlap. The receipt binds operation/artifact/build/profile identities, persistent
allocations, observed peak/transient use and cleanup status. It is host-reconciled
observation, not authorization. Do not infer bytes released just from logical
tensor sizes or a model destructor.

Failure, cancellation, expiry or budget overrun never publishes a holder. Partial
allocations and persistent framework memory stay charged until actual cleanup is
acknowledged. The host retains ownership even if the caller stops waiting. A
qualified allocation observer/bounding mechanism is required: LibTorch allocation
is not magically controlled by a struct containing a limit. If an in-process
profile cannot establish the bound/cleanup evidence, that profile cannot be
admitted; qualify process isolation or another enforcement boundary first.
Future device/dtype profiles require explicit new admission, compatibility/parity
and allocation qualification, including simultaneous CPU/device staging. Core
performs only the placement authorized by that context and never chooses a GPU.

Runtime accepts a successful holder and receipt only under current pins/admission,
then assumes its sole residency ownership; see the
[Runtime handoff](runtime-integration.md#loader-handoff). No eagerly constructed
provider can bypass this sequence. Symlinks, traversal, extra/missing files,
mutable-source races and untrusted native archives are rejected. These checks
do not sandbox a native deserializer. Malicious import conversion requires a
separate isolated design.

## Checkpoint contract

`maidionis.checkpoint.v1` manifest binds model/optimizer/RNG archives, state,
resolved descriptor/config/data/tokenizer inventories, toolchain/environment
record and history digest. Each member is hashed with exact size. A caller's
opaque `identity` string alone is insufficient.

State requires completed/next epoch, global step, planned total steps, scheduler
algorithm/version/phase/base LR, parameter-group ordering and decay roles,
best objective/epoch and best-weights digest, patience/stopping state, selection
scope, epoch-order version and all RNG inventory references. Resume is at an
epoch boundary only. Full config/descriptor/data/codec/environment hashes must
match; a supported migration must be explicit rather than guessing absent state.
Best and final objects are separate even if byte-identical. A training checkpoint
is never a serving artifact or Runtime continuation.

Publish in a fresh same-filesystem staging directory: write and flush/fsync
all files, verify hashes/required inventory, fsync directory, atomically rename
to a unique checkpoint name, fsync parent, then atomically update the latest
pointer with manifest digest and fsync parent again. One writer per run, no
overwrite. Every I/O failure is observable. A crash retains the previous good
pointer or an explicitly recoverable orphan; incomplete directories are never
resumed. Validate pointer path containment before reading archive files.

The source hashes only state behind its latest pointer and uses opaque run
identity; it does not yet independently verify the complete archive/config/RNG
inventory. Reuse its epoch-boundary save/resume algorithm with strengthened
validation, path containment and crash tests. Its POSIX fsync/locking is a Linux
reference, not portable Windows durability.

## Export, evaluation and registration

Export selected-best checkpoint as a new CPU FP32 candidate. Verify output
parity, then fit calibration and evaluate exact component bytes. Define
`evaluated_component_digest` as SHA-256 of canonical sorted inventory JSON for
descriptor, model config, weights, codec/schema/semantic-spec and calibration
members: same sorted-key UTF-8 JSON serialization plus LF as shared fixtures.
Exclude report, card and enclosing manifest to avoid cyclic references.

The digest input is an array sorted lexicographically by UTF-8 relative path;
each element has exactly `path`, `sha256`, `bytes`. Keys are sorted, integers
use decimal notation, non-ASCII text is emitted as UTF-8, separators have no
whitespace and the complete array ends with one LF. Shared native/Python fixtures
fix string escaping and reject invalid Unicode. No floating-point values occur
in this inventory digest representation.

Reports bind that digest; final bundle incorporates report hashes without
changing evaluated components. Finalization revalidates both inventories.

Reassessing unchanged components against a new evaluation/release policy binds
a new registration/report. Republishing those reports creates a new immutable
bundle/manifest digest, while the descriptor/evaluated-component digest stays
unchanged. Old bundles and their evidence remain intact. Runtime control or
placement policy is external registration data, never part of the model descriptor.

External registration records final manifest digest and approval policy/evidence;
artifact metadata cannot self-authorize production. Rollback selects another
previously approved immutable digest. No in-place weight edits, automatic
promotion or speculative calibration-schema substitution.
