# ExecPlan 0001: End-to-end tracer bullet

## Purpose and observable outcome

Produce a local prototype where a user can load the example Stack specification, see its claims and two registered realizations, run conformance checks, and receive an explainable compatibility result.

## Context

Read `AGENTS.md`, `ARCHITECTURE.md`, `docs/design/core-model.md`,
`docs/design/spec-language.md`, `docs/design/evidence-model.md`,
`docs/design/compatibility.md`, and `docs/design/tracer-bullet.md` first.

## Non-goals

- final language syntax;
- production authentication or hosting;
- automatic proof synthesis;
- general package resolver;
- performance optimization.

## Constraints

- Preserve representation independence; conformance compares declared observations,
  not host-language object identity or layout.
- Keep claim lifecycle, evidence review, evidence result, and assurance separate.
- Keep semantic satisfaction separate from realization interoperability.
- Retain failed, challenging, unknown, and inapplicable evidence.
- Use JSON as the temporary canonical interchange format while the `.pspec` surface
  syntax remains illustrative.
- Treat registry indexes and browser/API views as projections of canonical records,
  not separately maintained facts.

## Coordination model

The user retains mission and product-priority authority. This plan is a revisioned
work-dependency DAG: governing decisions authorize bounded work packages; hard
dependency edges order them; evidence and challenge edges may feed any affected
package or convergence gate; and passed gates release their declared dependents. The
lead owns graph framing, concern disposition, shared-surface integration assignment,
and convergence acceptance. Package owners may close reversible local nodes using
predeclared checks or delegated review without lead relay. Shared-file changes retain
one named integrator, and concurrent writers require disjoint paths or isolated
worktrees. The current broad audit changes must be captured as a stable baseline before
implementation writers begin.

Current cross-provider routing is operational policy for this plan, not architectural
authority: use Claude Sonnet 5 with explicit high effort for bounded routine execution,
and the Claude Fable 5 profile with explicit high effort for complex consultation or
skeptic review. Consultations are read-only and normally attach through `supports` or
`challenges`; implementation writers receive isolated worktrees and exclusive scope.
All launches use `agent-dispatch`. The lead integrates and accepts against repository
evidence, regardless of model. Each external node records the data scope approved for
disclosure and both its requested selector and runtime-reported model ID.

Planned gated waves:

| Wave | Delegated concerns | Integration gate |
|---|---|---|
| 1. design closure | identity/references; Stack observations and adapter boundary; profile/cost and evidence policy | reviewer ambiguity/counterexample matrix has no undisposed incompatible interpretation |
| 2. records | six linked schemas; independently authored positive/negative fixtures and gate wiring | schema and reference-integrity gates pass red-then-green |
| 3. execution substrate | loader/link checker; reference adapter; bounded proof probe | stable diagnostics and one named law evidence packet |
| 4. independent realizations | Rust and TypeScript implementations by separate authors; shared conformance reviewer | both satisfy the same external contract; broken variants fail |
| 5. product slice | evidence graph; compatibility explanation; browser/CLI projection | unknown, challenging, and unsupported results remain visible |
| 6. release and learning | fresh-clone reproduction; retrospective and next plan | gates reproduce and durable memory reflects discoveries |

Wave numbers communicate the dominant dependency order, not global barriers. Within
and across waves, a node may start when all declared hard predecessors have closed; it
need not wait for unrelated work. A convergence gate must close before another node
depends on its integrated result. Failed gates create successor revision nodes and
retain their observations. Owners, reviewers, dependencies, and exclusive paths are
recorded in delegation briefs rather than guessed in advance.

### Current design-closure DAG: DC1 revision 1

