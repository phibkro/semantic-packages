# Design spec 0007: risk-first roadmap to a usable semantic registry

## Contract status

Frozen roadmap proposal, not implementation authorization. Revision 1 freezes the
product outcome, critical-risk ordering, falsifiers, slice sequence, parked work, and
operator gates on 2026-07-23. It starts from the authorized, gate-verified #16–#21
stack at exact `master` commit `404c9c40be5173c993cd376aa2d2c5892f8503a1`.
This document and ExecPlan 0012 are the complete 1:1 documentation
increment; they add no product mechanism and authorize no code until the operator
accepts or revises this roadmap.

After operator acceptance, every execution slice below requires its own frozen design
spec, ExecPlan successor nodes, implementation branch, evidence, and 1:1 PR. A failed
spike may close a slice by killing its premise; it may not be converted into mechanical
breadth or hidden by weakening the product claim.

## Operator direction and product outcome

Make the registry usable end-to-end while attacking the hardest product-critical
technical risks before breadth:

1. publish a semantic Specification whose exact meaning and selected laws are checked
   in Lean;
2. publish independently implemented Rust and TypeScript packages against that same
   observable contract;
3. state exactly what each proof and conformance result supports, what it does not, and
   how a consumer policy derives an implementation decision;
4. publish, acquire, inspect, version, resolve, and reproduce those artifacts through a
   registry workflow without editing repository internals by hand; and
5. preserve exact identity, provenance, contradictions, unknowns, and directional
   deployment boundaries throughout.

“Lean-proved Specification” means exact specification-subject propositions are checked
under an explicit Lean model, assumptions, translation, and trusted kernel. It does
**not** mean Rust or TypeScript source, compiler output, adapter faithfulness, or every
Specification concern is formally verified. “Implementation satisfies Specification”
means a policy derives an explainable relation from separately selected realization-
subject Evidence; it must never arise by transferring specification proof to a
Realization.

The roadmap vehicle is one assurance successor of the existing Stack package because
Stack already has exact observations, a bounded Lean proof probe, independent Rust and
TypeScript Realizations, breakers, Claims/Evidence, and consumer projections. The
successor must prove and exercise at least `pop-empty`, `pop-push`, top-first extensional
observation, and retained-value persistence. It may add the smallest machine-readable
semantic aspect required by the decisive spike, but it may not make Lean, Stack, JSON,
or one transport universal.

## Definition of “usable” for this roadmap

Before web UI work, a fresh consumer using documented CLI/API surfaces can:

```text
publish exact immutable release bundle
  -> acquire and verify it from an explicit registry endpoint/source
  -> browse Specification, Lean proof coverage, Rust/TS Realizations, Evidence, and unknowns
  -> request an exact policy/profile/version constraint
  -> receive a deterministic selection or explained failure
  -> reproduce the selected proof/conformance Evidence from pinned inputs
  -> obtain the selected artifact and its directional execution/integration boundary
```

The user must not need to edit a manifest, know fixture paths, read domain-specific
resolver source, infer assurance from a badge, or accept implicit `latest`. The first
usable registry may be filesystem/HTTP-neutral and CLI-first. Production hosting,
large-scale search, and the web browser are later increments.

## Risk ordering rule

Order by **fatality before frequency, semantic authority before mechanics, and cheapest
decisive falsifier before build-out**. A risk is earlier when failure would make every
later package or UI conclusion misleading, even if its eventual implementation is
smaller. Adapter count, language count, visual polish, and provider breadth do not
advance while an earlier fatal premise remains open.

## Hardest product-critical technical problems

### R1 — One proposition must survive authoring → Lean → conformance without semantic drift

**Why first:** Current laws are hosted strings. The accepted `pop-empty` proof binds a
hand-written Lean theorem to a declaration digest, but translation fidelity remains an
assumption. Runtime harnesses separately own expected behavior. A green proof and green
campaign can therefore concern two plausible but different meanings while the registry
presents one declaration.

**Must hold:** One exact, observation-level semantic source or checked interpretation
must determine the proposition address, Lean model/theorem statement, and executable
observation contract. Independent protected examples still test user intent so a
self-consistent mistranslation cannot ratify itself. Lean-specific syntax stays in a
replaceable proof lane; the canonical model need only cover this tracer's selected
aspect.

