# Design spec 0004: finite user-defined resource composition inspection

## Contract status

Active draft for one stacked feature and one future pull request, based on ready PR #18
at `7b2f883f434155efd324f0bc92ae80e0514467d1`. This contract freezes only when its
complete experienceable PR opens. Revisions must record the observation that required
them; implementation convenience cannot turn this finite candidate into the project's
canonical resource logic.

## Felt user journey

A theory author can write one explicit resource composition algebra in PSpec, bind its
elements to exact resource declarations from the retained Stack and OrderedMap
Specifications, and inspect whether the finite authored operation is a commutative
monoid before any package or Evidence claims to realize it.

```text
nix develop --command python3 -m semantic_packages resource inspect \
  specs/persistence-composition.pspec \
  --dependency registry/stack/theory/records/stack-spec.json \
  --dependency registry/stack/theory/dependencies/stack-profile.json \
  --dependency registry/ordered-map/theory/records/ordered-map-spec.json \
  --dependency registry/ordered-map/theory/dependencies/ordered-map-profile.json \
  --resource retained-persistence \
  --output /tmp/resource-composition.json
```

The retained source imports both exact Specifications and defines one resource with a
finite four-element algebra: `none`, `stack-retained`, `ordered-map-retained`, and
`both-retained`. It explicitly authors the unit and all sixteen ordered composition
rows. Two bindings associate the exact Stack and OrderedMap `persistence` declarations
with their distinct elements. The command prints:

```text
inspected resource algebra retained-persistence: 4 elements, 16 compositions, 2 bindings, fold=both-retained; satisfaction unestablished -> /tmp/resource-composition.json
```

The report demonstrates that the authored table is closed, total over its finite
carrier, unital, commutative, and associative, and that folding the two bindings in
authored and reverse order yields `both-retained`. It does not establish that either
Realization satisfies persistence, that accepted persistence Evidence transfers into
this Specification, or that this algebra is suitable for arbitrary resources.

## Goal

Replace the current prose-only ceiling with the smallest inspectable user-defined
resource-composition candidate. Preserve resource meaning as authored Specification
data, make algebraic structure falsifiable, bind heterogeneous inputs explicitly, and
keep realization satisfaction and Evidence authority separate. Learn from one finite
cross-domain example before selecting partial composition, ownership, separation,
quantitative resource, graded, ordered, or higher-order semantics.

## Values and priorities

1. **Authored composition over a built-in resource taxonomy.** Carrier elements, unit,
   composition rows, and declaration bindings come from the named source; the checker
   supplies laws and diagnostics, not hidden semantic elements.
2. **Falsifiable structure over hosted algebra prose.** The existing `rule` remains
   hosted meaning. The finite operation is executable enough to refute closure,
   totality, unit, commutativity, or associativity.
3. **Explicit heterogeneous bindings over name resemblance.** Stack and OrderedMap
   `persistence` are selected by exact declaration references. Sharing a local ID does
   not merge them or imply an identity translation.
4. **Well-formedness over satisfaction.** A valid algebra and successful fold establish
   only structural inspection. Claims, Evidence, review, applicability, policy, and
   derived assurance remain separate axes.
5. **One candidate over a universal foundation.** `finite-commutative-monoid-v1` is a
   bounded experiment. It does not exclude partial commutative monoids, separation
   algebras, resource algebras with validity/core, semirings, quantales, QTT, ownership,
   linear capabilities, or domain-specific alternatives.
6. **Immutable predecessor domains over schema ripple.** Existing Stack/OrderedMap
   Specifications, runners, records, Claims, and Evidence remain byte-identical. The
   optional algebra surface is exercised only by the new importing Specification.

## Observable contract

### Authored source and schema surface

- `specs/persistence-composition.pspec` is a new exact PSpec v1 Specification with ID
  `persistence-composition`, version `0.1.0`, and exact imports of Stack `0.1.0` and
  OrderedMap `0.1.0`.
- It contains one resource declaration `retained-persistence`. The existing nonempty
  `rule` remains required. An optional `algebra` object adds only this candidate shape:
  `kind`, `carrier`, `unit`, `composition`, and `bindings`.
- `kind` is exactly `finite-commutative-monoid-v1`. `carrier` is a nonempty unique
  ordered list of local tokens. `unit` names one carrier element.
