# Core model

## Specification

A versioned semantic artifact containing one or more aspects:

```text
identity
vocabulary
operations and observations
laws and invariants
behavior/protocol transitions
effect contract
resource contract
performance/empirical claims
imports and refinements
```

Aspects may be sparse. A pure algebraic specification need not declare protocols or performance.

Every addressable artifact has a stable identity and an explicit version. For the
tracer bullet, a canonical record address is the exact tuple `(kind, id, version)`.
The tuple identifies immutable record content within one loaded registry; `id` and
`version` are opaque strings, and the same `id` may have multiple exact versions.
Content digests support provenance but are not record identities.

References are structured objects that pin `kind`, `id`, and `version`. Bare names,
implicit `latest`, version ranges, and compatibility inferred from version-number
syntax are invalid. Declarations within a specification that can be claimed or
evidenced have explicit local IDs in one flat namespace per specification version. A
declaration reference pins the enclosing specification address and local declaration
ID; serialization order and array position have no addressing meaning. Reuse of a
local ID in another specification version does not itself establish continuity or
compatibility.

Schema validation checks reference shape. Link validation separately rejects duplicate
record addresses, duplicate local IDs, dangling or wrong-kind targets, and incoherent
redundant scope such as evidence naming a realization different from its claim. A
well-formed record outside a requested profile is inapplicable; an incoherent reference
is invalid input, not inapplicable evidence. See
[ADR 0005](../decisions/0005-exact-typed-references.md).

The tracer loader treats supplied files and directories as one finite local source
set. Normalized source paths are provenance, not record identity, and imports never
search outside that set. A Specification import is provisionally only an exact visible
graph edge: it does not merge namespaces, re-export declarations, impose evaluation
order, or infer compatibility. Self-imports, cycles, diamonds, and repeated exact
edges remain valid while those additional semantics are absent; see
[ADR 0007](../decisions/0007-local-loader-and-import-edges.md).

A specification contains propositions, but does not contain the assurance that they
hold for a realization. For example, a law is a normative proposition. A `Claim`
scopes that proposition to a subject and assumptions, while `Evidence` records what
was actually checked. Inline claim syntax may be convenient authoring sugar, but it
must elaborate to the same separately addressable records.

### Observation and equivalence

Abstract values are never compared by representation identity. Each carrier used by
an executable law must provide a specification-level observation or equivalence
criterion. For the Stack tracer bullet, observing a reachable finite stack means
repeatedly applying `pop` until `None`, producing a top-first element sequence. Stack
equivalence is pointwise equivalence of those finite sequences. The selected test
instantiation declares element observation/equivalence; comparing Rust or TypeScript
object layouts, handles, or allocation strategies is not a semantic test.

## Realization

A mapping from a specification's vocabulary into executable artifacts, together with metadata about language, target, runtime, ABI, build, and limits.

A realization is not accepted merely because names and types align. It must be associated with claims and evidence.

A realization also declares which adapter exposes its operations and observations to
the conformance runner. Adapter correctness is an assumption or a separately
evidenced claim; it is not silently included in implementation conformance.
For the six-record tracer model, the adapter is a versioned descriptor nested in the
immutable Realization record, not a seventh canonical record. Realization-executing
Evidence repeats the adapter's `(id, version)` selector, and link validation requires
an exact match with the descriptor in the referenced Realization. Multiple independently
versioned adapters per Realization remain deferred until they demonstrate a need for a
realization-local namespace or a canonical Adapter kind.

## Claims and evidence

A claim records:

```text
stable identity and version
subject reference
proposition reference or inline proposition
concern
scope
assumptions
exclusions
applicable profile references
lifecycle state
```

A claim subject is either an exact specification record or an exact realization
record. Its proposition reference pins a declaration in the governing specification.
A specification-subject claim can receive proof evidence about the specification or
named law without inventing a realization. A realization-subject claim additionally
pins the realization and its governing specification.

Evidence records:

```text
stable identity and version
claim reference
mechanism
artifact/provenance
specification version
realization and adapter versions when applicable
environment
result: supports | challenges | inconclusive | error
freshness
review state
```

