# Evaluation and calibration contracts

Status: proposed v1. Numerical primitives are reusable; task metrics and release
policies belong to the specialization.

## Prediction accounting

`maidionis.prediction.v1` requires experiment/run/sample/dataset identity and
digest, split, descriptor/artifact/component digest, selection scope,
calibration status, model result, target joined outside forward, registered
raw-output schema/payload, timing/profile and error status. Its JSON Schema is
part of the first implementation contract slice. Labels/provenance never enter
`forward`; the evaluator joins them after inference.

One result per admitted sample. Record framing errors, missing/duplicate IDs,
numerical errors and incomplete execution; do not shrink denominators until
quality looks good. A release run with incomplete predictions is `invalid_run`.
Every metric stores name/version, value or explicit null, numerator/support,
denominator definition, exclusions and slice identity. Empty accepted sets or
zero-support classes produce explicit undefined/warning states. Research code
that returns a convenient zero is adapted at this boundary.

Core offers optional categorical, Bernoulli, ordinal and statistical primitives.
Profiles register exact conventions, eligible records and target mappings; not
every specialization must implement accuracy, confidence or selective risk.
For Decision, raw class metrics on answerable records and answerability metrics
on all records have separate denominators. Confusion matrices retain canonical
label order/support. Aggregate accuracy must accompany majority/rule baselines
and per-label recall to expose imbalance. Correlated paraphrase rows do not
become independent evidence by increasing count.

## Calibration mechanisms and policy

Reuse finite scalar-temperature fit, calibrated softmax/sigmoid and Wilson
bound primitives as optional algorithms. Register optimization bounds/stopping,
numerical precision and T=1 comparison explicitly. Calibration operates on
fixed selected weights and calibration_fit only. Record raw/fitted objective,
support, convergence and boundary flags. Nonfinite/insufficient/nonconvergent
fits produce diagnostics, not deployable calibrated claims.

Acceptance selection operates on calibration_select only, with a registered
finite threshold grid, risk function, minimum support, coverage/error bound and
tie-breaking policy. The source embeds Decision-specific support/coverage/risk
constants; extract the search algorithm while Arbitrium supplies those values
and the definition of an accepted error. Gate fit is adaptive tuning evidence,
not a postselection guarantee. If no gate passes, keep research diagnostics and
disable actionable output. No universal calibration/abstention gate is imposed
on musical output or other task families.

Calibration record binds descriptor, model config, weights, codec, dtype/profile,
fit/select dataset/split digests, algorithm/config digest and results. Changing
any bound component requires refitting/reevaluation. Arbitrium retains separate
class and answerability temperature meaning; Core never treats their product
as calibrated joint correctness. Raw research outputs are named uncalibrated
and cannot masquerade as calibrated serving results.

## Registration and independent evaluation

An `EvaluationRegistration` fixes experiment ID, dataset/split/family definitions,
candidate/selection/config/component digests, metric/baseline policy, sample
requirements, calibration/gate profiles, numerical tolerances and performance
environment before opening the test suite. Test evaluates a preselected
candidate; it cannot choose architecture, epoch, seed, gate or next lessons.
Access ledger stores admitted identity/reason/time/report digest. Public
diagnostic test files do not establish sealed evaluation.

Bootstrap resamples families with paired model results. Register replicate
count, RNG algorithm/seed and **exact percentile convention** before computing
intervals. The initial neutral convention is sorted replicates, linear
interpolation at `(n-1)*p` with adjacent indices; zero valid replicates is
undefined and blocks release inference. This is a new documented convention,
not a claim that historical reports used it. Existing Decision bootstrap design
has an unresolved percentile specification and must be amended separately.
Dev-selected intervals remain selection heuristics; family-bootstrap sensitivity
and within-family correlation limitations accompany binomial risk bounds.

Failed evaluation stays in the report. Once exact held-out errors are opened or
used for adaptation, retire that suite for independent claims and register a new
experiment. A human/operator reviews readiness after complete evidence; Core
never auto-promotes a bundle or weakens a task's release thresholds.

## Measurement and research ownership

Record latency phases, warmup, repetitions, input lengths, batch/thread/device/
dtype, parameter count and process memory. A configured dependency or tensor
fixture is not physical GPU/model-family qualification. Numerical parity tests,
training-set fit and language/musical usefulness are separate acceptance lanes.

Arbitrium retains all original Experiment 001/002 records, seeds, hashes,
selection scopes, label support/recall, failures and reproduction limitations.
Maidionis stores the neutral accounting and reproducibility mechanisms without
duplicating those measured results. Migration must preserve the distinction
between train-only memorization, held-out generalization, answerability and
class imbalance; none alone demonstrates production readiness.
