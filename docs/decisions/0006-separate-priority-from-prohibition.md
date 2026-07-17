# ADR 0006: Separate concern priority from semantic prohibition

## Status

Accepted for ExecPlan 0001.

## Context

The provisional policy list placed `forbidden` beside `required`, `preferred`,
`optional`, and `ignored`. That conflates how much a concern affects selection with
the polarity of the semantic proposition. It also makes evidence ambiguous: evidence
supporting absence should not be treated like evidence supporting occurrence.

## Decision

Use `required`, `preferred`, `optional`, and `ignored` as concern priorities. Represent
a prohibition as a required negative semantic obligation, such as absence of matching
`io.*` events. Evidence mechanisms, freshness, and minimum assurance remain separate
policy dimensions.

A required concern with selected challenging evidence is contested and does not pass.
A prohibition with missing, inapplicable, inconclusive, or erroneous evidence is not
proved; it remains unmet or unknown. Boundary-scoped absence evidence may satisfy it
only when the consumer policy explicitly accepts that evidence scope and mechanism.

## Alternatives and dissent

- Treating `forbidden` as a fifth priority makes the meaning of `supports` reverse
  implicitly and can cause a consumer forbidding I/O to accept evidence that I/O
  occurred.
- Treating unknown absence as success silently weakens a prohibition.
- Requiring evidence of global absence would exceed the tracer bullet's declared
  adapter-observed effect boundary.

The conservative default is fail-closed for required and negative obligations. A
future consumer policy may select supersession or acceptable scoped evidence
explicitly, but contradictory evidence is never erased.

## Consequences

- Resolver outcomes preserve concern priority, proposition polarity, evidence result,
  and assurance as separate axes.
- The effect contract can express forbidden events without inventing an inverse
  evidence-result vocabulary.
- Unknowns remain visible and do not satisfy protected requirements accidentally.

## Revisit conditions

Revisit if real consumer policies require a richer preference algebra or an explicit
conflict-resolution strategy. Do not reintroduce prohibition as an evidence rank.
