# Education and native training

Status: proposed v1. Education is finite offline work; inference never teaches itself.

## Candidate review and provider contracts

Core education envelopes carry task/descriptor/schema identity, generation
budget, attempt IDs and provenance. The specialization supplies concepts,
scenario facts, rendering/prompt templates, target semantics, verifier and audit
policy. Do not transfer recovery facts, fixed concept list or target labels into
generic `TeacherProvider`/`ReviewerProvider` types.

Blind review receives the input, task rubric and allowed facts, excluding the
teacher's proposed answer/rationale. Teacher/reviewer agreement remains a
proposal. A deterministic oracle verifies structured outcomes, but free-form
prose still needs semantic adjudication under the specialization's audit policy.
Do not automatically turn matching model answers into `verified` records.

Reuse bounded HTTP transport as a replaceable education adapter: trusted origin
configuration, no embedded credentials/query/fragment/redirect, explicit remote
opt-in, immutable model/template identities, final-content-only strict parsing,
finite input/response byte caps, deadlines, attempt budget and cancellation.
Credentials stay outside prompts/journal. Keep retry/backoff and uncertain
remote attempts distinct from student output semantics. The initial policy is
at most two transport retries for timeout/network/429/5xx; auth/schema failures
do not repeat identical requests. New corrective generations are new attempts
under the same cycle budget. Replayed committed responses do not invoke a teacher.
The source transport's type/byte checks occur after receiving a response;
implementation must enforce streaming/transport byte caps before allocation
and a true elapsed deadline, rather than claiming a post-hoc check cancels work.

## Finite cycle

An `EducationPlan` requires experiment ID, descriptor digest, curriculum/prompt
config digests, approved provider identities, verifier/audit policy, split/data
references, resolved training/selection configuration, separate calibration config
and preregistered evaluation-policy/config digests, and explicit maximum cycles,
attempts, examples, elapsed time and output/storage bytes. Every maximum is
positive and finite. No sentinel meaning unlimited is allowed in a registered
run. Policy belongs to the specialization; Core checks bounds and accounting.

Stages: plan → generate → review → adjudicate → freeze → train → calibrate →
dev-report. Failure/cancellation records stage and output digests; it does not
pretend later stages completed. Calibration stages may be explicitly absent
for a raw research diagnostic, recorded in the report. No sealed-test stage
feeds the cycle. Independent release evaluation is separately admitted.
Single-writer journal, immutable content-addressed response records and durable
stage outputs support restart. Reject corrupt/partially committed journal
entries; recovery is explicit. Journal durability does not prove remote work
was never attempted or give exactly-once provider behavior.

The plan fixes evaluation policy before candidate selection. The final
`EvaluationRegistration` adds the exact selected component/calibration/data
bindings after export, before any confirmatory test access. It does not need to
predict future weight bytes when the education plan is created. Journal both
records and reject a policy substitution at final registration; retrospective
policy assessments are explicitly separate work, not continuation of this plan.

Only aggregate supported dev slices propose new lessons. New families stay
disjoint from holdouts. Record dev adaptation; contaminated holdouts are retired.
Bound cycle count and stopping objective in advance. No automatic promotion,
production weight mutation, production outcome logging or indefinite retraining.

## Native training composition

Core training receives validated encoded batches, registered backbone/head/
objective composition, optimizer parameter groups, resolved config and an
explicit selection profile. It handles deterministic epoch order, schedule,
gradient finiteness/clipping, optimizer steps, history and checkpoint publication.
Specialization supplies target masks and objective semantics. The source's
combined categorical/answerability objective and fixed loss weight are a
Decision composition; they are not hardcoded into the neutral loop.
The [specialization-owned composition root](architecture.md#composition-root)
installs these compiled operations and freezes the registry before training.
Offline Arbitrium drivers link that root; Core does not import Decision code.

Initialization seed applies **before model construction**; loop reseeding is
insufficient. Record CPU/other RNG streams, epoch-order algorithm/version,
dropout settings, thread count, dependency/compiler/device profile and resolved
parameter ordering. Training is initially CPU FP32, one thread and one process
per run. Exact uninterrupted/resume parity is a same-build profile guarantee
to prove; statistical reproducibility across versions is a different claim.

Optimizer decay exclusions must be explicit parameter roles/groups, not guessed
from names such as `embedding.weight`/`norm`. Padding constraints come from the
batch/embedding profile and are enforced after optimizer updates. Never hardcode
source module names or assume every specialization has a PAD row.

| Selection scope | Constraint and report |
|---|---|
| `dev` | disjoint frozen dev, registered objective; no test/calibration selection |
| `train_diagnostic` | intentionally reuse train for selection; explicitly mark memorization; do not report dev or generalization |

Empty dev is an error for a dev-selection run. A train-only experiment may
select on train under the second profile; Core must never silently alias it.
Store both last and selected-best weights as distinct hashed objects and
reload the selected object for evaluation. Patience/schedule stopping cannot
discard the best object. Zero-support or undefined objectives are explicit,
not fabricated zeros. Bound epochs, steps, sample count and output size.

Python invokes native tools via an argv list, never shell-generated commands.
Exact CLI commands and dependency locks will be added only after implementation
and clean installed-package validation. This proposal does not invoke any live
teacher, server or OpenAI API, and requires no production credentials.
