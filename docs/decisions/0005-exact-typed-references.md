# ADR 0005: Exact typed references

## Status

Accepted for ExecPlan 0001.

## Context

The tracer bullet must link specifications, realizations, claims, evidence, profiles,
policies, and addressable declarations without silently retargeting records. Bare names,
array positions, implicit latest versions, and version-range resolution each permit a
reference to change meaning without new evidence.

## Decision

Address a canonical record by the exact tuple `(kind, id, version)`. Treat `id` and
`version` as opaque strings and permit the same ID at multiple exact versions. Every
reference carries all three fields. A declaration reference additionally carries the
enclosing specification's exact address and a local declaration ID from one flat
namespace per specification version.

Schemas validate shape. Link checking rejects duplicate addresses, duplicate local
IDs, dangling or wrong-kind targets, and incoherent redundant scope. Version or local-ID
reuse never implies semantic compatibility; that requires an explicit evidence-backed
relation. Content digests record provenance and immutability observations but do not
replace author-assigned identity.

## Alternatives and falsifiers

- Bare string references create an unvalidated delimiter language and cannot express
  target kind or local declaration scope reliably.
- Unpinned or ranged references can retarget claims and evidence without rerunning
  their gates.
- Array-position references change target when unrelated declarations are reordered.
- Globally unique IDs discard useful kind context and still do not solve version
  pinning; per-kind IDs with explicit typed references remain unambiguous.

Negative fixtures for each route belong to the record/link gate.

## Consequences

- Record lookup and diagnostics have one exact key.
- Cross-version compatibility remains explicit and separately evidenced.
- Reordering and projection do not change reference meaning.
- The tracer bullet does not select a global registry namespace or final identifier
  syntax.

## Revisit conditions

Revisit after the tracer bullet if content-addressed records, federated namespaces, or
cross-version declaration lineage demonstrate a requirement not representable as an
additional explicit relation.
