# ExecPlan 0011: stable approximate `norm2` numerical kernel

## Purpose and observable outcome

Deliver design-spec 0006 as semantic domain four and a separate stacked PR. One exact
command authenticates a finite package, runs twelve cases against two registered
kernels and a naïve overflow breaker, exposes every 2-ULP observation, derives
policy-relative decisions, and reports directional process boundaries separately.

Base is opened interaction-protocol PR branch exact head `9407be2`. No fragment PR may
open; design-spec 0006 remains the 1:1 governing contract.

## Context and repository map

Read the constitution, architecture, core model, specification language, evidence
model, compatibility, lifecycle, tracer design, design-spec 0006, completed ExecPlans
0009/0010, and the multi-provider workflow. Reuse only exact record/graph, authoring,
child-process, atomic-publication, and policy mechanics demonstrated domain-neutral.
Numerical semantics, oracle, candidate runner, and report remain domain-local.

## Non-goals and constraints

- Preserve every accepted Stack, OrderedMap, refinement, effects, resources, and
  lease-session byte and behavior.
- Do not generalize one kernel into a universal numerical type, tolerance policy,
  interval system, or floating-point semantics.
- Do not claim exhaustive inputs, correct rounding, real proof, alternate rounding
  modes, NaN/infinity behavior, hardware portability, or performance.
- Do not let candidate output, language/runtime identity, process success, report text,
  paths, or local-name resemblance become semantic authority.
- Keep approximate satisfaction, Evidence acceptance, and directional interoperability
  distinct.

## Revisioned work-dependency DAG

```text
N0 design-spec 0006 + substrate census
  -> N1 frozen refute-first controls
  -> N-R1 contract/oracle review
  -> N2 optional numerical authoring + exact spec/profile/plan
  -> N3 isolated kernels + breaker + campaign
  -> N-R2 implementation/oracle review
  -> N4 Claims/Evidence + manifest + projections + command
  -> N-R3 end-to-end authority/overclaim review
  -> N5 durable maintenance
  -> N-G clean convergence + frozen spec + one PR
```

| Node | Owner / exclusive scope | Evidence, gate, stop condition |
|---|---|---|
| N0 | lead; design-spec 0006 and this plan | need, relation, cases, falsifiers frozen before code; N1; stop if robust norm need cannot be observed without selecting an algorithm |
| N1 | test owner; new numerical journey tests | independent Decimal/bit-order oracle, exact 36 cases, negatives for encoding/nonfinite/tolerance/Evidence/authority/aliases; N-R1 |
| N-R1 | uninvolved reviewer; read-only | attack oracle circularity, ULP definition, rounded reference, case adequacy, candidate control, and finite wording; N2 or successor |
| N2 | lead; optional schema/PSpec plus stable-norm2 theory/profile/plan | predecessor validity and exact authoring equality; N3 |
| N3 | implementation owner; new candidates and numerical module runner only | two independent supports, exact naïve overflow counterexample, isolated complete responses; N-R2 |
| N-R2 | uninvolved reviewer; read-only | attack encoding, Decimal conversion, ordered bits, signed zero, malformed/nonfinite output, process isolation, and breaker specificity; N4 or successor |
| N4 | integrator; new records/manifest/resolution/projections/CLI only | exact fresh graph and Evidence, two accepted decisions, breaker challenge, boundary separation, atomic output; N-R3 |
| N-R3 | uninvolved reviewer; read-only | replay Evidence, authority, acquisition, alias, report-closure, finite-claim, and predecessor attacks; N5 or successor |
| N5 | lead; README/design/backlog/checker/plan | exact experience, assumptions, exclusions, recovery, reopen triggers; N-G |
| N-G | lead; freeze and PR report | focused/felt/full clean gates and hosted PR checks; stop before fragment PR |

No external disclosure is authorized by this plan. Reviews are local and evidence-based
unless the operator separately authorizes a cross-provider packet.

## Implementation order

1. Commit revision-1 design-spec and plan before production code.
2. Freeze exact cases and a test-owned 100-digit Decimal/ordered-bit oracle. The only
   intentional red is the absent numerical package.
3. Review the controls, retaining any BLOCK and successor.
4. Add the smallest optional declaration and exact theory/profile/plan.
5. Add isolated robust-primitive, scaled-ratio, and naïve candidates; make full case
   observations executable.
6. Bind exact Claims/Evidence and policy decisions from the authenticated manifest;
   add projections, boundaries, aliases, and atomic CLI publication.
7. Reconcile durable docs, archive this plan, freeze design-spec revision 2, run all
   gates, push, and open one PR based on `agent/interaction-protocol-journey`.

## Commands and expected observations

Focused:

```text
nix develop --command python3 -m unittest tests.journeys.test_n1_stable_norm2_kernel -v
```

Felt:

```text
nix develop --command python3 -m semantic_packages numerical inspect registry/stable-norm2/manifest.json --output /tmp/stable-norm2-inspection.json
```

Expected summary is frozen in design-spec 0006.

Complete:

```text
nix develop --command python3 scripts/check_repo.py
```

Expected: `Repository checks passed.` with exit status zero.

