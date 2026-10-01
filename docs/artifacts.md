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
codec/component versions. Reject unknown profiles; device fallback is explicit.

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

Loader order: trusted registry digest/profile → bounded manifest parse → path/
inventory/size validation → hash all members and cross-bindings → descriptor/
schema/component compatibility → compiled construction and trusted CPU archive
load → exact keys/shapes/dtypes/finiteness → codec control/profile validation →
eval/no-grad self-check → optional separately qualified device. A failure never
publishes a partially loaded model. Bundle files must remain immutable throughout
validation/load; trusted storage locking or a verified bounded snapshot prevents
hash/load races. Symlinks, traversal, extra/missing files and untrusted archives
are rejected. Malicious import conversion requires a separate isolated design.

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
