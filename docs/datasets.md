# Dataset, manifest and provenance contract

Status: proposed v1. Historical Decision data remains in Arbitrium.

## Sample and provenance separation

`maidionis.sample.v1` is a closed envelope with `schema_version`, `sample_id`,
`family_id`, `dataset_id`, `specialization_id`, `specialization_version`, `task_id`,
`task_version`, `split`, `input_schema`, `input`, `target_schema`, `target`,
`provenance_id`, `verification_profile`, `verification_status`, `tags`, `supersedes`.
Schema references resolve against the frozen descriptor. Inputs are inference
payloads, not full teaching/audit records. Targets are separately validated
specialization data; Core does not require `answerable` or `label`.
`tags` is at most 32 unique opaque curriculum IDs; difficulty is an optional
specialization-defined target-independent audit field, not a mandatory 1..5
Core taxonomy. IDs follow the specialization contract. `supersedes` is null or
an immutable earlier sample ID resolved by the provenance ancestry inventory.
Verification status must be `verified` in frozen data; that status is validated
against evidence, not trusted because the generator wrote a boolean.

Audit records require sample/scenario/template ancestry; source content digest;
source license/permission basis; generator/config digest; teacher/reviewer
identity, prompt, sampling and raw-response references; proposed/reviewed/final
targets; verification profile/code digest and outcome; review disposition;
human audit reference when required; UTC timestamp and correction lineage.
Absent teacher/reviewer identities use explicit null plus non-model-source
reason. Model alias alone is not reproducibility identity. Record identical
teacher/reviewer weights as the same source, even with blind prompts.
Audit payloads use a registered strict schema, bounded record sizes and retained
digest-addressed records. Private prompts/responses can remain in controlled
storage; public manifests expose only approved sanitized references.

Candidate, rejected and corrected samples remain append-only audit evidence.
A correction creates a new identity, retains the original and requires review.
Model inputs never contain targets, final-label source, rationale, reviewer
notes, model confidence or hidden structured oracle facts.

## Frozen manifest

`maidionis.dataset.v1` requires these fields plus `schema_version`:

| Field | Binding |
|---|---|
| `dataset_id`, `parent` | immutable logical ID; parent null or `{id,digest}` |
| `descriptor` | `{path,sha256}` for the exact specialization descriptor |
| `created_at`, `generator` | UTC timestamp and `{code_digest,config_digest}` |
| `split_profile` | algorithm ID/version, seed, config digest and grouping version |
| `dedup_profile`, `verification_profile` | registered ID/version/config digest |
| `files` | every member except manifest: relative path, SHA-256, exact bytes and optional record count |
| `counts` | per-split records, families, tags and profile-defined target/verification support |
| `provenance_index` | inventoried path/digest and ancestry references |
| `license_summary`, `limitations` | bounded text/list of research restrictions |
| `purpose` | `research_fixture` or `registered_evaluation` |

Schema/profile configs and semantic specification are inventoried members.
The external dataset digest is SHA-256 of **final manifest bytes**, with no
self-hash. Hash exact UTF-8/LF bytes rather than reparsing/reformatting historic
JSON. Freeze timestamp is allocated once and journaled for resumability.

Layout is manifest + descriptor/semantic spec/schemas/configs + five split JSONL
files + family and provenance indexes. Every JSONL has one nonblank strict
object per line and ends in LF. Default record limit 128 KiB; manifest/individual
schema/config limit 4 MiB, total dataset limit 1 GiB, at most 1,000,000 samples,
at most 1,000 inventoried files and 1,024 bytes per relative path. A registered
profile may reduce limits; increased profiles require allocation/I/O evidence.
No absolute paths, traversal, symlinks or request-directed paths are accepted.
Streaming validation is preferred over reading 1 GiB into memory at once.

## Splits and access

| Split | Permitted use |
|---|---|
| train | vocabulary/features and weights |
| dev | model/checkpoint selection and aggregate education feedback |
| calibration_fit | fit frozen-model calibration parameters |
| calibration_select | select registered acceptance thresholds |
| test | separately admitted confirmatory evaluation after choices are frozen |

Teacher input is aggregate dev slices only, never reserved payloads/answers.
Native train receives only train/dev split handles plus inventory metadata;
calibration/test paths are not given to it. Validation can inspect all data in
a controlled freeze stage; it does not entitle later training to use all splits.
Enforce access at program and host/storage boundaries. Public research fixtures
are not sealed benchmarks, even if a file is named `test.jsonl`.

Group scenario, template, paraphrase and contrast ancestry before assignment.
An equivalent example with a renamed family remains equivalent. The initial
new neutral hash profile uses SHA-256 of UTF-8
`maidionis-split-v1\n` + decimal seed + `\n` + family ID, first eight bytes
big-endian modulo 10000, with 60/15/10/5/10 percent bucket boundaries.
Freeze the grouping/profile before measuring performance. Report actual counts;
do not move families to improve scores. Exact historical split bytes/assignments
are preserved by a legacy Arbitrium adapter; they never run through the new salt.
Changing the algorithm creates a new dataset/experiment, not the same benchmark.

Core provides hashing/group integrity; the specialization supplies the semantic
dedup projection. The source's state-only casefold/space and token 5-gram
similarity belong to a text profile, not a music/image universal rule. Record
the projection/normalization version. New cross-split ancestry or semantic
duplicates invalidate the registered experiment until resolved and re-registered.

## Freeze and native revalidation

Validate strict schema and task binding, ID/lineage/provenance references,
verifier eligibility, license evidence, duplicates, family separation, counts,
limits, file inventory and hashes. Write a fresh same-filesystem staging
directory, flush/fsync files and directories, verify the complete tree, then
publish without overwriting an existing ID. One writer per freeze; refuse
conflicts instead of guessing recovery. Retain incomplete-stage diagnostics.

Native consumers independently recheck digest, relevant file hashes/schema and
profile, record count, split, task/codec and tensor contract. Fixture-only mode
never weakens integrity. The source freezer implements useful journal/family/
hash mechanics, but not the complete production audit/support schema: migration
must fill those gaps rather than certify its current output as release data.
