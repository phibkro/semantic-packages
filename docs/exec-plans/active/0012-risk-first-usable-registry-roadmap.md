# ExecPlan 0012: risk-first roadmap to a usable semantic registry

## Purpose and observable outcome

Deliver the docs-only contract in design-spec 0007 as one PR above merged #21. The
operator can inspect and gate a risk-ordered roadmap that:

- names the hardest fatal technical premises for a usable registry;
- gives each premise a cheap decisive spike and kill criterion;
- sequences Lean-proved Specification semantics plus Rust and TypeScript Realizations
  as the vehicle;
- keeps proof, implementation conformance, artifact origin, Evidence acceptance,
  resolution, and publication authority distinct; and
- parks proof/language/adapter breadth and the web app until their explicit triggers.

No product code, schema, registry record, proof, candidate, adapter, resolver, or UI
change is authorized by this plan before the operator gate.

## Governing context and repository map

- `design-specs/0007-risk-first-usable-registry-roadmap.md` owns the product outcome,
  risk order, spikes, slice sequence, global falsifiers, parked list, and reopen rules.
- The constitution and architecture protect meaning over mechanism, Claims/Evidence
  separation, competing Realizations, consumer authority, and separate semantic versus
  realization compatibility.
- Core-model, specification-language, evidence-model, compatibility, lifecycle, and
  tracer design define exact addresses, observation, bounded Evidence, resolver axes,
  and refute-first gates.
- ADR 0009 records the current Lean boundary and its unresolved hand-translation
  assumption. The adapter protocol records the perfect-shadow limitation and absence of
  registry-driven build/execution. Completed ExecPlans 0001/0002/0004/0005 and
  0007–0011 preserve the current local graph, proof, Rust/TypeScript, registry,
  evolution, protocol, and numerical observations.
- The operator authorized #16–#21 to merge. Each PR passed fresh hosted checks,
  conventional-commit hygiene, and exact 1:1 design-spec binding; each stacked child
  was content-identically rebased after its parent squash. `master` and `origin/master`
  now equal exact merge commit `404c9c40be5173c993cd376aa2d2c5892f8503a1`.
  This branch starts there and must not rewrite the merged history.

## Non-goals and protected boundaries

- Do not implement any roadmap slice in this PR.
- Do not imply Lean proof transfers to Rust/TypeScript implementations.
- Do not select Lean, JSON, Stack, semver, Wasm, an ABI, or a semantic IR as universal.
- Do not add proof assistants, languages, transport adapters, package-manager plugins,
  production hosting, or web UI.
- Do not call signatures assurance, tests proofs, version spelling compatibility, or a
  local edited manifest a usable registry.
- Do not change mission, accepted predecessor bytes, or operator priority.

## Revisioned work-dependency DAG

```text
RM0 operator direction + exact #21 base
  -> RM1 repository risk census
  -> RM2 design-spec 0007 risk ordering and falsifiers
  -> RM-R1 cross-boundary roadmap review
  -> RM3 ExecPlan agreement and docs-only gate
  -> RM-G1 frozen docs-only PR
  -> OP-G operator accept / revise / reject
       -> accepted: authorize separate S1 design spec only
       -> revised: RM2 successor, no code
       -> rejected: close roadmap, no code
```

| Node | Owner / exclusive scope | Evidence, downstream gate, stop condition |
|---|---|---|
| RM0 direction/base | successor manager; read-only direction and Git/PR state | named wake, #21 exact head, no-code gate; RM1 |
| RM1 risk census | lead; read-only architecture, proof, adapter, schemas, registry/resolver, completed-plan surfaces | current demonstrated capability versus fatal gaps; RM2; stop if direction conflicts with constitution |
| RM2 frozen design spec | lead; `design-specs/0007-risk-first-usable-registry-roadmap.md` only | seven risks, seven spikes/kill criteria, risk DAG, slices, fourteen falsifiers, parked list; RM-R1 |
| RM-R1 roadmap review | local evidence-based review; read-only actual docs | attack risk order, proof-to-implementation overclaim, hidden universal choices, usability definition, parked triggers, dependency cycles; RM3 or retained successor |
| RM3 plan/integration | lead; this ExecPlan only | design/plan agreement, explicit operator gate, exact future slice boundaries; RM-G1 |
| RM-G1 docs convergence | lead | Markdown links, `git diff --check`, full repository gate, conventional history, one docs-only PR above #21; OP-G |
| OP-G operator gate | operator | accept/revise/reject design-spec 0007; only acceptance may release a separate S1 design-spec increment |

