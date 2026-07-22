# Design spec 0005: retry-safe lease-session semantic package

## Contract status

Pre-implementation contract for one interaction-protocol tracer bullet and one stacked
pull request. Revision 1 freezes the user need, observable journey, values, falsifiers,
and Definition of Done on 2026-07-23 before production code. Those surfaces may change
only through an explicit numbered revision that records the observation requiring it
and reopens affected red controls. Representation, algorithms, module boundaries,
languages, and other implementation mechanisms remain free below that line. The full
contract freezes for PR only after review and complete convergence.

This feature is stacked on the finite resource-composition journey at exact head
`99fe79450b90e323d7f5f6c9df789045cc627063`. It is deliberately separate from the
later approximate-numerical-kernel contract and PR.

## User need

A package consumer integrating a distributed worker coordinator needs to choose a
lease-session implementation that preserves one logical holder through acquisition
retries and competing requests, rejects the wrong holder, closes permanently after
completion or expiry, and exposes the deployment boundary required to use each
semantically acceptable realization. The consumer needs to see exactly which finite
traces were checked, what Evidence supports or challenges each realization, and what
remains assumed or unknown; matching function names or transport compatibility is not
enough.

A theory author needs to publish that interaction meaning without choosing an internal
state representation, timer implementation, thread model, programming language, or
transport. A package author needs a bounded adapter contract against which an
independently implemented state machine can be exercised. A theory consumer needs the
protocol meaning and specification-scoped assurance without package implementation
details.

## Felt user journey

From a clean checkout, the package consumer runs:

```text
nix develop --command python3 -m semantic_packages protocol inspect \
  registry/lease-session/manifest.json \
  --output /tmp/lease-session-inspection.json
```

The command uses only the exact manifest and its authenticated finite members. It
reproduces the fixed protocol campaign against two registered independent realizations
and one deliberately broken candidate, checks the resulting Claim/Evidence graph under
the manifest's exact policy and profile, and prints:

```text
inspected lease-session 0.1.0: 2 registered realizations accepted, 1 breaker challenged across 18 trace cases; boundary=directional; satisfaction=policy-relative -> /tmp/lease-session-inspection.json
```

The deterministic `protocol-package-inspection-v1` report contains the exact
Specification, profile, policy, campaign plan, candidate provenance, six ordered trace
results per candidate, declaration-scoped Claims and Evidence, the two accepted
semantic decisions, the breaker's challenge, and each accepted candidate's directional
deployment boundary. It concludes only `bounded-protocol-package-observed`.

## Observable protocol contract

The Specification `lease-session` version `0.1.0` describes one server-side observable
session with four abstract states:

- `available`, the initial state;
- `held`, with one logical client and one logical lease token;
- `completed`, terminal;
- `expired`, terminal.

Inputs and outputs carry opaque client, request, and lease-token values. Equality of
those opaque values is observable; their representation is not. The six required
finite scenarios are:

1. **Acquire:** client A with request `r1` acquires from `available`, receives one token
   `t1`, and the session becomes `held(A,t1)`.
2. **Retry stability:** repeating the same client/request acquisition while held
   returns the same token `t1`, creates no second lease, and leaves the state unchanged.
3. **Exclusive holder:** client B's competing acquisition while A holds `t1` returns
   `busy`; A and `t1` remain the holder.
4. **Wrong-holder rejection:** completion with a token unequal to `t1` returns
   `denied`; A and `t1` remain the holder.
5. **Completion closure:** A completes with `t1`, receives `completed`, and all later
   acquire, renew, expiry, or completion inputs leave the session `completed` while
   returning a terminal response rather than resurrecting a lease.
6. **Expiry closure:** an explicit environment `expire` input while held transitions
   to `expired`; a later completion with `t1` is rejected and all later inputs leave
   the session `expired`.

The campaign supplies the expiry input directly. It observes ordering and terminal
closure but makes no claim about elapsed wall-clock duration, scheduler fairness, or
automatic timer delivery.

## Values and constraints