Evidence always pins its claim and governing specification. Realization and adapter
references are required when the claim subject is a realization or the evidence
mechanism executes a realization; they are absent for specification-only proof
evidence. When present, redundant specification, realization, and adapter scope must
agree exactly with the claim and realization records. Evidence always states its
applicable profile list; that list must equal the Claim's applicable-profile set by
exact typed address, independent of array order. A contradictory scope is invalid; a
coherent claim-and-evidence pair for a different consumer-requested profile is valid
but inapplicable.

Claim lifecycle, evidence review, and assurance are distinct. A claim may be active
while unsupported. Accepted evidence may challenge a claim. An assertion is a weak
evidence mechanism, not a truth status placed on the claim. Assurance is derived from
the visible set of applicable evidence under a consumer policy; it is never copied
from a badge or author declaration.

For the tracer, Claim lifecycle uses the provisional vocabulary
`draft | active | retired | withdrawn`. These values describe publication lifecycle,
not evidentiary result, review state, truth, or assurance.

Contradictory and failed evidence remains attached to the claim. Supersession affects
which evidence a policy selects, not whether historical results remain inspectable.

Record validity, review state, applicability, mechanism acceptability, result, and
derived assurance are separate axes. Applicable accepted `supports` evidence can
contribute assurance; `challenges` remains visible and blocks satisfaction of a
required concern while selected; `inconclusive` and `error` do not support a claim.
Assertion-only evidence contributes only when the consumer policy explicitly accepts
the assertion mechanism.

## Policies

A consumer policy stratifies concern priority:

```text
required | preferred | optional | ignored
```

It may also state acceptable evidence mechanisms and minimum assurance per concern.

`forbidden` is not a fifth evidence priority. Prohibition is the polarity of a
semantic constraint, such as absence of matching `io.*` events, and is evaluated as a
required negative obligation. Missing or inapplicable evidence does not prove absence;
the resolver reports the obligation as unmet or unknown unless the policy accepts
applicable evidence scoped to the declared observation boundary. See
[ADR 0006](../decisions/0006-separate-priority-from-prohibition.md).

When a prohibition repeats an effect `eventPattern`, link validation requires that
pattern to be declared by the referenced effect contract. The policy may select a
declared semantic event; it cannot create a second, drifting event vocabulary.

The tracer's provisional schemas encode the declaration forms needed by the Stack
slice. Inline Claim propositions and general behavior/protocol-transition declarations
remain explicit exclusions until a tracer observation requires their representation;
their absence is not a claim that those concepts are outside the architecture.

Unknown and unsupported are first-class resolver outcomes. A required concern with
no acceptable evidence fails resolution; an optional or ignored concern remains
visible but need not block selection.

## Profiles

A realization profile is a reusable description of an execution envelope or cost
model: platform, runtime capabilities, scale, workload, latency/memory measures,
concurrency, trust assumptions, and portability constraints. Claims and evidence
reference the profile under which they apply. Realizations declare supported
profiles or constraints; consumer policies state the requested envelope.

Workload and cost-measure IDs share one flat profile-local namespace within an exact
RealizationProfile version. Reusing an ID within or across those categories is invalid;
otherwise an exact profile-member reference could select more than one meaning.

A profile does not itself prove that a realization works in that environment. It
provides the shared vocabulary needed to make the claim and evidence comparable.
Performance propositions additionally name an operation family, workload and starting
state, input-size function, cost measure and unit, aggregation rule, predicate, and
permitted evidence method. Cost-measure definitions live under an exact profile and
have stable local IDs; a claim pins the profile and measure. The tracer bullet uses a
realization-specific declared step measure for its initial proposition. Other measures
remain possible, and results are not compared across different measures without an
explicit relation.

## Satisfaction

The system should initially support a family of conformance relations rather than pretending there is one universal boolean:

- schema/type conformance;
- exact law satisfaction;
- observational refinement;
- protocol simulation;
- test-suite threshold;
- benchmark/empirical threshold;
- human assertion.

Satisfaction is evaluated for a tuple of specification version, realization version,
required claim set, consumer policy, and profile. Registering two realizations for
the same specification is not sufficient to make them semantically substitutable.

The resolver reports the relation, assumptions, evidence, and unknowns used. It must
not collapse these conformance relations into one context-free boolean.
