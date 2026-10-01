# Specialization and inference contract

Status: proposed v1; field tables are implementation requirements, not shipped APIs.

## Identity and descriptor

Logical IDs use ASCII `[A-Za-z0-9._:-]`, length 1..128; SHA-256 values are lowercase
64 hex characters. Versioned schema IDs select an exact registered format. A
semantic ID is immutable: changed meaning requires a new task identity even if
shapes are unchanged. An artifact digest identifies exact bytes, not quality.

`maidionis.specialization.v1` requires:

| Field | Meaning |
|---|---|
| `specialization_id`, `specialization_version` | domain identity and explicit semantic version |
| `task_id`, `task_version` | one immutable bounded task and its semantic version |
| `input_schema`, `target_schema`, `output_schema` | `{id, version, sha256}` references to bundled strict schemas |
| `semantic_spec` | `{path, sha256}` reference to the bundled task meaning/rubric |
| `input_codec`, `output_codec` | registered compiled IDs/versions, each bound to its resolved config digest |
| `architecture`, `heads`, `objective` | registered compiled IDs/versions and fully resolved finite shape/config inventory |
| `diagnostics_schema` | null or `{id,version,sha256}` for intrinsic bounded model diagnostics |
| `numerical_compatibility` | registered ID/version/config digest for archive ABI, supported numerical formats and component requirements; no execution or release policy |

The descriptor is a closed object, includes `schema_version`, and has no endpoint,
command or downloadable implementation. Every referenced config/schema is an
inventoried bundle member. Registration occurs in trusted composition code,
never by importing a path supplied in data. Unknown component, schema, codec,
profile or extension is rejected; data cannot create plugin code or new heads.
Breaking contract versions require a new registry entry and explicit migration.
Calibration and evaluation evidence bind the full descriptor digest. Merely
renaming labels or altering their order in a descriptor invalidates that binding.

The descriptor identifies **what model/task is represented**. It contains no
metric minimum support, release threshold, chosen device/residency, scheduling,
deadline, retry, cancellation or allocation budget. Schema/shape caps intrinsic
to model validity remain here; host resource ceilings may only narrow them.
Numerical compatibility declares tested archive/ABI/dtype requirements, not a
command to allocate on a device or an automatic precision/device fallback.

Separate registrations identify the other two concerns:

| Record | Owner and binding |
|---|---|
| `EvaluationRegistration` | specialization/evaluator: immutable descriptor/component/data digests, metrics/denominators, calibration/selection algorithms, thresholds/support and external release policy; see [evaluation](evaluation.md) |
| Runtime registration | Runtime: immutable artifact pin, provider/build identity, qualified placement/numerical profile, residency/effects/limits/deadlines/retry/control support; see [Runtime integration](runtime-integration.md) |

Every registration has its own identity/version and digest. Changing a release
support requirement invalidates approval under the old evaluation registration;
it does not rewrite the descriptor or numerically invalidate an unchanged
calibration fit. Changing fit/select data, algorithms or gate selection does
require new calibration evidence. Changing Runtime control support changes its
capability fingerprint/qualification, not the descriptor/calibration identity.
Never reuse an old policy's passing report as proof of a new policy's approval.

Inference decode meaning and intrinsic validity rules belong to specialization
code. Fitted temperatures and selected gates are immutable artifact components
bound to their calibration configuration/data, not live release-policy lookups.
Runtime cannot change model outputs by substituting a new evaluation policy.

## Compiled specialization surface

| Operation | Specialization supplies | Core guarantees |
|---|---|---|
| Validate | payload/target/output semantics under the descriptor | strict envelope and version/digest checks |
| Encode/batch | allowed fields, normalization, segment/features, target masks | bounded buffers, dtype/shape checks, padding machinery |
| Compose | selected backbone, heads, objective and parameter groups | registered component construction and numerical execution |
| Decode | output meaning, validity/abstention rule and domain error metric | finite values, bounded serialization, identity echo |
| Verify lessons | domain oracle/semantic audit policy and provenance claims | journal, lineage, split integrity and immutable freeze |
| Evaluate | metric eligibility, denominators, baseline and release criteria | complete prediction accounting and primitive reducers |

These are conceptual operations, not final C++ declarations. Prefer a small
compiled registry and explicit value structs to a plugin framework. Native
operations return values/errors and receive immutable input; teacher/network/I/O
interfaces cannot be reached from a model component. Profile limits reject
overflow before tensor construction. Output shape is fixed by the descriptor.