No external repository disclosure is authorized. No provider/model review is claimed.
RM-R1 uses artifact-level cross-checks against durable architecture, accepted failure
fixtures, and the explicit falsifiers; model identity grants no assurance.

## Risk census: demonstrated versus missing

| Surface | Demonstrated now | Fatal missing premise routed to |
|---|---|---|
| Specification meaning | exact records, hosted laws, observations, bounded domain aspects | checked correspondence among authored proposition, Lean statement, and runtime observation — R1 |
| Lean proof | one core `pop-empty` model theorem with exact provenance/no axioms | machine-checked translation from canonical meaning and broader selected-law coverage — R1 |
| Rust/TypeScript | independent bounded Stack/OrderedMap candidates and reports | exact executable artifact subject, origin/build binding, portable contract — R2/R3 |
| Adapter | explicit child boundary, complete bounded traces, perfect-shadow fixture | honest artifact/adapter subject and policy treatment of faithfulness — R2 |
| Claims/Evidence | exact typed scope, review/result/applicability separation | typed mechanism provenance and package-neutral derivation — R4 |
| Resolution | exact domain-specific explainable selections | generic assurance plus evidence-backed release/dependency solving — R4/R5 |
| Evolution | exact successors and unestablished structural refinement reports | explicit compatibility/refinement Claims/Evidence used by deterministic locks — R5 |
| Registry | curated immutable local manifests and graph projections | atomic authorized publication, verified acquisition, rollback/tamper handling — R6 |
| UX | bounded domain commands and derived reports | stable generic cold CLI/API lifecycle without repository internals — R7 |
| Browser | absent by design | parked until generic APIs/projections stabilize after S6 |

## Work sequence for this increment

1. Preserve exact merged #21/master head and create a dedicated roadmap branch.
2. Read the governing architecture, current proof decision, adapter boundary, evidence
   and claim schemas, registry manifest, system map, backlog, and relevant completed
   plans. Record only gaps that can falsify the requested product outcome.
3. Freeze design-spec 0007 before any implementation. Rank fatal semantic/authority
   risks ahead of mechanical breadth and give every risk an observable spike and kill
   criterion.
4. Define an acyclic S0–S6 sequence. Every post-gate slice is separately spec-first and
   1:1; this plan does not pre-authorize its implementation details.
5. Review for silent proof transfer, circular evidence, package-specific resolver
   authority, semver inference, registry/signature overclaim, universal foundations,
   and premature UI/adapter work.
6. Run docs/repository gates, commit only design-spec 0007 and this plan, push, and open
   one docs-only PR based on `agent/approximate-numerical-kernel`.
7. Report the exact frozen spec path and PR. Hold all code until OP-G returns a named
   acceptance or revision.

## Future slice readiness rules

The roadmap describes future work but this ExecPlan releases only the next design node,
never implementation directly:

- OP-G acceptance releases **S1 design-spec authoring**, not S1 code.
- Each slice design spec freezes user need, semantic boundary, falsifiers, evidence,
  exclusions, and recovery before code.
- Each spike runs before broad realization. A killed premise closes truthfully and
  produces a design successor; it is not weakened to preserve schedule.
- S2 cannot claim named Realization satisfaction until R2 identifies the exact artifact
  executed. S3 cannot generalize acceptance until R1–R3 evidence subjects are stable.
- S4 cannot infer semantic compatibility from version strings. S5 cannot call signed
  bytes semantically assured. S6 cannot depend on the parked web app.
- One shared surface has one integrator. Parallel writers require disjoint worktrees and
  scopes under the lifecycle/multi-provider rules.

## Quality gates and required evidence

### Intent gate

- Operator direction appears verbatim in outcome and priorities without adding a web-
  first or adapter-breadth interpretation.
- “Lean-proved” and “implementation satisfies” are explicitly separated.
- The bounded CLI/API definition of usable is observable.

### Risk gate

- R1–R7 each name fatality, required invariant, cheapest spike, and kill/falsifier.
- Hard dependencies are acyclic and explain why semantic authority precedes mechanics.
- Stack assurance is a vehicle, not arbitrary-domain proof.

### Sequence gate

- S0–S6 attack risks in order with Lean + Rust + TypeScript visible in the vehicle.
- Every future increment remains 1:1 design spec → implementation → PR.
- Operator approval releases only the next design increment.

### Parking gate

- Proof assistants beyond Lean, languages beyond Rust/TypeScript, transport/adapter
  breadth, mechanical package breadth, production hosting, and universal foundations
  are parked.
- The web app is explicitly later, inspired by useful JSR/npm registry UX but extended
  with evidence/unknown/profile/policy and compatibility separation.