**Cheapest decisive spike — semantic mutation closure:** encode the smallest typed
Stack semantic fragment, elaborate/check it into both the Lean proof input and the
campaign oracle, then make one meaning-changing mutation such as reversing observation
order or changing empty-pop. Without changing downstream artifacts, both proof binding
and Rust/TypeScript conformance acceptance must become stale or fail at exact pointers.
A whitespace-only or documentation-only mutation must not change meaning.

**Kill/falsifier:** kill the proposed semantic-anchor representation if either proof or
campaign stays accepted after a semantic mutation, if downstream authors must repeat
normative semantics by hand, if the Lean theorem can change while the semantic digest
stays fixed, or if the anchor prescribes Rust/TypeScript representation. Do not recover
by declaring digest equality to be translation correctness.

### R2 — A conformance result must identify the Realization artifact actually exercised

**Why second:** Black-box behavior cannot detect a perfect shadow adapter. Current
metadata can name a library while an independently supplied process returns expected
answers. In that case campaign Evidence supports the observed process boundary, not the
claimed hidden package. Without a precise subject, “this implementation satisfies this
spec” is false advertising.

**Must hold:** Define the Realization for the tracer as an exact executable component or
package artifact whose build graph, source inputs, toolchain, adapter/binding, output
digest, and invocation are pinned. Keep separate propositions for artifact provenance,
boundary conformance, and any stronger source-to-artifact or adapter-faithfulness claim.
A resolver may combine only the propositions its policy explicitly requires.

**Cheapest decisive spike — perfect shadow and artifact swap:** run a behaviorally
perfect shadow and a post-build artifact substitution. Behavioral conformance may still
support the boundary proposition, but the named Rust/TypeScript Realization decision
must fail because origin/binding Evidence is missing or challenged. Rebuilding the exact
source/toolchain must recover the expected artifact identity or report reproducibility
as unknown rather than silently rebinding it.

**Kill/falsifier:** kill any model in which a Realization names one artifact while
Evidence executes another, an adapter declaration alone proves faithfulness, a green
exit proves origin, or non-reproducible builds are presented as byte-reproducible.

### R3 — Rust and TypeScript must share an observable contract without a language owning meaning

**Why third:** The tracer has domain-local JSON protocols and bounded values. A usable
registry needs one exact operation/value contract that Rust and TypeScript packages can
consume without host-number coercion, object identity, exception behavior, declaration
order, or generated binding code becoming semantic authority.

**Must hold:** The selected Stack contract has canonical tagged values, integer domain,
operation framing, observation/equivalence, errors, and protocol lifecycle. A contract
artifact is versioned and content-addressed independently of either language. Generated
bindings are permitted only if generated bytes and generator provenance remain derived
artifacts; hand-written Rust and TypeScript representations stay private.

**Cheapest decisive spike — differential codec boundary:** feed canonical and hostile
vectors through independently implemented Rust and TypeScript codecs/adapters,
including integer edges, absent/some tags, malformed values, retained handles, extra
fields, ordering variation, and process errors. Both must produce the same canonical
observations and classifications under a harness that imports neither implementation.

**Kill/falsifier:** kill the contract encoding if legal values narrow differently,
round-trip changes meaning, one language's exception/object/number model leaks into the
Specification, or adding a third language would require changing normative semantics
rather than implementing the same finite contract.

### R4 — Evidence acceptance and satisfaction derivation must be generic, typed, and non-circular

**Why fourth:** Existing product slices use domain-specific resolver code and largely
open `provenance` objects. They demonstrate semantics, but cannot safely scale into a
registry: a new package can accidentally define its own acceptance algorithm, and a
report can appear authoritative because the same code produced and accepted it.

**Must hold:** Mechanism contracts define required provenance and an independent
validator for Lean proof, bounded conformance, build/origin, and review Evidence. One
generic assurance engine separates graph validity, review state, applicability,
mechanism acceptability, result, freshness, selected challenges, and policy-derived
satisfaction. It consumes exact records/artifacts and emits an explanation, not a
badge. No package ID or domain-specific branch may grant acceptance.

**Cheapest decisive spike — hostile Evidence matrix:** replay the same policy over
Stack under systematically mutated theorem statement, semantic digest, source,
artifact, adapter, profile, toolchain, report, review state, result, freshness, and
challenge records. Then rename/package-clone the graph without changing structure; the
same generic decisions must result. Every unsupported or contradictory axis must fail
closed with one stable reason.