| Node | Edges and owner | Scope / write boundary | Evidence and status |
|---|---|---|---|
| DC1-I1 identity consultation | supports/challenges DC1-L1; Claude Sonnet 5 | read-only identity/reference analysis | exact typed-reference proposal and falsifiers returned; one contradictory ID-uniqueness statement rejected by the lead |
| DC1-S1 semantic skeptic | challenges DC1-L1 and DC1-G1; Claude Fable 5 | read-only Stack, adapter, effect, profile, and policy analysis | ambiguity matrix and O1–O8 obligations returned; conservative conflict/prohibition defaults retained |
| DC1-GPT1 diverse skeptic | challenges DC1-L1 and DC1-G1; internal Codex collaboration agent | read-only review of the same Wave-1 concerns | independently separated prohibition from priority and recommended blocking schema authorization until normative text lands |
| DC1-L1 integration | depends on the three concern packets; lead Codex | exclusive writer for affected design docs, ADRs, Stack sketch, and this plan | rejected by DC1-R1: cost semantics and conditional evidence scope remained ambiguous |
| DC1-R1 convergence review | challenges DC1-L1; independent Codex reviewer | read-only actual-diff audit | blocked the gate with two line-specific findings; all other concern dispositions passed |
| DC1-L2 successor integration | depends on DC1-R1; lead Codex | same exclusive shared surfaces | exact tracer cost predicate and conditional specification/realization evidence scope landed |
| DC1-R2 successor review | challenges/supports DC1-L2; same independent Codex reviewer | read-only focused regression review | both prior blockers closed; no new actionable finding |
| DC1-G1 convergence | depends on DC1-L2, DC1-R2, and G0 | lead acceptance owner | passed; Wave 2 schema/fixture work authorized |

The external consultations used Claude Code 2.1.212 through
`agent-dispatch --read-only`, pagu-box `strict`, the repository PWD, and explicit high
effort. Requested and runtime primary models matched: `claude-sonnet-5` for DC1-I1 and
`claude-fable-5` for DC1-S1; Claude also reported auxiliary
`claude-haiku-4-5-20251001` usage. Both briefs prohibited edits, delegation, and web
research. External disclosure was limited to the governing semantic-packages documents,
the schema/Stack scaffolds, and brief revision 1. Herdr remained lead-side and its
control socket was unavailable inside the sandbox.

### Current operational-memory DAG: MPW revision 1

| Node | Edges and owner | Scope / write boundary | Evidence and status |
|---|---|---|---|
| MPW-L1 runbook authoring | informed by the DC1 provider probes; lead Codex | exclusive writes to agent guidance, operations/lifecycle docs, README, checker, and this plan | capability/status matrix, secure dispatch patterns, reusable briefs, provenance, fusion, and failure handling authored |
| MPW-R1 requirements audit | challenges MPW-L1; independent Codex reviewer | read-only capability and governance inventory | required conditional claims, provenance, fusion rules, and anti-patterns returned |
| MPW-R2 convergence review | challenges MPW-L1; same independent reviewer | read-only actual-diff audit | blocked on a Herdr child-boundary contradiction, flattened verification status, unsupported route wording, and missing plan evidence |
| MPW-L2 successor integration | depends on MPW-R2; lead Codex | same exclusive shared surfaces | child-side `HERDR_*` is now a stop condition; verified, advertised-but-unprobed, and unsupported routes are distinct; this DAG retains the failed review |
| MPW-R3 successor review | challenges/supports MPW-L2; independent Codex reviewer | read-only focused regression review | passed after one final mandatory-entrypoint wording correction; no material objection remains |
| MPW-G1 repository-memory convergence | depends on MPW-L2, MPW-R3, and G0 | lead acceptance owner | passed; `git diff --check` and Nix-backed `python3 scripts/check_repo.py` both passed |

### Current record-schema DAG: W2 revision 1

