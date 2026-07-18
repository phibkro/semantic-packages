# ADR 0010: Wave 4 cross-language conformance boundary

## Status

Accepted experimentally for ExecPlan 0001 only, with retained dissent on the Rust
JSON/toolchain route.

## Context

Wave 3 proved that one opaque child-process adapter can be checked without making its
representation normative. Wave 4 must apply the same Stack semantics to independent
Rust and TypeScript Realizations and retain useful counterexamples and provenance.

The current Python runner is language-neutral at the child boundary, but its fixed
plan is not the profile-sized property campaign implied by its arguments. Five input
values cap its depth at five; `max_history` is another depth cap rather than a mixed
history bound; and observing depth eight requires at least nine `pop` observations.
Its one aggregate result also combines law, persistence, effect, and execution causes,
while every canonical Claim pins one Specification declaration.

Local preflight found dependency-free Deno 2.9.2 with TypeScript 6.0.3. Exact `rustc`
and a GCC linker are available offline, but Cargo and vendored crate sources are not.
Acquiring Cargo plus locked `serde_json` would add a new environment and dependency
step. A std-only Rust adapter instead owns more JSON parsing code.

## Decision

Retain `stack-runner-json-v1` and the Python runner as the tracer's shared semantic
oracle. Before either new Realization counts as evidence, introduce one immutable,
harness-owned deterministic conformance plan that separates the element domain from
histories and pins:

- Stack Specification and profile addresses plus input digests;
- integer domain `-2` through `2`;
- maximum depth 8, maximum history 32, and observation limit at least 9;
- curated empty, `pop-push`, order, repeated-value depth-boundary, retained-source
  push/pop, and effect cases;
- deterministic generated mixed histories with an explicit algorithm version and seed;
- timeout, event contract, case IDs, and a digestible result artifact.

Plans use logical state bindings and expected top-first sequences owned by the harness,
never adapter handles or implementation representations. The report retains an overall
execution/semantic result and declaration-level observations for `pop-empty`,
`pop-push`, `persistence`, and `stack-effects`. Execution errors remain distinct from
semantic challenges and never become evidence against a law.

Build and discovery stay outside the semantic runner. Each package is built with an
explicit shell-free argument vector; the resulting child argument vector is passed to
the runner. Canonical Realization `entrypoint` metadata remains descriptive and never
becomes registry-driven command execution.

Implement TypeScript with Deno's dependency-free offline typecheck/run boundary. Do
not add Node, npm, Bun, or a package manifest without a demonstrated need.

Implement Rust experimentally with direct edition-2024 `rustc`, the observed GCC
linker, and a std-only adapter codec. The codec must accept the harness's valid request
shapes independent of JSON member order and insignificant whitespace, preserve string
and integer meaning used by the protocol, and receive its own red-first controls. This
does not select a general Rust JSON library or claim support for malformed client
requests, which remain outside protocol v1.

Realization code and adapter code remain separate within each package. Candidate
authors may share the protocol document but never the runner's transition model,
expected traces, or another Realization's implementation. Rust and TypeScript use
different representation strategies.

Canonical Evidence is declaration-scoped. One reviewed run artifact may be referenced
by multiple Evidence records, but each record pins its own exact Claim, Realization,
adapter, profile, plan/runner/artifact digests, assumptions, exclusions, and result.
Do not use one aggregate report as a whole-Specification Claim. Broken candidates stay
fixture-only unless a real published failure requires immutable challenging Evidence.

## Retained dissent and alternatives

- The preferred production Rust route is Cargo with a locked, vendored JSON library.
  It was not selected because Cargo and vendor sources are absent and the tracer needs
  only valid bounded request shapes. This dissent is accepted, not falsified.
- Blocking all Rust work until dependency provisioning was rejected as unnecessary for
  this reversible tracer experiment.
- A fixed-field or delimiter-splitting Rust parser was rejected because JSON member
  order and insignificant whitespace have no protocol meaning.
- Reimplementing the semantic oracle in Rust and TypeScript was rejected because it
  would duplicate meaning and invite correlated drift rather than establish
  independence.
- One aggregate conformance Claim was rejected because current Claim identity pins one
  declaration and cannot honestly carry unrelated persistence/effect challenges.

## Consequences

- Wave 4 first hardens the campaign/report boundary, then freezes candidate/build
  controls, then implements Rust and TypeScript in parallel.
- Property-test Evidence is permitted only when generated histories, seeds, bounds,
  cases, and artifacts are retained. Otherwise the mechanism is reported honestly as
  conformance-test and may remain unsupported by policy.
- Existing runner lifecycle tests remain runner self-tests; they are not multiplied
  into 18 independent semantic tests per language.
- Adapter faithfulness and event completeness remain assumptions. External effects,
  realization-step performance, concurrency, remote transport, ABI/interoperation,
  browser, resolver, and registry execution remain exclusions.

## Revisit conditions

Revisit before accepting arbitrary client JSON, adding another Rust package, exposing
the codec as reusable infrastructure, requiring nontrivial Unicode/number domains,
introducing Cargo dependencies, changing the child protocol, creating an aggregate
conformance proposition, or claiming cross-language interoperability.
