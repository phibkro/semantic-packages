# ExecPlan 0010: retry-safe lease-session semantic package

## Purpose and observable outcome

Deliver design-spec 0005 as the third complete semantic package and the first
interaction-protocol domain. A package consumer runs one exact command and inspects two
independent registered lease-session realizations that satisfy six finite ordered trace
scenarios, one resurrection breaker that is challenged, policy-relative Claim/Evidence
decisions, and separate directional deployment boundaries.

This plan is stacked on the ready finite-resource PR branch at exact base
`99fe79450b90e323d7f5f6c9df789045cc627063`. Work remains on
`agent/interaction-protocol-journey` until the complete felt journey is experienceable.
No PR opens for a schema, record, runner, implementation, Evidence, or projection
fragment. The approximate numerical kernel begins only after this plan's PR opens and
uses a separate design spec, plan, branch, and PR.

## Governing sources and context

- `design-specs/0005-retry-safe-lease-session-package.md` owns the frozen user need,
  observable journey, six scenarios, fourteen falsifiers, Definition of Done,
  exclusions, recovery, and reopen triggers.
- `docs/vision/constitution.md`, `ARCHITECTURE.md`, `docs/design/core-model.md`,
  `docs/design/spec-language.md`, `docs/design/evidence-model.md`,
  `docs/design/compatibility.md`, `docs/design/lifecycle.md`, and
  `docs/design/tracer-bullet.md` preserve plural mathematics, representation-neutral
  observation, exact addresses, Claims/Evidence separation, policy-relative
  satisfaction, compatibility separation, refute-first delivery, and regression
  continuity.
- Completed ExecPlans 0001/0002/0004 establish the Stack and OrderedMap product
  substrate. Completed ExecPlans 0007/0008/0009 add bounded refinement, effects, and
  resources without accepting arbitrary generality. Every accepted predecessor remains
  immutable unless this plan records an explicit falsifier and successor.
- The core model names state transitions, protocols, and protocol simulation, while
  the current schema and PSpec intentionally omit their representation until a tracer
  requires it. This journey is that concrete requirement; it does not authorize a
  universal protocol foundation.

## Non-goals and protected boundaries

- Do not weaken or rewrite Stack, OrderedMap, explicit authoring, refinement,
  effect-separation, or resource-composition behavior to fit the new domain.
- Do not infer semantic authority from language/runtime identity, process success,
  transport compatibility, manifest order, paths, local-name resemblance, or adapter
  output without exact plan binding.
- Do not claim wall-clock deadlines, liveness, fairness, concurrency/partition/crash
  behavior, token security, exhaustive verification, protocol refinement,
  bisimulation, session typing, protocol composition, or arbitrary-domain generality.
- Do not add hosted discovery, implicit latest, version ranges, network acquisition,
  production deployment, a browser UI, or automatic Evidence transfer.
- Do not begin numerical-kernel files on this branch or include them in this PR.

## Revisioned work-dependency DAG

```text
I0 design-spec 0005 + substrate census
  -> I1 frozen refute-first author/package/consumer controls
  -> I-R1 contract, oracle, and anti-overfitting review (BLOCK)
  -> I1-S1 exact full-trace oracle successor
  -> I-R1b successor contract/oracle review (BLOCK)
  -> I1-S2 authority, phase, independence, and closure successor
  -> I-R1c successor contract/oracle review (BLOCK)
  -> I1-S3 exact execution, membership, authoring, alias, Evidence, and report successor
  -> I-R1d final contract/oracle review
  -> I2 optional protocol authoring/schema + exact Specification/profile/plan
  -> I3 isolated runner + two independent realizations + resurrection breaker
  -> I-R2 implementation, trace, isolation, and authority review
  -> I4 Claims/Evidence + exact manifest/product authority + both projections
  -> I-R3 end-to-end actor, Evidence, boundary, and overclaim review
  -> I5 durable documentation, recovery, and maintenance reconciliation
  -> I-G complete clean gate, full contract freeze, and one experienceable stacked PR
```

