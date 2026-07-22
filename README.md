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

**Finite authored resource composition experienceable; satisfaction unestablished.**

The accepted Stack tracer publishes one nontrivial specification, binds proof and
conformance Evidence, registers two independent Realizations, resolves them under an
explicit policy/profile, projects theory meaning, and retains a failed exact successor
with predecessor recovery. An exact inspection command is ready, while its
uninvolved-human observation is retained as deferred backlog work. OrderedMap now
traverses the same bounded lifecycle with a different semantic shape: independent
Realizations, policy-relative resolution, a separate directional boundary, and an
append-only zero-candidate successor with exact predecessor recovery. This establishes
only Stack-plus-finite-OrderedMap generality and does not claim that the deferred human
observation or arbitrary-domain generality passed. Its exact-profile successor now
selects Rust for a native-process envelope and TypeScript for a Deno-sandbox envelope
from one append-only graph, retaining every nonmatching Claim and Evidence record as
inapplicable rather than transferring assurance.
The shared authoring boundary now supports both its strict canonical-JSON conformance
control and an explicit human-editable PSpec surface. The candidate command authors the
exact Stack and OrderedMap Specification documents, validates explicitly named finite
profile contexts, publishes output atomically, and returns deterministic source-local
diagnostics without hidden identity, defaults, acquisition, or hosted-text
interpretation. Automated journey controls pass; eligible uninvolved-author observation
and final independent acceptance remain open.
On top of that still-gated authoring PR, a theory maintainer can now inspect an explicit
proposal between exact Stack or OrderedMap Specification versions. The report preserves
authored declaration mappings and structural changes while fixing semantic refinement
at `unestablished`; it creates no compatibility decision, resolver edge, migration, or
Evidence transfer.
Above those exact runners, a package author or Evidence reviewer can now run one
Stack-plus-OrderedMap observation. Optional, forbidden, and unspecified reported events
retain their complete ledgers while the exact non-effect campaign projections remain
unchanged; adapter errors stay nonauthoritative. This is a deterministic observation of
the adapter-invocation boundary, not whole-process purity, arbitrary effect erasure,
semantic equivalence, accepted Evidence, or arbitrary-domain generality.
Above that observation, a theory author can now define one explicit finite resource
composition in PSpec, bind its elements to the exact Stack and OrderedMap persistence
declarations, and inspect closure, totality, unit, commutativity, associativity, and two
derived folds. The report keeps algebraic well-formedness separate from Realization
satisfaction, Claim/Evidence transfer, compatibility, refinement, resolver authority,
and arbitrary resource semantics.

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
- [`design-specs/0001-explicit-pspec-author-journey.md`](design-specs/0001-explicit-pspec-author-journey.md): observable contract and falsifiers for the complete PSpec author experience.
- [`design-specs/0002-explicit-refinement-inspection-journey.md`](design-specs/0002-explicit-refinement-inspection-journey.md): observable contract and falsifiers for exact proposal-local cross-version inspection.
- [`design-specs/0003-bounded-effect-separation-observation.md`](design-specs/0003-bounded-effect-separation-observation.md): observable contract and falsifiers for the exact two-domain effect-separation probe.
- [`design-specs/0004-finite-resource-composition-inspection.md`](design-specs/0004-finite-resource-composition-inspection.md): observable contract and falsifiers for the finite authored resource-composition journey.
- [`docs/exec-plans/active/0009-finite-resource-composition.md`](docs/exec-plans/active/0009-finite-resource-composition.md): active design-to-review lifecycle and retained concern dispositions for that journey.
- [`docs/exec-plans/completed/0008-bounded-effect-separation.md`](docs/exec-plans/completed/0008-bounded-effect-separation.md): completed red controls, independent reviews, implementation, maintenance, and convergence evidence for that probe.
- [`docs/exec-plans/completed/0007-explicit-refinement-inspection.md`](docs/exec-plans/completed/0007-explicit-refinement-inspection.md): completed refinement journey, independent review, and convergence evidence.
- [`docs/exec-plans/active/0003-cold-human-inspection.md`](docs/exec-plans/active/0003-cold-human-inspection.md): executable inspection surface and deferred uninvolved-human gate.
- [`docs/exec-plans/completed/0004-ordered-map-generality.md`](docs/exec-plans/completed/0004-ordered-map-generality.md): completed OrderedMap second-domain research, implementation, maintenance, and convergence history.
- [`docs/exec-plans/completed/0005-deployment-profile-choice.md`](docs/exec-plans/completed/0005-deployment-profile-choice.md): completed differentiated-profile research, Evidence, authority, actor, maintenance, and convergence history.
- [`docs/exec-plans/completed/0001-tracer-bullet.md`](docs/exec-plans/completed/0001-tracer-bullet.md): completed design, record, proof, adapter, independent-Realization, and Evidence history.
- [`docs/exec-plans/completed/0002-actor-journeys.md`](docs/exec-plans/completed/0002-actor-journeys.md): completed actor registry, resolver, projection, maintenance, release, and workflow-governance history.
- [`tasks/backlog.md`](tasks/backlog.md): ordered research and engineering backlog.

