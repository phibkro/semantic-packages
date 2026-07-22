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

**Two-domain local tracer accepted → human inspection and differentiated profiles.**

The accepted Stack tracer publishes one nontrivial specification, binds proof and
conformance Evidence, registers two independent Realizations, resolves them under an
explicit policy/profile, projects theory meaning, and retains a failed exact successor
with predecessor recovery. An exact inspection command is ready, while its
uninvolved-human observation is retained as deferred backlog work. OrderedMap now
traverses the same bounded lifecycle with a different semantic shape: independent
Realizations, policy-relative resolution, a separate directional boundary, and an
append-only zero-candidate successor with exact predecessor recovery. This establishes
only Stack-plus-finite-OrderedMap generality and does not claim that the deferred human
observation or arbitrary-domain generality passed.

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
- [`docs/exec-plans/active/0003-cold-human-inspection.md`](docs/exec-plans/active/0003-cold-human-inspection.md): executable inspection surface and deferred uninvolved-human gate.
- [`docs/exec-plans/active/0004-ordered-map-generality.md`](docs/exec-plans/active/0004-ordered-map-generality.md): final convergence and closeout for the accepted second-domain route.
- [`docs/exec-plans/completed/0001-tracer-bullet.md`](docs/exec-plans/completed/0001-tracer-bullet.md): completed design, record, proof, adapter, independent-Realization, and Evidence history.
- [`docs/exec-plans/completed/0002-actor-journeys.md`](docs/exec-plans/completed/0002-actor-journeys.md): completed actor registry, resolver, projection, maintenance, release, and workflow-governance history.
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

The gate includes record/link fixtures, 18 loader groups, 50 adapter/campaign tests,
59 cross-language candidate/Evidence-binding controls, 204 actor journeys, 16 research
probes, 20 governance tests, two fresh Stack reports/eight records, two fresh OrderedMap
reports plus one selective breaker, the exact 2/14/14 OrderedMap candidate census, and
the 49-group proof boundary. Check the accepted proof Evidence directly with:

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

Inspect the exact predecessor and failed-successor Stack snapshots without executing
artifacts or selecting an implicit latest version:

```sh
python3 -m semantic_packages.inspection \
  --predecessor-manifest registry/stack/manifest.json \
  --successor-manifest registry/stack/successor-manifest.json \
  --profile realizationProfile/stack-default/0.1.0 \
  --predecessor-specification specification/stack/0.1.0 \
  --successor-specification specification/stack/0.2.0 \
  --predecessor-policy consumerPolicy/stack-bounded-policy/0.1.0 \
  --successor-policy consumerPolicy/stack-bounded-policy/0.2.0
```

The output keeps authored meaning, Claim and Evidence qualifications, semantic
acceptability, directional deployment boundaries, and exact-version recovery separate.
It is a read-only renderer over the two named local graph snapshots; it does not run
proofs or Realizations, acquire records, reproduce Evidence, or choose a recovery
candidate. The retained uninvolved-human protocol is documented in
[`docs/operations/cold-human-inspection.md`](docs/operations/cold-human-inspection.md).

Then open the repository in Codex, an IDE extension, or another coding agent. The agent should begin with `AGENTS.md`, then follow the active ExecPlan.

## Status

This repository is an executable research prototype with complete bounded local Stack
and finite OrderedMap lifecycles. It is not yet a stable standard, an arbitrary-domain
semantic-package ecosystem, or a hosted production registry.