- Each composition row has exactly `left`, `right`, and `result`, all carrier tokens.
  Every ordered carrier pair must occur exactly once; document order is retained in the
  report but creates no evaluation precedence.
- Each binding has exactly one canonical `declarationReference` and one carrier
  `element`. The declaration reference must target a resource in an exact imported
  Specification supplied explicitly through `--dependency`.
- The optional schema addition does not change the canonical value of any existing
  Specification. A resource without `algebra` retains its current exact shape and
  meaning.

### Algebra and binding inspection

- The command reuses the existing representation-neutral PSpec authoring boundary and
  its strict phases: decode, schema, explicit dependency schema, and exact graph links.
  It does not implement a second PSpec parser or accept canonical defaults.
- Inspection selects exactly one caller-named local resource. Absence, ambiguity, or a
  resource without the candidate algebra fails.
- Structural checks require carrier uniqueness, unit membership, row shape, operand and
  result closure, exact `|carrier|²` ordered-pair coverage, and no duplicate pair.
- Law checks enumerate the finite carrier exactly: left/right unit for every element,
  commutativity for every pair, and associativity for every triple. The report retains
  the number of observations and the first deterministic counterexample on failure.
- Binding checks preserve authored order, reject duplicate exact declaration
  references, require resource-kind targets in exact imports, and require every bound
  element to belong to the carrier. Bindings are semantic mappings authored by this
  Specification; they do not transfer Claims or Evidence from the imported domains.
- The command folds binding elements from the authored unit in authored order and
  reverse order. For the retained source both yield `both-retained`. Equality of those
  two folds is a consequence/control of the inspected table, not a cross-domain
  satisfaction result.

### Report and failure behavior

- Success exits `0`, atomically writes one deterministic
  `resource-algebra-inspection-v1` JSON report, and emits the exact summary above.
- The report names source format and digest, Specification address and imports,
  resource ID and hosted rule, complete carrier/unit/composition/binding data, exact
  dependency and declaration bindings, structural/law observations, both fold traces,
  assumptions, exclusions, `algebraConclusion: finite-algebra-well-formed`, and
  `satisfaction: unestablished`.
- Algebra failure exits `1`, writes no partial report, preserves prior output, and emits
  one deterministic diagnostic naming the exact source pointer and the smallest
  counterexample. Raw/schema/link failures retain the authoring boundary's exact
  diagnostics. Required-argument failure exits `2`.
- Output may not alias the source or any explicit dependency. The command does not
  discover manifests, registries, versions, Claims, Evidence, profiles, policies,
  packages, or executable entrypoints and performs no network or child execution.

## Constraints and protected boundaries

- Preserve every accepted Stack and OrderedMap Specification, PSpec, successor,
  campaign plan, runner, fixture, report, Claim, Evidence, manifest, resolver result,
  consumer projection, refinement proposal/report, and effect-separation byte.
- Preserve current global declaration-ID uniqueness and exact import/link semantics.
  Algebra carrier tokens are resource-local and never become Specification declaration
  IDs or global record addresses.
- Do not infer a binding from equal resource IDs, prose, declaration order, import
  order, or Evidence concern strings. Only exact authored declaration references bind.
- Do not infer satisfaction, compatibility, refinement, Evidence transfer, policy
  acceptance, assurance, implementation composition, memory ownership, disjointness,
  frame rules, cancellation, validity, or resource availability.
- Do not make commutativity or totality mandatory for future resource mechanisms. They
  belong to this exact candidate kind only.

## Mechanism freedom

The contract fixes the PSpec surface, exact command, finite candidate meaning,
diagnostic phase behavior, report observations, and authority boundaries. It does not
prescribe internal dataclasses, table indexes, iteration implementation, serializer
layout below the report, reuse boundaries, or caching. A generic finite-algebra helper
is permitted only if its published authority remains the caller-named resource and
candidate kind.

## Falsifiers

The feature is false if any of these observations occur:

1. Existing Specification bytes or their authored outputs change merely because the
   optional algebra shape exists.
2. The retained PSpec cannot round-trip through the existing authoring boundary with
   the four caller-named exact context records: the two bound Specifications and the
   exact profile dependencies required to make those Specifications link-valid.
