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
| creative generality | specialization-contract.md Drum substitution |

## Focused implementation slices

Dependencies below are logical commit/PR boundaries, not permission to implement
in this design PR. Keep each meaningful unit committed and verified promptly.

| Slice | Repository and scope | Acceptance prerequisite |
|---|---|---|
| M1 | Maidionis: shared JSON Schemas, strict envelope/descriptor/manifest/prediction validators, explicit registry builder/freeze and neutral fixtures | reviewed field/version/rejection contracts; A01–A03 |
| M2 | Maidionis: dependency locks, optional numerical components, batch/codec primitives and neutral objectives | M1; A04–A06, clean CPU build; no Decision label defaults |
| M3 | Maidionis: deterministic training, structured full checkpoints and selected-best export | M2; A07–A09, same-build resume/crash/identity evidence |
| M4 | Maidionis: education transport/journal/freeze plus generic verification hooks | M1; A10–A12, no live teacher needed for offline checks |
| M5 | Maidionis: artifact loader, calibration/statistical primitives and complete evaluation accounting | M2–M4; A13–A16; defined persisted schemas before export |
| A1 | Arbitrium: immutable sanitized research archive and integrity inventory | may precede Core code; original meaning/digests and disclosure verified |
| A2 | Arbitrium: Decision descriptor/registration, codec, oracle, heads/objective/gate policies, compiled composition root/offline drivers/provider bridge and legacy adapters | relevant M1–M5 contracts; A17/A22; keep legacy data/readers distinct; Runtime integration deferred to R1 |
| A3 | Arbitrium: new public-architecture controlled reproduction reports | A1/A2; all seeds/scopes/negative evidence reported separately |
| R1 | AI Runtime: registered bounded provider integration and explicit resource/control profile | Core/Decision artifacts stable; A18–A20; actual current main rechecked |

Schemas, tooling names and build/test commands are documented when real code
exists. No migration combines changes to all three repositories into one
unreviewable PR. A1 is research publishing, not copying source history or
claiming Core implementation. No new autonomous education/Drum implementation.

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
| A22 | Core and its neutral tests build/link without Arbitrium/Runtime; Arbitrium composition explicitly registers all operations; reject duplicate/missing/unknown compiled bindings; Runtime base builds without Decision code; shared operation/build identity used by train/export/infer |

Tests should exercise production components and deliberate faults, not duplicate
implementation expressions. Unit fixtures establish numerical/contracts only.
Arbitrium research reruns establish their actual scope; sealed quality,
performance/GPU qualification and real host enforcement are separate evidence.
Do not claim the source's recorded passing counts were rerun by this PR.

## Design review and stop condition

Review neutral substitution, dependency direction, exact persisted field
coverage, archive/config identity, undefined metric behavior, holdout controls,
partial source implementation, Runtime's concrete current seams and public
privacy. Resolve discrepancies before implementation. Once accepted, divide
Issue #1's implementation/migration checkboxes into focused follow-on work;
reviewed design is not evidence those boxes are complete. This PR references
Issue #1 without auto-closing it.