| Node | Owner and exclusive boundary | Required evidence, downstream gate, stop condition |
|---|---|---|
| I0 contract/census | lead; design-spec 0005 and this plan | frozen need/scenarios/falsifiers; exact reusable versus domain-local substrate; I1; stop if the bounded server-side observation cannot express the user need without wall-clock or concurrency claims |
| I1 red controls | lead/test owner; new interaction journey tests and negative fixtures only | intentional absent-protocol-surface/command failures plus independent oracles for authoring, traces, identity, isolation, breaker, Evidence, projections, boundaries, authority, atomicity, and regressions; I-R1; stop if a falsifier has no representation-independent oracle |
| I-R1 | uninvolved read-only reviewer | challenge semantic completeness, oracle independence, trace prefix/final-state shortcuts, token identity, terminal closure, finite-evidence wording, and phase precedence; I2 or explicit successor |
| I1-S1 | lead/test owner; journey tests and this plan only | freeze every exact input/before/output/after step, six trace lengths, all identity shapes, terminal suffixes, and breaker's valid prefix before its exact step-2 divergence; I-R1b |
| I-R1b | same uninvolved read-only reviewer | replay final-state-only, truncation, reorder/renumber, identity loss, fabricated intermediate, and terminal-resurrection attacks against the successor; I2 or another retained successor |
| I1-S2 | lead/test owner; journey tests and this plan only | bind breaker's first five exact traces and campaign-first mismatch; exact candidate import allowlist; separate valid unaccepted Evidence from schema/link-invalid mutations; exact process/acquisition/governed-input allowlists; closed authority/specification/theory values; duplicate input/output/declaration and stable phase diagnostics; I-R1c |
| I-R1c | same uninvolved read-only reviewer | replay every I-R1/I-R1b counterexample against the complete red successor; I2 or another retained successor |
| I1-S3 | lead/test owner; journey tests and this plan only | exact six-per-candidate command multiset; literal manifest-governed member list plus rogue-file rejection; post-link authoring semantics; normalized/symbolic/hard-link output aliases; missing/error/inconclusive Evidence; exact nested report values and full exclusions; I-R1d |
| I-R1d | same uninvolved read-only reviewer | replay all retained counterexamples against exact committed I1-S3 controls; I2 or another retained successor |
| I2 semantic artifacts | lead; optional schema/PSpec surface plus new lease Specification/profile/campaign-plan artifacts only | old Specifications remain valid; exact states/transitions/propositions/profile/plan are independently inspectable; I3; stop if a new canonical record kind or implicit cross-record relation is required |
| I3 candidates/campaign | lead; new lease runner, adapters, realization sources, breaker, and candidate reports only | isolated six-scenario sessions; complete ordered traces; two independent passes; exact resurrection challenge; source/build/runner provenance; I-R2; stop if shared code implements candidate state or the adapter cannot observe required identity/terminal behavior |
| I-R2 | uninvolved read-only reviewer | execute/reason over trace truncation/reordering, reused state, fabricated identity, candidate dependence, runner self-ratification, breaker specificity, cleanup, input mutation, and overclaim; I4 or successor |
| I4 product graph | lead/integrator; new lease Claims, Evidence, policy, Realizations, ProductContract/manifest, resolver/projections, and command only | exact fresh graph; two accepted registered realizations; breaker excluded/challenged; theory/package separation; directional boundary; atomic one-command experience; I-R3; stop if accepted Evidence needs an unimplemented observation mechanism or policy semantics must change globally |
| I-R3 | uninvolved end-to-end reviewer | reproduce all four actors, exact authority, negative controls, Evidence axes, semantic/deployment separation, known exclusions, and predecessor regressions; I5 or successor |
| I5 maintenance | lead; README, design docs, system map, user journeys, backlog, runbooks, and this plan | exact experience/safe failure/recovery, maintainers, exclusions, third-domain claim boundary, numerical successor route; I-G |
| I-G | lead; freeze and PR report | focused and complete clean gates, conventional range, 1:1 frozen spec/PR, exact command and real-underneath line, hosted gates; stop before fragment PR |

Parallel writers are not permitted on shared repository surfaces. Any later delegated
review is read-only and records its exact provider/model/tool provenance and disclosed
scope under the multi-provider workflow. Failed review/gate observations remain in this
plan and create explicit successor nodes rather than rewriting history.

## Implementation order and verification

1. Keep design-spec revision history and this plan ahead of code. The user need and
   falsifiers are frozen before I1; any correction is an explicit revision.
2. Census the existing schema, PSpec authoring boundary, candidate runner/report
   mechanics, graph/product authority, resolver, projections, and command dispatch.
   Reuse only behavior demonstrated domain-neutral; keep protocol semantics local.
3. Freeze I1 from all fourteen falsifiers. Its intentional failures name absent
   protocol authoring/inspection surfaces, not arbitrary import errors.
4. Obtain I-R1 PASS before production implementation. Preserve BLOCK observations and
   add successor controls without weakening accepted assertions.
5. Add the smallest optional semantic/artifact surface, then isolated candidates and
   campaign. Obtain I-R2 PASS before Claims/Evidence/product authority.
6. Build the exact graph and both consumer projections. The command consumes only the
   explicit manifest, reproduces fresh campaign results, resolves the exact policy, and
   publishes one closed report atomically. Obtain I-R3 PASS.
