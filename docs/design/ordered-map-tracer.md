# OrderedMap second-domain tracer contract

## Status and acceptance boundary

This document is the O-G2-accepted design contract for ExecPlan 0004. It turns the
accepted paper probe into exact actor observations. O-R2 and O-R2b's BLOCKs remain in
the plan history; O-R2c passed their successor. O-G2 authorizes only the ordered nodes
starting with exact O3a contract artifacts, not Evidence or out-of-order implementation.

The slice establishes generality only across Stack and one structurally different
finite OrderedMap. It does not establish a universal collection abstraction, quotient
type checker, higher-order function transport, or general resolver language.

## Normative meaning and bounded executable profile

The normative `ordered-map` Specification keeps the paper contract's three abstract
carriers, two operations, two observations, three equivalences, five laws, effect
contract, and persistence rule. It adds one optional performance proposition,
`put-amortized-constant`, solely to keep an unsupported concern visible. The
Specification never chooses a tree, hash table, object layout, mutation strategy,
stored key representative, or algorithm.

The exact `ordered-map-ascii-fold` profile supplies the finite observation domain used
by bounded test Evidence:

- input keys are the exact one-byte ASCII strings `A`, `a`, `B`, `b`, `C`, and `c`;
- two keys are equivalent exactly when their ASCII lowercase strings are equal;
- the serialized key-class token is that lowercase string: `a`, `b`, or `c`;
- values are JSON integers from `-2` through `2` under ordinary integer equality;
- histories contain at most three `put` operations and at most three live key classes;
- requests are single-threaded and lockstep; an observation must terminate within the
  exact `0.20` second per-response timeout and three-entry bound.

It also declares the exact performance vocabulary needed by the unsupported
`put-amortized-constant` proposition:

- workload `put-sequence`: start at `empty`; `n` is the number of consecutive `put`
  operations; for arbitrary `n >= 0`, apply `n` puts using keys and values from the
  profile domains;
- cost measure `realization-steps`: a primitive Realization step, summed across the
  workload; future performance instrumentation would report a nonnegative count for
  every `put` invocation;
- proposition: for `operationFamily: ["put"]`, there exist constants `a,b >= 0` such
  that for every `n >= 0` and every permitted length-`n` key/value sequence, total
  `realization-steps` is at most `a*n+b`;
- permitted Evidence methods: exactly `proof` and `proof-audit`.

The current adapter protocol does not report `realization-steps`, so neither a clean
campaign nor bounded timing can support the proposition. “Unsupported” therefore
means well-formed and unclaimed, not unspecified.

For this profile, `entries` returns a JSON sequence of exact objects
`{"class": <lowercase-token>, "value": <integer>}`. The `class` field identifies the
equivalence class; it is not a promise about which input spelling the Realization
stores or would return. This profile-specific quotient serialization closes the O-G1
`KeyClass` concern without claiming the current schema typechecks quotient signatures
or making ASCII folding normative for other profiles.

The smallest non-vacuous overwrite witness is exact:

```text
m0 = put(put(empty, "A", 1), "B", 2)
m1 = put(m0, "a", -1)
entries(m1) == [{"class":"a","value":-1},
                {"class":"b","value":2}]
```

`"A"` and `"a"` select one class; `"B"` selects an inequivalent class. Replacing the
first, non-last class changes its value but not its position. The concrete retained key
spelling is unobserved.

## Exact records, ownership, and source sets

All accepted records use version `0.1.0` and exact typed references. The canonical
OrderedMap manifest has explicit source roles and content digests; physical placement
does not transfer authorship.

| Source and role | Exact records | Ownership observation |
|---|---|---|
| `ordered-map-theory`, `theory-authored` | `specification/ordered-map` | the theory author owns observable meaning; no proof mechanism is privileged in this slice |
| `ordered-map-theory`, `dependency` | `realizationProfile/ordered-map-ascii-fold` | the finite execution/observation envelope is supplied, then explicitly selected by the package consumer |
| `ordered-map-rust`, `package-authored` | `realization/ordered-map-rust`; seven declaration-scoped Claims; seven Evidence records | the Rust package author owns its implementation packet, adapter assumptions, scope, exclusions, and reproduction metadata |
| `ordered-map-typescript`, `package-authored` | `realization/ordered-map-typescript`; seven declaration-scoped Claims; seven Evidence records | the TypeScript package author owns a separately represented implementation packet under the same exact campaign |
| `ordered-map-consumer`, `package-consumer-authored` | `consumerPolicy/ordered-map-bounded-policy` | the consumer owns priorities, accepted mechanisms, assurance token, exact profile, and effect-scope requirement |

