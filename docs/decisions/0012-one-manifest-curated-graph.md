# ADR 0012: One manifest owns the curated graph boundary

## Status

Accepted by J3-G in ExecPlan 0002. J3-DR0 and J3-DR1 retain the rejected wording;
J3-DR2 accepted the design successor, J3-F1R rejected controls that would have
reintroduced hidden role/source oracles, and J3-F2/I1/M1 plus the full locked gate
demonstrate one 24-record authority without resolver or execution behavior.

## Context

J1 and J2 accept four theory records and two independent nine-record package sets, but
publication and registration currently repeat exact address, digest, and role maps in
product code. Those maps are bounded tracer predicates, not a sustainable canonical
graph. Later resolver and browser views must consume one honest source set without
turning fixture history, filesystem layout, test constants, a report, or a projection
into a competing truth.

The accepted 22 records also do not yet contain the consumer-owned policy required by
J4P or the second Specification required to demonstrate J4T's exact import. Deferring
either artifact until after J3 would require a downstream consumer to mutate or bypass
the graph that J3 is meant to canonize.

## Decision

For the Stack tracer, `registry/stack/manifest.json` is the sole runtime authority for
curated membership, expected source digest, source ownership, and explanatory role.
Its narrow conceptual shape is:

```text
formatVersion: 1
sources[]: { id, root, roles[] }
members[]: { source, address: { kind, id, version }, sha256, role }
```

Source roots are safe, relative, non-overlapping paths beneath the manifest's registry
boundary. Each source declares the subset of canonical explanatory roles its packet
may contain. Member entries do not name record filenames: observed paths remain
provenance, and a byte-preserving rename within one source does not change membership,
identity, or role. Source, role, and member array order carries no meaning. Source IDs,
addresses, and member assignments are unique; digests are exact SHA-256 values.

The closed J3 role vocabulary is `theory-authored`, `dependency`, `package-authored`,
and `package-consumer-authored`. The theory packet permits the first two; each package
packet permits only `package-authored`; the policy packet permits only
`package-consumer-authored`; and the separate composition-theory packet permits only
`theory-authored`. A member role outside both this enum and its source's declared subset
is invalid. Source membership governs validity; a misplaced exact record retains its
address-owned role in the explanatory inventory while producing missing and unexpected
diagnostics.

Canonical record bytes continue to own `(kind, id, version)` and all semantic content,
as required by ADR 0005. The manifest repeats the address only as a checked selector;
disagreement is a deterministic diagnostic and never retargets the record. Digests
bind the selected bytes but do not replace author identity.

The accepted J3 graph will contain the 22 J1/J2 records plus two separately owned and
reviewed records: one package-consumer ConsumerPolicy suitable for the bounded J4P
query, and one theory-author composition Specification with an exact import of Stack
for J4T. The theory consumer selects and inspects that second Specification; creating
its semantics remains theory-author authority, even if one person occupies both roles.
It must contain at least one meaningful declaration accepted by the current schema;
an empty declaration array or schema/checker weakening is not an import demonstration.
Their concern owners author the semantics; the graph integrator only validates and
includes them.

Graph assembly first lstat/loads/validates the supplied manifest without following it
or any ancestor symlink. A manifest input/shape failure returns only manifest-phase
diagnostics and performs no source-root I/O. On success it snapshots that manifest,
observes only its declared roots through the governed finite-source boundary, preserves
the record input/schema phase barrier, validates the whole record graph, and compares
observed membership and digests per source. Each inspection is an uncached snapshot:
later filesystem mutation cannot change the returned value, while a new inspection
reloads both manifest and records. It returns deterministic, immutable records and
diagnostics without executing proof tools, adapters, campaigns, build instructions,
or record metadata.

The assembled graph is the sole canonical **record source** for J4. It is not a hidden
default query: J4P must explicitly select exact ConsumerPolicy and RealizationProfile
addresses, and J4T must explicitly select an exact Specification address from a
successful supplied graph. Neither consumer accepts filesystem roots or private maps.

J1 publication and J2 registration must derive their accepted membership, digests,
and roles from this manifest without weakening their existing no-follow, root-ownership,
rename, phase-barrier, totality, or no-execution contracts. Tests retain independent
oracles; product modules retain no second literal selection or digest map. A shared
manifest module may materialize one immutable canonical projection for these legacy
APIs at module import; its missing/malformed diagnostics and reload boundary are frozen,
and the unknown-selector call performs no additional manifest or root I/O.

The manifest's canonical roles remain unchanged in graph and J2 observations. J1's
accepted legacy presentation is an explicit shared view projection only:
`theory-authored -> authored` and `dependency -> dependency`. This compatibility view
does not select members or redefine ownership, lives beside the manifest loader rather
than in publication, and is independently tested so it cannot become a hidden second
role authority.

The manifest contains no Evidence disposition, assurance, policy evaluation, selected
profile, resolver result, compatibility conclusion, command, entrypoint, or acquisition
instruction. A ConsumerPolicy is a canonical record in the graph, not policy encoded
by the manifest. Graph validity is not Evidence acceptance or assurance.

## Alternatives and dissent

- Listing addresses without digests would leave J1/J2's accepted immutable-source
  predicate in another product map or an additional lock file. That preserves the
  second source J3 exists to remove, so digests remain in the manifest.
- Deriving roles only from record kind, directory spelling, or observed root repeats
  representation leaks already rejected by J2-R1/R2. The supplied profile dependency
  is a curation fact rather than a universal `realizationProfile` rule, so roles remain
  explicit and source-constrained.
- Binding each member to a filename would make incidental layout semantic and break
  accepted byte-preserving rename behavior. The manifest names source roots, not files.
- Deferring the ConsumerPolicy and importing Specification to J4P/J4T keeps J3 at 22
  records, but then downstream consumers would own canonical-graph mutations or read
  outside their supplied graph. A separate package-consumer policy node and
  theory-author composition node inside J3 are the smaller honest boundary.
- Assigning the importing Specification to a theory consumer would move semantic
  authorship across the actor contract. It is theory-author/composition work; the
  consumer's authority begins at exact selection and import inspection.
- An imports-only record would be locally smaller, but the current Specification schema
  correctly rejects it as empty. J3 will author meaningful minimal content or stop and
  propose a separately reviewed language change; it will not exploit empty arrays.
- A generated Python constant could make import behavior simple, but the generated
  artifact would be another runtime selection source unless generation and freshness
  became a separately governed build boundary. Direct derivation remains the tracer
  choice.

## Consequences

- The product has one finite, inspectable answer to “which exact bytes form this graph?”
- Whole-source relocation requires a manifest root change; member renames within that
  source remain provenance-only.
- Publication, registration, graph assembly, and both future projections can be
  challenged against one membership boundary while retaining distinct actor outcomes.
- Consumer policy authorship and theory-author composition authorship become explicit J3
  work nodes rather than hidden graph-integrator decisions.
- Literal test oracles, proof manifests, W4 reports, source/binary/toolchain bindings,
  and Evidence review fields remain independent evidence layers, not duplicate product
  selectors.
- Quiescent-tree trust, private finite-source coupling, fixture-backed proof provenance,
  and the bounded W4 byte bridge remain declared debt.

## Revisit conditions

Revisit before hosted or federated publication, signatures, content-addressed storage,
multiple publisher manifests, untrusted concurrent filesystem traversal, successor
selection, policy composition, or any requirement for per-record acquisition paths.
Reopen J3 if a product consumer needs a record outside the manifest, a second runtime
selection map appears, or source roles cannot express a demonstrated ownership case.
