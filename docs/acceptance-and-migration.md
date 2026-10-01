# Acceptance and implementation migration plan

Status: design completion proposal for [Issue #1](https://github.com/flamoris-jp/Maidionis/issues/1).
This PR stops at reviewable design. Implementation, research migration, release,
deployment and merge are separate work.

## Issue coverage

| Issue #1 topic | Design location |
|---|---|
| Core responsibility | architecture.md ownership/components |
| specialization interface and identity/versioning | specialization-contract.md descriptor/compiled surface |
| dataset/manifest | datasets.md |
| education | education.md |
| checkpoint/reproducibility | artifacts.md and education.md native training |
| artifacts and namespace/naming | artifacts.md and architecture.md layout |
| inference | specialization-contract.md envelopes/decoding |
| evaluation/calibration | evaluation.md |
| Runtime adapter/shared-state input | runtime-integration.md |
| model lifecycle | architecture.md lifecycle and runtime-integration.md cleanup |
| C++/Python split and source layout | architecture.md and education.md |
| test strategy | acceptance cases below |
| provenance/migration and research ownership | arbitrium-extraction-map.md and datasets.md |
| public/private boundary | arbitrium-extraction-map.md public migration controls |
| creative generality | specialization-contract.md Drum substitution and A21 non-Decision E2E gate |

## Focused implementation slices

Dependencies below are logical commit/PR boundaries, not permission to implement
in this design PR. Keep each meaningful unit committed and verified promptly.

| Slice | Repository and scope | Acceptance prerequisite |
|---|---|---|
| M1 | Maidionis: shared JSON Schemas, strict envelope/descriptor/manifest/prediction validators, explicit registry builder/freeze and neutral fixtures | reviewed field/version/rejection contracts; A01–A03 |
| M2 | Maidionis: dependency locks, optional numerical components, batch/codec primitives, neutral objectives and synthetic test composition | M1; A04–A06/A22, clean CPU build; no Decision label defaults |
| M3 | Maidionis: deterministic training, structured full checkpoints and selected-best export | M2; A07–A09, same-build resume/crash/identity evidence |
| M4 | Maidionis: education transport/journal/freeze plus generic verification hooks | M1; A10–A12, no live teacher needed for offline checks |
| M5 | Maidionis: metadata-only validation and explicit host-context materialization, calibration/statistical primitives and complete evaluation accounting | M2–M4; A13–A16/A21/A23; defined persisted schemas before export; non-Decision full lifecycle is a completion gate |
| A1 | Arbitrium: immutable sanitized research archive and integrity inventory | may precede Core code; original meaning/digests and disclosure verified |
| A2 | Arbitrium: Decision descriptor/registration, codec, oracle, heads/objective/gate policies, compiled composition root/offline drivers/provider bridge and legacy adapters | relevant M1–M5 contracts; A17/A22; keep legacy data/readers distinct; Runtime integration deferred to R1 |
| A3 | Arbitrium: new public-architecture controlled reproduction reports | A1/A2; all seeds/scopes/negative evidence reported separately |
| R1 | AI Runtime and separate specialization bridge: registered bounded provider, admitted loader/holder/receipt handoff and explicit resource/control profile | Core/Decision artifacts stable; A18–A20/A23; actual current main rechecked; qualification before production use |

Schemas, tooling names and build/test commands are documented when real code
exists. No migration combines changes to all three repositories into one
unreviewable PR. A1 is research publishing, not copying source history or
claiming Core implementation. No new autonomous education or product Drum
implementation. The bounded synthetic test composition below is required Core
verification, not a creative model product.

## Acceptance cases

| ID | Observable obligation and meaningful negative case |
|---|---|
| A01 | native/Python strict parsing agree; reject duplicate/unknown keys, coercion, invalid UTF-8, unsupported versions, deep/oversized payload and nonfinite values |
| A02 | descriptor pins intrinsic schema/code/config/numerical compatibility only; changing release minimum support or Runtime cancellability leaves its digest/calibration components unchanged, changes the appropriate registration and never inherits old approval; reject unknown component, missing schema, mismatched task/version and request-supplied artifact path |
| A03 | neutral non-Decision fixture traverses envelopes/registry/data boundaries without question, labels or answerability requirements |
| A04 | padding/batch/single/eval/archive parity for optional pooled/encoder components; reject dimension/dtype/mask overflow; preserve finite gradients |
| A05 | Decision loss masking does not index invalid targets; objective is selected by composition; other objective needs no answerability tensor |
| A06 | same seed produces same initial parameters despite prior RNG use, different seed changes them; no unqualified concurrent global-RNG training |
| A07 | uninterrupted and epoch-resume parameter/history/schedule/best-object parity in exact tested CPU profile |
| A08 | alter each weights/optimizer/RNG/config/data/descriptor/environment inventory member: reject before resume; latest pointer traversal and missing state rejected |
| A09 | injected write/fsync/rename/pointer/crash failures leave prior good checkpoint usable; no partial publication; best/final objects are explicit |
| A10 | teacher proposals remain unverified; blind review excludes original label/rationale; same-model agreement does not grant audit status; corrections retain lineage |
| A11 | bounded transport timeout/status/redirect/truncation/oversize/cancellation/replay tests using fakes; committed replay makes zero network requests |
| A12 | freeze deterministic bytes on interrupted resume, no overwrite; rename family IDs or add equivalent paraphrases/corrections without moving splits; reject forged/missing anchors, inconsistent fingerprints, changed seed and cross-split ancestry; tokenizer sees only train, teacher no held-out payload; legacy assignments preserved |
| A13 | trusted bundle digest and every file/key/shape/codec/calibration binding validated; reject untrusted provenance, symlink/race/extra file and unsupported profile |
| A14 | finite calibration/T=1/support/gate tie fixtures; policy parameterized; failed gate disables actionable output and raw values never claim calibration |
| A15 | hand-calculable metrics include zero support/empty acceptance, all-unanswerable and imbalance; missing/duplicate/error predictions invalidate complete release accounting |
| A16 | preregistration/ledger prevents test-driven selection; exact percentile fixtures; finalization changes reports/card but not evaluated-component digest |
| A17 | Arbitrium fixed-label/order semantics, answerability, ordinal/binary and abstention/error remain compatible under explicit adapter; native/Python codec parity |
| A18 | Runtime rejects stale/revoked pins/grants, invalid input/output/identity and overflow; success/abstention/model error/provider failure distinct |
| A19 | serialized worker, late/cancelled/race losing completion fenced; retained resources drain before release; unsupported controls rejected |
| A20 | state changes after inference block action; no teacher needed during inference; no Core action/Workflow/global-state authority |
| A21 | one compiled non-Decision fixture traverses frozen dataset → real train → epoch checkpoint/resume → selected-best export → artifact validation/admitted load → inference → complete evaluation, with no Decision imports/defaults; parameter mutation, resume/parity and deliberate corrupt/mismatched records prove production-path use |
| A22 | Core and its neutral tests build/link without Arbitrium/Runtime; Arbitrium composition explicitly registers all operations; reject duplicate/missing/unknown compiled bindings; Runtime base builds without Decision code; shared operation/build identity used by train/export/infer |
| A23 | validation constructs no model/tensor/device context; rejected capacity invokes no materializer; explicit admitted CPU/peak budgets and no automatic device move; failed/expired/stale/overflow loads publish no holder; receipt handoff, retained caches, partial allocation cleanup and exactly-once residency accounting tested with faults; fakes do not qualify real LibTorch bounds |

Tests should exercise production components and deliberate faults, not duplicate
implementation expressions. Unit fixtures establish numerical/contracts only.
Arbitrium research reruns establish their actual scope; sealed quality,
performance/GPU qualification and real host enforcement are separate evidence.
Do not claim the source's recorded passing counts were rerun by this PR.

## Non-Decision end-to-end gate (A21)

Use a **Tiny Beat synthetic test specialization**, owned only by Maidionis's test
tree. This is a mechanics fixture, not the proposed Drum product or research
claim. Its compiled composition links Core only; no Arbitrium/Decision package,
Runtime, SentencePiece, question/label/order or answerability field is required.

| Part | Fixed test obligation |
|---|---|
| Input | strict finite `energy` integer 0..100 and `beat_position` integer 0..15; registered feature normalization independent of targets |
| Target/output | two independently valid booleans, `kick` and `snare`; deterministic fixture oracle supplied by test specialization |
| Model/objective | small registered two-feature native network with two Bernoulli logits and BCE objective; no categorical/answerability head or target mask |
| Decode | two fixed sigmoid thresholds in test codec; no confidence/answerability diagnostics, diagnostics schema null |
| Data | deterministic source scenarios, canonical ancestry/fingerprints, frozen schemas/config/manifest/provenance; split integrity is validated rather than bypassed |
| Selection/evidence | preregistered `train_diagnostic` selection; synthetic verification/evaluation registration allows calibration `not_applicable`, raw outputs explicitly uncalibrated and artifact `research_only` |

The implementation pins fixture bytes, oracle/normalization, seed, optimizer,
schedule, total epochs, selection ties and numerical tolerance **before** running
training. Its immutable grouping projection declares shared scenario/template/
contrast ancestry, rejects equivalent inputs across families and reports actual
split counts. Use only the resulting nonempty train split for this train-only
mechanics proof; do not search seeds/family IDs or relabel held-out rows to get
more support. No tokenizer or teacher is needed. A separately constructed frozen
fixture is acceptable only with explicit new identity and test review.

Required observable path:

1. Resolve the test's immutable registry/descriptor, then freeze with the real
   data/provenance components and native revalidation. Unknown or missing Bernoulli
   operations fail; nothing supplies a Decision default.
2. Train actual Core model/optimizer components in the exact serialized CPU FP32
   profile. Assert finite nonzero gradients and changed parameters after updates,
   so a validator-only/stub training pass cannot satisfy the gate.
3. Save a real epoch-boundary checkpoint after at least one optimizer update;
   resume in a fresh process and perform at least one further update. Compare
   final parameters, optimizer/schedule/history and selected-best identity with
   the uninterrupted run under the preregistered tolerance. Final and best remain
   separate objects even if the same epoch wins.
4. Export selected-best, verify prediction parity, assemble a research-only
   artifact with the permitted absent-calibration record, and validate it using
   the metadata-only loader. Materialize through an explicit bounded offline
   host context; no Runtime lifecycle extension is needed for this offline test.
   In-memory pre-export model reuse cannot stand in for actual archive load.
5. Infer through real envelopes/codec/model/decode on the diagnostic inputs.
   Compare loaded-model logits within tolerance and boolean outputs exactly;
   threshold-adjacent cases require explicit registered handling. Verify null
   diagnostics and absence of class/answerability requirements.
6. Produce one prediction per admitted input, join targets outside forward and
   evaluate both Bernoulli outputs with the registered reducer/support rules.
   Recompute metric denominators from the recorded predictions and compare with
   hand-calculable fixtures. The report binds the same descriptor/component/data
   and evaluation-registration identities at every stage and says train-only
   synthetic mechanics, not generalization or musical quality.

Negative runs corrupt weights/checkpoint inventory, change descriptor/codec,
exceed a host budget or omit/duplicate a prediction. They must respectively fail
resume/load/compatibility/admission or complete evaluation accounting. A new
process/network-free run must need neither a teacher nor Decision services.
M2 supplies the composition, M3 proves real train/resume, and M5 completes A21;
passing only A03/A05 does not satisfy M5. Physical resource bounding/Runtime
qualification remains A23/R1, separate from an offline mechanics success.

## Design review and stop condition

Review neutral substitution, dependency direction, exact persisted field
coverage, archive/config identity, undefined metric behavior, holdout controls,
partial source implementation, Runtime's concrete current seams and public
privacy. Resolve discrepancies before implementation. Once accepted, divide
Issue #1's implementation/migration checkboxes into focused follow-on work;
reviewed design is not evidence those boxes are complete. This PR references
Issue #1 without auto-closing it.