Each package has one Claim and one Evidence record for each of:

```text
law:      lookup-empty, lookup-put-same, lookup-put-other,
          put-existing-position, put-new-appends
resource: persistence
effect:   ordered-map-effects
```

IDs use the deterministic forms
`ordered-map-{rust|typescript}-<declaration>` and
`ordered-map-{rust|typescript}-<declaration>-conformance`. Every Evidence record pins
its Claim, Specification, Realization, nested adapter selector, exact profile, campaign
report, runner, plan, inputs, sources, toolchain, review, assumptions, exclusions, and
bounded parameters. One green report can be provenance for multiple declaration-level
Evidence records, but it is never itself accepted Evidence and each declaration keeps
an independently inspectable result.

The nested adapter selectors are exactly
`ordered-map-rust-json-adapter/0.1.0` and
`ordered-map-typescript-json-adapter/0.1.0`, both naming
`ordered-map-runner-json-v1`. They are descriptors inside their Realization records,
not new canonical record kinds.

There is no Claim or Evidence for `put-amortized-constant`. No runner instrumentation
is inferred and the concern remains explicitly `unclaimed`/`optional`.

## Trusted product authority

Manifest membership and resolver rules are trusted product-integration inputs, not
authority supplied by theory, package, or policy actors. Each domain wrapper closes
over one immutable, canonical-JSON `ProductContract` with an ID, version, and SHA-256.
The OrderedMap contract is `ordered-map-product-contract/0.1.0`; its canonical content
pins:

- the exact canonical manifest path and SHA-256 plus permitted source selectors and
  roles;
- exact Specification and profile addresses and content digests;
- concern-to-declaration categories, the assurance token, accepted campaign mechanism,
  and effect-scope token;
- the exact accepted conformance-plan SHA-256 that establishes the
  `adapter-invocation-trace` scope;
- the recognized deployment interface string and its directional boundary
  classification.

Authority converges in stages without pretending future bytes already exist:

1. O3a owns the exact Specification, profile, and one canonical conformance-plan JSON
   artifact, then O-R3a reviews their bytes and digests. O3b controls consume that
   artifact directly and do not encode a second plan oracle.
2. O5 owns a separately identified theory-source manifest/authority for pre-execution
   publication and projection. Its results surface that provisional exact authority
   and do not claim final product convergence.
3. Only after O6 creates package records, reports, and Evidence can O6-G create the
   complete product manifest and final `ordered-map-product-contract/0.1.0`. O6-G then
   replays publication, registration, graph, and package views under the final
   contract before O7 resolution.

The product wrapper and repository gate pin the final ProductContract digest before
any Evidence is accepted into the complete product source set. Previously reviewed
reports/Evidence candidates remain outside final membership until that convergence.
Actor-facing publication, registration, resolution, and inspection entrypoints do not
accept contract overrides. Lower-level shared primitives require the complete contract
and fail closed on ID, version, digest, selector, manifest, plan, Specification,
profile, mechanism, effect-scope, or boundary mismatch. Every observation/result
surfaces product-contract ID/digest and manifest digest. A test may construct a
separately identified fixture contract, but cannot relabel it as the canonical product
contract.

Stack retains an independently pinned `stack-product-contract` compatibility wrapper
whose observable results and diagnostics stay unchanged. Extraction moves hard-coded
values into trusted immutable product integration; it does not make them caller policy.

## Author and consumer terminal outcomes

### Theory author: manifest-governed publication

At O5, given the theory-source-contract-pinned manifest and selected theory source,
publication inventories
only the two approved theory records, validates schema/link/content digests and roles,
and returns immutable exact addresses and provenance without following symlinks or
executing content. Missing, unexpected, moved, aliased, mutated, malformed, or
wrong-version records fail in the same input, graph, then membership phases as Stack.
O6-G must replay the same outcome under the complete ProductContract manifest before
it is final. The existing Stack entrypoint remains a compatibility wrapper over the
same manifest-driven observation and preserves its diagnostics.