3. A missing, duplicate, extra, out-of-carrier, or defaulted composition pair passes,
   or source order changes pair identity.
4. A nonunital, noncommutative, or nonassociative table passes, including a law failure
   whose counterexample is hidden or nondeterministic.
5. A binding to an unimported, missing, wrong-kind, wrong-version, or duplicate exact
   declaration passes; equal local ID `persistence` creates an implicit merge.
6. Forward or reverse fold loses a binding, starts from a hidden unit, disagrees with
   the authored table, or yields something other than `both-retained` for the retained
   source.
7. Algebra well-formedness becomes resource satisfaction, Claim/Evidence transfer,
   resolver authority, compatibility, refinement, implementation composition, or a
   consumer decision.
8. The command discovers or executes registry/package metadata, accesses the network,
   mutates an input, aliases output to an input, or changes prior output on failure.
9. Documentation or output calls this candidate a universal resource algebra,
   separation logic, ownership model, quantitative resource semantics, or arbitrary-
   domain composition result.
10. Existing authoring, refinement, effect-separation, record/link, runner, campaign,
    Evidence, resolver, projection, maintenance, proof, or complete repository checks
    regress.

## Definition of done

- The exact documented command is experienceable from a clean checkout and produces
  the fixed summary plus a complete deterministic report.
- Refute-first controls derive from all ten falsifiers, including unchanged predecessor
  bytes, exact authoring/dependency phases, algebra structural/law counterexamples,
  binding authority, fold traces, atomic failure, and nonauthority language.
- A retained negative source changes one composition result so associativity fails with
  a stable smallest triple; dangling/wrong-kind binding controls fail in link/binding
  phases rather than being reclassified as algebra counterexamples.
- Independent reviews attack schema compatibility, algebra-law oracle independence,
  exact binding, phase ordering, hidden defaults, fold completeness, authority, and
  overclaim. Material concerns remain in the active ExecPlan until disposed.
- README, resource semantics, system map, actor journey, backlog, assumptions,
  exclusions, recovery, maintenance owner, and reopen triggers agree.
- One PR maps 1:1 to this frozen design spec and opens only when the author can run the
  complete source-to-report journey. Its description begins with the exact command and
  one line stating what is real underneath.

## Known exclusions

- This inspects one finite total commutative monoid table; it does not define partial
  composition, validity, core, order, implication, cancellation, frames, ownership,
  quantities, grades, effects, concurrency, allocation, deallocation, or time.
- Declaration bindings are authored semantic mappings, not proofs that two resource
  meanings are equivalent or that either imported resource is satisfied.
- The fold composes two authored elements, not runtime resources, implementation
  states, handles, memory regions, Evidence results, or consumer-selected packages.
- It does not register the new Specification, accept Evidence, alter policy/resolution,
  or establish semantic refinement from either imported Specification.
- One cross-domain example tests reusable inspection mechanics, not arbitrary resource
  or domain generality.

## Recovery and reopen triggers

Revert the eventual squash commit to remove the optional candidate shape, retained
source, inspector, and derived documentation. Existing Specification documents remain
valid and byte-identical throughout. Failed inspection preserves prior output so the
same explicit inputs can be corrected and rerun.

Reopen if a concrete user needs partial composition, invalid elements, core/duplication,
an order or implication operation, cancellation, resource transformations, quantities,
grades, ownership/frame reasoning, runtime observation, Evidence for algebra laws,
resolver consumption, or more than one algebra on a resource. Reopen rather than
silently encoding any of those in hosted `rule` text or candidate-specific defaults.

## Revision history

- **2026-07-22, revision 1:** Initial active contract. Selects the next authored backlog
  node after bounded effect separation. Introduces one explicit finite commutative-
  monoid candidate and exact cross-domain resource bindings while preserving existing
  Specification bytes and fixing satisfaction at `unestablished`. Not frozen for PR.
- **2026-07-22, revision 2:** First implementation observation corrected the finite
  authoring context from two to four caller-named records. The imported Stack and
  OrderedMap Specifications each reference an exact profile member, so their profile
  records are required for the accepted authoring boundary's link phase. The felt
  command now names both profiles explicitly rather than weakening graph validation or
  discovering transitive context. Resource bindings still target only the two exact
  imported Specifications. Not frozen for PR.
