# AGENTS.md

This repository is part of the FLAMORIS ecosystem.

Maidionis is a specialization-neutral trainable AI foundation. AI agents and human contributors must preserve the distinction between **Maidionis Core**, **specialization-specific intelligence**, and **Runtime execution authority**.

Before substantial changes, read README.md and Issue #1, inspect the current implementation, and inspect the relevant source research when migration work is involved.

## Maidionis-specific boundaries

- Keep Maidionis Core free of Decision-, music-, image-, motion-, or other domain-specific semantics unless the contract is intentionally specialization-extensible.
- The first specialization is Decision / Arbitrium. Do not mechanically rename Arbitrium code into Core.
- Preserve research provenance, including failed experiments and limitations, not only successful metrics.
- Do not describe memorization diagnostics as held-out generalization.
- Maidionis may return bounded model outputs; it does not gain authority to execute tools, actions, retries, workflows, host changes, or product mutations.
- FLAMORIS AI Runtime owns execution/orchestration concerns such as Workflow execution, Jobs, scheduling, shared execution state, retry/fallback, and output routing.
- Repository-specific build/test commands must come from the current implementation. Do not copy commands from Arbitrium or another FLAMORIS repository until the corresponding code has actually migrated.

## Core principles

1. **Current implementation is authoritative**
   - Read the repository documentation, configuration, tests, and relevant source before changing behavior.
   - Do not invent repository-specific commands, paths, services, or configuration.

2. **Keep responsibility clear**
   - Keep this repository focused on its documented purpose.
   - Preserve application, Runtime, model, and service ownership boundaries.
   - Do not create a second source of truth for state owned elsewhere.

3. **Reuse deliberately**
   - Check existing FLAMORIS shared packages and repositories before duplicating common infrastructure.
   - Reuse code only when the dependency direction and ownership boundary remain clear.
   - Avoid speculative abstractions for requirements that do not yet exist.

4. **Security and privacy are architectural requirements**
   - Never commit or log secrets, credentials, tokens, private keys, or sensitive user data.
   - Prefer least-privilege access and bounded resource use.
   - Treat external input and remote responses as untrusted.

5. **Stable behavior over cleverness**
   - Prefer explicit, testable contracts and straightforward implementations.
   - Preserve existing public behavior unless a change intentionally modifies it.
   - Document externally visible behavior and compatibility impact.

6. **Documentation must track reality**
   - Mark current implementation/status explicitly.
   - Do not describe implemented behavior as merely planned, and do not describe planned behavior as already shipped.
   - Keep public architecture portable. Machine names, private topology, credentials, and deployment-only paths belong in private deployment documentation rather than public repository defaults.

7. **Research evidence must stay honest**
   - Keep dataset identity, seeds, hashes, metrics, evaluation splits, and known failures traceable when moving research into public implementation.
   - A working training pipeline is not evidence of a useful production model.
   - Do not silently change the meaning of historical results during migration.

8. **AI-native, human-authoritative**
   - AI-assisted development is welcome.
   - Humans remain responsible for reviewing behavior, security, licensing, scientific claims, and compatibility.

## Before implementing a substantial change

- read this file and README.md;
- read Issue #1 and any issue governing the current phase;
- identify what belongs to Core, a specialization, Runtime, or external research provenance;
- read the [organization map](https://github.com/flamoris-jp/.github) and [FLAMORIS AI ecosystem](https://github.com/flamoris-jp/flamoris-ai/blob/main/docs/ai-ecosystem.md) when cross-repository context matters;
- inspect current implementation and tests;
- inspect source research before migration;
- identify the source of truth and dependency direction;
- check whether reusable FLAMORIS infrastructure already exists;
- verify repository-specific setup details instead of guessing.

## Testing

Add or update tests where practical.

Prefer deterministic tests and explicit contracts. For education and evaluation work, preserve split boundaries and reproducibility evidence. When behavior differs by platform, runtime, model architecture, or environment, document and test the supported boundary.

## Licensing

Unless stated otherwise, code in this repository is licensed under Apache License 2.0.

Do not add third-party code, models, model weights, datasets, fonts, media, or generated assets unless their licenses are compatible and clearly documented.

## Support

FLAMORIS does not provide guaranteed individual support.

Use the repository documentation, Issues, tests, logs, source code, and preserved research evidence as primary references when diagnosing problems.