**Kill/falsifier:** kill the engine if package-specific code is required for acceptance,
unknown provenance keys carry authority, accepted proof transfers to a Realization,
selected challenge is hidden, assertion passes without explicit policy, or producer and
validator are indistinguishable in the evidence graph.

### R5 — Version and dependency resolution must use explicit semantic relations, not version spelling

**Why fifth:** Exact pinning is safe but not yet usable for selecting among releases.
Existing refinement reports deliberately leave semantic refinement unestablished.
Inferring compatibility from semver or choosing `latest` would erase the project's core
semantic distinction; refusing every choice leaves the registry impractical.

**Must hold:** Release constraints, dependency edges, specification refinement or
compatibility Claims, realization compatibility, profiles, and Evidence are explicit
inputs. Resolution is deterministic, explains rejected versions and unknown relations,
and never fabricates compatibility from a version string. Exact lock output is
reproducible. Semantic compatibility and directional integration cost remain separate.

**Cheapest decisive spike — hostile version diamond:** publish one additive successor,
one behavior-breaking successor with an attractive higher version, two dependencies
that form a satisfiable exact diamond, and one conflict. The resolver must choose only
a policy/evidence-supported solution, reject or explain the conflict, retain the higher
but semantically unsuitable release, and reproduce the same lock independent of
registry enumeration order.

**Kill/falsifier:** kill the resolver if member order changes selection, semver syntax
creates a semantic edge, stale predecessor Evidence transfers, implicit latest enters
a lock, backtracking hides an unmet required concern, or realization interoperability
is treated as semantic satisfaction.

### R6 — Publication and acquisition must preserve immutable authority under hostile updates

**Why sixth:** Current curated manifests are local and exact, but authors edit them in a
repository. A usable registry needs a transaction and trust model before remote or
multi-author use. Otherwise a correct resolver can consume tampered, partially
published, replayed, or equivocating metadata.

**Must hold:** A release bundle has a canonical member set, exact addresses and content
digests, ownership/authorization statement, immutable publication identity, and atomic
commit. Acquisition verifies bytes before graph use. Indexes and search results are
derived projections. Key rotation, revocation, rollback visibility, and registry trust
roots are explicit policy; signatures attest bytes/authority, never semantic truth.

**Cheapest decisive spike — tamper/replay/partial-publish campaign:** publish one Stack
release to a disposable registry, then mutate a member, omit a member, substitute an
Evidence artifact, replay an older index, publish half a transaction, and present two
contents at one address. Every attack must fail or remain visibly historical before
resolution. An authorized append-only successor must publish and acquire cleanly.

**Kill/falsifier:** kill the publication design if one address can resolve to two byte
sets, partial state is queryable as a release, an index becomes a second source of
truth, signatures are shown as assurance, revocation erases history, or offline exact
locks cannot detect rollback/substitution.

### R7 — The CLI/API workflow must be usable without bypassing the assurance model

**Why seventh:** Once the authority and decision risks close, mechanical integration
can still make the product unusable. This risk is later because UI over a misleading
model only accelerates incorrect decisions.

**Must hold:** Stable commands or APIs cover author/check, Lean prove, Rust/TypeScript
build and conformance, publish, acquire, inspect, resolve, lock, reproduce, and fetch.
Outputs expose evidence mechanism/result/review/applicability, assumptions, exclusions,
unknowns, selected challenges, and boundary mechanism. Machine-readable output is
canonical; human output is a projection.

**Cheapest decisive spike — cold CLI journey:** from a clean environment with only an
explicit registry source and trust policy, a user publishes the vehicle, resolves one
Rust and one TypeScript deployment profile, reproduces the selected Evidence, fetches
the exact artifact, and explains a deliberately failing policy. No fixture path,
manifest edit, source scan, or domain-specific command is allowed.

**Kill/falsifier:** the registry is not usable if the journey needs repository-internal
knowledge, a hand-edited manifest, hidden network discovery, unexplained fallback,
context-free “verified” output, or a web UI to complete a core task.

## Risk map and hard dependencies