7. Reconcile durable project memory, run the focused and complete clean gates, freeze
   the full design spec, archive this plan, and open one PR based on
   `agent/resource-algebra-journey`.

Planned focused journey command:

```text
python3 -m unittest tests.journeys.test_i1_retry_safe_lease_session -v
```

Complete gate:

```text
python3 scripts/check_repo.py
```

Felt command:

```text
nix develop --command python3 -m semantic_packages protocol inspect \
  registry/lease-session/manifest.json \
  --output /tmp/lease-session-inspection.json
```

## Quality gates and evidence

- **Intent/specification:** design-spec 0005 names all actor outcomes, observations,
  equality assumptions, finite limits, fourteen falsifiers, and prohibited claims.
- **Authoring/link:** existing Specifications remain valid; malformed protocol graphs
  fail at stable raw/schema/link phases before candidate execution.
- **Realization:** two independently represented candidates build and pass; a retained
  resurrection candidate fails; candidate sessions are isolated and traces complete.
- **Evidence:** exact Claims/Evidence bind Specification, Realization, adapter, profile,
  plan, report, environment, mechanism, result, review, freshness, assumptions, and
  exclusions; contradictions and errors remain visible.
- **Integration:** theory/package projections and semantic/directional compatibility
  remain separate; exact policy resolution fails closed under every challenged axis.
- **Release:** felt/failure commands are reproducible, inputs immutable, output atomic,
  conventional commits pass, and local plus hosted repository checks are green.
- **Learning:** system map/backlog record exactly three demonstrated semantic domains
  and route the already-authorized numerical-kernel successor without treating this
  lease tracer as arbitrary-domain proof.

## Progress checklist

- [x] I0 design-spec 0005 user need/scenarios/falsifiers frozen
- [x] I0 substrate census and red-oracle inventory
- [x] I1 refute-first controls
- [x] I-R1 independent contract/oracle review — BLOCK retained
- [x] I1-S1 exact full-trace oracle successor
- [x] I-R1b successor contract/oracle review — BLOCK retained
- [x] I1-S2 authority, phase, independence, and closure successor
- [x] I-R1c successor contract/oracle review — BLOCK retained
- [x] I1-S3 exact execution, membership, authoring, alias, Evidence, and report successor
- [ ] I-R1d final contract/oracle review
- [ ] I2 semantic artifacts
- [ ] I3 candidates and campaign
- [ ] I-R2 implementation review
- [ ] I4 product graph, Evidence, projections, and command
- [ ] I-R3 end-to-end review
- [ ] I5 maintenance reconciliation
- [ ] I-G convergence, freeze, and one PR

## Discoveries and changed assumptions

- 2026-07-23: the operator selected both proposed anti-overfitting domains and fixed
  their sequence: interaction protocol first, approximate numerical kernel second,
  never bundled. The interaction choice releases this plan without choosing a universal
  protocol formalism.
- 2026-07-23: core-model `state / transition` and `protocol simulation` are durable
  intent, but the current canonical Specification schema deliberately omits their
  representation until a tracer needs them. Lease-session is the first concrete need.
- 2026-07-23: an explicit environment `expire` input preserves observable terminal
  behavior while keeping wall-clock scheduling out of scope. A real-time deadline claim
  would be a different feature and Evidence profile.
- 2026-07-23: I0 finds the optional Specification schema and PSpec nested-value
  transport are the only shared semantic surfaces that need extension. Existing
  Realization, Claim, Evidence, profile, policy, and registry-manifest schemas already
  admit a new concern/mechanism and exact package graph without a new record kind.
  Claims can address one retained protocol-conformance law while the new protocol block
  supplies its executable finite observation, avoiding a change to the byte-bound
  shared declaration linker.
- 2026-07-23: OrderedMap campaign/product/resolution modules are intentionally
  domain-bound and embedded in accepted report provenance. I0 rejects editing or
  generalizing them. Lease-session gets a local runner, resolver/report boundary, and
  command dispatch; it reuses only canonical record schemas, graph capture, theory
  projection, atomic publication patterns, and the explicit process adapter shape.
- 2026-07-23: two independently represented Python child adapters are sufficient to
  falsify state-machine representation coupling in this domain: one table-driven and
  one object/branch-driven, plus a separate resurrection breaker. Language diversity
  is not the semantic claim and is deferred; process isolation, source independence,
  complete traces, and exact provenance remain required.
