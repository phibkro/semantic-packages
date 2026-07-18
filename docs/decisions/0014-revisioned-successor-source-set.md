# ADR 0014: Revisioned successor source-set authority

## Status

Accepted by J5-G in ExecPlan 0002 after implementation successor `56c4114`, all 12
frozen J5 controls, the bounded J5-R1 Fable 5 advisor replay, and the full locked
repository gate passed. The advisor's PASS supports but does not ratify this lead
acceptance act.

## Context

The accepted Stack product graph is one manifest-governed snapshot of 24 exact records.
J5 must introduce an exact successor while retaining the predecessor as selectable
product state. Mutating `registry/stack/manifest.json` would rewrite accepted history;
copying all predecessor records would create drifting byte-level truths; and a runtime
overlay would add an unreviewed merge authority and implicit succession semantics.

Exact-version references already prevent old Evidence from satisfying a differently
versioned Claim when link coherence and resolver selection hold. The J5 phrase “stale
until rerun” therefore needs one explicit tracer meaning: exact-bound predecessor
Evidence remains historical and browseable but is not selected for successor addresses.
This is not a general freshness, expiry, lineage, or semantic-version relation.

## Decision

Keep `registry/stack/manifest.json` and all 24 predecessor record bytes immutable. Add
`registry/stack/successor-manifest.json` beside it as an append-only snapshot revision.
Each graph observation receives exactly one explicit manifest path; product code gains
no successor default, overlay, composition step, version range, or implicit `latest`.

The successor manifest shares the predecessor source roots and repeats all predecessor
member entries. Every repeated source and member entry must be field-identical to the
predecessor manifest. A frozen cross-manifest control independently enforces that
append-only invariant, including a mutation that changes one repeated digest. Shared
record roots are load-bearing: byte drift makes both exact digest bindings fail rather
than allowing separately copied histories to diverge while individually green.

Successor records live under actor-owned roots beneath `registry/stack/successors/j5`:
theory, Rust package, and package-consumer packets use the existing authorship roles.
Succession is a version fact, not a new role. Source IDs remain safe single segments.

The bounded successor snapshot adds seven exact records and no Evidence: Stack
Specification 0.2.0 with one honest semantic revision, Rust Realization 0.2.0, bounded
ConsumerPolicy 0.2.0, and four active realization-scoped Claims covering the two laws,
persistence rule, and effect declaration. It deliberately reuses exact profile
`stack-default` 0.1.0. Reuse demonstrates that staleness follows changed governing
addresses rather than ritual version bumping. Optional performance stays claim-free and
unsupported. Claims without Evidence are honest propositions; no Evidence record may
be authored without a real observation.

Recovery is evaluated inside the successor snapshot: exact 0.1.0 selectors remain
acceptable while exact 0.2.0 selectors are explainably unsupported. The projection
shows the successor Specification without inheriting the 0.1.0 proof. Old Evidence
addresses appear in history but in no successor disposition. Claim `retired` and
`withdrawn` states are exercised as publication lifecycle independently of Evidence
result/review and without mutating predecessor bytes.

## Alternatives and dissent

- Mutating the predecessor manifest keeps only Git history, not selectable predecessor
  product state. Rejected.
- Copying all predecessor records under the successor tree permits two byte sets to
  drift independently. Rejected.
- Runtime overlay or manifest composition adds a trusted merge rule and implicit
  selection behavior. Rejected for the tracer.
- A general staleness/freshness engine would require time, lineage, or compatibility
  semantics not demonstrated by J5. Exact nonselection is sufficient and narrower.
- Fabricating challenging or error Evidence to dramatize failure would violate the
  evidence model. Absence of successor Evidence is the honest failed-successor state.

## Consequences

- Predecessor and successor are two immutable graph snapshots, not two simultaneous
  authorities inside one observation.
- Repeated manifest metadata moves from convention to a test-enforced derivation rung.
- The existing resolver and theory projection remain the actor-visible recovery views;
  maintenance does not create a competing truth.
- No semantic compatibility, declaration lineage, automatic migration, expiry, or
  hosted acquisition conclusion is created.

## Revisit conditions

Revisit before a third manifest, hosted or federated acquisition, manifest composition,
implicit successor discovery, content-addressed snapshot derivation, signatures, or a
demonstrated need for time/freshness/TTL semantics.

Stop J5 if any predecessor byte changes, if product code defaults to the successor
manifest, if re-pointed old Evidence can become a graph-valid supporting successor
record, if a census control is weakened without a red-first successor, or if Evidence
would be authored without an actual observation.
