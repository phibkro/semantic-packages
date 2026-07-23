# ExecPlan 0008: bounded effect-separation observation

## Purpose and observable outcome

Deliver design-spec 0003 as one complete two-domain evaluator tracer: a package author
or Evidence reviewer runs one retained command and sees that adapter-reported event
variation leaves each complete campaign's non-effect semantic projection unchanged,
while optional, forbidden, unspecified, and execution-error dispositions remain
distinct and visible.

This plan is stacked on draft PR #17 and exact base `bc8607b`. It develops on
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
- [x] E1 red command/report journey and controls
- [x] E-R1 independent contract/projection review
- [x] E2 effect-separation observation and command
- [x] E-R2 independent implementation review
- [x] E3 durable documentation and maintenance
- [x] E-G convergence, freeze, and one PR

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
- 2026-07-22: E1's first executable census rejected an assumed round Stack event
  multiplicity. Each complete eventful Stack campaign retains exactly 177 invocation
  events; OrderedMap retains 30. The oracle now derives from the exact runners and the
  initial red topology was two passing substrate controls, one intentional absent-probe
  failure, and seven skipped successor controls.
- 2026-07-22: E-R1 initially BLOCKed three false-positive paths: empty domain-shaped
  projections could satisfy key/equality checks, count-only ledgers could lose ordered
  event detail, and displayed fixture metadata could disagree with actual execution.
  E1 now independently serializes and compares every native non-effect outcome and
  event, asserts all ten exact runner calls in order, and rejects auxiliary file,
  process, or network authority during mocked evaluation. The review remains open
  until the reviewer attacks the strengthened successor.
- 2026-07-22: the remaining E-R1 counterexamples required symmetric OrderedMap drift,
  spillover, permitted-event, and error mutations; an invented Stack error event;
  both wildcard boundaries; injected publication interruption; and positive exact
  report shapes rather than phrase-only overclaim filtering. Those successors are now
  part of E1, and the reviewer must re-evaluate them before E2.
- 2026-07-22: E-R1's final authority attack showed that blocking only the common
  `Path`, subprocess, and convenience-network entry points did not exclude alternate
  host APIs, and one fixture hardlink did not represent every protected input class.
  Mocked evaluation now rejects direct open/glob/iteration, shell and subprocess
  variants, and raw sockets; alias controls sample both adapters plus an exact plan,
  Specification, registry record, and accepted report.
- 2026-07-22: E-R1 PASSed the strengthened E1 topology: two substrate controls pass,
  the absent probe is the sole intentional failure, and nine successor controls skip.
  The reviewer found no remaining concrete bypass across complete native projections,
  full ordered ledgers, symmetric mutations, exact execution authority, governed
  aliases, atomic failure, wildcard boundaries, report shape, or bounded language.
- 2026-07-22: E2 composes only the ten exact fixture commands through their existing
  runners, retains each domain's native projection shape and complete event ledger,
  validates concern locality before publication, and writes one deterministic report
  atomically. The first green attempt exposed only diagnostic precedence: a permitted
  effect mutation also changed the aggregate. Validation now reports the local effect
  mismatch before the complete-campaign aggregate, while adapter errors retain
  execution-status precedence. The focused suite passes 11 active controls with the
  intentional red predecessor skipped.
- 2026-07-22: E-R2 BLOCKed equality without completeness and ordered events without
  exact attribution. Five consistently stripped Stack reports could compare equal, and
  OrderedMap could retain event names/counts while changing case and operation. The E2
  successor now exact-binds canonical complete/error projection values, all ten native
  ledgers, and OrderedMap's nested effect surface; explicit mutations cover stripped
  projections, moved invocation attribution, and hidden nested error authority. E-R2
  must re-review this successor before E3.
- 2026-07-22: E-R2 also demonstrated that a completed ExecPlan hardlink fell outside
  the initial protected-directory alias census. Output now rejects identity with every
  existing repository file, while direct paths within the fixture/contract/spec/registry
  and accepted-report roots remain rejected even before they exist. The completed-plan
  hardlink joins the executable alias controls.
- 2026-07-22: E-R2 PASSed the successor with 12 active focused controls and one
  predecessor skip. Independent replay confirmed that stripped or altered projections,
  moved event attribution, both nested-effect authority mutations, and a completed-plan
  hardlink all fail closed. Canonical bindings retain list order and key/value shape;
  the reviewer found no uncovered published surface or executable bypass. E3 is
  released.
- 2026-07-22: E3 makes the exact command, output, safe governed-input failure, and
  real-underneath boundary experienceable from README; adds the bounded observation to
  effect semantics, system layers/trust/reopen boundaries, and the actor journeys;
  moves the authored backlog item to completed; and makes the contract, plan, module,
  and script required repository memory. Maintenance reopens on any design-spec trigger
  or exact campaign/projection/ledger fingerprint change.
- 2026-07-22: E-G passed the complete clean repository gate: 24/20/38/3 record
  fixtures, 18 loader groups, 50 adapter tests, 59 candidate controls, 285 actor
  journeys, 42 research probes, 20 governance tests, all retained Stack/OrderedMap
  report and Evidence bindings, both profile-choice bindings, and 49 proof groups.
  Design-spec 0003 revision 3 is frozen for the single experienceable stacked PR.

## Result and remaining work

ExecPlan 0008 is complete. The probe is experienceable, its 12 active focused controls
pass with the red predecessor skipped, both independent reviews pass, durable memory
agrees, and the complete repository gate is green. No accepted Effect relation, new
Evidence, resolver behavior, or whole-process conclusion is manufactured. Maintenance
reopens through design-spec 0003's explicit triggers or any exact campaign/projection/
ledger binding change.

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
