# ExecPlan 0008: bounded effect-separation observation

## Purpose and observable outcome

Deliver design-spec 0003 as one complete two-domain evaluator tracer: a package author
or Evidence reviewer runs one retained command and sees that adapter-reported event
variation leaves each complete campaign's non-effect semantic projection unchanged,
while optional, forbidden, unspecified, and execution-error dispositions remain
distinct and visible.

This plan is stacked on draft PR #17 and exact base `78ecc5d`. It develops on
`agent/effect-classification-journey` without waiting for upstream merge. It must not
open a PR until the exact two-domain observation is experienceable and all falsifiers
pass.

## Governing sources and exact substrate

- `design-specs/0003-bounded-effect-separation-observation.md` owns the felt command,
  Goal/Values/Constraints, ten falsifiers, DoD, exclusions, recovery, and explicit
  revision history.
- `docs/vision/constitution.md`, `ARCHITECTURE.md`, `docs/design/core-model.md`,
  `docs/design/spec-language.md`, and `docs/design/evidence-model.md` preserve plural
  semantics, observable rather than implementation effects, Claim/Evidence separation,
  and unknown/exclusion visibility.
- ADR 0013 bounds effect absence to exact mechanism/provenance and the
  `adapter-invocation-trace`; it prohibits prose-derived or whole-process scope.
- The exact Stack campaign is `default_stack_conformance_plan()` and
  `fixtures/adapters/v1/fake_stack_adapter.py`. The exact OrderedMap campaign is the
  authenticated `contracts/ordered-map/conformance-plan.json` and
  `fixtures/adapters/ordered-map-v1/fake_ordered_map_adapter.py`.
- Design-spec revision 2 retains an intentional domain asymmetry: Stack `status-error`
  reports no event, while OrderedMap `adapter-error-forbidden` reports `io.read` before
  its adapter error. Both are execution errors and neither receives a projection
  comparison.

## Non-goals and protected boundaries

- Do not claim whole-process purity, contextual noninterference, general effect erasure,
  semantic equivalence, adapter completeness, or arbitrary-domain generality.
- Do not add a canonical effect algebra/row/handler, scope taxonomy, Evidence mechanism,
  Claim, policy token, resolver behavior, or registry-driven execution edge.
- Do not modify accepted Specifications, runners, exact campaign plans, adapter fixtures,
  reports, Claims, Evidence, manifests, decisions, or predecessor/successor actors.
- Do not normalize Stack and OrderedMap into one runner/report authority. Shared code may
  compare explicit domain-owned projections only after each exact runner completes.
- Do not hide event ledgers to demonstrate erasure; erasure is only equality of the
  explicitly defined non-effect semantic projection.

## Revisioned work-dependency DAG

```text
E0 design-spec 0003 and exact five-mode census
  -> E1 red command/report journey and negative controls
  -> E-R1 independent contract/projection review
  -> E2 exact campaign orchestration, projections, comparison, report, atomic command
  -> E-R2 independent implementation and overclaim review
  -> E3 README/effect semantics/system-map/user-journey/backlog maintenance
  -> E-G complete clean gate, design-spec freeze, and one experienceable stacked PR
```

| Node | Owner and exclusive boundary | Required evidence, downstream gate, stop condition |
|---|---|---|
| E0 contract/census | lead; design-spec 0003 and this plan only | exact Stack/OrderedMap modes, error asymmetry, fixed summary, ten falsifiers; E1; stop on runner/fixture contradiction |
| E1 red journey | lead/test owner; new effect-separation journey tests only | one intentional missing-probe failure plus successor controls for report, projections, classifications, errors, immutability, authority, and overclaim; E-R1; stop if projection cannot exclude only the exact effect concern |
| E-R1 | uninvolved read-only reviewer | attack projection completeness, oracle sensitivity, event retention, domain asymmetry, execution authority, phase/failure behavior, and red topology; E2 or explicit successor |
| E2 implementation | lead; new effect-separation module/probe script only | compose exact existing runners, immutable projections, stable report, atomic output, no registry metadata; E-R2; stop if an accepted runner/fixture must change |
| E-R2 | uninvolved read-only reviewer | executable counterexamples for semantic drift, concern spillover, error reclassification, event loss, hidden execution, Stack authority leakage, and overclaim; E3 or successor |
| E3 maintenance | lead; README and durable project memory | exact experience/failure/recovery, boundary/assumptions/exclusions, capability map, backlog disposition, known exclusions; E-G |
| E-G | lead; freeze and PR report | focused and complete clean gates, conventional range, validated metadata, 1:1 design-spec/PR, exact command and real-underneath line; stop before fragment PR |

## Exact observation matrix

