# Design spec 0002: explicit refinement inspection journey

## Contract status

Frozen for one stacked feature and one pull request, based on draft PR #16. The complete
clean repository gate passed at `0931340` before freeze. Any later change must be
recorded in the revision history with the observation that requires it; the
implementation never silently changes the target.

## Felt user journey

A theory maintainer can author one explicit proposal relating two exact Specification
versions, run one command with both immutable Specification files named, and inspect a
complete cross-version declaration disposition without the tool inferring lineage,
compatibility, or semantic meaning from matching IDs or version strings.

The repository provides two deliberately different complete examples:

```text
nix develop --command python3 -m semantic_packages refinement inspect \
  refinements/stack-0.1.0-to-0.2.0.prefine \
  --predecessor registry/stack/theory/records/stack-spec.json \
  --successor registry/stack/successors/j5/theory/stack-spec.json \
  --output /tmp/stack-refinement.json

nix develop --command python3 -m semantic_packages refinement inspect \
  refinements/ordered-map-0.1.0-to-0.2.0.prefine \
  --predecessor registry/ordered-map/theory/records/ordered-map-spec.json \
  --successor registry/ordered-map/successors/o8/theory/ordered-map-spec.json \
  --output /tmp/ordered-map-refinement.json
```

The Stack report shows ten explicitly mapped declarations whose documents are
unchanged and one explicitly mapped changed effect contract: `metrics.emit` becomes
optional. The OrderedMap report shows eighteen explicitly mapped unchanged
declarations plus two explicit additions, observation `size` and law `size-put`.
Neither report says that `0.2.0` refines, is compatible with, replaces, or may inherit
Evidence from `0.1.0`; both say semantic refinement remains unestablished.

The maintainer can change, omit, duplicate, or mis-map one disposition and receive a
deterministic diagnostic at the proposal path and exact declaration reference. A
corrected proposal can be rerun without changing either Specification.

## Goal

Make cross-version reasoning start from an explicit, reviewable relation between exact
semantic artifacts rather than semantic-version syntax, repeated local IDs, directory
placement, or automatic predecessor discovery. Demonstrate one complete author/check/
inspect loop across two real successor shapes while preserving the boundary between a
structural proposal and an evidence-backed semantic compatibility conclusion.

## Values and priorities

1. **Explicit relation over version folklore.** `0.1.0` and `0.2.0` are opaque exact
   versions; neither ordering nor compatibility follows from their spelling.
2. **Complete disposition over convenient diff.** Every predecessor declaration is
   explicitly mapped or removed, and every successor declaration is explicitly mapped
   or added. Reused local IDs never create continuity by themselves.
3. **Obligations over premature verdicts.** Exact structural equality and difference
   are observable; semantic refinement, substitutability, and Evidence transfer remain
   unestablished until separately governed Claims and Evidence support them.
4. **Plural semantics over one refinement logic.** Algebraic declarations, hosted
   laws, effects, resources, observations, and performance propositions retain their
   distinct shapes. The command does not interpret all of them through one logic.
5. **Two-domain asymmetry over toy sameness.** Stack changes an existing effect
   contract; OrderedMap conservatively adds an observation and law at the document
   level. The journey must preserve that difference rather than force one result.
6. **Reversibility over canonical expansion.** The first proposal surface and report
   establish the user need without yet adding a canonical registry kind or changing
   resolver behavior.

## Observable contract

### Explicit proposal

- A `.prefine` input is UTF-8 TOML with explicit proposal identity and version, exact
  predecessor and successor Specification addresses, and the expected SHA-256 of each
  supplied raw Specification file. Digests bind the reviewed campaign bytes for
  provenance; they do not replace record identity.
- Each declaration reference explicitly names its family and local ID. The effect
  contract is addressed as family `effects` plus its declared local ID. Array position,
  source order, and matching spelling have no addressing authority.
- Every predecessor declaration appears exactly once as the source of a mapping or a
  declared removal. Every successor declaration appears exactly once as the target of
  a mapping or a declared addition. A mapping may cross local IDs only when both exact
  references are written; it may not cross declaration families.
- Additions and removals are explicit dispositions, not entries inferred solely from
  an implementation diff. The checker compares the supplied exact documents against
  the authored complete disposition and rejects omissions, duplicates, dangling
  references, family mismatches, or overlaps.
