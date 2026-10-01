# Initial Core implementation and acceptance

This implements Issue #4 on the existing `feat/core-m1-m5` branch, preserving
the three original commits through `d220eb9`. The reviewed main baseline was
`650a21a`. No Arbitrium research archive, Runtime implementation, live provider
call, deployment or merge is included.

## Implemented reference slices

| Slice | Implemented components | Observable acceptance |
|---|---|---|
| M1 | shared generated schemas; bounded closed native/Python parsing; explicit frozen registries | parity/rejection fixtures, schema validity, missing/duplicate bindings, neutral inputs |
| M2 | CPU dense/pooled/encoder modules, explicit roles, Bernoulli/categorical objective primitives, specialization-owned test composition | initialization seed, batch/padding/archive parity and finite gradients; no Decision dependencies |
| M3 | deterministic digest-sorted epochs, AdamW/schedule, full epoch inventories, selected-best and final objects, resume | fresh-process bit-exact weights/history/best/logits in the tested build; corruption of all ten inventory members; rehashed schedule/role substitution; real publication fault recovery |
| M4 | explicit bound Python hooks/providers, finite controller, immutable response journal, strict family/provenance freeze | blind review and non-oracle agreement stays unverified; replay makes zero calls; finite deadline worker termination; no-overwrite/fault/digest/split/provenance checks |
| M5 | metadata-only immutable bundle snapshot, explicit isolated offline load, statistical primitives, complete prediction accounting, preregistration ledger, research finalization | A21 whole path; capacity/expiry/fault/shape/evidence rejection; missing/duplicate/error predictions invalidate complete accounting |

Public APIs are experimental. Descriptor and schema definitions remain compiled
and explicitly registered; imported records cannot install new executable code.
Core imports neither Arbitrium nor Runtime. Tiny Beat supplies its own oracle,
grouping, codecs, heads, objective, metric reducer and passing mechanics policy.
The compiled build digest hashes the sorted Core/native/Python/schema and test
composition source inventory plus build configuration. CMake tracks content
changes as configure dependencies; a source edit invalidates the build pin.
The Python composition independently computes the same digest. Compiler/ABI/
LibTorch compatibility remains a separate exact numerical environment binding.
Persisted Core schemas are embedded in native binaries; Python package schema
bytes must match the generated pins included in that build inventory. A schema
file replacement cannot silently change an existing binary/package contract.
Shared validation applies sibling constraints after `anyOf` succeeds.

Python evaluation seals a complete verified split into `EvaluationDataset`.
Registration must match its dataset/descriptor/build/split identities, and the
original plan must admit its dataset digest. Every expected sample remains in
accounting, including valid abstentions; metric eligibility and quality policy
are specialization-owned. These are experimental API changes from bare lists.

## Reproduce acceptance

Use the README setup and `python tools/verify.py`. This runs production components
and real LibTorch archives; the lifecycle does not reuse the pre-export model
as a substitute for archive loading. `test_lifecycle.py` launches each operation
in a fresh process under a 2 GiB `RLIMIT_AS`, 30-second CPU limit and finite
parent deadline. The input grid, seed 42, six epochs, optimizer, threshold ties
and train-diagnostic selection are fixed in code before measurement. All 176
source rows receive the documented ancestry hash split; no aliases/seeds are
searched to increase training support. The actual counts are validated from
the frozen manifest. Only the resulting train subset is evaluated in A21.

The tested environment is Linux x86_64/glibc 2.39, GCC 13.3.0, Python 3.12,
Torch 2.5.1+cpu, CMake 3.31.6, Ninja 1.11.1.4, nlohmann_json 3.11.3 and
jsonschema 4.23.0. Exact parity is a same-build/profile claim; it does not promise
equal floating-point results across dependency/compiler upgrades. CI installs
the pinned dependencies and verifies both numerical and reduced builds.

## Loading and physical accounting

`validate_bundle` hashes the trusted manifest, takes a bounded verified byte
snapshot and resolves descriptor/config/schema/tensor/evidence identities without
constructing a model. A real constructor counter checks this in the native
validation driver. Snapshot bytes remain charged to the validation reservation;
materialization reads those bytes instead of reopening mutable source paths.

The offline host owns a disposable process, sets a finite kernel address-space
limit before native startup, reserves that whole process envelope (libraries,
framework caches, snapshot, model, archive overlap and inference), and waits for
process exit before acknowledging cleanup. Core verifies that the kernel limit
is present and no greater than both the admitted process and peak budgets.
The persistent tensor budget is an additional minimum check, not a replacement
for the whole-process reservation. The receipt records exact pins, snapshot/
tensor bytes and process peak RSS; RSS is observation, not an admission grant.
Neither a model destructor nor a fake observer proves physical cleanup.

There is no Runtime holder/receipt transfer here. Serving validation is rejected
until R1 supplies its independent approval, pins, host lifecycle and accounting.
The isolated host is tested on Tiny Beat; GPU/device allocation and other model
family production qualification are not claimed. Checksums and OS memory limits
do not make a malicious native archive safe: sources require trusted provenance.

## Deliberate limits and follow-on work

- Python freeze is a bounded in-memory reference, tested on the synthetic grid;
  million-row streaming/large-artifact performance is not qualified. Strict JSON
  depth/value limits may reject files below their byte cap.
- The controller provides generate, blind review, adjudication, budgets and
  replay primitives. Specialization drivers explicitly compose freeze/train/
  calibration/evaluation. It does not autonomously choose lessons or promote
  artifacts. A recorded uncertain remote attempt requires explicit recovery;
  journal replay does not promise exactly-once remote execution. All HTTP tests
  use fakes; no live teacher/provider credential was used.
- The loader initially accepts explicitly permitted absent calibration.
  Bernoulli temperature fitting, sigmoid, Wilson/gate and percentile primitives
  are implemented; production calibrated archive registrations and additional
  task-specific/categorical/ordinal reducers remain specialization follow-on work.
- The test-only Tiny Beat native verifier accepts the preregistered grid/oracle
  profile, including its null correction lineage. Generic Python freeze supports
  same-family correction ancestry, retaining unverified/rejected originals in
  a separate inventoried audit stream rather than admitting them to training;
  native support for other verification or
  legacy profiles requires an explicit specialization composition.
- Checkpoint recovery never silently overwrites a published epoch. After a
  pointer-publication failure, the previous pointer remains usable and an orphan
  may remain. The regression demonstrates explicit recovery by selecting the
  prior verified epoch into a new run root. Inspect and preserve evidence before
  choosing recovery; no automatic orphan deletion is shipped.
- Public fixture holdouts are not sealed evaluation, train-diagnostic passing
  means mechanical accounting, and no musical/generalization quality follows.
  Failed evidence can be finalized as research; it cannot become a passing release.
- Arbitrium A1–A3, Runtime R1/A17–A20, GPU/distributed work, UI/MCP and deployment
  are outside this Core PR. Original specialization research stays in Arbitrium.

The broader reviewed requirements in `acceptance-and-migration.md` remain the
roadmap for those profiles. This initial offline acceptance does not mark every
future qualification obligation complete.