| Node | Edges and owner | Scope / write boundary | Closure evidence |
|---|---|---|---|
| W2-S1 schema realization | depends on DC1-G1; Claude Sonnet 5 | isolated `agent/wave2-schemas` worktree; exclusive `schemas/` writer | seven-file family returned; exact primary runtime `claude-sonnet-5`; lead metaschema validation passed |
| W2-GPT1 schema skeptic | challenges W2-S1/W2-G1; internal Codex collaboration agent | read-only same governing concern | 26-case counterexample matrix returned; exposed hidden seventh Adapter-record risk |
| W2-L1 schema integration | depends on W2-S1 and W2-GPT1; lead Codex | exclusive shared-surface integrator | adapter fixed as nested Realization descriptor; strict schema interfaces frozen for fixtures |
| W2-F1 fixture authoring | depends on W2-L1; independent GPT fixture writer | exclusive `fixtures/records/` | 8 valid records, 11 schema-negative records, and 8 isolated link-negative graphs returned; schema controls passed |
| W2-D1 diagnostic-oracle review | challenges W2-F1/W2-G1; independent internal Codex reviewer | read-only fixture and expected-diagnostic audit | blocked checkpoint: wrong-kind/version and reference-surface controls were missing, and diagnostics were not yet actionable exact oracles |
| W2-R1 semantic convergence review | challenges/supports W2-L1/W2-F1; Claude Fable 5 | read-only actual-diff audit | no schema redesign blocker; exposed Claim-state, adapter-shape, profile-set, policy-event, date-format, and expected-reason gaps retained for the successor |
| W2-L2 successor integration | depends on W2-D1/W2-R1; lead Codex | exclusive schema, core-model, dependency, and plan surfaces | bounded Claim lifecycle, exact profile-set semantics, policy event resolution, and asserted date validation landed; lead schema controls pass |
| W2-F2 successor fixture oracle | depends on W2-L2; independent GPT fixture writer | exclusive `fixtures/records/` | complete: 15 schema-negative controls with expected reasons and 21 isolated link graphs with actionable exact diagnostics |
| W2-D2 successor oracle review | challenges W2-L2/W2-F2; same independent internal Codex reviewer | read-only actual-diff regression review | blocked checkpoint: order-independent profile-set equality and typed reference-role paths still lacked decisive controls |
| W2-F3 final oracle successor | depends on W2-D2; independent GPT fixture writer | exclusive `fixtures/records/` | complete: one zero-diagnostic order-independence graph and eight remaining typed-role/coherence falsifiers; 15 schema and 29 link negatives total |
| W2-D3 checkpoint review | challenges/supports W2-F3; same independent reviewer | read-only focused regression review | passed; all W2-D2 gaps closed with isolated exact controls |
| W2-P1 reviewed checkpoint | depends on W2-L2, W2-F3, W2-D3, and lead controls | lead acceptance owner | passed for checkpoint: 7 metaschemas, 8 flat valid records, 15 schema negatives, 29 link negatives, 1 valid link graph, 105 parsed JSON; does not imply W2-G1 acceptance |
| W2-C1 durable record gate | depends on W2-P1; Claude Sonnet 5 plus lead integration | isolated checker worktree; exclusive checker surfaces | pending |
| W2-G1 records gate | depends on W2-L2, W2-F2, W2-C1, successor review, and G0 | lead acceptance owner | pending |

The published design baseline is commit `87ffbb1` and draft PR #1. Wave 2 runs on a
stacked isolated branch so schema implementation cannot silently expand that review.
Delegated briefs retain the same approved external disclosure scope as DC1 and add only
the schema/fixture/checker artifacts created in this worktree.

W2-S1 used Claude Code 2.1.212 through `agent-dispatch`, pagu-box `strict`, read-write
PWD mode in the isolated worktree, explicit high effort, and no web research. The
requested and runtime primary model was `claude-sonnet-5`; Claude also reported
auxiliary `claude-haiku-4-5-20251001` usage. Its exclusive scope was `schemas/` and the
lead independently reran the repository and JSON Schema metaschema gates.

W2-R1 used Claude Code 2.1.212 through `agent-dispatch --read-only`, pagu-box
`strict`, the isolated worktree PWD, explicit high effort, and no web research. The
requested and runtime primary model was `claude-fable-5`; auxiliary
`claude-haiku-4-5-20251001` usage was reported. Git/Python probes were denied inside
the child, so its manual artifact review does not replace lead-executed validation.
W2-D1 was an independent internal Codex collaboration node and did execute the fixture
shape controls. Both reviews received the same governing worktree independently and
neither model identity nor Fable's PASS overrode W2-D1's decisive missing falsifiers.

## Specification changes required before implementation

The design audit found prerequisites that the original implementation order omitted:

1. Define provisional identity, version pinning, local declaration IDs, and reference
   integrity without assuming semantic version compatibility.
2. Define Stack's empty-pop behavior and extensional observation/equivalence.
3. Define the conformance adapter protocol, including generated values, observations,
   and adapter-observed effect events.
4. Define persistence as an observable obligation over both the pre- and post-`push`
   logical stacks.
5. Define the execution profile, workload, and cost measure referenced by the
   performance claim, even if acceptable performance evidence remains absent.
6. Define how a consumer policy treats missing, inapplicable, supporting, challenging,
   and assertion-only evidence.

## Proposed implementation order

1. Record the identity/reference invariants and temporary JSON interchange decision.
2. Define strict provisional JSON Schema records for `Specification`, `Realization`,
   `Claim`, `Evidence`, `RealizationProfile`, and `ConsumerPolicy`.