- A mapped pair is reported `document-unchanged` only when the two declaration JSON
  values are equal as documents after ignoring their array position. Otherwise it is
  reported `document-changed`. This is a structural observation, not semantic
  equivalence or incompatibility.
- Hosted law text, effect patterns, signatures, resource rules, and performance
  predicates remain opaque values. The command may report exact equality or change but
  never interprets their meaning.

### Inspection command and report

- `python3 -m semantic_packages refinement inspect PROPOSAL --predecessor PREDECESSOR
  --successor SUCCESSOR --output OUTPUT` is the documented entry point. All four paths
  are explicit; there is no version discovery, registry search, implicit latest,
  directory convention, or write outside `OUTPUT`.
- The command validates raw UTF-8/TOML/JSON, duplicate members, Specification schema,
  exact addresses/digests, proposal coverage, and declaration references before
  publishing a report. Failure is all-or-none, exits `1`, emits deterministic
  `CODE PATH#POINTER: MESSAGE` diagnostics, and preserves any existing output.
  Command-usage failure exits `2`; success exits `0` without diagnostics.
- Success atomically writes one stable JSON inspection report containing proposal
  identity, exact predecessor/successor addresses and observed raw digests, mappings
  with `document-unchanged` or `document-changed`, additions, removals, and the fixed
  conclusion `semanticRefinement: "unestablished"`.
- Report order follows explicit proposal disposition order. Reordering declarations in
  a Specification while updating its reviewed digest cannot manufacture, erase, or
  reorder an authored relation.
- The report contains no selected Realization, migrated Claim/Evidence, inferred
  declaration lineage, resolver choice, automatic fallback, or compatibility verdict.

### Exact examples

- The Stack proposal binds predecessor raw digest
  `dd083a71a4631cc44be051a16b8e20ff0cee7199e46d3823322665d1fdeec6c1`
  and successor raw digest
  `070a9c7aff764ad6acbbd7b3deb8e32026164c12db85936cc0f2627927035aa8`.
  It explicitly maps all eleven declarations. Ten report unchanged; the
  `effects/stack-effects` mapping reports changed. There are no additions or removals.
- The OrderedMap proposal binds predecessor raw digest
  `6049d371603cbdac0e722685f1fd25c7369872f7d963ae2e4f4bae90cce7fd7f`
  and successor raw digest
  `05bd1dee68216834a81e9095425905a3fb5a5c93530bbe2479c07ef1a6a3afd0`.
  It explicitly maps all eighteen predecessor declarations unchanged and explicitly
  adds `observations/size` and `laws/size-put`; it removes nothing.
- The README provides both copy-paste commands, expected summaries, one disposable
  mis-mapping failure/recovery exercise, the fixed unestablished conclusion, and the
  boundary between structural continuity and semantic compatibility.

## Constraints and protected boundaries

- Preserve every accepted Stack and OrderedMap predecessor/successor byte. Proposal
  inputs and generated reports never rewrite canonical Specifications or manifests.
- Preserve exact `(kind, id, version)` identity, flat declaration IDs within each
  Specification version, and the rule that reused IDs do not imply continuity.
- Preserve ADR 0005 exact typed references, ADR 0007 import-edge limits, ADR 0014's
  bounded successor-source semantics, and the existing Stack/OrderedMap maintenance
  results. Do not add `latest`, ranges, semver ordering, or automatic fallback.
- Keep semantic compatibility separate from directional realization/interoperation
  compatibility. This journey does not inspect Realization metadata or execution
  boundaries.
- Do not migrate, inherit, repoint, or manufacture Claims or Evidence. Historical
  Evidence remains bound to its exact predecessor Claim and Specification.
- Do not establish a canonical Refinement record kind, resolver edge, universal
  refinement calculus, declaration namespace merge, or migration engine in this slice.
- Do not infer that an added law is conservative, that a relaxed optional effect is
  compatible, or that exact declaration equality proves substitutability.

## Mechanism freedom

The contract does not prescribe parser architecture, internal diff representation,
data classes, indexing strategy, report serializer, module layout, or optimization.
Any mechanism is acceptable if it upholds the complete explicit-disposition journey,
stable diagnostics, exact examples, and protected boundaries.

