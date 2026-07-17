# Contributing

## Lifecycle

```text
research → design → realize → test/verify → observe → maintain/refine
```

Every stage produces an artifact and ends at a quality gate.

| Stage | Required artifact | Gate |
|---|---|---|
| Research | question, sources, synthesis | design implications are explicit |
| Design | contract, alternatives, decision | observable boundaries are testable |
| Realize | implementation and adapter | builds and local checks pass |
| Verify | evidence bundle | claims match evidence scope |
| Observe | results and failures | empirical method is documented |
| Maintain | refinement or process proposal | governing intent is preserved |

## Change workflow

1. State the observable outcome.
2. Identify the governing specification and affected claims.
3. Create or update an ExecPlan for cross-cutting work.
4. Implement the smallest vertical slice.
5. Attempt to falsify the result, not merely confirm it.
6. Record evidence, assumptions, and exclusions.
7. Run repository checks.
8. Update the backlog and design docs when the work reveals a bottleneck.

## Governance

Agents may change implementations, tests, plans, and nonconstitutional design documents. Changes to the constitution or project intent require explicit human review.
