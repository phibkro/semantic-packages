# Minimum viable specification language

## Design target

The first language is not universal. It is sufficient when it can express one useful abstract data type, its observations, laws, one resource/effect property, and scoped claims that can be connected to external proof and test systems.

The tracer bullet uses JSON as its temporary canonical interchange format. The curly
surface form below is the retained pre-A5 sketch, not PSpec v1 syntax. The first
experienceable PSpec candidate is the explicit TOML-shaped surface governed by
[design-spec 0001](../../design-specs/0001-explicit-pspec-author-journey.md); it does not
turn the historical sketch into an implicit desugaring authority.

Categorical logic and propositions-as-types may guide an individual semantic aspect or
proof checker, but they do not make one type theory the canonical Specification
language. A dependent type such as “inputs mapped to outputs carrying a correctness
witness” can specify a useful relation while Claims and externally governed Evidence
remain separate records. The forbidden move is to universalize that encoding or treat
mere inhabitation as consumer-accepted assurance: doing so would privilege one proof
mechanism over testing, benchmarking, audit, and assertion. Higher-order logic is one
hosted logic, not a universal foundation. Cross-logic composition remains an explicit
translation/satisfaction problem rather than an implicit encoding into whichever proof
assistant is selected.

## Proposed core forms

```text
specification
import
carrier/type
operation
observation
law
state / transition
resource
 effect
claim
profile
```

Claim and profile declarations may appear inline for author convenience, but they
elaborate to separately identified records. Evidence is never embedded as an
unscoped badge on a declaration.

## Illustrative syntax

```text
spec Stack[A] {
  type Stack

  op empty : Stack
  op push  : Stack * A -> Stack
  obs pop  : Stack -> Option[A * Stack]

  observe elements(s: Stack):
    top_first_sequence_by_repeated_pop_until_none(s)

  equivalence Stack:
    pointwise_equal(elements(left), elements(right))

  law pop_empty:
    pop(empty) == None

  law pop_push(s: Stack, x: A):
    pop(push(s, x)) == Some((x, s))

  effects {
    forbidden: io.*
    optional: debug.emit
    default: unspecified
  }

  resources {
    persistence: retained_values_remain_observationally_unchanged
  }

  claim push_cost {
    concern: performance
    proposition: amortized_O(1)
    profile: stack_default
    workload: push_sequence
    cost_measure: realization_steps
  }
}
```

This syntax is provisional. The initial parser may use JSON/YAML internally while this form guides semantics.

## Authoring boundary

[ADR 0016](../decisions/0016-representation-neutral-authoring-boundary.md) accepts a
surface-neutral boundary for ExecPlan 0006. Explicit source bytes, one exact format
token, an opaque diagnostic label, and the explicit finite dependency context clarified
by [ADR 0017](../decisions/0017-explicit-authoring-dependency-context.md) produce either
one exact canonical Specification document or ordered source-local diagnostics. The
labels have no identity or content authority; all root/local IDs and references remain
explicit. The boundary performs no filesystem, manifest, registry, network, version,
or profile discovery. Raw duplicate members, invalid encoding/syntax, and unsupported
formats fail before record validation. Hosted semantic payloads remain unchecked text.

`canonical-spec-json-v1` is the first conformance control, not the final human surface.
`semantic_packages.authoring.author_specification` now implements that exact token:
strict raw decoding, source/dependency schema phases, graph-relative link checking,
all-or-none observations, and detached exact output. Its dependency context is
caller-supplied and finite; it performs no acquisition or selection. The generic record
checker retains its historical coarse fallback, while this author-facing boundary
refines the accepted blank-law counterexample to its exact source pointer.

`pspec-toml-v1` is the first non-control adapter through the same boundary. It maps
explicit UTF-8 TOML keys and tables losslessly to the canonical Specification document,
rejects invalid TOML and non-JSON TOML values before schema conclusions, preserves
authored declaration order and hosted text, and grants comments no canonical meaning.
`python3 -m semantic_packages author` owns the explicit source/dependency/output file
boundary and atomic output publication; it performs no dependency discovery or registry
publication. Stack and OrderedMap exercise the same command and schema/link authority.

The automated non-control journey is implemented, but the lifecycle cannot close
without eligible uninvolved-author observation across Stack and OrderedMap and A-R5
review. A separate authoring IR remains unjustified until a second useful frontend or
non-identity transformation demonstrates the need.

## Semantic rules

- A field-like declaration denotes an observation, not a memory slot.
- Canonical records and references use exact typed addresses; surface names and
  declaration order do not create identity.
