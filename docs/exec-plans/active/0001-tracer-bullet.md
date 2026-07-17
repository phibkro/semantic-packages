# ExecPlan 0001: End-to-end tracer bullet

## Purpose and observable outcome

Produce a local prototype where a user can load the example Stack specification, see its claims and two registered realizations, run conformance checks, and receive an explainable compatibility result.

## Context

Read `AGENTS.md`, `ARCHITECTURE.md`, `docs/design/core-model.md`, `docs/design/spec-language.md`, and `docs/design/tracer-bullet.md` first.

## Non-goals

- final language syntax;
- production authentication or hosting;
- automatic proof synthesis;
- general package resolver;
- performance optimization.

## Proposed implementation order

1. Define JSON Schema records for specification, realization, claim, and evidence.
2. Encode `specs/stack.pspec` or a temporary JSON equivalent.
3. Implement a parser/loader with stable IDs and diagnostics.
4. Implement one in-process reference model for conformance tests.
5. Add Rust and TypeScript realizations plus adapters.
6. Add property/model tests reusable across both realizations.
7. Persist the semantic and realization graphs locally.
8. Expose a minimal CLI or web browser for inspection.
9. Implement an explainable compatibility query.
10. Record discoveries and revise the core model.

## Quality gates

- Both realizations satisfy the same reusable conformance suite.
- A deliberately broken realization is rejected with a useful counterexample.
- The browser distinguishes proof/test/assertion evidence.
- Compatibility output distinguishes semantic substitutability from boundary mechanism.
- The repository can be cloned and checked with documented commands.

## Progress

- [x] Repository knowledge scaffold
- [ ] Core JSON schemas
- [ ] Spec loader
- [ ] Reference model
- [ ] Rust realization
- [ ] TypeScript realization
- [ ] Shared conformance suite
- [ ] Evidence records
- [ ] Browser/CLI
- [ ] Compatibility explanation
- [ ] Retrospective and next ExecPlan

## Discoveries

Record implementation discoveries here as they occur.

## Decision log

- Start with Stack to validate the pipeline; move to OrderedMap only after the loop closes.
- Keep the storage format replaceable and the surface syntax provisional.

## Result

Not yet implemented.
