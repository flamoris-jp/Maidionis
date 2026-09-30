# Maidionis

**A small trainable AI foundation that becomes specialized intelligence through education.**

> Maidionis begins with no role. Training gives it one. Runtime gives it a place in the whole.

Maidionis is a FLAMORIS project for building **small specialized intelligences** from a common trainable foundation.

It is not intended to be one universal model. A Maidionis specialization learns one bounded role, exposes a stable inference contract, and can be composed with other specializations by the FLAMORIS AI Runtime.

## 🧭 Repository identity / このRepositoryは何者？

### What it is / 何者か

Maidionis is a specialization-neutral foundation for training, evaluating, and packaging small task-specific AI models with bounded inference contracts.

The base has no fixed domain role. Education and specialization define what a resulting model can do.

### What it owns / 主な責任範囲

The intended Core boundary includes reusable, specialization-neutral contracts and implementation for:

- model architecture
- training and inference
- bounded state/context input
- dataset and manifest contracts
- education orchestration
- checkpointing and reproducibility
- artifact serialization
- evaluation and calibration
- specialization identity and versioning
- a stable Runtime-facing model interface

### What it does not own / 持たない責任

Maidionis does **not** own:

- Workflow execution
- tool or action execution
- authorization
- host or service lifecycle
- retry/fallback orchestration
- global shared-state ownership
- product/application state
- GPU/runtime lifecycle policy

Those responsibilities belong to the surrounding Runtime, applications, and other FLAMORIS services.

### Current status / 現在の状態

**Bootstrap / architecture design.**

The repository is being established from controlled Arbitrium research. The reusable Core boundary, specialization interface, migration map, and Runtime adapter contract are being defined in [Issue #1](https://github.com/flamoris-jp/Maidionis/issues/1).

No production-ready Maidionis model, stable artifact format, or Runtime integration is claimed yet.

The existing research has demonstrated that a small native training path can learn tightly bounded lessons. It has **not** demonstrated sufficient held-out generalization, reliable abstention, or production quality. Those limitations remain part of the migration evidence rather than being hidden by the rename.

### Where it fits / FLAMORISのどこに属する？

Maidionis provides specialized model intelligence.

```text
Maidionis specialization
        ↓ bounded inference
FLAMORIS AI Runtime
        ↓ workflow / jobs / shared execution state
Application / Studio / creative pipeline
```

The intended separation is:

```text
Maidionis = specialized intelligence
Runtime   = execution / orchestration
Workflow  = composition strategy
State     = shared execution context
```

See the [FLAMORIS AI ecosystem](https://github.com/flamoris-jp/flamoris-ai/blob/main/docs/ai-ecosystem.md) and [FLAMORIS AI Runtime](https://github.com/flamoris-jp/flamoris-ai-runtime).

## Specializations

The first specialization is **Decision / Arbitrium**.

Its existing research task interprets bounded English evidence and returns a bounded advisory judgment such as `retry`, `fallback`, or `stop`, with answerability/abstention handled separately.

Decision-specific semantics remain outside Maidionis Core.

Conceptually:

```text
Maidionis Core
    │
    ├─ education → Decision specialization
    ├─ education → Drum specialization
    ├─ education → Bass specialization
    ├─ education → Melody specialization
    ├─ education → Critic specialization
    └─ education → other bounded specializations
```

A **Drum** specialization is a candidate for the first creative proof after the Core/Decision split is established.

## Research origin and provenance

Maidionis begins from the current Arbitrium research, but this repository is **not** a mechanical rename or a clean-slate rewrite.

Maidionis owns the reusable mechanisms needed to make specialization research reproducible: dataset/manifest contracts, training/evaluation infrastructure, checkpointing, calibration, artifact contracts, and provenance hooks.

**Specialization-specific curricula, experiment reports, measured results, failure analysis, and research history belong with the specialization repository.** For the first Decision specialization, those materials belong in Arbitrium rather than Maidionis.

Historical Arbitrium research must remain traceable during migration, but Maidionis does not need to duplicate its experiment results.

## Implementation boundary

The Arbitrium research prototype currently uses:

- **C++20 / CMake / LibTorch** for model architecture, native training, calibration, and inference
- **Python** for curriculum/dataset generation, research orchestration, evaluation support, and analysis

Maidionis starts from that evidence, but the final C++ / Python responsibility split is part of the design work. Do not treat the current split as a frozen public API.

## Design principles

- Keep Core specialization-neutral.
- Keep Decision semantics in the Decision specialization.
- Prefer bounded inputs and bounded outputs.
- Keep execution authority outside the model.
- Preserve reproducibility and research provenance.
- Separate memorization diagnostics from held-out generalization.
- Treat evaluation and calibration as first-class architecture.
- Do not report research diagnostics as release quality.
- Prefer explicit boundaries over speculative abstractions.

## Getting started

There is no supported build or run command yet because implementation migration has not started in this repository.

Start with [Issue #1: Design Maidionis Core and migrate Arbitrium as the first specialization](https://github.com/flamoris-jp/Maidionis/issues/1).

Repository-specific build, test, and experiment commands will be documented only after they exist and are verified against the current implementation.

## FLAMORIS

FLAMORIS is open-source software for creative work and AI-native production.

Use it however you like.

Commercial use is welcome and does not require permission. If you'd like, we'd be happy to hear what you used FLAMORIS for. This is completely optional.

FLAMORIS software is provided as-is. We do not provide individual support or guaranteed assistance.

If you run into trouble, let your AI assistant read the repository, documentation, Issues, tests, logs, and source code and help you solve it.

If FLAMORIS helps you or you find it interesting, your support helps fund development and keeps the project growing. 🌱

<sub>Mostly GPU bills.</sub>

---

## FLAMORISについて

FLAMORISは、クリエイティブ制作とAIネイティブな制作環境のためのオープンソースソフトウェアです。

勝手に使ってください。改造しても、組み込んでも、面白いものや変なものを作ってもOKです。

商用作品や製品で使う場合も許可は不要です。もしよければ「こんなのに使ったよ」と教えてもらえるとうれしいです。もちろん強制ではありません。

FLAMORISのソフトウェアは現状のまま提供されます。個別サポートや動作保証はありません。

困ったときは、README、ドキュメント、Issue、テスト、ログ、ソースコードをあなたのAIに読ませて、自己サポートしてもらってください。

もしお役に立てたり、面白いと思っていただけたなら、開発費用をご支援いただけるとうれしいです。FLAMORISは元気になって育ちます。🌱

<sub>主にGPU代とか。</sub>

## License

Code in this repository is licensed under the [Apache License 2.0](LICENSE), unless otherwise noted.

AI models, model weights, datasets, media, and other non-code assets may use separate licenses. Their applicable licenses must be stated alongside those assets.