- For the tracer, an import is an exact edge within the explicitly loaded local record
  set. It does not acquire a file, create a namespace, re-export declarations, impose
  order, or imply compatibility. Self-imports, cycles, diamonds, and repeated exact
  edges are therefore structurally valid until an elaboration semantics demonstrates
  a stronger requirement.
- Equality over an abstract carrier denotes specification-defined observational
  equivalence, never host-language object or representation equality.
- Every executable law must identify how its quantified values and results can be
  generated, observed, and compared. A law that cannot be falsified by the selected
  checker remains unchecked rather than implicitly true.
- Effects describe observable or permitted interactions, not specific syscalls.
- The first effect model is an adapter-observed event trace. Events outside that
  boundary are an explicit exclusion, not proof of their absence.
- An effect contract states the disposition of unlisted observed event classes; it
  never acquires an implicit permissive or pure-by-default meaning.
- Design-spec 0003's cross-domain probe compares an exact non-effect campaign projection
  while retaining the original event ledger. Equality across quiet, optional,
  forbidden, and unspecified Stack and OrderedMap fixtures observes separation only
  inside those bounded campaigns. Adapter-error partials remain visible but are not
  compared. The `adapter-event-completeness` assumption and `adapter-external-effects`
  exclusion therefore survive unchanged; this is neither a purity claim nor an effect
  algebra, handler semantics, contextual noninterference theorem, or accepted Evidence.
- Resource properties are user-definable abstractions with declared observations,
  composition rules, and a falsification method.
- Performance claims are profile-relative and name a cost measure, workload model,
  and measurement or proof method.
- Claims do not carry their own assurance. Acceptance is computed from applicable
  evidence and consumer policy.
- Unknown or unsupported semantic aspects remain visible rather than being silently ignored.

## Stack tracer obligations

The Stack tracer fixes the following meaning without prescribing a representation:

- `pop(empty)` is `None`.
- Repeated `pop` observes a reachable finite Stack as a top-first sequence ending in
  `None`; Stack equality is pointwise equality of those sequences under the declared
  element equivalence.
- Conformance generators construct stacks from `empty` and `push`. Element domains,
  maximum depth/history, enumeration or seed, timeouts, and termination limits scope
  evidence rather than narrowing the laws.
- The harness owns expected traces and comparison. Adapters execute operations behind
  opaque handles and return canonical results; they do not define Stack equality.
- A retained handle remains usable and observationally unchanged after operations on
  it or derived handles. A witness compares it with its construction-implied trace;
  neither object identity nor allocation is observed.
- Each invocation has a delimited adapter-emitted event trace and a declared observable
  event vocabulary. Passing excludes only matching events inside that boundary;
  adapter-external effects remain visible exclusions.
- The Stack tracer's concrete process framing, opaque-handle lifecycle, tagged results,
  and error boundary are defined in
  [the adapter protocol](adapter-protocol.md); that protocol is not a universal
  transport or semantic model.
- The push-cost proposition names a profile, push-sequence workload, size function,
  aggregate cost measure, and amortized predicate such as total cost bounded by
  `a*n+b`. Evidence may instantiate a plural cost model; absent acceptable evidence,
  the claim remains visibly unsupported.

These obligations authorize canonical record design. `specs/stack.pspec` and
`specs/ordered-map.pspec` are now complete PSpec v1 candidate inputs whose outputs equal
the accepted records; their final author-experience acceptance still depends on the
uninvolved-author and A-R5 gates.

### Initial conformance and performance profile

The canonical tracer records will define the exact profile address
`(realizationProfile, stack-default, 0.1.0)`. Within that profile:

- conformance generation uses JSON integers from `-2` through `2`, constructed Stack
  depth at most `8`, and operation histories at most `32`; enumeration/seed and actual
  timeout remain evidence metadata;
- local workload `push-sequence` starts at `empty`, applies `n` consecutive `push`
  operations for arbitrary `n >= 0`, and uses `n` as its size function;
- local measure `realization-steps` counts nonnegative primitive steps under an exact
  instrumentation/cost definition supplied by each realization claim; that definition
  is an assumption or separately evidenced artifact, and different definitions are
  not silently comparable;
- aggregate cost is the sum of per-operation `realization-steps` over the workload;
- `amortized_O(1)` means that constants `a,b >= 0`, independent of `n` and the selected
  elements, bound every workload cost by `a*n+b` under that exact measure;
- supporting evidence must be a checked proof or a policy-accepted audit of a proof
  under the pinned cost definition. Bounded tests or benchmarks may challenge the
  claim or remain inconclusive, but cannot establish the universal asymptotic bound.

The inline `push_cost` form is authoring sugar for a realization-scoped claim template
that pins this profile and its local workload and measure. The tracer initially
attaches no acceptable supporting evidence, so the claim remains unsupported.
