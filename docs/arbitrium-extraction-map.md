# Arbitrium extraction map

Status: design inventory, **no implementation/data migration performed**.
Relative paths refer to the reviewed research tree, not files already shipped in
public Arbitrium. Public repository coordinates, source revision metadata and
personal stewardship documents are intentionally absent.

## Four responsibilities

| Code | Destination | Rule |
|---|---|---|
| C | Maidionis Core | genuinely neutral mechanisms after explicit refactoring |
| D | Arbitrium Decision specialization | task meaning, codec/assembly, oracle, heads/loss composition and policy |
| R | public Arbitrium research archive | historical curricula/configs/reports/results/limitations, kept separately from new runs |
| N | do not migrate verbatim / replace | old scaffolding, environment instructions, unfinished assumptions and private metadata |

A mixed C+D row requires a function/type-level split. It never authorizes copying
the whole file into Core. R code can preserve a historical generator/runner for
reproducibility without becoming the production Decision implementation.

## Function-level extraction decisions

| Source responsibility | C extraction | D/R retention and required adaptation |
|---|---|---|
| `contracts.cpp` / `contracts.py` | strict bounded parse, IDs, duplicate-key checks, hashes and shape machinery | TaskSpec, canonical policy/question, fixed labels and Decision result semantics stay D; legacy schemas stay D |
| `model.cpp` | optional pooled/encoder, embeddings, Q/K/V, masks, finite tensors and generic categorical/Bernoulli components | `ChoiceModel` composition, output names and masked categorical + answerability loss stay D; remove hardcoded three-label/default assumptions |
| `data.cpp` | registered deterministic order, padding/buffer primitives and manifest/hash validation | request-to-token and target/answerability mapping stays D; preserve legacy epoch-order algorithm/version rather than silently changing research seeds |
| `training.cpp` | optimizer loop, schedule, gradient checks, checkpoint primitives and selection mechanism | objective/dev metric composition stays D; replace name-based decay/PAD invariants with registered roles; add finite limits/full checkpoint inventory |
| `tokenizer.cpp` / `tokenizer.py` | optional SentencePiece loading/trainer primitives and hash/control verification | fixed field order, English train corpus projection, segment/control vocabulary and assembly version stay D |
| `metrics.cpp` | optional categorical/Bernoulli/ordinal reducers and Wilson math | Decision eligible subsets, support conventions and accepted-error meaning stay D; undefined denominators explicit |
| `calibration.cpp` | bounded scalar fit, finite softmax/sigmoid and parameterized finite grid search | answerability meaning, grid/support/coverage/risk constants and tie policy stay D; no universal readiness gate |
| `postprocess.cpp` | reusable numeric transforms only, already covered above | DecisionResult, canonical ties, request probability order, ordinal score and abstention precedence stay D |
| Python `dataset.py` | durable freeze, immutable manifest/inventory, family integrity hooks | state-text dedup and mutable-family-ID split hash are legacy D; new neutral data uses canonical ancestry fingerprints and changes dataset identity; full audit/support checking is additional work |
| Python `journal.py` | single-writer response journal, digest/replay and atomic output | POSIX implementation is the Linux profile; bound paths/storage and corruption recovery before broader support |
| Python `gpt_oss.py` | configurable bounded HTTP/replay/budget skeleton and provider identity | recovery prompts/target validation/facts stay D; receiving bytes before checking size is not a transport cap |
| Python `teacher.py` / `orchestrator.py` | finite provider/review/adjudication hooks and audit transitions | concept list, recovery facts and oracle binding stay D; agreement remains pending audit |
| Experiment runners/generators | useful design patterns only, no historical results in Core | keep exact research code/config/results R; replace embedded three-class reports only in new registered runs |
| Artifact loader/export | reviewed integrity/compatibility requirements | source complete serving engine is absent; implement metadata-only validation and host-admitted materialization/receipts, not a guessed existing loader |