3. Add valid and invalid fixtures, including dangling references, unknown fields, and
   mismatched subject/profile versions; validate them in the repository gate.
4. Encode Stack as linked canonical records and keep `specs/stack.pspec` explicitly
   illustrative until a parser is justified.
5. Implement a loader and link checker with stable diagnostics and no silent dropping
   of required or unsupported aspects.
6. Define the adapter protocol and implement one in-process reference model.
7. Select one bounded proof integration and machine-check one named Stack law without
   treating that proof assistant as the platform's universal foundation.
8. Add independently authored Rust and TypeScript realizations plus adapters.
9. Run shared property/model checks against both realizations and the resource/effect
   observations; demonstrate rejection of deliberately broken fixtures.
10. Persist the specification, realization, claim, evidence, and profile/policy links
    locally with provenance.
11. Expose a minimal CLI or web browser that makes evidence mechanism, result,
    applicability, assumptions, exclusions, and unknowns visible.
12. Implement an explainable compatibility query with separate semantic and
    directional realization-compatibility conclusions.
13. Record discoveries, revise the core model, and decide whether OrderedMap is the
    next semantic package.

## Quality gates

- Schema validation accepts every valid fixture and rejects every invalid fixture;
  undeclared required data is not silently ignored.
- The loader rejects dangling and version-mismatched references with stable,
  actionable diagnostics.
- Evidence and acceptance records pin their governing input revisions; a relevant
  predecessor change marks downstream acceptance stale until its gates are rerun.
- One named law is checked by a machine-invoked proof checker whose version,
  assumptions, inputs, and result are recorded.
- Both independent realizations satisfy the same reusable conformance suite.
- A law-breaking realization and a persistence-breaking realization are rejected with
  useful counterexamples.
- The effect boundary and its exclusions are shown explicitly; no claim is made about
  effects the adapter cannot observe.
- The browser/CLI distinguishes claim lifecycle from proof, test, benchmark, audit,
  and assertion evidence, and shows challenging, inapplicable, and unknown evidence.
- An unsubstantiated performance claim remains visible and is not reported as proved
  or measured.
- Compatibility output demonstrates semantic substitutability separately from its
  directional boundary mechanism and includes an operationally compatible but
  semantically unacceptable case.
- A fresh clone can run the documented gate commands and reproduce recorded fixture
  results.

## Verification commands

Current repository-structure gate:

```sh
python3 -m pip install -r requirements-dev.txt
python3 scripts/check_repo.py
```

On a host without ambient Python, the equivalent reproducible invocation currently is:

```sh
nix shell nixpkgs#python3 --command python3 scripts/check_repo.py
```

Schema milestones additionally use `jsonschema[format]==4.26.0`; the checker must
enable format assertion explicitly. A Nix-only equivalent is a temporary Python
environment composed with `python3Packages.jsonschema` and its format dependencies.

Expected observation: `Repository checks passed.` with exit status 0. Each later
milestone must add its executable command and expected observation here before its
progress item may be marked complete. Gate the command's exit status, not a grep or
summary proxy.

## Progress

- [x] Repository knowledge scaffold
- [x] Research-to-design handoff audit
- [x] Temporary canonical interchange decision
- [x] Identity and reference invariants
- [x] Stack empty behavior and extensional observation
- [x] Adapter operation/observation/effect boundary
- [x] Persistence witness and falsifier
- [x] Execution profile, workload, and cost measure
- [x] Consumer treatment of evidence states
- [x] Conditional specification/realization claim and evidence scope
- [x] Design-closure ambiguity and counterexample review
- [ ] Six core JSON schemas
- [ ] Positive and negative schema fixtures
- [ ] Spec loader
- [ ] Reference model
- [ ] Proof integration
- [ ] Rust realization
- [ ] TypeScript realization
- [ ] Shared conformance suite
- [ ] Evidence records
- [ ] Browser/CLI
- [ ] Compatibility explanation
- [ ] Retrospective and next ExecPlan

## Discoveries

- The existing `schemas/spec.schema.json` is a permissive scaffold, not a completed
  milestone: it neither models the six core entities nor closes references.
- The illustrative Stack law uses equality over an abstract carrier without defining
  extensional observation, so it is not yet portable executable semantics.
- Empty-pop behavior, generator bounds, the persistence witness, and the observable
  effect boundary are undefined.
