# Architecture

## Core proposition

A conventional package distributes an implementation and a shallow interface. This project separates five concerns:

```mermaid
flowchart LR
    S[Specification] --> R[Realization]
    S --> C[Claims]
    R --> C
    E[Evidence] -->|supports / challenges| C
    P[Realization profile] --> C
    U[Consumer policy] --> X[Resolver]
    S --> X
    R --> X
    C --> X
    E --> X
    P --> X
```

## Core entities

### Specification

Defines vocabulary and observable meaning:

- types or carriers;
- operations and observations;
- laws and invariants;
- state transitions and protocols;
- required, permitted, optional, and forbidden effects;
- user-defined resource obligations;
- optional performance and empirical propositions.

It must avoid unnecessary commitments to layout, algorithms, ownership mechanisms, runtimes, or languages.

### Realization

A concrete implementation of a specification. It records:

- implementation language and version;
- target platform and runtime;
- ABI/component/interface mechanism;
- build and execution instructions;
- declared capabilities and limitations.

### Claim

A separately addressable, scoped proposition about a specification or realization,
including assumptions, exclusions, concern, and applicable profiles. Its assurance is
derived from evidence rather than declared on the claim.

### Evidence

An artifact supporting a claim:

- proof;
- conformance test result;
- property/model/differential test result;
- fuzzing campaign;
- benchmark;
- audit;
- assertion.

Evidence mechanisms are not interchangeable and must remain visible.
Evidence may support, challenge, or fail to decide a claim; contradictory evidence is
retained.

### Realization profile

The execution envelope: platform, host capabilities, scale, latency, memory, concurrency, trust, and portability constraints.

Profiles scope claims and evidence and provide a vocabulary for matching realization
capabilities to a consumer's requested environment. A profile is not evidence by
itself.

### Consumer policy

The subscriber's required and preferred semantic concerns, evidence levels, effects, resources, performance, and interoperability costs.

## Two compatibility relations

### Semantic compatibility

Whether a realization satisfies the required observable contract, possibly by refinement rather than exact equality.

This relation is evaluated under an explicit specification version, policy, profile,
claim set, and evidence set.

### Realization compatibility

Whether selected realizations can be combined efficiently and safely: same ecosystem, compatible ABI, shared runtime, FFI, Wasm component boundary, or process/message boundary.

This relation is directional and deployment-context dependent.

These relations must never be conflated.

## Trust boundary

The first trusted computing base should be small:

- parser and schema validator;
- claim/evidence graph checker;
- selected proof assistant kernel when proofs are used;
- conformance runner;
- registry provenance mechanism.

The web UI and implementation code are not inherently trusted.

## Sources and projections

Versioned specifications, realizations, claims, evidence, profiles, and policies are
the canonical records. Registry indexes, compatibility views, browser pages, badges,
and summaries are derived projections. Where a projection can be generated or
checked from canonical records, it must not become a second hand-maintained source of
truth.

This keeps a visible result reproducible and prevents the browser from claiming more
than the underlying graph and policy evaluation justify.
