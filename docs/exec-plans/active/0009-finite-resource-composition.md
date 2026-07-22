# ExecPlan 0009: finite resource-composition inspection

## Purpose and observable outcome

Deliver design-spec 0004 as one complete theory-author tracer: an author writes one
finite resource-composition algebra in PSpec, binds its elements to the exact Stack and
OrderedMap persistence declarations, and runs one command that checks the authored
table and reports a deterministic fold while keeping realization satisfaction
unestablished.

This plan is stacked on ready PR #18 and exact base `7b2f883`. Development remains on
`agent/resource-algebra-journey` until the complete journey is experienceable. No PR
opens for a schema, test, or command fragment.

## Governing sources and exact substrate

- `design-specs/0004-finite-resource-composition-inspection.md` owns the felt command,
  finite candidate semantics, ten falsifiers, Definition of Done, exclusions, and
  recovery.
- `docs/vision/constitution.md`, `ARCHITECTURE.md`, `docs/design/core-model.md`, and
  `docs/design/spec-language.md` preserve plural mathematics, exact typed addresses,
  observable semantics, and the separation of structural inspection from satisfaction
  and Evidence.
- ADRs 0005, 0007, 0016, and 0017 govern exact declaration references, finite local
  imports, representation-neutral authoring, and explicit dependency context.
- `specs/stack.pspec`, `specs/ordered-map.pspec`, and their accepted registry records
  are immutable predecessors. Both expose a resource named `persistence`; equal local
  IDs do not merge those declarations.
- `semantic_packages.authoring.author_specification` is the only PSpec decode/schema/
  link boundary. The resource command must reuse it with caller-supplied dependencies.

## Non-goals and protected boundaries

- Do not establish Realization satisfaction, Claim/Evidence transfer, semantic
  compatibility, refinement, resolver authority, or a consumer decision.
- Do not claim a universal resource algebra, separation logic, ownership model,
  quantitative resource system, effect algebra, or arbitrary-domain composition.
- Do not modify accepted Stack or OrderedMap PSpecs, records, runners, fixtures,
  reports, Claims, Evidence, policies, manifests, resolver results, projections,
  refinement outputs, or effect-separation outputs.
- Do not infer bindings from local IDs, declaration order, import order, prose, or
  Evidence concerns. Only exact authored declaration references bind.
- Do not discover a registry, manifest, version, profile, package, Claim, Evidence, or
  executable entrypoint; do not access the network or launch a child process.

## Revisioned work-dependency DAG

```text
R0 design-spec 0004 and exact schema/source census
  -> R1 red author/inspect journey and negative controls
  -> R-R1 independent contract, oracle, and phase review
  -> R2 optional schema/link surface and retained PSpec
  -> R3 finite-law inspector, fold report, and atomic command
  -> R-R2 independent implementation, authority, and overclaim review
  -> R4 README/resource semantics/system map/user journey/backlog maintenance
  -> R-G complete clean gate, design-spec freeze, and one experienceable stacked PR
```

| Node | Owner and exclusive boundary | Required evidence, downstream gate, stop condition |
|---|---|---|
| R0 contract/census | lead; design-spec 0004 and this plan only | exact predecessor bytes, existing resource/schema/link surfaces, fixed command/report and candidate table; R1; stop if exact imports cannot name both resources without predecessor changes |
| R1 red journey | lead/test owner; new resource journey tests and retained source fixtures only | intentional absent-resource-command failure plus controls for authoring phases, table coverage/laws, exact bindings, folds, atomicity, no discovery/execution, regressions, and nonauthority; R-R1; stop if a falsifier lacks an independent oracle |
| R-R1 | uninvolved read-only reviewer | attack schema compatibility, law-oracle independence, phase ordering, implicit bindings/defaults, fold completeness, failure preservation, and overclaim; R2 or explicit successor |
| R2 schema/source | lead; `schemas/spec.schema.json`, resource classification/link checks, and new retained PSpec only | optional candidate shape; exact imported resource references; old accepted bytes and validations unchanged; R3; stop if global declaration identity or import semantics must change |
| R3 implementation | lead; new resource-inspection module and CLI integration only | exhaustive finite laws, deterministic first counterexample, authored/reverse fold, complete report, atomic output, no hidden acquisition or execution; R-R2; stop if accepted authoring behavior must weaken |
| R-R2 | uninvolved read-only reviewer | executable counterexamples for incomplete/duplicate tables, false laws, wrong bindings, fold loss/reordering, input mutation/aliasing, hidden authority, and semantic overclaim; R4 or explicit successor |
| R4 maintenance | lead; README and durable project memory | exact experience/failure/recovery, resource boundary, assumptions/exclusions, system map, actor journey, backlog disposition, maintenance owner and reopen triggers; R-G |
| R-G | lead; freeze and PR report | focused and complete clean gates, conventional range, 1:1 frozen spec/PR, exact command and real-underneath line; stop before fragment PR |

## Exact retained candidate

The new `specs/persistence-composition.pspec` imports exact Stack and OrderedMap
`0.1.0` Specifications and declares one `retained-persistence` resource. Its candidate
kind is `finite-commutative-monoid-v1`; its ordered carrier is `none`,
`stack-retained`, `ordered-map-retained`, and `both-retained`; its unit is `none`.
The source authors all sixteen ordered rows. It binds the exact Stack and OrderedMap
`persistence` declaration references to their distinct singleton elements. Both the
authored-order and reverse-order folds must end at `both-retained`.