## Falsifiers

The feature is false if any of these observations occur:

1. The exact Stack proposal does not report ten unchanged mappings, one changed effect
   mapping, zero additions/removals, and semantic refinement unestablished.
2. The exact OrderedMap proposal does not report eighteen unchanged mappings, two exact
   additions, zero removals, and semantic refinement unestablished.
3. Version spelling, path, source order, or a reused local ID creates a mapping,
   successor choice, compatibility conclusion, or declaration continuity not authored
   in the proposal.
4. A missing, duplicate, overlapping, dangling, or wrong-family disposition succeeds
   or yields a partial report.
5. A substituted Specification address, raw digest, kind, or changed campaign byte is
   accepted under an unchanged proposal.
6. Invalid UTF-8/TOML/JSON, duplicate keys/members, schema-invalid Specifications, or
   ordinary parser limits escape as tracebacks, mutate output, or skip their phase.
7. Reordering Specification declaration arrays, with the reviewed digest updated,
   changes explicit mapping identity or report order.
8. A changed hosted string, signature, effect contract, resource rule, or performance
   proposition is interpreted as proof of semantic compatibility or incompatibility.
9. The command discovers versions, falls back to a predecessor, executes artifacts,
   resolves a package, or migrates/repoints Claims or Evidence.
10. Existing authoring, Stack/OrderedMap maintenance, consumer, resolver, campaign,
    Evidence, record, or proof checks regress.
11. Documentation or output describes two examples as arbitrary-domain generality, a
    universal refinement logic, a canonical relation, or a merge/upgrade decision.

## Definition of done

- Both documented commands are experienceable from a clean checkout and produce the
  exact bounded reports above.
- Focused red/green journey controls derive from all eleven falsifiers, including
  all-or-none output, explicit complete coverage, semver/ID nonauthority, reordered
  declaration metamorphism, and no Evidence migration.
- The complete repository gate passes without weakening any predecessor assertion.
- Documentation states exact steps, report meaning, failure recovery, exclusions,
  maintenance owner, and reopen triggers.
- An independent review attacks the proposal completeness model, change
  classification, source/digest authority, semantic overclaim, two-domain boundary,
  and all existing maintenance regressions; every material concern is dispositioned.
- One PR maps 1:1 to this frozen design spec, opens only when the complete two-domain
  journey is experienceable, and reports exact steps plus what is real underneath.

## Known exclusions

- This slice authors and inspects a refinement proposal; it does not accept a semantic
  refinement relation or assert cross-version compatibility.
- It does not define declaration lineage beyond the exact mappings inside one proposal,
  and does not make those mappings canonical registry authority.
- It does not define a logic for proving refinement, Claim/Evidence shapes for a
  refinement proposition, Evidence transfer rules, migrations, deprecations, version
  ranges, automatic upgrade, resolver preference, or realization compatibility.
- Two exact successor pairs demonstrate reusable mechanics and contrasting change
  shapes, not arbitrary-domain or universal refinement generality.

## Recovery and reopen triggers

Revert the eventual single squash commit to remove the proposal surface, inspector,
and reports; all accepted exact successor and recovery actors remain unchanged. Failed
inspection preserves existing output, so a maintainer can correct the proposal or
explicit paths and retry.

Reopen this contract if a proposal cannot express a concrete third change shape,
semantic refinement Claims/Evidence require a canonical relation record, declaration
splits/merges require non-bijective mappings, imports require signature morphisms, or
consumer upgrade decisions require a separately governed compatibility policy.

## Revision history

- **2026-07-22, revision 1:** Initial active contract. Selects the next authored
  roadmap node after the PSpec journey and grounds it in the accepted Stack effect-
  change and OrderedMap additive successor. It freezes a complete explicit proposal
  and inspection experience while leaving semantic refinement unestablished and the
  realization free. Not yet frozen for PR.
- **2026-07-22, revision 2:** Freeze the unchanged observable contract after both
  independent implementation reviews and the complete clean repository gate passed.
  The output/input-alias counterexample was corrected below the mechanism-freedom line;
  it strengthens the existing immutable-input requirement without changing the user
  journey, conclusion, or known exclusions.