- `amortized_O(1)` lacks a cost measure, workload, and profile. The initial fixture's
  `status: asserted` conflated claim state with evidence; the field was removed, so
  the claim remains visibly unsupported until linked evidence exists.
- The original plan omitted `RealizationProfile` and `ConsumerPolicy` schemas even
  though both are resolver inputs in the architecture.
- Same-spec registration is only a candidate relation. Semantic substitutability
  requires policy-, profile-, claim-, and evidence-relative evaluation.
- Realization compatibility is directional and context-dependent; language/runtime
  metadata alone cannot establish it.
- The repository gate currently checks required project-memory files, Markdown links,
  and JSON syntax. Schema validation, reference integrity, permanent negative
  fixtures, proof checking, conformance, and evidence provenance must become
  executable gates as their milestones land.
- The documented Python command is not available in every host environment. The
  fresh-clone gate needs a small reproducible development environment before it can
  be considered portable.
- `lang-bang` demonstrates a useful project-system ladder: keep durable invariants,
  volatile work, decisions, and derived views in different homes; de-risk with
  refuting probes; and promote repeated prose facts into generated or checked
  artifacts. ExecPlan 0001 adopts those principles without its mature-project
  orchestration overhead.
- A content-free dispatcher probe on 2026-07-18 verified strict read-only Claude
  launches through Claude Code 2.1.210 with explicit high effort. `sonnet` resolved
  to `claude-sonnet-5`.
  Both `fable` and the pinned `claude-fable-5` selector reported runtime usage as
  `claude-opus-4-8`; therefore evidence must retain requested and resolved identities
  rather than treating the friendly selector as provider proof.
- The tested homelab generation was activated on 2026-07-18. The live Claude Code
  2.1.212 profile resolved the pinned selector to runtime `claude-fable-5` through
  `agent-dispatch --read-only` with explicit high effort. The official manifest
  hashes, dedicated dispatcher regression test, Home Manager activation build,
  formatter, full homelab flake checks, and post-activation content-free probe all
  passed.
- Read-only external review prevents repository mutation but still discloses readable
  prompts, files, and tool results. The current approval boundary rejected sending
  repository documents during this probe, so no project content was disclosed. A
  future Claude node must record explicit authorization for its scoped disclosure.
- A content-free Herdr pilot created and supervised an interactive Sonnet 5 pane,
  detected its state, delivered follow-up input, and exposed output to the lead. Herdr
  is therefore the preferred observable PTY/worktree control plane around delegated
  processes, but not a replacement for `agent-dispatch`: it does not enforce sandbox,
  provider, depth, concurrency, or read-only policy.
- The prior dispatcher forwarded Herdr's arbitrary-process-launch socket into strict
  children, creating a confused-deputy escape from pagu-box. The activated generation
  removes that forwarding, adds a regression test, and records the boundary in its
  ADR. Inspection of the live wrapper confirms that neither `HERDR_*` nor Herdr's
  configuration directory is forwarded into delegated children.
- DC1 model-diverse review converged on exact `(kind, id, version)` record addresses,
  flat per-specification-version declaration IDs, top-first repeated-pop Stack
  observation, harness-owned comparison, opaque durable adapter handles, and
  boundary-scoped effect evidence. Sonnet's packet also proposed ID uniqueness across
  all same-kind records, which contradicted its own multi-version rule; the integrated
  invariant instead makes the full address tuple unique and permits one ID at multiple
  exact versions.
- The policy list conflated concern priority with proposition polarity. DC1 separates
  `required | preferred | optional | ignored` from semantic prohibitions. Selected
  challenging evidence blocks a required concern; missing or inapplicable evidence
  does not prove a required negative obligation. The conservative behavior is
  explicit and may later be parameterized without erasing contradictory evidence.
- DC1-R1 rejected the first integrated draft because named cost fields did not yet
  define a falsifiable proposition and evidence appeared to require a realization even
  for a specification-law proof. DC1-L2 now fixes the tracer profile, workload, unit,
  aggregation, bound, and supporting methods, and makes realization/adapter scope
  conditional on claim subject and evidence mechanism. The failed review remains in
  the DAG rather than being rewritten as an initial pass.
- W2-GPT1 found that treating an adapter as a canonical exact reference would silently
  create a seventh record kind. For the tracer, each immutable Realization instead
  embeds one versioned adapter descriptor; realization-executing Evidence repeats its
  `(id, version)` selector and the link checker requires an exact match. Multiple
  independently versioned adapters remain deferred until they justify another local
  namespace or canonical kind.