- 2026-07-23: I1 freezes fourteen journey tests. Three pre-code controls pass for the
  contract/plan, exact predecessor bytes, and independent six-scenario/three-candidate
  oracle; the absent lease-session module is the sole intentional failure; ten
  production controls skip. The successor must turn the same suite green without
  weakening report closure, trace completeness, exact retry/conflict/token/terminal
  observations, breaker location, representation independence, Evidence/projection/
  boundary separation, structural fail-closure, output safety, or nonauthority.
- 2026-07-23: I-R1 BLOCK at exact committed red predecessor `5bde6dd`. The alleged
  independent oracle froze only six scenario names and three candidate IDs; successor
  checks allowed a one-step final-state-only transcript with fabricated empty identity,
  renumbered order, and omitted intermediate resurrection to pass. I1-S1 retains that
  failure and freezes all 19 exact steps per passing candidate: every input, before
  state, output, after state, opaque identity, scenario length/order, four-step terminal
  suffix, and the breaker's valid expiry prefix plus exact late-completion input.
- 2026-07-23: I-R1b BLOCK at exact committed successor `45e0c08`. Exact passing traces
  close final-state/truncation/reordering/identity/resurrection attacks, but the breaker
  may fail an earlier scenario; `ImportFrom.module` can hide a shared state engine;
  schema/link-invalid Evidence mutations are incorrectly treated as valid policy axes;
  acquisition/process/member aliasing lacks an exact allowlist; nested authority,
  Specification, and theory values remain open; and duplicate input/output/declaration
  plus stable protocol-phase diagnostics are incomplete. I1-S2 must close all six
  classes before I2/I3 can be accepted.
- 2026-07-23: I1-S2 expands the frozen suite to eighteen controls: seventeen active
  passes against the provisional implementation and one retained predecessor skip.
  It compares the breaker's first five scenarios and derives the first mismatch across
  campaign order; admits only `__future__`, `json`, and `sys` in each registered
  adapter; separates valid pending/challenging/assertion/withdrawn/inapplicable/policy-
  empty axes from schema/link-invalid mutations; binds all 14 governed paths and all 18
  child commands; closes manifest/plan/specification/theory/report values; and adds
  duplicate input/output/declaration plus stable raw/schema/protocol pointers.
- 2026-07-23: I-R1c BLOCK at exact committed successor `4bf4c45`. The execution
  allowlist fixed only a total and source set rather than six invocations of each exact
  two-argument command; the governed-file oracle discovered its own expected members
  and therefore admitted rogue unmanifested JSON; malformed protocol semantics could
  bypass the authoring surface; normalized, symbolic, and hard-link output aliases
  were not all challenged; missing/error/inconclusive Evidence states were absent; and
  nested candidate/scenario/Evidence values plus the complete known-exclusion set
  remained open. I1-S3 retains all six failures and closes them independently.
- 2026-07-23: I1-S3 keeps eighteen controls but strengthens their independent oracles.
  It freezes a command multiset with six exact invocations per source; names the nine
  governed registry records literally and injects a rogue valid record; observes
  protocol semantics only after raw/schema/link authoring phases; challenges lexical,
  symbolic, and inode aliases; distinguishes missing, error, and inconclusive Evidence;
  and closes every candidate representation/source/result, scenario result, Evidence
  identity, and six-part exclusion list. The focused journey is green with seventeen
  active passes and one historical predecessor skip; I-R1d must still challenge the
  exact committed successor before semantic artifacts are accepted.

## Decision log

- **Bounded domain:** choose one server-side retry-safe lease session over payment,
  consensus, or multiparty choreography. It exposes history, identity, conflict,
  environment transition, and terminality with a finite falsifiable campaign. Reopen
  if the finite server view cannot represent the selected user need honestly.
- **Evidence strength:** use finite scenario Evidence and report the limitation rather
  than calling the campaign a proof or protocol simulation theorem. Reopen if policy
  requires exhaustive assurance.
- **Package boundary:** require the same full actor lifecycle as OrderedMap while
  allowing domain-local protocol runner/semantics. Reuse mechanics only after the
  census demonstrates they are not Stack/OrderedMap semantics in disguise.

## Result and remaining work

The pre-implementation contract is frozen. I1-S3 is the current red-control successor;
I-R1d is the live convergence gate before the provisional semantic artifacts and
implementation may be accepted. The numerical-kernel journey is authorized but cannot
begin until the interaction-protocol PR opens.

## Stop and escalation conditions

Stop and revise the contract if the user need requires real elapsed-time guarantees,
concurrent interleavings, multiple active leases, durable crash recovery, or protocol
composition. Stop if satisfying the journey would weaken exact authority,
Claims/Evidence separation, compatibility separation, predecessor behavior, or the
finite-evidence wording. Escalate only a protected-intent/value choice; ordinary schema,
runner, representation, language, and module decisions remain implementation choices.
