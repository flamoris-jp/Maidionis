# Design self-review

Reviewed on 2026-10-01. Status: **self-reviewed proposal awaiting human/PR review**.
This record covers documentation consistency and source inspection. It does
not certify implementation, model quality, deployment or future acceptance tests.

## Findings corrected before PR

| Finding | Resolution |
|---|---|
| Copying the source's two-head model would make Core Decision-shaped | optional backbone/head primitives; specialization owns target/loss/decode; Drum substitution requires no class argmax or answerability |
| Source checkpoints have narrower integrity than their design specification | full member/config/data/environment inventory, explicit best/final objects, contained pointer paths and crash/fsync acceptance |
| Runtime's registered provider seam does not imply generic model residency | document concrete TinyModel residency and require a Runtime-owned loader/holder/allocation extension before integration |
| Post-call deadline checks could be mistaken for interruption guarantees | synchronous noncancellable/nonpausable profile; retain accounting until actual stop; hard deadlines require separately qualified isolation |
| Combined source metrics can throw on all-unanswerable slices or produce NaN | independent metric eligibility; nullable undefined values with support; strict JSON never emits NaN |
| Canonical component digest could differ across native/Python serialization | fixed sorted inventory array, exact keys/integers/escaping/UTF-8/LF and shared fixtures |
| New split salt could silently change historical benchmark membership | preserve legacy bytes/readers; neutral-schema conversion is a new derived dataset/experiment |
| Privacy edits inside hashed research files could invalidate provenance | retain protected original, publish labeled derivative/new digest and explicit mapping/omission; never claim unchanged hash after editing |

## PR review findings corrected

The first PR review identified four ownership/integrity blockers and a missing
generality proof. This amendment corrects their contracts without starting code.

| Finding | Resolution and future acceptance |
|---|---|
| Mutable family IDs controlled split assignment | canonical immutable ancestry fingerprints; alias/correction inheritance, fixed preregistered seed, recomputation and cross-family invalidation; A12 |
| Descriptor mixed model identity with release/Runtime policy | intrinsic schemas/code/numerical requirements only; separate EvaluationRegistration and Runtime registration digests; policy-only changes preserve model/calibration identity and require new approval/qualification; A02 |
| Compiled registration had no owner | Arbitrium owns specialization/composition/drivers/provider bridge; Core and Runtime base build without Decision; registry freezes before descriptor resolution; A22 |
| Core loader could allocate/move a model outside Runtime admission | metadata-only validation, explicit host-admitted materialization, physical allocation receipt/handoff and failure cleanup; CPU as well as device memory charged; A23 |
| Non-Decision fixtures stopped before full lifecycle | test-only Tiny Beat dataset/train/fresh-process resume/export/load/infer/evaluate gate, real parameter mutation and negative cases; A21 required for M5 |

## Boundary review

| Question | Finding |
|---|---|
| Is Decision meaning absent from Core contracts? | request/target/output schemas and policy are registered specialization data; recovery oracle/labels/answerability/gates remain Arbitrium |
| Does Runtime keep action and live-state authority? | Core returns values; Runtime owns grants/Jobs/residency/deadlines; caller freshness and action policy checked separately |
| Are demonstrated source mechanisms reused? | explicit model/mask/training/order/journal/freeze/calibration primitives are mapped; no duplicate Python model |
| Are source gaps and failures retained? | incomplete bundle/checkpoint/prediction/support/calibration/encoder evidence stated; historic reports stay Arbitrium |
| Can another bounded domain use the contract? | Drum thought experiment and concrete required A21 test-only full lifecycle; no claim it has run yet |
| Are design and implementation separated? | all docs marked proposal; schemas/CLI/bundle/adapter support await implementation evidence |
| Is migration concrete? | per-file inventory, function-level split, specialization-owned composition, M1–M5/A1–A3/R1 slices and A01–A23 acceptance cases |
| Is publication scoped? | no source history/code/data copied; private source coordinates/personal metadata omitted; public Runtime revision pinned |

## Verification scope

- Inspected current main for Maidionis, public Arbitrium, source research and AI
  Runtime, plus both design/migration Issues and repository instructions.
- Read the native/Python source and tests, specification/implementation-gap
  records, experiment generators/configs/reports and dataset manifests. Full
  dataset payload/hash publication verification is an A1 obligation, not a
  completed task in this PR.
- Checked local Markdown link targets, fence balance, required design-topic
  coverage, complete 135-path extraction inventory, closed acceptance IDs and
  public privacy patterns. Checked GitHub tree/diff preservation and committed
  file contents against the local candidate before PR completion.
- No model build/training, native/Python acceptance suite, teacher call, Runtime
  integration or live host checks were run. Existing recorded research test
  counts are source evidence only and are not reported as passing here.

No unresolved blocker was found within the design-only delivery scope after
these corrections. Human review can still amend the proposal. M1 must turn the
field tables into shared schemas and fixtures before persisted implementation;
R1 must implement and qualify the stated Runtime lifecycle extension. Those
requirements remain future work, not a claim this PR is ready to deploy.
