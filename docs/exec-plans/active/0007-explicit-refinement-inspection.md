# ExecPlan 0007: explicit refinement inspection

## Purpose and observable outcome

Deliver design-spec 0002 as one complete two-domain tracer bullet: a theory maintainer
authors an explicit cross-version declaration disposition for exact Stack or OrderedMap
Specification files and receives a deterministic structural inspection report that
leaves semantic refinement unestablished.

This plan is stacked on draft PR #16. It may develop and open its own PR without waiting
for #16 to merge, but its eventual PR base remains the #16 feature branch until the
stack is rebased after upstream disposition.

## Governing sources and exact substrate

- `design-specs/0002-explicit-refinement-inspection-journey.md` owns the user journey,
  Goal/Values/Constraints, eleven falsifiers, DoD, exclusions, and recovery.
- `docs/vision/constitution.md`, `docs/vision/problem-statement.md`,
  `docs/design/core-model.md`, and `docs/design/compatibility.md` preserve exact
  identity, plural semantics, Claim/Evidence separation, and semantic versus
  realization compatibility.
- ADRs 0005, 0007, and 0014 prohibit implicit cross-version lineage, import semantics,
  latest selection, and general successor inference.
- The exact predecessor/successor Specification files are the only feature inputs:
  Stack `0.1.0`/`0.2.0` and OrderedMap `0.1.0`/`0.2.0` at the paths and raw digests
  frozen in design-spec 0002.

## Non-goals and protected boundaries

- Do not add a canonical Refinement record kind, resolver edge, accepted compatibility
  verdict, version range, automatic migration, latest selection, or fallback.
- Do not infer declaration continuity from equal local IDs, paths, order, or version
  spelling. Every relation is proposal-local and explicit.
- Do not interpret hosted semantic text or transfer, inherit, repoint, or manufacture
  Claims or Evidence.
- Do not mutate accepted Specifications, manifests, maintenance actors, or canonical
  records from either domain.
- Do not claim arbitrary-domain generality from two bounded examples.

## Revisioned work-dependency DAG

```text
V0 exact two-domain census and design-spec 0002
  -> V1 red complete proposals and journey controls
  -> V-R1 independent contract/control review
  -> V2 proposal decoder, validator, inspector, report, and CLI
  -> V-R2 independent implementation review
  -> V3 README/design/system-map/backlog maintenance
  -> V-G complete gate, design-spec freeze, and one experienceable PR
```

| Node | Owner and exclusive boundary | Required evidence, downstream gate, stop condition |
|---|---|---|
| V0 contract | lead; design-spec 0002 only | exact 10/1 Stack and 18/2 OrderedMap census, raw digests, felt commands, falsifiers; V1; stop on source contradiction |
| V1 red journey | lead/test owner; `refinements/*.prefine`, V1 journey tests, this plan | TOML parses, complete explicit dispositions, intentional absent refinement command, successor controls; V-R1; stop if proposal cannot represent both examples |
| V-R1 | uninvolved read-only reviewer | attack completeness, nonauthority, digest binding, phase order, no overclaim, and red topology; V2 or explicit successor |
| V2 implementation | lead; new refinement modules/CLI plus exact report serialization | both exact reports, all falsifiers, atomic output, unchanged predecessor actors; V-R2; stop on canonical-model or resolver expansion |
| V-R2 | uninvolved read-only reviewer | counterexamples for mappings, parsing, ordering, hosted opacity, no Evidence migration, generality boundary; V3 or successor |
| V3 maintenance | lead; README and durable project memory | exact experience/failure/recovery, changed capability map, backlog disposition, known exclusions; V-G |
| V-G | lead; spec freeze and PR report | complete clean repository gate, conventional range, validated PR metadata, 1:1 PR; stop before fragment PR or unsupported refinement claim |

## Implementation order and verification

1. Commit design-spec 0002 before any proposal, test, or implementation artifact.
2. Freeze two complete proposal inputs and a red journey suite derived from all eleven
   falsifiers. The red predecessor names only the absent `refinement inspect` command;
   successor controls skip rather than fail for unrelated missing mechanisms.
3. Obtain V-R1 PASS before implementing. Retain every BLOCK and successor in this plan.
4. Implement the smallest explicit parser/validator/inspector below the contract line.
   Reuse record/schema authority rather than duplicating it; preserve all-or-none and
   atomic output behavior established by the author command where appropriate.
5. Run focused V1/V2 controls plus Stack and OrderedMap maintenance regressions, then
   obtain V-R2 PASS.
6. Reconcile durable docs and run `python3 scripts/check_repo.py` from a clean exact
   head. Freeze design-spec 0002 only after all evidence passes.
7. Open one PR whose base is `agent/human-authoring-journey` while PR #16 remains open.
   Its description is the report and begins with the two exact experience commands and
   one line stating what is real underneath.

Focused journey command:

```text
python3 -m unittest tests.journeys.test_v1_explicit_refinement_inspection -v
```

Complete gate:

```text
python3 scripts/check_repo.py
```

## Progress checklist

- [x] V0 exact census and design-spec 0002 active draft
- [x] V1 red complete proposals and journey controls
- [ ] V-R1 independent contract/control review
- [ ] V2 inspector and CLI
- [ ] V-R2 independent implementation review
- [ ] V3 durable documentation and maintenance
- [ ] V-G convergence, freeze, and one PR

## Discoveries and changed assumptions

- 2026-07-22: the authored roadmap after the PSpec surface is explicit refinement and
  evolution grounded in accepted two-domain successors, ahead of a third domain or
  abstract effect/resource work. The exact declaration census is Stack 10 unchanged /
  1 changed effect / 0 additions / 0 removals and OrderedMap 18 unchanged / 0 changed /
  2 additions / 0 removals. This supports one shared explicit-disposition mechanic but
  not one shared semantic refinement conclusion.
- 2026-07-22: design-spec 0002 is the first artifact on stacked branch
  `agent/specification-refinement-journey` at `96195ac`. No feature PR exists because
  the journey is not yet experienceable.
- 2026-07-22: V1 freezes two complete TOML proposals whose exact addresses, raw
  digests, mappings, additions, and removals cover both Specification documents once.
  The focused predecessor has 11 tests: one exact-census PASS, one intentional FAIL
  naming only the absent `refinement` command, and nine successor controls SKIP. Those
  controls cover both exact reports and all eleven falsifiers through grouped negative
  matrices. V-R1 must attack completeness and oracle sensitivity before V2 begins.

## Result and remaining work

V0 and V1 are complete. V-R1 is the next released node. No inspector, report, accepted
refinement relation, compatibility conclusion, Evidence transfer, or resolver change
exists yet; the red predecessor is intentional.

## Stop and escalation conditions

- stop if implementation derives a mapping or compatibility conclusion from semver,
  matching local IDs, paths, declaration order, or source adjacency;
- stop if exact structural equality is described as semantic equivalence or refinement;
- stop if a proposal mutates canonical Specifications or repoints predecessor Evidence;
- stop if a canonical record kind, universal logic, or resolver behavior becomes
  necessary without an explicit design-spec revision and independently reviewed need;
- escalate only a genuine product choice between materially different maintainer
  journeys or a protected-intent change, not parser/module micro-decisions.
