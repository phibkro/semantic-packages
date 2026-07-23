# Design spec 0003: bounded effect-separation observation

## Contract status

Frozen on 2026-07-22 for one complete stacked feature and its experienceable pull
request, based on PR #17 at `bc8607b`. Any successor revision must record the
observation that requires it; implementation discoveries never silently expand
adapter-reported behavior into a whole-process effect claim.

## Felt user journey

A package author or Evidence reviewer can run one retained two-domain probe and see
whether changing only the adapter-reported event channel leaves the bounded semantic
campaign observation unchanged, while permitted, forbidden, unspecified, and errored
events retain distinct dispositions.

```text
nix develop --command python3 scripts/effect_separation_probe.py \
  --output /tmp/effect-separation.json
```

The command executes the repository-owned exact Stack and OrderedMap fixture campaigns
in five named modes: quiet baseline, optional `debug.emit`, forbidden `io.read`,
unspecified domain-specific event, and each domain's retained adapter-error control.
OrderedMap's error response carries `io.read`; Stack's does not carry an event. It
writes one deterministic report and prints:

```text
observed bounded effect separation: 2 domains, 10 observations, 0 semantic drifts, 2 effect challenges, 2 execution errors -> /tmp/effect-separation.json
```

For each domain, the optional, forbidden, and unspecified variants have the same
non-effect declaration outcomes and case observations as the quiet baseline. Optional
and unspecified variants retain their exact event ledgers without challenging the
effect declaration. The forbidden variant changes only the effect declaration to
`challenges`, so the whole campaign challenges without manufacturing a law or resource
failure. Each adapter-error variant remains an execution `error`; OrderedMap retains
the forbidden event observed before its error, while Stack truthfully retains no event.
An incomplete semantic campaign is never reclassified as an effect-conformance
counterexample.

The report calls this `bounded-separation-observed`. It never calls it program
noninterference, effect erasure for arbitrary contexts, external-effect absence,
purity, or semantic equivalence.

## Goal

Turn the existing adapter-event distinction into one inspectable cross-domain product
observation: instrumentation and effect policy remain orthogonal to the bounded
semantic projection unless a forbidden observed event challenges the exact effect
declaration. Preserve execution failure as a separate axis. Give future effect-language
and Evidence work a concrete falsifier without selecting a universal effect calculus.

## Values and priorities

1. **Separation over purity folklore.** A stable semantic projection under one reported
   event variation is useful evidence about this harness boundary, not proof that the
   implementation has no other effects.
2. **Retained events over erasure by deletion.** “Erasure” means the semantic projection
   is invariant when the event ledger is excluded; the original ordered event ledger
   remains present and reviewable in the complete observation.
3. **Concern locality over global contamination.** A forbidden event challenges the
   effect declaration and campaign aggregate, not unrelated laws or resources.
4. **Errors over false counterexamples.** An incomplete campaign caused by adapter or
   process failure remains `error`; an event observed before failure does not turn it
   into conformance Evidence.
5. **Two-domain reproduction over Stack-specific confidence.** Stack and OrderedMap
   must independently exhibit the same separation using their existing domain-shaped
   reports without one runner becoming normative for the other.
6. **Exact boundary over ambient execution.** The probe owns a finite, reviewed set of
   repository fixture commands and campaign inputs. It performs no registry-driven
   execution, package discovery, network access, or latest selection.

## Observable contract

### Exact campaigns and variants

- The probe runs only the retained Stack and OrderedMap fixture adapters under the
  exact campaign plans already governed by their runners and repository gate.
- Each domain has exactly five observation roles in stable order: `quiet`, `optional`,
  `forbidden`, `unspecified`, and `adapter-error`. The report also retains the exact
  adapter mode: Stack uses `reference`, `optional-event`, `forbidden-event`,
  `unspecified-event`, and `status-error`; OrderedMap uses `reference`,
  `optional-event`, `forbidden-event`, `unspecified-event`, and
  `adapter-error-forbidden`.