The [composition root](architecture.md#composition-root) is the specialization's
trusted native target. It installs compiled implementations into a Core registry
builder and freezes the registry before validating a descriptor. Serialized IDs
select these existing entries; they never perform registration themselves.

## Request and result envelopes

`maidionis.request.v1` fields are `schema_version`, `request_id`,
`specialization_id`, `specialization_version`, `task_id`, `task_version`,
`payload_schema`, `payload`, and nullable `context_ref`. `payload_schema` is an
exact schema ID/version reference resolved against the pinned descriptor.
`context_ref`, when present, is `{source_id, snapshot_id, projection_version,
digest}`: bounded caller bookkeeping only. All actual model features are in
`payload`. Neither descriptor nor artifact selection is accepted as a path or
arbitrary remote URL. The trusted caller binds the expected artifact digest.

`maidionis.result.v1` fields are `schema_version`, nullable `request_id`,
`specialization_id`, `specialization_version`, `task_id`, `task_version`,
`artifact_digest`, `context_ref`, `payload_schema`, `status`, `payload`,
`diagnostics`, `error`. Null identity fields are permitted only on a framing/load
error where identity could not be verified. On a framed invocation, echo exact
request/context identity. The host checks every echoed identity against its
pending request, including its trusted artifact digest.

| Status | Required semantics |
|---|---|
| `ok` | verified output-schema payload; error null; still advisory |
| `abstain` | payload null, error null; bounded profile-defined diagnostics only; no actionable output |
| `error` | payload and diagnostics null; structured `{code, message}`; no invented answer |

Diagnostics are nullable and validated by the bundled `diagnostics_schema` in
the descriptor; a null schema permits null diagnostics only. Probability/confidence/answerability are
not universal envelope fields. Error codes are closed: `invalid_request`,
`unsupported_schema`, `unsupported_specialization`, `incompatible_contract`,
`input_too_large`, `artifact_invalid`, `profile_unsupported`, `resource_exhausted`,
`nonfinite_output`, `cancelled`, `deadline_exceeded`, `internal_error`. Runtime
retryability is decided by its own policy; no domain action is an error flag.
Messages are bounded, sanitized and contain no raw upstream data or paths.

All public JSON rejects duplicate keys, unknown fields, invalid UTF-8, coercion
and nonfinite numbers. An extension must have a registered schema and finite
limits; an opaque unchecked `metadata` object is not an escape hatch. Default
envelope caps: request 64 KiB, result 64 KiB, error message 1 KiB. Profiles may
reduce caps; increases require registration and resource tests.

All JSON parsing additionally caps nesting at 32, values at 65,536 and key bytes
at 256, before constructing an unbounded DOM. Versions are explicit nonempty
bounded ASCII strings checked by the registry; schema-version strings never
select unknown fallback parsers. Dates in persisted records use RFC 3339 UTC
with `Z`. Schema/config references resolve only inside the pinned inventory.

## Decision adaptation

Arbitrium preserves fixed TaskSpec policy/question/labels and its request-order
probability presentation. Its codec owns English input and field assembly;
its composition uses categorical outputs plus optional answerability head and
masked categorical loss + binary loss. The neutral component can be a generic
categorical head or Bernoulli head; Core does not know recovery labels.
Arbitrium owns answerability meaning, gate precedence, ordinal anchors and
conversion into its typed DecisionResult. Abstention is distinct from any
action label. Legacy Decision schemas remain under Arbitrium; a reviewed
adapter translates them without promising binary/archive compatibility.

## Creative substitution check

A hypothetical Drum descriptor can encode BPM, meter, section, energy and
previous-bar events as finite features, and produce a fixed grid of kick/snare/
hi-hat/accent Bernoulli outputs. It supplies its own target schema, masks,
objective, admissibility rules and musical metrics. It needs neither canonical
English question, one class argmax, SentencePiece nor answerability probability.
The same envelopes, registration, freeze/checkpoint/bundle integrity and Runtime
admission remain valid. This is a contract thought experiment; no Drum
architecture, training or music-quality claim is included in this phase. A
separate test-only Tiny Beat composition must prove the full native lifecycle
in [A21](acceptance-and-migration.md#non-decision-end-to-end-gate-a21); envelope
and objective fixtures alone do not establish specialization-neutral Core.