### Repository/release gate

```text
git diff --check
nix develop --command python3 scripts/check_repo.py
```

Expected: no whitespace errors and `Repository checks passed.` No source/schema/record
or accepted predecessor byte changes. Hosted prospective metadata and repository
contract must pass for the docs-only PR.

## Progress

- [x] RM0 named operator wake, gated #16–#21 merge, and exact merged base observed
- [x] RM1 proof/adapter/evidence/registry/resolution risk census
- [x] RM2 design-spec 0007 risk ordering, spikes, slices, falsifiers, and parked list
- [x] RM-R1 local cross-boundary review
- [x] RM3 design/plan agreement and no-code operator gate
- [ ] RM-G1 local/hosted docs-only convergence and PR report
- [ ] OP-G operator accept/revise/reject

## Discoveries and changed assumptions

- 2026-07-23: authorized stack merge completed bottom-up. PRs #16–#21 each passed
  hosted prospective-metadata/repository-contract checks, local conventional commit
  range validation, and a one-added-design-spec/body-binding check before squash.
  Child branches required content-identical rebases after parent squashes; all rerun
  hosted/local gates passed. Final `master == origin/master` is `404c9c40`.
- 2026-07-23: the existing tracer already has the requested nouns—Lean proof, Rust and
  TypeScript packages, Evidence, exact records, resolver, and registry projections—but
  they do not yet form one generally trustworthy reusable product path. Mechanical
  breadth would replicate unresolved authority gaps.
- 2026-07-23: ADR 0009 names R1 directly: theorem translation fidelity remains assumed.
  The adapter protocol names R2 directly: a perfect shadow is behaviorally
  undetectable. These are retained product falsifiers, not defects to hide.
- 2026-07-23: schemas correctly separate Claim/Evidence axes but leave mechanism
  provenance open; package-specific code currently validates accepted report bindings.
  Generic assurance is therefore later than stable semantic/artifact subjects and
  earlier than version resolution.
- 2026-07-23: exact version pinning is a safe starting point, not a usable selector.
  Explicit evidence-backed compatibility must precede ranges/locks; semver syntax alone
  remains nonauthoritative.
- 2026-07-23: publication authenticity and semantic assurance are orthogonal. Registry
  transactions/signatures wait until record/evidence/release semantics stabilize, but
  precede a cold usable release or web app.
- 2026-07-23: a web app can reuse JSR/npm information architecture later, but building
  it before generic APIs and authoritative projections would create a polished second
  source of truth.

## Decision log

- **Vehicle:** use an exact Stack assurance successor rather than a new broad domain.
  Stack already exposes every cross-boundary gap and minimizes semantic distraction.
- **First risk:** close semantic correspondence before deeper proofs or more languages.
  A proof about a hand-mapped proposition is not yet an end-to-end registry guarantee.
- **Realization subject:** test an exact executable/package artifact and keep origin,
  conformance, and faithfulness Claims separate. Black-box behavior cannot prove a
  hidden library was exercised.
- **Assurance order:** stabilize semantic and artifact subjects, then genericize Evidence
  acceptance, then solve versions/releases, then publication/acquisition, then cold UX.
- **Breadth:** Lean + Rust + TypeScript are sufficient to test extension boundaries.
  More adapters/languages are parked until the boundary survives this vehicle.
- **Web:** explicitly later than S6. Use JSR/npm design inspiration, not their shallow
  package-as-code or popularity-as-trust semantics.

## Result and remaining work

Design-spec 0007 revision 1 and this plan form the complete docs-only roadmap increment.
The risk order is R1 semantic correspondence, R2 exact Realization subject, R3 portable
Rust/TypeScript contract, R4 generic assurance, R5 evidence-backed version resolution,
R6 transactional publication/acquisition, and R7 cold CLI/API usability. Future work is
S1–S6, each separately gated and 1:1. RM-G1 and operator gate OP-G remain; no product
code is authorized.

## Stop and escalation conditions

- Stop on any request to implement S1 before OP-G acceptance.
- Stop if roadmap wording transfers Lean proof to a Realization or calls finite tests
  formal verification.
- Stop if a risk is reordered for implementation convenience rather than fatality or
  decisive evidence.
- Stop if this PR changes anything beyond design-spec 0007 and ExecPlan 0012.
- Escalate to the operator if “usable registry” is intended to require production remote
  hosting in the first release, if Stack is rejected as the risk vehicle, or if a parked
  item becomes current priority.
- After PR opening, hold idle until a named operator/manager wake accepts or revises the
  frozen roadmap.