### Package authors: independent registration and reproduction

Each package author supplies the exact theory source and one explicitly selected
package source governed by the same manifest. Registration validates the union and
returns theory/package roles by accepted address identity without building or running
the package. A separate documented reproduction command builds the candidate, runs
the exact campaign, and verifies the retained report before declaration-level Evidence
can be reviewed.

The two accepted private representations are deliberately different:

- Rust uses an immutable ordered sequence of `(class token, value)` pairs and linear
  class lookup;
- TypeScript uses an immutable class-to-value table plus a separate class-order
  sequence.

These choices are review facts, not normative semantics. Neither candidate may import
the other, the harness oracle, or a shared OrderedMap implementation. Shared protocol
framing is allowed; shared state-transition or expected-result code is not.

### Theory consumer: exact graph projection

Selecting `(specification, ordered-map, 0.1.0)` from the complete manifest graph shows
all declarations, specification-scoped Claims/Evidence, assumptions, exclusions,
support/challenge state, and every unknown. This slice publishes no
Specification-subject Claim or Evidence, so every declaration is honestly unclaimed in
the theory view. Realization-scoped conformance appears only in a separately labeled
package/consumer projection; it never becomes assurance about the Specification.
Operations and observation vocabulary do not become assured merely because package
laws have Evidence. The unsupported performance proposition remains visible. No
import, namespace merge, refinement, acquisition, proof-term interpretation, or
cross-version declaration lineage is inferred.

### Package consumer: policy-relative decision plus separate boundary

`ordered-map-bounded-policy/0.1.0` selects the exact Specification and
`ordered-map-ascii-fold/0.1.0` profile. It requires every declaration under
`law.conformance`, `resource.persistence`, and `effect.conformance`; accepts only
`bounded-conformance-campaign`; requires one accepted applicable support and no
selected challenge per declaration; and makes `performance` optional with proof and
proof-audit as its only accepted mechanisms. It separately prohibits `io.*` inside
the exact adapter-invocation trace scope.

Both accepted Realizations must resolve semantically acceptable when all seven exact
Evidence records support their declarations. Missing, inapplicable, unaccepted,
inconclusive, error, or challenging Evidence remains visible on its own axis and cannot
satisfy the requirement. The absent performance Claim remains visible and non-blocking.

The deployment observation is separately directional:
`consumer -> realization` uses `child-process-ndjson`, is non-direct, and says nothing
about semantic acceptability. The conformance adapter protocol and this deployment
boundary may currently share transport facts, but the resolver reports them as
different conclusions. A later deployment-profile tracer may introduce direct and
non-direct alternatives; this slice does not fake that distinction.

## Executable adapter and campaign boundary

The new protocol is named `ordered-map-runner-json-v1`; it is not an extension or alias
of `stack-runner-json-v1`. One explicitly supplied child process receives lockstep
UTF-8 NDJSON requests with exact `seq`, `op`, and `args` fields:

```json
{"seq":0,"op":"empty","args":{}}
{"seq":1,"op":"put","args":{"map":"h0","key":"A","value":1}}
{"seq":2,"op":"lookup","args":{"map":"h1","key":"a"}}
{"seq":3,"op":"entries","args":{"map":"h1"}}
```

No other request member, operation, or operation-specific argument is accepted. The
exact successful response shapes are:

```json
{"seq":0,"status":"ok","result":{"map":"h0"},"events":[]}
{"seq":2,"status":"ok","result":{"tag":"none"},"events":[]}
{"seq":2,"status":"ok","result":{"tag":"some","value":1},"events":[]}
{"seq":3,"status":"ok","result":{"entries":[{"class":"a","value":1}]},"events":[]}
```

