# ADR 0011: Scaled evidence-bearing change lifecycles

## Status

Accepted by J0-G in ExecPlan 0002 after the independent J0-R4 successor review and
exact repository gate. Protected intent and authority boundaries remain unchanged.

## Context

The existing lifecycle names research, design, realization, verification, observation,
and maintenance, but it does not say how a feature, defect, refactor, incident, or
governance experiment may scale that work without either ceremony explosion or an
evidence bypass. A single forward-only sequence would also misrepresent security
containment, pure refactoring, optimization, and reversible DAG successors.

## Decision

Every change instantiates a common spine: intent/classification, baseline/falsifier,
design/risk, realization, evidence, convergence/release, and learning/maintenance.
Each node records an observable outcome, authority and ownership boundary, cheapest
useful falsifier, retained disposition, and rollback or successor trigger.

Change class selects a proportional profile; it never removes the common minimum.
Features exercise the full actor journey. Defects may inherit accepted research and
design but retain reproduction and regression evidence. Refactors characterize and
preserve declared behavior. Optimizations require a measured baseline and target and
are optional when no justified deficit exists. Dependency/toolchain changes,
migrations, security or operational incidents, experiments, documentation or
specification changes, deprecation/removal, release/configuration changes, and
governance/self-improvement each use their explicit profile in the lifecycle design.

Within bounded implementation work, use a refute-first cycle with
red–green–refactor as the default where meaningful. “Red” is an observed unmet claim,
not necessarily a unit test. Pure refactors use characterization and test-sensitivity
evidence; optimizations use a measured deficit; proofs use counterexample attempts and
proof checking; security incidents may contain exposure before authoring a regression.

Failure or changed inputs create successor nodes and reopen affected downstream gates.
They do not alter a predecessor's recorded result. Gate criteria change prospectively.
A consequential acceptance gate cannot be both defined and independently ratified by
the same owner. A gate-weakening proposal, retroactive pass, protected-intent change,
or hard-to-reverse governance amendment escalates to the user.

Process changes are bounded experiments with a baseline, hypothesis, target, canary
scope, safety invariants, observation window, independent review, and rollback. They
cannot ratify themselves or redefine their own success criteria.

## Consequences

- Risk changes evidence breadth, independence, environments, rollout, and artifact
  weight; it never permits no evidence.
- Maintenance is continuing ownership and observation rather than a final phase.
- Optimization is evidence-triggered rather than mandatory feature work.
- Micro red/green/refactor steps remain inside a work package unless they release
  another owner, change a shared surface, create canonical Evidence, cross authority,
  or need independent review.
- Security and operational incidents gain containment-first paths while preserving
  mandatory successor investigation and learning.
- Contribution and CI controls should teach and check the selected change class and
  retained evidence without turning every small edit into a separate ExecPlan.

## Rejected alternatives

- A mandatory serial `research -> design -> implement -> optimize -> document ->
  maintain` waterfall was rejected because verification is continuous, optimization
  may be unjustified, normative documentation can precede realization, and maintenance
  does not terminate.
- Treating TDD as the universal evidence mechanism was rejected because proof,
  performance, migration, security, probabilistic, UX, and governance claims require
  other observations.
- Allowing “small” changes to bypass classification and evidence was rejected because
  their actual risk is determined by semantics, authority, shared surfaces, external
  state, and reversibility rather than line count.

## Revisit conditions

Revisit when the profiles cause measurable ceremony without catching relevant
failures, a new recurring change class does not fit them, or an executable governance
check begins rejecting valid low-risk work or accepting a protected-boundary change.