| Risk | Fatal premise | Hard predecessors | Releases |
|---|---|---|---|
| R1 semantic correspondence | proof and conformance concern one meaning | operator roadmap gate | R2, R3 |
| R2 artifact subject/binding | Evidence identifies what ran | R1 address/meaning | R4 |
| R3 cross-language contract | Rust/TS expose one observation | R1 observation contract | R4 |
| R4 generic assurance | satisfaction is derived honestly | R1–R3 evidence subjects | R5, R7 |
| R5 version/dependency resolution | releases can be selected safely | R4 generic decisions | R6, R7 |
| R6 publication/acquisition integrity | registry bytes and history are trustworthy | R4 records, R5 release model | R7 |
| R7 usable CLI/API | users can complete the lifecycle | R4–R6 | release convergence |

R2 and R3 may execute in parallel only with disjoint files after R1 freezes their shared
semantic and artifact boundaries. No later risk may be called complete through a
hard-coded Stack-only exception.

## Proposed 1:1 slice sequence

### Slice S0 — roadmap gate (this PR)

Freeze this risk inventory, spikes, order, vehicle, usability boundary, and parked list.
Observable result: the operator can accept, revise, or reject the roadmap before any
product code. Closure is operator approval plus green repository/PR metadata checks.

### Slice S1 — semantic correspondence tracer (attacks R1)

One design spec and PR introduce the smallest typed, observation-level Stack semantic
anchor and checked elaborations/interpretations needed for Lean and the executable
campaign. Lean checks the selected Stack laws with no `sorry` or undeclared axioms.
Existing/new Rust and TypeScript vehicle executions are used only to test that semantic
mutations invalidate conformance binding; S1 does not yet claim artifact origin.

Required close: semantic-mutation closure passes; independent intent fixtures catch a
self-consistent wrong top/bottom order; proof coverage and unchecked declarations are
visible. If the spike kills the representation, S1 ends with the retained counterexample
and a successor design choice rather than continuing.

### Slice S2 — exact Rust/TypeScript Realization artifacts (attacks R2 and R3)

One design spec and PR define the vehicle's language-neutral value/operation boundary,
build exact Rust and TypeScript package artifacts, and bind source, toolchain, build,
artifact, component boundary, and campaign invocation. Deliberate perfect-shadow,
artifact-swap, codec, malformed-value, retained-handle, and differential controls run.

Required close: both implementations conform under the same external oracle; origin
and boundary Claims remain separate; shadows cannot satisfy the named artifact policy;
no representation or language runtime becomes semantic authority.

### Slice S3 — generic assurance engine (attacks R4)

One design spec and PR types the minimum Lean-proof, conformance, build/origin, and
review provenance contracts and replaces vehicle acceptance with a package-neutral
engine. Existing domain-specific resolvers remain regression references until the new
engine demonstrates equivalent or more conservative outcomes; they are not silently
rewritten.

Required close: hostile Evidence matrix and package-rename test pass; proof never
transfers to Realizations; mixed support/challenge and unknowns remain visible; Rust and
TypeScript decisions cite exact selected Evidence.

### Slice S4 — evidence-backed release resolution (attacks R5)

One design spec and PR adds explicit release/dependency constraints, compatibility or
refinement Claims/Evidence, deterministic lock output, and separate directional
realization compatibility. It uses exact Stack assurance successors and a conflict
fixture rather than inventing general semver meaning.

Required close: hostile diamond passes, ordering is irrelevant, unsupported higher
versions remain visible but unselected, and exact lock reproduction is stable.

### Slice S5 — transactional registry and acquisition (attacks R6)

One design spec and PR creates the smallest filesystem/HTTP-neutral publication API,
immutable release bundle, trust/authorization envelope, atomic append, verified fetch,
and derived index. Cryptography and ownership enter only to preserve publication
authority; they do not become assurance.

Required close: tamper/replay/partial/equivocation campaign passes, authorized successor
publishes, exact lock fetches offline-verifiable bytes, and historical contradiction or
revocation remains inspectable.

### Slice S6 — cold end-to-end usable registry release (attacks R7)

One design spec and PR integrates stable generic CLI/API verbs and a fresh-environment
journey: author/check, Lean prove, Rust/TypeScript build/conform, publish, acquire,
inspect, resolve, lock, reproduce, and fetch. It includes one success per language and
one policy failure with explanation.

Required close: an uninvolved operator completes the journey without repository
internals; hosted gates reproduce it; durable docs record limitations and recovery.
Only then does the roadmap call the registry usable for its bounded vehicle.

## Explicitly parked work

Parked means deliberately not on the critical path; it is not rejected forever.

- **Proof-assistant breadth:** Coq, Isabelle, Agda, F*, SMT, model-checker, and generic
  proof-adapter plugin fleets. Lean is the only proof lane until R1/R4 close and a
  concrete second mechanism tests the extension boundary.
