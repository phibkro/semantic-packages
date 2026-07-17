# Package Specification Language

A research and engineering project for making **semantic specifications**—rather than executable third-party implementations—the primary unit of software reuse and distribution.

The project explores a shared specification language that:

- describes observable domain semantics independently of representation and execution;
- supports algebraic laws, coalgebraic behavior, effects, resources, protocols, and performance claims;
- can be checked by proof assistants and conformance tooling;
- can be realized by competing implementations in general-purpose programming languages;
- records proofs, tests, benchmarks, assumptions, and provenance as first-class evidence;
- resolves both semantic compatibility and practical implementation interoperability.

## Current phase

**Design → tracer-bullet realization.**

The first milestone is deliberately narrow: publish one nontrivial specification, connect it to evidence, register two realizations, and determine how those realizations may interoperate.

## Repository map

- [`AGENTS.md`](AGENTS.md): durable instructions and map for coding agents.
- [`ARCHITECTURE.md`](ARCHITECTURE.md): system boundaries and core entities.
- [`docs/vision/constitution.md`](docs/vision/constitution.md): stable intent and non-negotiable principles.
- [`docs/research/synthesis.md`](docs/research/synthesis.md): condensed research developed before implementation.
- [`docs/design/core-model.md`](docs/design/core-model.md): specification, realization, evidence, profile, and policy model.
- [`docs/design/spec-language.md`](docs/design/spec-language.md): minimum viable specification calculus.
- [`docs/design/evidence-model.md`](docs/design/evidence-model.md): claim, evidence, result, and assurance boundaries.
- [`docs/design/compatibility.md`](docs/design/compatibility.md): semantic and realization resolution.
- [`docs/design/lifecycle.md`](docs/design/lifecycle.md): project knowledge, feedback loops, and quality gates.
- [`docs/operations/multi-provider-workflow.md`](docs/operations/multi-provider-workflow.md): agent route status, model-diverse delegation, security boundaries, and provenance.
- [`docs/design/tracer-bullet.md`](docs/design/tracer-bullet.md): first vertical slice.
- [`docs/exec-plans/active/0001-tracer-bullet.md`](docs/exec-plans/active/0001-tracer-bullet.md): active implementation plan.
- [`tasks/backlog.md`](tasks/backlog.md): ordered research and engineering backlog.

## Local use

Run the repository quality gate:

```sh
python3 scripts/check_repo.py
```

Then open the repository in Codex, an IDE extension, or another coding agent. The agent should begin with `AGENTS.md`, then follow the active ExecPlan.

## Status

This repository is a design substrate, not yet a stable standard or implementation.