`empty` and `put` return an opaque `map` handle. `lookup` returns exactly the tagged
`none` or `some` result above. `entries` returns the bounded class/value sequence.
An adapter error to a valid request has exact shape
`{"seq":n,"status":"error","error":{"code":s,"message":s},"events":e}` with
nonempty strings; it is always an execution error, not a semantic counterexample.
Every response echoes `seq`, has exactly one of `result` or `error`,
and carries that invocation's event list `e`, whose elements are ordered nonempty
event-class strings. Error responses may report nonempty events; those events remain
visible, but the invocation's overall Evidence contribution stays `error`. Stdout contains
only one response line per request; stderr is retained as diagnostic provenance but
has no semantic meaning. Handles retain stable observational denotation for the
session; handle identity, spelling, freshness, and stored key spelling have no meaning.

`seq` starts at integer `0` and increments by exactly one for every request. Requests
are never pipelined. The harness ends the session by closing stdin after the last
response; the adapter must then emit no more stdout and exit with status zero within
`0.20` seconds. Unexpected EOF, output before a request, missing or extra response
lines, extra stdout after close, invalid UTF-8/JSON/shape, sequence mismatch, timeout,
or nonzero exit is an execution `error`. An adapter error response to any valid request
is always an execution `error`, never `inconclusive` and never a semantic challenge.
Malformed client requests are outside v1; controls mutate adapter responses and
lifecycle behavior instead.

The harness owns ASCII class-token derivation, expected lookup results, expected entry
order, retained-handle observations, and effect matching. Adapters only translate and
execute requests. Malformed framing, timeouts, process failures, and adapter errors are
execution errors, not semantic counterexamples. An `io.*` event is a counterexample
only inside the adapter-reported invocation boundary; completeness and adapter
faithfulness remain explicit assumptions/exclusions.

O3a authors one immutable JSON plan artifact with algorithm
`ordered-map-conformance-campaign`, version `1`, response/exit timeout `0.20` seconds,
exact key and value domains above, maximum history three, maximum live classes three,
and observation limit three. It uses one schema-governed representation for logical
handle bindings, requests, expected results, per-invocation effect attribution, and
per-observation declaration attribution; JSON numbers use the canonical integer
spellings already required by the profile. Canonical sorted/minified JSON is hashed for
identity. O-R3a must reject any ambiguous encoding or second oracle before O3b exists.
O3b loads this artifact rather than reconstructing its cases; O6 Evidence must match
its reviewed digest exactly. The artifact instantiates exactly this case table:

| Case | Exact issued steps and expected observation | Declaration attribution |
|---|---|---|
| `lookup-empty` | `empty -> h0`; `lookup(h0,"A") -> none` | `lookup-empty` |
| `same-class-replacement` | `empty -> h0`; `put(h0,"A",1) -> h1`; `lookup(h1,"a") -> some(1)`; `put(h1,"a",-1) -> h2`; `lookup(h2,"A") -> some(-1)` | `lookup-put-same` |
| `other-class-preservation` | `empty -> h0`; `put(h0,"A",1) -> h1`; `put(h1,"B",2) -> h2`; `lookup(h2,"a") -> some(1)` | `lookup-put-other` |
| `nonlast-overwrite-order` | exact `m0`/`m1` witness above, then `entries(m1) -> [(a,-1),(b,2)]` | `put-existing-position` |
| `new-class-append-three` | `empty -> h0`; successive puts `("A",1)`, `("B",2)`, `("C",-2)`; final entries `[(a,1),(b,2),(c,-2)]` | `put-new-appends` |
| `retained-new-class-source` | retain `h1=[(a,1)]`; issue `put(h1,"B",2) -> h2`; re-observe only retained `h1` as `[(a,1)]` | retained-source observation: `persistence`; derived `h2` is not a persistence oracle |
| `retained-existing-class-source` | retain `h2=[(a,1),(b,2)]`; issue `put(h2,"a",-1) -> h3`; re-observe only retained `h2` unchanged | retained-source observation: `persistence`; derived `h3` is not a persistence oracle |

Every invocation in every case is also attributed to `ordered-map-effects`; a clean
candidate supports only the observation that no forbidden event was reported inside
those exact invocation traces. Optional absence is not required and unlisted events
remain visible under `default: unspecified`.

Transport mutations for malformed result, sequence, framing, timeout, process failure,
extra output, `debug.emit`, `io.read`, and an unlisted `network.send` event are exact
red-test controls around the canonical plan, not additional campaign cases and not
supporting Evidence. They must respectively establish protocol `error`, optional,
challenge, and unspecified classifications without changing plan identity.