The schema addition is optional. The candidate kind, totality, unit, commutativity,
and associativity are requirements only for the named algebra object, never defaults
for existing or future resource declarations.

## Implementation order and verification

1. Keep design-spec 0004 and this plan ahead of code. Record any contract correction
   as a numbered design-spec revision before changing an oracle.
2. Freeze R1 from all ten falsifiers. Its only intentional failure names the absent
   `resource inspect` command; production successors skip until the command exists.
3. Obtain R-R1 PASS before production implementation. Retain every BLOCK and successor
   disposition in this plan.
4. Add the optional schema surface and graph-relative exact resource-binding checks,
   then the smallest inspector and CLI boundary. Reuse `author_specification` rather
   than adding a second PSpec parser.
5. Run focused resource, authoring, record/link, refinement, and effect regressions,
   then obtain R-R2 PASS.
6. Reconcile durable docs and run `python3 scripts/check_repo.py` from a clean exact
   head. Freeze design-spec 0004 only after all evidence passes.
7. Open one PR with base `agent/effect-classification-journey`. Its report begins with
   the exact command and one line stating that the real substrate is authored finite
   table inspection and exact imported-resource bindings, not satisfaction.

Focused journey command:

```text
python3 -m unittest tests.journeys.test_r1_finite_resource_composition -v
```

Complete gate:

```text
python3 scripts/check_repo.py
```

## Progress checklist

- [x] R0 design-spec 0004 and exact substrate census
- [x] R1 red author/inspect journey and controls
- [ ] R-R1 independent contract/oracle review
- [ ] R2 optional schema/link surface and retained PSpec
- [ ] R3 finite-law inspector, fold report, and atomic command
- [ ] R-R2 independent implementation review
- [ ] R4 durable documentation and maintenance
- [ ] R-G convergence, freeze, and one PR

## Discoveries and changed assumptions

- 2026-07-22: the authored backlog's next unconditional node after bounded effect
  separation is a user-defined resource algebra. This releases a bounded implementation
  route rather than requiring an operator values choice.
- 2026-07-22: both retained Specifications use the same local resource ID
  `persistence`, but exact declaration identity includes the enclosing Specification.
  The candidate therefore needs explicit declaration bindings; ID equality is an
  anti-oracle, not evidence of common meaning.
- 2026-07-22: the existing authoring boundary already carries nested explicit TOML
  values into canonical JSON and validates a finite dependency graph. The missing
  mechanics are an optional exact candidate schema, resource-binding link checks, and
  finite algebra inspection; a second parser or authoring IR remains unjustified.
- 2026-07-22: R1 initially froze fourteen focused controls: three substrate/oracle controls
  passed, the absent `resource` command was the sole intentional failure, and ten
  production successors skip. The independent law oracle enumerates all 16 pairs and
  64 triples from the authored table rather than importing future checker code.
- 2026-07-22: R-R1 BLOCK at exact clean `fcbef38`. The associativity mutation's
  asserted smallest triple was false: changing `stack-retained * stack-retained` to
  `ordered-map-retained` first fails at `(stack-retained, stack-retained,
  ordered-map-retained)`, not the all-Stack triple. The alleged unimported-binding case
  was only dangling because its target record was absent. The successor corrects both,
  retains a loaded-but-unimported dependency, and expands schema, report, dynamic-fold,
  normalized-alias, and acquisition sensitivity before R-R1 re-review. R2/R3 remain
  blocked until that successor passes.
- 2026-07-22: the strengthened R1 successor has sixteen controls: three substrate
  controls pass, the same absent command is the sole intentional failure, and twelve
  production successors skip. New controls make raw/schema/link phase precedence,
  candidate shape, loaded-but-unimported bindings, full report content, dynamic fold
  evaluation, normalized aliases, and discovery-free authority independently
  observable.
- 2026-07-22: R-R1 successor BLOCK at exact clean `95e5ec8`. The corrected
  associativity and loaded-but-unimported controls are sound, but exact success fields
  did not exclude extra authoritative report fields; single-phase failures did not
  prove raw/schema/link precedence over algebra inspection; and the dynamic reverse
  fold did not assert its exact changed sequence and transitions. The next successor
  requires an exact closed report/observation shape, compound schema/link plus algebra
  failures with no algebra diagnostic, and both exact dynamic fold traces.

## Maintenance, recovery, and reopen conditions

The semantic-model maintainer owns the candidate schema/link behavior and exact law
checker; the authoring maintainer owns only the reused decode/dependency boundary; the
CLI maintainer owns atomic publication. Failures preserve prior output and never alter
inputs. Revert the eventual feature squash to remove the optional candidate, retained
source, inspector, command, and derived documentation without changing predecessor
records.

Reopen when a concrete journey requires partial composition, invalid/core elements,
order or implication, cancellation, quantities/grades, ownership/frame reasoning,
runtime resource observations, Evidence for algebra laws, resolver consumption, or
multiple algebras on one resource. Those are successors, not silent extensions of
`finite-commutative-monoid-v1`.