1. **Trace behavior over container snapshots.** Acceptance depends on ordered
   interaction histories, intermediate outputs, and terminality rather than a final
   extensional collection observation.
2. **Meaning over mechanism.** States and transitions are abstract semantic labels;
   implementations may use enums, tables, objects, actors, processes, or another
   representation.
3. **Opaque identity over representation.** Client, request, and token equality is part
   of observation; token syntax, allocation, randomness, and memory identity are not.
4. **Finite evidence over universal claims.** The campaign checks six named scenarios.
   Passing them is Evidence for the scoped claims, not a proof of every trace, liveness,
   refinement, or distributed correctness.
5. **Claims separate from Evidence.** Protocol propositions live in the Specification;
   realization Claims scope them; fresh reports support or challenge those Claims.
6. **Semantic acceptance separate from deployment.** Both realizations may be
   semantically acceptable while requiring different directional process/runtime
   boundaries. Transport reachability cannot satisfy the protocol policy.
7. **Exact authority over discovery.** The manifest and every member are exact and
   immutable. No implicit latest, registry search, network acquisition, or source-tree
   scan may influence the decision.
8. **Plural semantics over a universal protocol calculus.** This bounded labelled
   transition candidate must coexist with Stack/OrderedMap algebra, effects, resources,
   proofs, tests, profiles, and policy without redefining them.

## Required actor outcomes

### Theory author

The author can express the four abstract states, initial and terminal states, input and
output observations, transition obligations, equality assumptions for opaque values,
and the six named protocol propositions. Invalid state targets, duplicate transition
keys, unknown labels, an initial terminal state, and unreachable required states fail
with stable source-relative diagnostics. Publishing the Specification does not publish
a realization or Evidence.

### Package author

Two independently represented implementations expose the same bounded adapter
protocol. Each is built from its own source and exercised in an isolated session per
scenario. The shared runner may define framing and observations but must not implement
the state machine for a candidate. A deliberately broken candidate resurrects a lease
after expiry and is rejected with the smallest exact counterexample.

### Theory consumer

The theory projection shows the protocol vocabulary, transition propositions,
assumptions, exclusions, specification-scoped Claims/Evidence, and unknowns. It does
not expose realization source, adapter commands, package campaign internals, or a
consumer selection.

### Package consumer

The exact policy/profile query shows both registered realizations as semantically
acceptable, the breaker as challenged and ineligible, every Evidence axis and finite
trace limitation, and a separate directional deployment boundary for each accepted
candidate. Missing, stale, mismatched, assertion-only, challenged, or error Evidence
fails closed for a required protocol concern.

## Frozen falsifiers

The feature is false if any of the following occurs:

1. Existing Stack, OrderedMap, explicit-authoring, refinement, effect-separation, or
   resource-composition bytes or accepted behavior change to admit the protocol domain.
2. A protocol-less existing Specification becomes invalid, or the new authoring shape
   silently assigns protocol meaning to an omitted field.
3. Unknown/duplicate states, inputs, outputs, transition keys, or declaration IDs;
   dangling transition endpoints; an initial terminal state; or an unreachable required
   state passes authoring/link validation.
4. A realization can pass by returning only the expected final state while omitting,
   reordering, or fabricating intermediate inputs, outputs, states, opaque identities,
   or terminal observations.
5. Repeating client A/request `r1` produces a different token, a second lease, or any
   state change and is still accepted.
6. A competing client or wrong token displaces the holder, completes the lease, or
   mutates the held identity and is still accepted.
7. Completion or expiry can be followed by any state other than the same terminal
   state, or late completion after expiry is accepted.
8. The resurrection breaker is not challenged at its exact smallest failing step, or
   a passing realization is rejected by an oracle derived from the breaker's code.
9. Candidate code, mutable process state, stderr, declaration order, paths, local IDs,
   or language-specific object identity becomes semantic authority.
10. Claims, Evidence, profiles, policies, adapters, campaign plans, reports, or manifest
    members are stale, mismatched, incomplete, forged, or inapplicable yet contribute
    to an accepted protocol decision.