- W2-D1 proved that eight cleanly isolated link-negative graphs were still an
  insufficient oracle: a checker could ignore wrong-kind and exact-version handling or
  skip several reference-bearing surfaces and pass. W2-F2 therefore expands controls
  before checker implementation and makes each expected diagnostic include a code,
  source path, JSON pointer, and requested target.
- W2-R1 found that free-form Claim lifecycle could smuggle result/assurance language,
  JSON Schema date formats are annotations unless the validator asserts them, and
  policy event patterns could drift from the referenced effect contract. The successor
  uses a provisional lifecycle enum, explicit exact-set Evidence profile scope, asserted
  date validation, and a link rule binding policy patterns to declared events.
- W2-D2 rejected the first expanded oracle because unequal profile sets did not prove
  order-independent equality and typed local-role paths remained skippable. W2-F3 adds
  one zero-diagnostic `[A, B]` versus `[B, A]` graph plus isolated cost-measure,
  carrier, operation-family, Claim, and policy coherence falsifiers. W2-D3 passed the
  successor; the failed checkpoint review remains visible rather than being rewritten.
- The W2-P1 lead control used `jsonschema` 4.26.0 with `rfc3339-validator` 0.1.4
  and an explicit `FormatChecker`: all 7 schemas passed metaschema validation; 8 flat
  valid records and all valid/link-graph records passed shape validation; all 15 schema
  negatives rejected; all 105 JSON files parsed. This temporary lead control supports
  a checkpoint only; W2-C1 must make the same observations durable in the repository
  before W2-G1 can close.

## Decision log

- Start with Stack to validate the pipeline; move to OrderedMap only after the loop closes.
- Keep the storage format replaceable and the surface syntax provisional.
- Use JSON as the tracer bullet's temporary canonical interchange format; see
  [ADR 0003](../../decisions/0003-temporary-json-interchange.md).
- Treat unknown and assertion-only concerns as visible outcomes, not implicit passes.
- Use human-directed, lead-accountable collaboration over a revisioned work-dependency
  DAG; see
  [ADR 0004](../../decisions/0004-human-led-agent-team.md).
- Use model/provider diversity for independent concerns and reviews when useful, but
  derive authority and assurance only from the governing brief, artifacts, and evidence.
- Route routine execution to Sonnet 5 and complex consultation or skepticism to the
  Fable 5 profile, normally at high effort. Keep this choice in the active plan so it
  can change with availability and observed performance; do not encode it as a
  constitutional or architectural guarantee.
- Use Herdr for lead-side pane/worktree observability and interaction while retaining
  `agent-dispatch` as the bounded provider and sandbox boundary. Do not grant the
  Herdr control socket to delegated children.
- Address canonical records and references by exact typed `(kind, id, version)` tuples,
  with flat stable local declaration IDs per specification version; see
  [ADR 0005](../../decisions/0005-exact-typed-references.md).
- Treat prohibition as a required negative semantic obligation rather than an
  evidence-priority rank. Contested required concerns and unproved prohibitions do not
  pass by default; see
  [ADR 0006](../../decisions/0006-separate-priority-from-prohibition.md).
- Treat the multi-provider capability and verification-status matrix and secure dispatch workflow as
  operational project memory, with versioned facts re-probed before reuse; see
  [the multi-provider workflow](../../operations/multi-provider-workflow.md).

## Result

Wave 1 design closure passed DC1-G1 after one rejected integration and a reviewed
successor. No product implementation has started. Wave 2 is authorized: define the six
linked provisional schemas, positive fixtures, and falsifying fixtures, then close the
schema/reference-integrity gate before loader work begins.

## Stop and escalation conditions

- Stop before schema implementation if identity/reference or Stack observation rules
  are still ambiguous enough to permit incompatible interpretations.
- Stop and revise the design if a schema or resolver would collapse claim lifecycle,
  evidence review, evidence result, and assurance into one field.
- Stop and revise the design if a conformance adapter requires either realization's
  representation to become normative.
- Escalate to the user before changing constitutional intent, weakening an observable
  requirement, or selecting a universal proof/transport foundation.
- Treat a falsifying fixture as a design result; do not weaken it merely to recover a
  green gate.