- `quiet` reports no events and is the semantic baseline. `optional` reports exactly
  `debug.emit`; `forbidden` reports exactly `io.read`; and `unspecified` reports the
  domain's retained nonmatching event. OrderedMap's adapter-error response also reports
  `io.read`; Stack's retained adapter-error response reports no event.
- Event classification comes from each exact Specification contract: `debug.emit` is
  optional, proper descendants of `io.*` are forbidden, and the retained nonmatching
  event follows `default: unspecified`. A prefix resemblance such as `io` or `io.`
  does not acquire wildcard-match authority.

### Semantic projection and comparison

- A domain's semantic projection contains every case observation and every declaration
  outcome except its exact effect declaration. It excludes only the ordered event
  ledger, effect-declaration outcome, and campaign aggregate that necessarily reflects
  an effect challenge or execution error.
- The probe compares each nonbaseline semantic projection to the quiet projection by
  exact immutable value equality. It does not rerun or reinterpret hosted law text,
  infer observational equivalence beyond the existing campaign, or compare private
  implementation state.
- Optional, forbidden, and unspecified projections must equal quiet. The forbidden
  variant must have exactly one challenged declaration, the exact effect declaration.
  Optional and unspecified variants must have no challenged declaration.
- The adapter-error variant must remain `error`; it is reported separately from the
  three complete semantic comparisons. Any partial observations remain visible, but
  they cannot establish projection equality or inequality.

### Report and failure behavior

- Success exits `0`, writes one stable `effect-separation-observation-v1` JSON report
  atomically, emits the exact summary above, and leaves all fixtures, plans, accepted
  reports, records, and registries unchanged.
- The report names the adapter-invocation event boundary, exact domain/variant names,
  ordered event ledgers, campaign and effect results, projection comparison state,
  assumptions, exclusions, and fixed conclusion `bounded-separation-observed`.
- A semantic drift, wrong event classification, concern spillover, missing variant,
  changed exact plan/fixture binding, or unexpected execution result exits `1`, emits
  deterministic diagnostics, and preserves any existing output. There is no partial
  success report.
- Required-argument failure exits `2`. Output may not alias any governed input or
  repository fixture. The command executes no path obtained from registry metadata.

## Constraints and protected boundaries

- Preserve every accepted Specification, plan, adapter fixture, campaign report,
  Claim, Evidence, manifest, resolver decision, and predecessor/successor byte.
- Preserve each existing runner's report shape and domain ownership. A shared
  projection/comparison helper may consume both shapes but may not make Stack's runner,
  transition model, or declaration set authoritative for OrderedMap.
- Keep event classification, semantic declaration outcomes, execution status, Evidence
  review, and consumer policy selection as distinct axes.
- Retain `adapter-event-completeness` as an assumption and adapter-external effects as
  an exclusion. Do not state that an empty or permitted reported trace proves absence
  of filesystem, network, runtime, or other process effects.
- Do not create a canonical effect algebra, effect row, handler semantics, global scope
  taxonomy, new Evidence mechanism, resolver rule, policy token, Claim, or assurance.
- Do not describe exact projection equality as a theorem of contextual equivalence,
  noninterference, commutation, or arbitrary instrumentation erasure.

## Mechanism freedom

The contract fixes the command, exact bounded observations, comparison meaning,
diagnostic behavior, and report. It does not prescribe internal dataclasses, shared
projection representation, process orchestration, serializer structure below the
published report, module layout, or caching. Existing runners may be composed or a
smaller observation boundary introduced if every protected report and behavior remains
unchanged.

## Falsifiers

The feature is false if any of these observations occur:

1. Either domain is absent, uses a nonexact campaign, or reports fewer/more than the
   five frozen variants.
2. Optional `debug.emit` is hidden, challenges any declaration, or changes the semantic
   projection relative to quiet.
3. Forbidden `io.read` fails to challenge the exact effect declaration and campaign,
   changes a law/resource/other declaration outcome, or changes the semantic projection.
