# Backlog

## Now

1. Complete ExecPlan 0001.
2. Define strict linked schemas for Specification, Realization, Claim, Evidence, RealizationProfile, and ConsumerPolicy.
3. Add positive and falsifying schema/reference fixtures and wire them into the G1 record gate.
4. Select one bounded proof-checking integration for the Stack law.
5. Add a minimal reproducible development environment for the documented Python and schema-validation gates.

## Next

- Extend `scripts/check_repo.py` with schema validation, linked-fixture checks, and negative cases as those artifacts land.
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