Compiled Decision operations are assembled in Arbitrium's
[composition root](architecture.md#composition-root), not Core or Runtime's base
library. The registry builder and neutral numerical mechanisms live in Core;
Decision factories/drivers and the separate provider bridge remain Arbitrium.
Model descriptor, evaluation registration and Runtime capability registration
have separate identities. No legacy evidence is rewritten to fit these new rules.

## Known specification/implementation gaps

- Complete persisted bundle/model-config/calibration/training-metadata/evaluation
  schemas and loader/export/serving engine are not yet implemented in the source.
- Persisted prediction schema and bootstrap percentile rule are unresolved there;
  the neutral proposal supplies a new convention, not retrospective evidence.
- Source checkpoint resume verifies a state hash plus opaque identity, not each
  model/optimizer/RNG/config/environment member. Exact resume fixture parity is
  useful but does not discharge full integrity or crash-boundary requirements.
- Source training tracks the best epoch; selected-best export/publication and
  metadata need explicit Core contracts. The research runner reloads the epoch.
- Source freezer proves useful fixture lineage/split/hash properties, not complete
  production provenance, sealed support or semantic audit.
- Source dataset design has inconsistent minimum sealed-family counts. Arbitrium
  must retain the stronger release requirement until an explicit reviewed amendment;
  Core parameterization must not quietly weaken it.
- Optional encoder numerical/gradient tests are present; useful held-out encoder
  superiority and a released calibrated model are not demonstrated.
- Research experiments distinguish train diagnostics from dev, raw probabilities
  from fitted calibration, and reserved payloads from freeze validation. Preserve
  those distinctions and all failed/low-support results.

## Public migration controls

Use new public commits; do not import earlier Git history, author metadata,
personal attribution/stewardship documents or host-specific instructions.
Read source internally; publish only the reviewed public design and approved
research content. Scan file text, JSON metadata, examples, comments, PR/Issue
bodies and commit identity before publication.

Historical research belongs to Arbitrium only. Preserve original record/input/
target bytes, family assignments, manifest/file digests, seeds, selection scope,
raw/calibrated status and unsuccessful reports where publication is permissible.
Before A1, inspect the full dataset/audit/report payloads, not just manifests.
If forbidden metadata occurs inside a hashed file, retain the original in the
controlled audit record and publish an explicitly labeled sanitized derivative
with a new digest and original-to-derivative mapping. Never edit a file and claim
its original hash still matches. If faithful public evidence cannot be produced,
record the omission and its reproducibility limitation instead of fabricating it.
New Core conversions get new manifests/IDs and are not the historical dataset.

The historical archive uses a separate legacy reader/schemas. A neutral-schema
export is a derived dataset. Historical reports remain historic observations;
new public-architecture runs record their public code/dependency digests and
comparison tolerances separately. Scientific provenance survives without
publishing private repository coordinates or personal metadata.

## File inventory

The following enumerates every reviewed model/education/contract/test/document/
dataset/config responsibility. Personal stewardship material is excluded from
the public inventory. Repository root instructions/build defaults are assessed
for replacement, not copied into Core. Dataset payload classifications use their
manifests, generators and tests; full byte/hash publication verification belongs
to A1 and is not claimed here.

| Relative source path | Class | Migration treatment |
|---|---|---|
| `.gitignore` | N | Rebuild public instructions/package/build defaults against actual migrated code |
| `AGENTS.md` | N | Rebuild public instructions/package/build defaults against actual migrated code |
| `CMakeLists.txt` | N | Rebuild public instructions/package/build defaults against actual migrated code |
| `README.md` | N | Rebuild public instructions/package/build defaults against actual migrated code |
| `configs/education-gpt-oss.yaml` | R+N | Archive research intent; do not advertise old scaffold as runnable public configuration |
| `configs/experiments/current-diagnostic.json` | R+N | Archive research intent; do not advertise old scaffold as runnable public configuration |
| `configs/experiments/current-generalization.json` | R+N | Archive research intent; do not advertise old scaffold as runnable public configuration |
| `configs/experiments/current-tiny.json` | R+N | Archive research intent; do not advertise old scaffold as runnable public configuration |
| `configs/tiny.yaml` | R+N | Archive research intent; do not advertise old scaffold as runnable public configuration |
| `docs/architecture.md` | C+D | Extract neutral invariants; Decision specifications remain Arbitrium |
| `docs/artifact-format.md` | C+D | Extract neutral invariants; Decision specifications remain Arbitrium |
| `docs/build.md` | N+R | Archive relevant rationale; replace stale commands/status/environment assumptions |
| `docs/calibration.md` | C+D | Extract neutral invariants; Decision specifications remain Arbitrium |
| `docs/checkpoint-repair-2026-09-30.md` | R | Historical results/limitations or repair history; sanitize source coordinates |
| `docs/contracts/request.schema.json` | D | Legacy Decision schemas/fixtures; extract neutral shapes through new schemas |
| `docs/contracts/result.schema.json` | D | Legacy Decision schemas/fixtures; extract neutral shapes through new schemas |
| `docs/contracts/sample.schema.json` | D | Legacy Decision schemas/fixtures; extract neutral shapes through new schemas |
| `docs/contracts/task.schema.json` | D | Legacy Decision schemas/fixtures; extract neutral shapes through new schemas |
| `docs/dataset-design.md` | C+D | Extract neutral invariants; Decision specifications remain Arbitrium |
| `docs/dependencies.md` | N+R | Archive relevant rationale; replace stale commands/status/environment assumptions |
| `docs/design-review.md` | N+R | Archive relevant rationale; replace stale commands/status/environment assumptions |
| `docs/education-system.md` | C+D | Extract neutral invariants; Decision specifications remain Arbitrium |
| `docs/evaluation.md` | C+D | Extract neutral invariants; Decision specifications remain Arbitrium |
| `docs/examples/README.md` | D | Legacy Decision schemas/fixtures; extract neutral shapes through new schemas |
| `docs/examples/abstain-result.json` | D | Legacy Decision schemas/fixtures; extract neutral shapes through new schemas |
| `docs/examples/error-result.json` | D | Legacy Decision schemas/fixtures; extract neutral shapes through new schemas |
| `docs/examples/recovery-request.json` | D | Legacy Decision schemas/fixtures; extract neutral shapes through new schemas |
| `docs/examples/recovery-result.json` | D | Legacy Decision schemas/fixtures; extract neutral shapes through new schemas |
| `docs/examples/recovery-sample.json` | D | Legacy Decision schemas/fixtures; extract neutral shapes through new schemas |
| `docs/examples/recovery-task.json` | D | Legacy Decision schemas/fixtures; extract neutral shapes through new schemas |
| `docs/experiment-001.md` | R | Historical results/limitations or repair history; sanitize source coordinates |
| `docs/experiment-002.md` | R | Historical results/limitations or repair history; sanitize source coordinates |
| `docs/experiments/experiment-001-results.json` | R | Historical results/limitations or repair history; sanitize source coordinates |
| `docs/experiments/experiment-002-diagnostic-results.json` | R | Historical results/limitations or repair history; sanitize source coordinates |
| `docs/experiments/experiment-002-grouped-results.json` | R | Historical results/limitations or repair history; sanitize source coordinates |
| `docs/experiments/experiment-002-tiny-results.json` | R | Historical results/limitations or repair history; sanitize source coordinates |
| `docs/implementation-plan.md` | N+R | Archive relevant rationale; replace stale commands/status/environment assumptions |
| `docs/implementation-status.md` | R | Historical results/limitations or repair history; sanitize source coordinates |
| `docs/integration.md` | C+D | Extract neutral invariants; Decision specifications remain Arbitrium |
| `docs/interfaces.md` | C+D | Extract neutral invariants; Decision specifications remain Arbitrium |
| `docs/model-design.md` | C+D | Extract neutral invariants; Decision specifications remain Arbitrium |
| `docs/operations.md` | N+R | Archive relevant rationale; replace stale commands/status/environment assumptions |
| `docs/requirements.md` | C+D | Extract neutral invariants; Decision specifications remain Arbitrium |
| `docs/roadmap.md` | N+R | Archive relevant rationale; replace stale commands/status/environment assumptions |
| `docs/security.md` | C+D | Extract neutral invariants; Decision specifications remain Arbitrium |
| `docs/sources.md` | N+R | Archive relevant rationale; replace stale commands/status/environment assumptions |
| `docs/teacher-loop.md` | C+D | Extract neutral invariants; Decision specifications remain Arbitrium |
| `docs/tokenizer.md` | C+D | Extract neutral invariants; Decision specifications remain Arbitrium |
| `docs/training.md` | C+D | Extract neutral invariants; Decision specifications remain Arbitrium |
| `education/python/pyproject.toml` | N | Rebuild public instructions/package/build defaults against actual migrated code |
| `education/python/src/arbitrium_education/__init__.py` | N | Rebuild public instructions/package/build defaults against actual migrated code |
| `education/python/src/arbitrium_education/contracts.py` | C+D | Split mechanisms from Decision types/composition as detailed above |
| `education/python/src/arbitrium_education/current_curriculum.py` | R | Historical generator/runner; new neutral execution needs explicit composition |
| `education/python/src/arbitrium_education/dataset.py` | C+D | Split mechanisms from Decision types/composition as detailed above |
| `education/python/src/arbitrium_education/experiment.py` | R | Historical generator/runner; new neutral execution needs explicit composition |
| `education/python/src/arbitrium_education/gpt_oss.py` | C+D | Split mechanisms from Decision types/composition as detailed above |
| `education/python/src/arbitrium_education/journal.py` | C | Generic POSIX journal/replay; strengthen bounds/paths before migration |
| `education/python/src/arbitrium_education/oracle.py` | D | Finite recovery oracle and missing/conflicting-evidence semantics |
| `education/python/src/arbitrium_education/orchestrator.py` | C+D | Split mechanisms from Decision types/composition as detailed above |
| `education/python/src/arbitrium_education/schemas/request.schema.json` | D | Legacy Decision schemas/fixtures; extract neutral shapes through new schemas |
| `education/python/src/arbitrium_education/schemas/result.schema.json` | D | Legacy Decision schemas/fixtures; extract neutral shapes through new schemas |
| `education/python/src/arbitrium_education/schemas/sample.schema.json` | D | Legacy Decision schemas/fixtures; extract neutral shapes through new schemas |
| `education/python/src/arbitrium_education/schemas/task.schema.json` | D | Legacy Decision schemas/fixtures; extract neutral shapes through new schemas |
| `education/python/src/arbitrium_education/teacher.py` | C+D | Split mechanisms from Decision types/composition as detailed above |
| `education/python/src/arbitrium_education/tiny_curriculum.py` | R | Historical generator/runner; new neutral execution needs explicit composition |
| `education/python/src/arbitrium_education/tokenizer.py` | C+D | Split mechanisms from Decision types/composition as detailed above |
| `education/python/tests/test_contracts_oracle.py` | C+D | Strict parse fixtures to Core; Decision contract/oracle fixtures stay |
| `education/python/tests/test_current_curriculum.py` | R+D | Historical regeneration/research scope and Decision-specific checks |
| `education/python/tests/test_dataset.py` | C+D | Generic integrity tests to Core; field assembly/legacy split fixtures stay |
| `education/python/tests/test_experiment.py` | R+D | Historical regeneration/research scope and Decision-specific checks |
| `education/python/tests/test_orchestrator.py` | C+D | Transport/journal faults to Core; recovery prompts/audit fixtures stay |
| `education/python/tests/test_tokenizer.py` | C+D | Generic integrity tests to Core; field assembly/legacy split fixtures stay |
| `examples/education/README.md` | R | Preserve research fixture meaning and exact-byte inventory; legacy format |
| `examples/education/controlled-recovery-1000-v1/calibration_fit.jsonl` | R | Preserve research fixture meaning and exact-byte inventory; legacy format |
| `examples/education/controlled-recovery-1000-v1/calibration_select.jsonl` | R | Preserve research fixture meaning and exact-byte inventory; legacy format |
| `examples/education/controlled-recovery-1000-v1/dev.jsonl` | R | Preserve research fixture meaning and exact-byte inventory; legacy format |
| `examples/education/controlled-recovery-1000-v1/families.jsonl` | R | Preserve research fixture meaning and exact-byte inventory; legacy format |
| `examples/education/controlled-recovery-1000-v1/manifest.json` | R | Preserve research fixture meaning and exact-byte inventory; legacy format |
| `examples/education/controlled-recovery-1000-v1/provenance-index.jsonl` | R | Preserve research fixture meaning and exact-byte inventory; legacy format |
| `examples/education/controlled-recovery-1000-v1/task.json` | R | Preserve research fixture meaning and exact-byte inventory; legacy format |
| `examples/education/controlled-recovery-1000-v1/test.jsonl` | R | Preserve research fixture meaning and exact-byte inventory; legacy format |
| `examples/education/controlled-recovery-1000-v1/train.jsonl` | R | Preserve research fixture meaning and exact-byte inventory; legacy format |
| `examples/education/recovery-current-diagnostic-v1/calibration_fit.jsonl` | R | Preserve research fixture meaning and exact-byte inventory; legacy format |
| `examples/education/recovery-current-diagnostic-v1/calibration_select.jsonl` | R | Preserve research fixture meaning and exact-byte inventory; legacy format |
| `examples/education/recovery-current-diagnostic-v1/dev.jsonl` | R | Preserve research fixture meaning and exact-byte inventory; legacy format |
| `examples/education/recovery-current-diagnostic-v1/families.jsonl` | R | Preserve research fixture meaning and exact-byte inventory; legacy format |
| `examples/education/recovery-current-diagnostic-v1/manifest.json` | R | Preserve research fixture meaning and exact-byte inventory; legacy format |
| `examples/education/recovery-current-diagnostic-v1/provenance-index.jsonl` | R | Preserve research fixture meaning and exact-byte inventory; legacy format |
| `examples/education/recovery-current-diagnostic-v1/task.json` | R | Preserve research fixture meaning and exact-byte inventory; legacy format |
| `examples/education/recovery-current-diagnostic-v1/test.jsonl` | R | Preserve research fixture meaning and exact-byte inventory; legacy format |
| `examples/education/recovery-current-diagnostic-v1/train.jsonl` | R | Preserve research fixture meaning and exact-byte inventory; legacy format |
| `examples/education/recovery-current-grouped-v1/calibration_fit.jsonl` | R | Preserve research fixture meaning and exact-byte inventory; legacy format |
| `examples/education/recovery-current-grouped-v1/calibration_select.jsonl` | R | Preserve research fixture meaning and exact-byte inventory; legacy format |
| `examples/education/recovery-current-grouped-v1/dev.jsonl` | R | Preserve research fixture meaning and exact-byte inventory; legacy format |
| `examples/education/recovery-current-grouped-v1/families.jsonl` | R | Preserve research fixture meaning and exact-byte inventory; legacy format |
| `examples/education/recovery-current-grouped-v1/manifest.json` | R | Preserve research fixture meaning and exact-byte inventory; legacy format |
| `examples/education/recovery-current-grouped-v1/provenance-index.jsonl` | R | Preserve research fixture meaning and exact-byte inventory; legacy format |
| `examples/education/recovery-current-grouped-v1/task.json` | R | Preserve research fixture meaning and exact-byte inventory; legacy format |
| `examples/education/recovery-current-grouped-v1/test.jsonl` | R | Preserve research fixture meaning and exact-byte inventory; legacy format |
| `examples/education/recovery-current-grouped-v1/train.jsonl` | R | Preserve research fixture meaning and exact-byte inventory; legacy format |
| `examples/education/recovery-current-tiny-v1/calibration_fit.jsonl` | R | Preserve research fixture meaning and exact-byte inventory; legacy format |
| `examples/education/recovery-current-tiny-v1/calibration_select.jsonl` | R | Preserve research fixture meaning and exact-byte inventory; legacy format |
| `examples/education/recovery-current-tiny-v1/dev.jsonl` | R | Preserve research fixture meaning and exact-byte inventory; legacy format |
| `examples/education/recovery-current-tiny-v1/families.jsonl` | R | Preserve research fixture meaning and exact-byte inventory; legacy format |
| `examples/education/recovery-current-tiny-v1/manifest.json` | R | Preserve research fixture meaning and exact-byte inventory; legacy format |
| `examples/education/recovery-current-tiny-v1/provenance-index.jsonl` | R | Preserve research fixture meaning and exact-byte inventory; legacy format |
| `examples/education/recovery-current-tiny-v1/task.json` | R | Preserve research fixture meaning and exact-byte inventory; legacy format |
| `examples/education/recovery-current-tiny-v1/test.jsonl` | R | Preserve research fixture meaning and exact-byte inventory; legacy format |
| `examples/education/recovery-current-tiny-v1/train.jsonl` | R | Preserve research fixture meaning and exact-byte inventory; legacy format |
| `include/arbitrium/calibration.h` | C+D | Split mechanisms from Decision types/composition as detailed above |
| `include/arbitrium/contracts.h` | C+D | Split mechanisms from Decision types/composition as detailed above |
| `include/arbitrium/data.h` | C+D | Split mechanisms from Decision types/composition as detailed above |
| `include/arbitrium/metrics.h` | C+D | Split mechanisms from Decision types/composition as detailed above |
| `include/arbitrium/model.h` | C+D | Split mechanisms from Decision types/composition as detailed above |
| `include/arbitrium/postprocess.h` | D | Decision output/gate semantics; numeric primitives extracted separately |
| `include/arbitrium/tokenizer.h` | C+D | Split mechanisms from Decision types/composition as detailed above |
| `include/arbitrium/training.h` | C+D | Split mechanisms from Decision types/composition as detailed above |
| `src/app/contract_check.cpp` | C+D | Generic CLI framing; Decision validators/assembly remain specialization |
| `src/app/experiment.cpp` | R | Historical generator/runner; new neutral execution needs explicit composition |
| `src/app/smoke.cpp` | N | Replace bootstrap smoke entry point with meaningful migrated acceptance |
| `src/app/tokenize.cpp` | C+D | Generic CLI framing; Decision validators/assembly remain specialization |
| `src/calibration/calibration.cpp` | C+D | Split mechanisms from Decision types/composition as detailed above |
| `src/contracts/contracts.cpp` | C+D | Split mechanisms from Decision types/composition as detailed above |
| `src/data/data.cpp` | C+D | Split mechanisms from Decision types/composition as detailed above |
| `src/evaluation/metrics.cpp` | C+D | Split mechanisms from Decision types/composition as detailed above |
| `src/inference/postprocess.cpp` | D | Decision output/gate semantics; numeric primitives extracted separately |
| `src/model/model.cpp` | C+D | Split mechanisms from Decision types/composition as detailed above |
| `src/tokenizer/tokenizer.cpp` | C+D | Split mechanisms from Decision types/composition as detailed above |
| `src/training/training.cpp` | C+D | Split mechanisms from Decision types/composition as detailed above |
| `tests/contracts_test.cpp` | C+D | Retain numerical/integrity tests; split embedded Decision fixtures |
| `tests/data_test.cpp` | C+D | Retain numerical/integrity tests; split embedded Decision fixtures |
| `tests/metrics_test.cpp` | C+D | Retain numerical/integrity tests; split embedded Decision fixtures |
| `tests/model_smoke.cpp` | C+D | Retain numerical/integrity tests; split embedded Decision fixtures |
| `tests/postprocess_test.cpp` | C+D | Retain numerical/integrity tests; split embedded Decision fixtures |
| `tests/training_test.cpp` | C+D | Retain numerical/integrity tests; split embedded Decision fixtures |