4. An unspecified event is dropped, treated as optional/forbidden, or used to claim
   effect absence.
5. `io` or `io.` matches `io.*`, or a proper descendant such as `io.read` does not.
6. An adapter error becomes `supports`/`challenges`, establishes a projection comparison,
   invents an event for Stack, or loses OrderedMap's event observed before failure.
7. The probe mutates an accepted input, follows registry execution metadata, searches
   for packages/versions, accesses the network, or publishes a partial report.
8. Stack-specific declarations, transitions, or runner types become authority for the
   OrderedMap observation, or either existing runner/report regresses.
9. Output, documentation, or PR language upgrades the result to whole-process purity,
   arbitrary effect erasure, contextual noninterference, semantic equivalence, accepted
   Evidence, or arbitrary-domain generality.
10. Existing authoring, refinement, record, resolver, campaign, Evidence, maintenance,
    proof, or complete repository checks regress.

## Definition of done

- The documented command is experienceable from a clean checkout and produces the
  exact summary plus a complete deterministic report.
- Refute-first controls derive from all ten falsifiers, including output/input
  immutability, exact plan/fixture binding, wildcard boundaries, concern locality,
  partial-error nonauthority, and unchanged predecessor reports.
- Both existing domain runners and their accepted report/Evidence checks remain green;
  the complete repository gate passes without weakened assertions.
- README, effect semantics, system map, user journey, backlog, assumptions, exclusions,
  maintenance owner, and reopen triggers agree.
- An independent review attacks projection omissions, event/effect coupling, error
  handling, cross-domain leakage, execution authority, and overclaim. Every material
  concern and successor remains in the active ExecPlan.
- One PR maps 1:1 to this frozen design spec and opens only when the two-domain probe is
  experienceable. Its description begins with the command and one line stating what is
  real underneath.

## Known exclusions

- This observes separation inside exact bounded campaigns; it does not prove
  noninterference for arbitrary programs, traces, contexts, concurrency, or time.
- It does not observe effects outside adapter-reported invocation events and does not
  validate the completeness or faithfulness of that reporting channel.
- It does not accept effect conformance Evidence, modify consumer resolution, define
  effect composition/handlers, or relate effects across Specification versions.
- It does not decide whether unspecified events should be permitted by a future policy;
  it only preserves the exact Specification's current `unspecified` disposition.
- Two domains and a finite variant set demonstrate one repeated separation property,
  not arbitrary-domain or arbitrary-effect generality.

## Recovery and reopen triggers

Revert the eventual single squash commit to remove the probe and its derived report;
all accepted runners, fixtures, campaigns, records, and decisions remain unchanged.
Failed observation preserves existing output, so a corrected implementation can rerun
the exact probe.

Reopen if a third domain has multiple effect declarations, event order itself becomes
semantic, operations permit effect-dependent results, concurrent traces require a
partial order, Evidence needs an independently declared observation scope, a new effect
mechanism cannot use the current classification, or a consumer needs effect composition
rather than bounded separation.

## Revision history

- **2026-07-22, revision 1:** Initial active contract. Selects the first unconditional
  post-refinement backlog item and turns existing event classification into a bounded
  two-domain evaluator observation. It distinguishes semantic projection invariance,
  effect concern locality, and execution failure while retaining the completeness and
  external-effect exclusions. Not yet frozen for PR.
- **2026-07-22, revision 2:** Correct the initial false symmetry discovered by the
  exact fixture census before planning or implementation. OrderedMap's retained
  adapter-error mode reports `io.read`; Stack's retained `status-error` mode reports no
  event. Both remain execution errors and establish no projection comparison. The user
  journey and bounded-separation goal are unchanged.
- **2026-07-22, revision 3 (frozen):** Freeze the observable contract after independent
  red-control and implementation reviews, exact native projection/ledger/effect-surface
  counterexamples, the experienceable command and safe-failure path, durable project
  memory, and the complete clean repository gate. No Claim, Evidence, resolver rule,
  effect algebra, external-effect observation, or generality claim was added.