| Domain | Role | Adapter mode | Expected events | Campaign/effect expectation | Projection authority |
|---|---|---|---|---|---|
| Stack | quiet | `reference` | none | supports / supports | baseline |
| Stack | optional | `optional-event` | `debug.emit: optional` per invocation | supports / supports | equals baseline |
| Stack | forbidden | `forbidden-event` | `io.read: forbidden` per invocation | challenges / challenges | equals baseline; only effect declaration challenges |
| Stack | unspecified | `unspecified-event` | `custom.audit: unspecified` per invocation | supports / supports | equals baseline |
| Stack | adapter-error | `status-error` | none | error / nonauthoritative | not compared |
| OrderedMap | quiet | `reference` | none | supports / supports | baseline |
| OrderedMap | optional | `optional-event` | `debug.emit: optional` per invocation | supports / supports | equals baseline |
| OrderedMap | forbidden | `forbidden-event` | `io.read: forbidden` per invocation | challenges / challenges | equals baseline; only effect declaration challenges |
| OrderedMap | unspecified | `unspecified-event` | `network.send: unspecified` per invocation | supports / supports | equals baseline |
| OrderedMap | adapter-error | `adapter-error-forbidden` | first `io.read: forbidden` | error / nonauthoritative | not compared |

Counts and repeated event multiplicity must come from exact reports, not the table's
human shorthand. E1 freezes the full ordered ledgers and exact projection values after
read-only census; an implementation may not satisfy the contract with only aggregate
counts.

## Implementation order and verification

1. Keep design-spec 0003 as the first branch artifact. Retain revision 2's corrected
   error-mode asymmetry before any plan/test/implementation claim.
2. Freeze an E1 predecessor derived from every falsifier. The single red reason names
   only the absent `scripts/effect_separation_probe.py`; controls for future behavior
   skip rather than fail until the observation module exists.
3. Obtain E-R1 PASS before implementing. Retain every BLOCK and successor in this plan.
4. Implement the smallest domain-owned projection adapters and comparison/report
   boundary. Reuse exact runners without changing their code or report shapes.
5. Run focused effect-separation, Stack campaign/runner, OrderedMap runner, report, and
   Evidence checks, then obtain E-R2 PASS.
6. Reconcile durable docs and run `python3 scripts/check_repo.py` from a clean exact
   head. Freeze design-spec 0003 only after all evidence passes.
7. Open one PR whose base is `agent/specification-refinement-journey` while PR #17 is
   open. Its description is the report and begins with the exact command and one line
   stating the adapter-invocation boundary that is real underneath.

Focused journey command:

```text
python3 -m unittest tests.journeys.test_e1_bounded_effect_separation -v
```

Complete gate:

```text
python3 scripts/check_repo.py
```

## Progress checklist

- [x] E0 design-spec 0003 revision 2 and exact five-mode census
- [ ] E1 red command/report journey and controls
- [ ] E-R1 independent contract/projection review
- [ ] E2 effect-separation observation and command
- [ ] E-R2 independent implementation review
- [ ] E3 durable documentation and maintenance
- [ ] E-G convergence, freeze, and one PR

## Discoveries and changed assumptions

- 2026-07-22: the authored backlog's first unconditional node after explicit refinement
  is effect classification plus erasure/noninterference tests. Earlier entries require
  new adapter-faithfulness, diagnostic, or orientation counterexamples; the resource
  algebra follows effect separation. This selects an authored route rather than a new
  product-direction preference.
- 2026-07-22: design-spec 0003 revision 1 incorrectly assumed both retained error modes
  report `io.read`. Exact pre-planning census showed Stack `status-error` reports no
  event while OrderedMap `adapter-error-forbidden` does. Revision 2 preserves the
  asymmetry and the shared rule: execution error establishes no semantic-projection
  comparison.
- 2026-07-22: existing adapter unit tests already classify optional, forbidden, and
  unspecified events, and OrderedMap already asserts forbidden concern locality. The
  missing product observation is an experienceable exact cross-domain comparison with
  durable report, assumptions, exclusions, failure behavior, and no overclaim.

## Result and remaining work

E0 is complete. No probe, comparison report, accepted Effect relation, new Evidence,
resolver behavior, or whole-process conclusion exists. E1 is the next released node.

## Stop and escalation conditions

- stop if a semantic projection can be made equal only by dropping a non-effect case or
  declaration outcome;
- stop if a forbidden event contaminates unrelated declaration outcomes in an accepted
  runner, because that is a predecessor contradiction rather than probe behavior;
- stop if implementation requires changing an accepted fixture, exact campaign, runner,
  report, Claim/Evidence record, resolver, or registry execution boundary;
- stop if an event-before-error cannot be retained without describing partial semantics
  as complete;
- escalate only a genuine choice about effect meaning, consumer policy, or expanding the
  observed boundary, not projection representation or serializer mechanics.
