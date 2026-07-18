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
- [`docs/design/system-map.md`](docs/design/system-map.md): end-to-end data plane, decision plane, control plane, tracer layers, trust boundaries, and lifecycles.
- [`docs/design/user-journeys.md`](docs/design/user-journeys.md): acceptance contracts being made executable for theory authors, package authors, theory consumers, and package consumers.
- [`docs/design/spec-language.md`](docs/design/spec-language.md): minimum viable specification calculus.
- [`docs/design/adapter-protocol.md`](docs/design/adapter-protocol.md): tracer-scoped executable Stack adapter boundary.
- [`docs/design/evidence-model.md`](docs/design/evidence-model.md): claim, evidence, result, and assurance boundaries.
- [`docs/design/compatibility.md`](docs/design/compatibility.md): semantic and realization resolution.
- [`docs/design/lifecycle.md`](docs/design/lifecycle.md): project knowledge, feedback loops, and quality gates.
- [`docs/operations/multi-provider-workflow.md`](docs/operations/multi-provider-workflow.md): agent route status, model-diverse delegation, security boundaries, and provenance.
- [`docs/design/tracer-bullet.md`](docs/design/tracer-bullet.md): first vertical slice.
- [`docs/exec-plans/active/0001-tracer-bullet.md`](docs/exec-plans/active/0001-tracer-bullet.md): active implementation plan.
- [`docs/exec-plans/active/0002-actor-journeys.md`](docs/exec-plans/active/0002-actor-journeys.md): actor-complete registry, resolver, projection, and maintenance plan.
- [`tasks/backlog.md`](tasks/backlog.md): ordered research and engineering backlog.

## Local use

Run the repository quality gate:

```sh
python3 -m pip install -r requirements-dev.txt
# Lean must resolve to 4.30.0, commit d024af099ca4bf2c86f649261ebf59565dc8c622.
# Set LEAN=/path/to/lean when that binary is not on PATH.
# Rust, a C linker, and Deno must resolve through RUSTC/CC/DENO or PATH.
python3 scripts/check_repo.py
```

The gate includes record/link fixtures, 18 loader groups, 36 shared adapter/campaign
tests, 18 cross-language candidate/Evidence-binding controls, two freshly reproduced Wave 4 reports,
eight bound realization Evidence records, and the 49-group proof boundary. Check the
accepted proof Evidence directly with:

```sh
python3 scripts/proof_check.py \
  --manifest proofs/stack-pop-empty/manifest.json \
  --evidence fixtures/records/valid/stack-pop-empty-model-proof-evidence.json \
  --lean "${LEAN:-lean}"
```

This supports only model satisfaction and operation of the proof-evidence pipeline
for Stack `pop-empty`. It does not establish Realization or adapter conformance, the
whole Specification, or general authority for Lean.

Validate one local canonical-record source set directly:

```sh
python3 scripts/record_check.py path/to/record.json path/to/registry-directory
```

Directories are searched recursively for lowercase `.json` regular files. Repeated
lexical aliases and file/directory overlap are idempotent; symbolic links and explicit
non-JSON files are rejected. Imports are exact edges within the supplied source set and
never acquire files from elsewhere. The source tree must remain quiescent during one
load; this tracer loader is not a secure traversal boundary for concurrently mutated or
adversarial filesystems.

Run the tracer-scoped Stack conformance suite, including the executable reference
Realization and child adapter:

```sh
python3 -m unittest discover -s tests/adapter -v
python3 -m semantic_packages.stack_adapter < /dev/null
```

The adapter uses `stack-runner-json-v1` for this tracer only. Passing the bounded suite
retains adapter-faithfulness and event-completeness assumptions and does not produce
performance evidence.

Rust and TypeScript independently realize the same bounded contract using different
private representations. With `RUSTC`, `CC`, and `DENO` selecting the reviewed tools,
run their offline build/protocol checks, negative controls, and exact campaign with:

```sh
python3 -m unittest tests.candidates.test_cross_language_candidates -v
```

The same 18 controls can be run alone with that command. Their reviewed outcomes are
recorded as declaration-scoped Evidence; the green report itself is only a provenance
artifact, and the repository gate reproduces and binds it before accepting the records.

Then open the repository in Codex, an IDE extension, or another coding agent. The agent should begin with `AGENTS.md`, then follow the active ExecPlan.

## Status

This repository is a design substrate, not yet a stable standard or implementation.