## Quality gates and evidence

- **Intent/specification:** exact real proposition, profile-local approximation relation,
  cases, finite limit, actors, falsifiers, exclusions, and non-goals precede code.
- **Authoring:** omission remains valid; malformed numerical declarations fail after
  raw/schema/link phases with stable pointers.
- **Realization:** two independent kernels support all cases; the naïve kernel fails the
  first large finite-result case; each candidate/case is a fresh process.
- **Evidence:** every decision binds exact spec/realization/adapter/profile/plan/source,
  result/review/freshness, assumptions, exclusions, and visible unsupported scope.
- **Integration:** theory/package and numerical/deployment authority remain separate.
- **Release:** immutable inputs, atomic output, alias rejection, exact acquisition and
  execution allowlists, focused/full gates, conventional history, and 1:1 PR.
- **Learning:** docs claim exactly one approximate kernel, not arbitrary numerics.

## Progress

- [x] N0 user need, approximation relation, cases, falsifiers, and exclusions frozen
- [x] N0 substrate census and domain-local boundary
- [x] N1 refute-first controls
- [x] N-R1 control review
- [x] N2 semantic artifacts
- [x] N3 candidates/campaign
- [x] N-R2 implementation/oracle review
- [x] N4 product graph/projections/command
- [x] N-R3 end-to-end review
- [x] N5 maintenance
- [x] N-G convergence and PR

## Discoveries and changed assumptions

- 2026-07-23: the interaction-protocol PR opened as #20, releasing the separately
  authorized numerical journey.
- 2026-07-23: stable 2D norm is the smallest useful anti-overfitting probe because naïve
  intermediate overflow/underflow distinguishes mathematical meaning from an obvious
  representation while a finite ULP relation remains directly observable.
- 2026-07-23: canonical hex-float transport avoids decimal round-trip ambiguity at the
  child boundary. Decimal high precision is campaign oracle machinery, not normative
  candidate representation or proof.
- 2026-07-23: existing record kinds admit a numerical concern/mechanism. Only the
  optional Specification declaration needs schema/authoring extension; resolver and
  campaign semantics remain local to avoid changing accepted domain-specific modules.
- 2026-07-23: N1 froze twelve exact hex pairs, candidate/source order, predecessor
  digests, complete report observations, the first breaker divergence, Evidence axes,
  execution multiset, alias safety, and exclusions before the module existed. The sole
  intentional failure was the absent numerical package.
- 2026-07-23: N-R1 retained the rounded-oracle versus real-value distinction and found
  that the plan's threshold must agree with the Specification rather than merely be
  internally usable. N2/N3 therefore bind oracle kind, decimal precision, profile, and
  max ULPs across Specification and plan.
- 2026-07-23: N-R2/N-R3 were local evidence-based adversarial passes because this plan
  authorized no external repository disclosure. Reviewer independence comes from the
  pre-code test-owned Decimal/bit oracle and candidate isolation, not model identity.
  The passes attacked signed zero, negative/nonfinite/malformed outputs, first-failure
  order, source/plan digests, profile and Evidence parameters, candidate process count,
  discovery/network denial, aliasing, atomic failure, and finite-claim wording. No
  material concern remained; external model review is not claimed.
- 2026-07-23: the scaled kernel and host hypot kernel both match every rounded oracle in
  the retained environment (0 ULP observed); the acceptance threshold remains 2 ULPs
  as frozen and is not weakened to fit either implementation. The naïve breaker first
  returns infinity at `large-equal`, then also exposes underflow on small cases.
- 2026-07-23: N-G passed the exact felt command, 13-test focused journey (12 active and
  one historical predecessor skip), `git diff --check`, and the complete Nix-backed
  repository gate with 333 actor journeys and every predecessor record, loader,
  adapter, candidate, research, governance, report/Evidence, and proof group.

## Decision log

- **Kernel:** choose robust `norm2` over matrix multiplication or iterative solvers. It
  exposes approximate relation, range hazards, signed inputs, symmetry, and scale with
  one operation and a decisive breaker.
- **Metric:** freeze distance from a 100-digit exact-input Decimal oracle rounded to
  binary64 at 2 ULPs. This is inspectable and profile-relative; do not call it correct
  rounding or a universal epsilon.
- **Evidence:** finite twelve-case campaign only. Universal error bounds require a proof
  or exhaustive mechanism and remain excluded.

## Result and remaining work

Design-spec 0006 revision 2 is frozen without changing its pre-code user need,
approximation relation, cases, falsifiers, or exclusions. The command executes 36 fresh
candidate cases, accepts both registered robust kernels, challenges the naïve breaker
at exact case index 8, and keeps policy-relative numerical decisions separate from
directional child-process boundaries. Focused, felt, and complete gates pass; the plan
is complete and its one stacked PR may open.

## Stop and escalation conditions

Stop if the oracle depends on candidate code, exact input transport cannot be preserved,
a passing candidate needs a widened tolerance, predecessor behavior changes, or report
language implies universal assurance. Escalate only protected intent or a new user-value
choice; local schema, runner, algorithm, and module decisions remain reversible.