- **Language breadth:** implementations, SDKs, code generators, package-manager plugins,
  and adapters beyond Rust and TypeScript. The two selected languages must first share
  one honest artifact/contract/evidence path.
- **Transport/ABI breadth:** universal FFI, Wasm component, RPC, in-process, native ABI,
  and every runtime bridge. Record directional child/component boundaries now; choose a
  broader transport only when the usable journey demonstrates the need.
- **Web application:** later increment after S6 stabilizes registry/query APIs and
  canonical projections. The intended browser should draw UX inspiration from JSR and
  npm: prominent package identity/version, search, version history, install/use snippets,
  implementation tabs, provenance, and dependency navigation—while adding this
  product's essential Claim/Evidence/unknown/assumption/profile/policy and semantic-vs-
  deployment views. The web app is never a source of truth or required for core use.
- **Production-scale hosting:** CDN, mirrors, billing, organizations, moderation,
  analytics, ranking, recommendation, and high-availability search.
- **Universal foundations:** universal semantic DSL, proof calculus, institution engine,
  refinement logic, synthesis, arbitrary effect/resource/protocol/numerical composition,
  and verified compilers.
- **Mechanical package breadth:** porting every existing tracer domain into the new path
  before the Stack assurance vehicle closes all fatal risks.

## Global falsifiers and Definition of Done

The roadmap is wrong and must reopen if:

1. it permits code before operator acceptance of this frozen increment;
2. a later slice can pass while an earlier fatal premise remains unobserved;
3. “Lean-proved” is allowed to imply a formally verified Rust/TypeScript Realization;
4. proof and conformance can bind different meanings under one declaration;
5. a shadow or swapped artifact can satisfy a named Realization policy;
6. Rust or TypeScript representation becomes normative;
7. package-specific resolver branches are required to grant assurance;
8. version spelling or registry order creates semantic compatibility;
9. publication integrity is confused with semantic truth;
10. a usable journey requires hand-edited repository manifests or the web app;
11. contradictory, failed, stale, inapplicable, or unknown Evidence is erased;
12. parked breadth starts before its named reopen trigger;
13. a slice bundles multiple design specs or opens a fragment PR; or
14. the final fresh-environment journey cannot reproduce both Lean proof checking and
    Rust/TypeScript package decisions from exact acquired artifacts.

This roadmap increment is done when the design spec and ExecPlan agree, all fourteen
falsifiers and seven spikes are explicit, the risk dependencies are acyclic, parked
work is unambiguous, repository checks pass, one docs-only PR is stacked above #21, and
the operator receives the exact frozen spec path for gating.

## Assumptions and known exclusions

- Stack is a risk vehicle, not the product's ultimate domain or evidence of arbitrary
  generality.
- Lean checks specification models and laws; source/compiler verification is excluded.
- Finite Rust/TypeScript conformance remains bounded Evidence unless a later explicit
  proof mechanism strengthens it.
- The first usable registry is bounded and CLI/API-first, not production hosting.
- Cryptographic publication authenticity does not prove Claims or Evidence results.
- Exact versions remain the safe baseline until S4 establishes explicit selection.
- The roadmap estimates technical dependency and fatality, not calendar duration.

## Recovery and reopen triggers

Revert this docs-only PR to remove the roadmap without affecting PRs #16–#21. Before
operator approval, revisions change only this design spec and ExecPlan 0012 and retain
revision history. After approval, a material discovery creates a numbered design-spec
revision and an ExecPlan successor node; accepted slice history remains visible.

Reopen the ordering when a cheap spike shows a later risk blocks an earlier probe,
when the Stack vehicle cannot expose a required product risk, or when operator priority
changes. Unpark proof/language/transport breadth only after S1–S3 demonstrate a stable
extension boundary and a concrete user need. Unpark the web app only after S6 freezes
usable registry APIs/projections and the operator selects browser work.

## Revision history

- **2026-07-23, revision 1 (risk-first roadmap frozen for operator gate):** Defines the
  bounded usable-registry outcome, seven fatal risks with decisive spikes/kill criteria,
  six post-gate 1:1 execution slices using Lean + Rust + TypeScript Stack assurance,
  fourteen global falsifiers, and the explicit adapter/language/proof/web/hosting parked
  list. No product code is authorized.
