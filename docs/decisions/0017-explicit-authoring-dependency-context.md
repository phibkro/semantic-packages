# ADR 0017: Explicit finite authoring dependency context

## Status

Proposed for ExecPlan 0006 A3 independent contract review.

## Context

ADR 0016 requires a successful authoring observation to return one schema- and
link-valid canonical Specification document. Its boundary diagram named source bytes,
an exact format token, and an opaque source label, but did not name the graph context
needed to establish external references.

Both retained domains make that omission observable. The accepted Stack and OrderedMap
Specifications each contain workload and cost-measure references to a separate
`realizationProfile` record. Checking either Specification alone yields two exact
`LINK_DANGLING_REFERENCE` diagnostics. Discovering the profiles from paths, manifests,
the registry, or spelling would add hidden ambient authority and make authoring depend
on deployment layout.

## Decision

Clarify the representation-neutral boundary as:

```text
source bytes + exact format token + opaque source label
  + ordered finite dependency records with opaque labels
  -> exact canonical Specification document | ordered diagnostics
```

- The caller supplies the complete finite dependency context explicitly. There is no
  filesystem, manifest, registry, network, version, or profile discovery and no
  default dependency.
- Each dependency is one canonical record document plus an opaque diagnostic label.
  The boundary schema-validates the source and dependencies, then link-validates their
  isolated graph. A successful result establishes validity only relative to that
  exact supplied context.
- Source and dependency labels locate diagnostics only. They cannot alter document
  identity, content, ordering, references, selection, or authority.
- Dependency input order controls deterministic dependency-schema diagnostic traversal
  only; it creates no canonical record identity or semantic priority. Source-record
  diagnostics precede dependency-schema diagnostics, and any schema failure suppresses
  link conclusions. Once every record is schema-valid, link diagnostics retain the
  existing `(path, pointer, code)` order. Duplicate canonical addresses remain graph
  errors attributed to the later duplicate in dependency input order.
- The returned document is the authored Specification only. Dependency records are
  context, not inferred output, copied declarations, imports, or Evidence.
- The all-or-none result and raw-phase precedence from ADR 0016 remain unchanged.
- Raw failures retain the source label and root pointer plus stable actionable detail:
  a byte offset for invalid UTF-8, line/column/character for malformed JSON, and the
  repeated key for a duplicate member.

## Consequences

- A3 can truthfully require exact Stack and OrderedMap round trips without weakening
  link validity or smuggling registry discovery into A4.
- A4 receives one additional required `dependencies` input. Empty context is valid as
  an explicit choice but makes the retained Specifications fail closed at their exact
  external reference paths.
- A later author workflow may assemble this finite context for convenience, but that
  adapter must make its acquisition and selection authority explicit; it cannot hide
  those choices inside the representation-neutral elaborator.

## Rejected alternatives

- **Schema-valid output with unresolved external references:** weakens ADR 0016's
  accepted success condition and postpones an author-visible failure.
- **Read profiles from the repository or manifest:** couples the boundary to ambient
  layout and lets external state affect authoring meaning.
- **Infer a profile from the Specification ID or format:** introduces the exact hidden
  defaults rejected by A1 and A2.
- **Return the entire context graph:** changes a Specification-authoring boundary into
  publication and obscures which document the author produced.

## Reopen triggers

Reopen if canonical Specification records become closed under references, if a later
surface has an independently governed acquisition authority that must be composed with
authoring, or if human observation shows that explicit context cannot support a usable
workflow without changing the boundary.