The targeted reorder breaker uses the Rust protocol surface but moves an existing class
to the end. It must pass lookup and new-class append cases while challenging only
`put-existing-position` and scenarios that observe the changed class order. Breaker
source and its failed report remain retained test inputs outside canonical accepted
manifest membership; the report is not promoted to Evidence. A synthetic resolver
control binds a challenging declaration-level Evidence record to demonstrate that a
transport-compatible candidate is semantically unacceptable without contaminating the
accepted product source set.

## Shared-surface extraction boundary

O4 may extract only mechanics required by both accepted domains:

- supplied-manifest publication and package-registration authority;
- finite-source capture, phase barriers, exact membership/digest/role diagnostics;
- graph and theory projection parameterized by exact selectors;
- bounded concern-to-declaration coverage and Evidence-axis evaluation for the four
  already shared concern tokens;
- the immutable, digest-addressed ProductContract integration described above,
  replacing neither policy nor review authority and accepting no actor override;
- directional boundary classification from exact Realization metadata.

Stack-facing functions and diagnostics remain compatibility wrappers. Stack campaigns,
proofs, adapters, inspection prose, maintenance records, and domain laws stay local.
OrderedMap gets its own runner/protocol and domain campaign. No extraction may create a
universal resolver, execute registry records, weaken exact plan/report provenance, or
turn current string signatures into a type system.

## Maintenance successor and recovery

The append-only maintenance fixture adds exact
`(specification, ordered-map, 0.2.0)` and
`(consumerPolicy, ordered-map-bounded-policy, 0.2.0)` without mutating `0.1.0`. The successor adds a
`size` observation (number of live key-equivalence classes) and a required `size-put`
law: `size(put(m,k,v)) == size(m)` when `k` is equivalent to a live class, and
`size(put(m,k,v)) == size(m)+1` otherwise. It retains all predecessor declarations
byte-for-byte where practical but
asserts no declaration lineage or semantic-version compatibility.

The `0.2.0` policy pins the successor Specification and reuses the exact
`ordered-map-ascii-fold/0.1.0` profile; it cannot select the `0.1.0` Realizations. No
successor Realization, Claim, or Evidence is added. Resolution therefore succeeds as a
query with exactly zero exact-version candidates, rather than fabricating a partial
candidate or claiming specifically that only `size-put` is missing. Theory projection
shows `size`, `size-put`, and all other successor declarations unclaimed. The accepted
`0.1.0` policy and candidates remain recoverable by exact selectors with their original
explanations. The system does not automatically select the predecessor, migrate
Evidence, infer refinement, or define removal and reinsertion semantics.

## Review falsifiers and exclusions

Any successor review must reopen O-G2 if any of these observations can occur:

- a returned concrete key spelling becomes normative instead of the class token;
- `A` then `B` then overwrite through `a` can reorder without challenge;
- a candidate or adapter supplies the harness oracle;
- a green report, active Claim, accepted review, or profile match becomes assurance by
  itself;
- challenging Evidence is hidden because supporting Evidence exists;
- Stack Evidence or `0.1.0` Evidence satisfies OrderedMap or `0.2.0`;
- semantic acceptability is inferred from NDJSON/process compatibility or vice versa;
- publication/registration accepts undeclared membership, partial invalid input, moved
  ownership, symlink traversal, or execution;
- the optional performance proposition disappears or is reported supported;
- test-only breaker records enter accepted manifest membership;
- an O3b control reconstructs or mutates the reviewed O3a plan instead of consuming it;
- a theory-source authority is reported as final ProductContract convergence, or the
  final contract is created before every referenced manifest member and digest exists;
- an actor overrides the ProductContract, manifest trust root, accepted plan digest,
  concern mapping, effect scope, or boundary mapping;
- a theory projection presents realization-scoped conformance as Specification
  assurance;
- O4 generalizes Stack semantics rather than extracting a demonstrated shared seam.

Deletion, arbitrary key/value serialization, higher-order map/fold transport,
performance Evidence, concurrency, remote transport, discovery, hosted acquisition,
signatures, refinement, and human usability acceptance remain explicit exclusions.
