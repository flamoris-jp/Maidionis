# Maidionis Core design

Status: **design proposal for Issue #1; no implementation or stable public API**.
The documents define a reviewable v1 target. Acceptance requires implementation
evidence in later PRs; source research test results are not Maidionis test results.

| Read | Contract |
|---|---|
| [Architecture](architecture.md) | ownership, compiled composition root, dependencies, lifecycle, language and source layout |
| [Specialization](specialization-contract.md) | identity, registration, bounded input/output, model components |
| [Datasets](datasets.md) | sample/manifest envelope, freeze, split and provenance boundaries |
| [Education](education.md) | reviewed lessons, finite training cycles and reproducibility |
| [Artifacts](artifacts.md) | checkpoint integrity, bundle binding, metadata validation, admitted materialization and compatibility |
| [Evaluation](evaluation.md) | measurement, calibration, release evidence and denominators |
| [Runtime integration](runtime-integration.md) | existing Runtime seams, proposed adapter and state authority |
| [Extraction map](arbitrium-extraction-map.md) | source inventory, four-way classification and known gaps |
| [Acceptance and migration](acceptance-and-migration.md) | Issue coverage, focused implementation PRs, A01–A23 checks and non-Decision E2E gate |
| [Design self-review](design-review.md) | corrected findings, verification and remaining implementation gates |

Within this proposal, the tables specifying required fields, invariants and
rejection behavior are the contract target. Examples are illustrative. No
persisted `maidionis.*.v1` schema has shipped. The first implementation slice must
encode these rules in shared JSON Schemas, strict native/Python validators and
positive/negative fixtures before producing persisted records. A substantive
change to these reviewed semantics requires a design amendment; an implementation
may refine names and types without silently changing ownership or compatibility.

## Evidence used

The design was prepared on 2026-10-01 from the current Maidionis and public
Arbitrium repository contracts, the existing Arbitrium research implementation,
its native and Python tests, datasets/manifests and experimental reports, and
the actual FLAMORIS AI Runtime adapter/native types. The extraction map records
relative source paths and distinguishes implemented mechanisms from specification
gaps. Source-location and revision bookkeeping stays in the internal review
record; public documentation contains no private repository coordinates.

Public authority references:

- [Maidionis Issue #1](https://github.com/flamoris-jp/Maidionis/issues/1)
- [Arbitrium Issue #1](https://github.com/flamoris-jp/Arbitrium/issues/1)
- [Arbitrium research migration](https://github.com/flamoris-jp/Arbitrium/blob/main/docs/research-migration.md)
- [Runtime inspected revision](https://github.com/flamoris-jp/flamoris-ai-runtime/tree/3e8b04137b7510023cb1799aaacfbe3e9cf73771)

Runtime links pin the public revision inspected for this proposal. Recheck its
current main before implementing the adapter; these links are not a live-state
or deployment claim.