11. Package Evidence leaks into the theory projection, protocol acceptance is inferred
    from process/transport compatibility, or deployment compatibility is inferred from
    semantic acceptance.
12. The command discovers inputs, accesses the network, reuses candidate state between
    scenarios, aliases output to a governed input, mutates inputs, executes an
    unmanifested candidate, or changes prior output after a failed run.
13. Documentation or output claims real-time deadlines, fairness, liveness, crash or
    partition safety, consensus, cryptographic token security, exhaustive trace proof,
    protocol composition, universal session typing, semantic refinement, or arbitrary-
    domain generality.
14. The exact command, focused negative controls, independent review, fresh campaign,
    complete actor journey, or full repository gate does not pass from a clean exact
    head.

## Definition of Done

- The exact felt command builds/runs the three candidates, reproduces all eighteen
  scenario results, writes the closed report atomically, and prints the fixed summary.
- The authored protocol surface is optional, exact, source-diagnostic, and able to
  reject every structural falsifier without prescribing implementation state layout.
- Two independent realizations pass all six scenarios; the retained resurrection
  breaker fails the exact expiry-closure step; candidate isolation and complete traces
  are observable.
- Exact Claims and fresh Evidence support every required protocol concern for the two
  registered realizations. Challenging, error, unsupported, and inapplicable axes
  remain visible and fail closed under the exact policy.
- Both consumer projections and directional boundary explanations are executable;
  neither crosses semantic/package authority.
- Review attacks the oracle, state isolation, trace completeness, exact authority,
  Evidence scope, projection separation, boundary direction, and overclaim. Every
  material concern is retained and disposed in ExecPlan 0010.
- README, semantic design, system map, user journeys, backlog, recovery, ownership,
  exclusions, and reopen triggers agree.
- One PR maps 1:1 to this design spec and opens only after the complete journey is
  experienceable and all local gates pass. The PR report begins with the exact command
  and one sentence stating what is real underneath.

## Known exclusions

- The protocol is one finite server-side observation candidate, not a multiparty
  choreography, universal labelled-transition-system format, session-type calculus,
  bisimulation/refinement engine, or protocol-composition rule.
- `expire` is an explicit campaign input. No Evidence covers wall-clock deadlines,
  timer delivery, fairness, concurrency races, scheduling, network delay, partitions,
  process crashes, durable recovery, or lease transfer.
- Opaque tokens are compared only for equality. Their entropy, secrecy, authenticity,
  collision resistance, allocation strategy, and wire representation are unclaimed.
- Six finite scenarios do not prove every possible trace. Adapter faithfulness and
  observation completeness remain explicit assumptions unless separately evidenced.
- The command uses local pinned candidates. It does not acquire hosted packages,
  deploy a coordinator, contact a service, or make a production rollout decision.
- This is the third semantic domain and a stronger anti-overfitting observation, not
  proof that the architecture fits arbitrary protocols or arbitrary mathematics.

## Recovery and reopen triggers

Revert the eventual squash commit to remove the lease-session schema surface,
Specification, candidates, reports, records, command, and derived documentation. The
Stack, OrderedMap, authoring, refinement, effect, and resource predecessors remain
unchanged. Failed runs preserve governed inputs and prior output, so the exact command
can be replayed after correcting the explicit finite source set.

Reopen when a concrete user needs payload schemas, multiple concurrent leases,
transfer, crash recovery, durable logs, wall-clock guarantees, fairness/liveness,
partial-order traces, multiparty roles, protocol refinement/evolution, compositional
session types, stronger adapter-faithfulness Evidence, or hosted acquisition.

## Revision history

- **2026-07-23, revision 1 (user need and falsifiers frozen):** Selects the operator's
  interaction-protocol route as semantic domain three. Freezes one retry-safe lease
  session, six finite scenarios, two independent registered realizations, one
  resurrection breaker, policy-relative consumer inspection, and fourteen falsifiers.
  Leaves every implementation mechanism open and makes the explicit expiry-input and
  finite-evidence limits part of the observable contract before code.