## Local use

### Author an exact semantic Specification

Author Stack from the human-editable PSpec source and its explicit profile dependency:

```sh
nix develop --command python3 -m semantic_packages author \
  specs/stack.pspec \
  --dependency registry/stack/theory/dependencies/stack-profile.json \
  --output /tmp/stack-spec.json
```

Expected output:

```text
authored specification stack@0.1.0 -> /tmp/stack-spec.json
```

The same command and surface author the structurally different OrderedMap domain:

```sh
nix develop --command python3 -m semantic_packages author \
  specs/ordered-map.pspec \
  --dependency registry/ordered-map/theory/dependencies/ordered-map-profile.json \
  --output /tmp/ordered-map-spec.json
```

Expected output:

```text
authored specification ordered-map@0.1.0 -> /tmp/ordered-map-spec.json
```

To experience an author-local failure without changing repository files, blank one law
in a disposable copy and run the same boundary:

```sh
sed '0,/statement = "pop(empty) == None"/s//statement = ""/' \
  specs/stack.pspec > /tmp/stack-broken.pspec
nix develop --command python3 -m semantic_packages author \
  /tmp/stack-broken.pspec \
  --dependency registry/stack/theory/dependencies/stack-profile.json \
  --output /tmp/stack-broken.json
```

The command exits `1`, leaves the requested output absent or unchanged, and reports:

```text
SCHEMA_NONEMPTY_STRING /tmp/stack-broken.pspec#/laws/0/statement: value must be a nonempty string
```

What is real underneath: PSpec TOML values enter the same all-or-none canonical schema
and graph boundary as the JSON control, relative only to the dependency files named on
the command line. Parsing does not prove hosted laws, create Evidence, publish records,
or discover profiles.

The exact privacy-bounded acceptance task for an eligible uninvolved author is in
[`docs/operations/explicit-pspec-author-observation.md`](docs/operations/explicit-pspec-author-observation.md).

### Inspect an explicit exact-version refinement proposal

Inspect Stack's exact effect-contract change:

```sh
nix develop --command python3 -m semantic_packages refinement inspect \
  refinements/stack-0.1.0-to-0.2.0.prefine \
  --predecessor registry/stack/theory/records/stack-spec.json \
  --successor registry/stack/successors/j5/theory/stack-spec.json \
  --output /tmp/stack-refinement.json
```

Expected summary:

```text
inspected refinement stack-0.1.0-to-0.2.0: 10 unchanged, 1 changed, 0 additions, 0 removals; semantic refinement unestablished -> /tmp/stack-refinement.json
```

Inspect OrderedMap's exact additive successor through the same surface:

```sh
nix develop --command python3 -m semantic_packages refinement inspect \
  refinements/ordered-map-0.1.0-to-0.2.0.prefine \
  --predecessor registry/ordered-map/theory/records/ordered-map-spec.json \
  --successor registry/ordered-map/successors/o8/theory/ordered-map-spec.json \
  --output /tmp/ordered-map-refinement.json
```

Expected summary:

```text
inspected refinement ordered-map-0.1.0-to-0.2.0: 18 unchanged, 0 changed, 2 additions, 0 removals; semantic refinement unestablished -> /tmp/ordered-map-refinement.json
```

To experience a safe failure and recovery, mis-map one declaration in a disposable
proposal, then restore the reviewed bytes:

```sh
sed '0,/family = "carriers"/s//family = "laws"/' \
  refinements/stack-0.1.0-to-0.2.0.prefine \
  > /tmp/stack-mis-mapped.prefine
nix develop --command python3 -m semantic_packages refinement inspect \
  /tmp/stack-mis-mapped.prefine \
  --predecessor registry/stack/theory/records/stack-spec.json \
  --successor registry/stack/successors/j5/theory/stack-spec.json \
  --output /tmp/stack-refinement.json
cp refinements/stack-0.1.0-to-0.2.0.prefine /tmp/stack-mis-mapped.prefine
```

The failed command exits `1`, preserves the prior report and every input, and identifies
the exact dangling declaration reference. Rerun it after the `cp` to recover.

What is real underneath: the command strictly parses one explicit TOML disposition,
schema-validates two caller-named Specification files, binds their exact addresses and
raw digests, and atomically writes a structural report. Equal documents are not treated
as semantic equivalence; no versions are discovered, no artifacts execute, and no
Claim or Evidence moves between versions.

### Observe bounded semantic/effect separation

Run the exact retained Stack and OrderedMap campaigns in quiet, optional, forbidden,
unspecified, and adapter-error modes:

```sh
nix develop --command python3 scripts/effect_separation_probe.py \
  --output /tmp/effect-separation.json
```

Expected summary:

```text
observed bounded effect separation: 2 domains, 10 observations, 0 semantic drifts, 2 effect challenges, 2 execution errors -> /tmp/effect-separation.json
```

The JSON report preserves every native non-effect case/declaration outcome and complete
ordered event ledger. Optional and unspecified events do not challenge the effect
declaration; forbidden `io.read` challenges only that declaration and the campaign
aggregate. Stack's error truthfully retains no event, while OrderedMap retains the one
`io.read` observed before its error; neither receives a projection comparison.

To experience fail-closed recovery without changing an accepted input, request a
governed Specification as the output:

```sh
nix develop --command python3 scripts/effect_separation_probe.py \
  --output specs/stack.pspec
```

The command exits `1`, leaves `specs/stack.pspec` unchanged, and reports
`OUTPUT_INPUT_ALIAS`. Semantic drift, ledger drift, concern spillover, or an incomplete
exact campaign likewise preserves any prior output rather than publishing a partial
report.

What is real underneath: the probe invokes only two repository fixture adapters through
their existing exact runners and compares immutable, domain-owned projections. It does
not discover or execute registry metadata, observe effects outside adapter reports,
create Claim/Evidence records, select policy, or establish a general effect calculus.

### Inspect finite authored resource composition

Inspect the retained PSpec algebra against the two exact imported Specifications and
the profiles required to make those Specifications link-valid:

```sh
nix develop --command python3 -m semantic_packages resource inspect \
  specs/persistence-composition.pspec \
  --dependency registry/stack/theory/records/stack-spec.json \
  --dependency registry/stack/theory/dependencies/stack-profile.json \
  --dependency registry/ordered-map/theory/records/ordered-map-spec.json \
  --dependency registry/ordered-map/theory/dependencies/ordered-map-profile.json \
  --resource retained-persistence \
  --output /tmp/resource-composition.json
```

Expected summary:

```text
inspected resource algebra retained-persistence: 4 elements, 16 compositions, 2 bindings, fold=both-retained; satisfaction unestablished -> /tmp/resource-composition.json
```

The report preserves the complete authored carrier, all sixteen ordered composition
rows, both exact declaration bindings, 8 unit/16 commutativity/64 associativity
observations, and every transition in authored-order and reverse-order folds.

To observe fail-closed law checking, copy the source and change the
`stack-retained * stack-retained` result from `stack-retained` to
`ordered-map-retained`; the command reports the smallest associativity counterexample
and preserves any prior output. Output paths that alias any of the five explicit inputs
also fail without changing an input.

What is real underneath: the command reuses the all-or-none PSpec authoring boundary,
resolves bindings only to resource declarations in exact imports, and exhaustively
enumerates one authored `finite-commutative-monoid-v1` table. The fold composes authored
semantic elements, not runtime resources or Evidence results. A well-formed table does
not establish persistence satisfaction, compatibility, refinement, ownership,
separation, quantities, resolver acceptance, or a universal resource logic.

### Verify the repository

Run the repository quality gate:

```sh
python3 -m pip install -r requirements-dev.txt
# Lean must resolve to 4.30.0, commit d024af099ca4bf2c86f649261ebf59565dc8c622.
# Set LEAN=/path/to/lean when that binary is not on PATH.
# Rust, a C linker, and Deno must resolve through RUSTC/CC/DENO or PATH.
python3 scripts/check_repo.py
```

The gate includes record/link fixtures, 18 loader groups, 50 adapter/campaign tests,
59 cross-language candidate/Evidence-binding controls, 302 actor journeys, 42 research
probes, 20 governance tests, two fresh Stack reports/eight records, two fresh base
OrderedMap reports plus one selective breaker, the exact base and profile-choice
2/14/14 candidate censuses, two fresh profile-bound reports, and the 49-group proof
boundary. Check the accepted proof Evidence directly with:

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

Inspect both exact OrderedMap deployment choices without executing either Realization:

```sh
python3 -c 'from semantic_packages.ordered_map_profile_choice import inspect_ordered_map_profile_choices as inspect; result = inspect(); assert result.ok; print(result.output, end="")'
```

The read-only actor authenticates one 69-member graph, selects Rust `0.2.0` only for
the native-process policy/profile and TypeScript `0.2.0` only for the Deno-sandbox
policy/profile, and renders every selected or inapplicable Claim and Evidence item.
It does not infer profile refinement, move Evidence between profiles, benchmark the
candidates, execute them, or treat the separate child-process boundary as assurance.

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

This repository is an executable research prototype with complete bounded local Stack,
finite OrderedMap, and exact differentiated-profile lifecycles, plus an independently
reviewed two-domain authoring control, explicit refinement inspection, and bounded
effect-separation observation. The automated author journey is green; uninvolved-author
observation and final review remain required before ExecPlan 0006 closes. This is not
yet a stable standard, a proof of noninterference, an arbitrary-domain semantic-package
ecosystem, or a hosted production registry.
