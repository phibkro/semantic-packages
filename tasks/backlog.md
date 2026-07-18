# Backlog

## Now

1. Complete ExecPlan 0001.
2. Implement the bounded specification loader and reference model for the tracer bullet.
3. Normalize loader input paths before duplicate and identity handling.
4. Define and falsify specification self-import and cyclic-import behavior.
5. Select one bounded proof-checking integration for the Stack law.
6. Add a minimal reproducible development environment for the documented Python and schema-validation gates.

## Next

- Promote fallback schema diagnostics into exact actionable oracles when a new
  counterexample demonstrates that the coarse diagnostic is insufficient.
- Define how adapter correctness is claimed and evidenced.
- Add generated indexes or richer orientation tooling only when multiple plans or derived views create measurable drift.
- Add effect classification and erasure/noninterference tests.
- Add a user-defined resource algebra.
- Add performance claims relative to an execution profile.
- Replace Stack with OrderedMap as the first nontrivial semantic package.
- Model spec refinement and version compatibility.
- Integrate one proof assistant without making it the universal foundation.

## Resolved during design audit

- Use JSON as the temporary canonical interchange format for the tracer bullet; keep
  the human-facing `.pspec` syntax provisional
  ([ADR 0003](../docs/decisions/0003-temporary-json-interchange.md)).
- Use exact typed record/reference addresses and flat stable local declaration IDs for
  the tracer bullet
  ([ADR 0005](../docs/decisions/0005-exact-typed-references.md)).
- Define Stack empty behavior, finite extensional observation, adapter/effect boundary,
  persistence witness, and the initial conformance/performance profile in
  [the specification-language design](../docs/design/spec-language.md).
- Separate concern priority from semantic prohibition and conservatively retain
  conflicting, inapplicable, missing, error, and assertion-only outcomes
  ([ADR 0006](../docs/decisions/0006-separate-priority-from-prohibition.md)).

## Research

- Institution-based composition and satisfaction across heterogeneous logics.
- Coalgebraic behavioral refinement and finite conformance testing.
- Evidence lattices and provenance.
- Resource algebras, QTT, ownership, and separation concerns.
- Cross-language realization compatibility through Wasm components.
