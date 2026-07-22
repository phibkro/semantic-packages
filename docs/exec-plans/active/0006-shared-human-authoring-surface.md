# ExecPlan 0006: shared human authoring surface

## Purpose and observable outcome

Enable a theory author to express the accepted Stack and OrderedMap Specification
records through one documented human-facing authoring contract and receive exact
canonical records plus actionable diagnostics, without hidden identity/default rules
or a universal semantic logic.

The first bounded outcome is smaller: freeze what both accepted domains actually
require, demonstrate why the illustrative Stack `.pspec` cannot yet round-trip, and
prevent parser or syntax selection until an independently reviewed contract comparison
passes.

## Context and repository map

ExecPlans 0001, 0004, and 0005 accepted complete Stack, OrderedMap, and exact-profile
lifecycles. ADR 0003 deliberately kept canonical JSON temporary and `.pspec`
illustrative for ExecPlan 0001; later accepted plans retained that boundary without
turning its scoped status into a permanent format decision. The governing sources are
the constitution, `ARCHITECTURE.md`, `docs/design/core-model.md`,
`docs/design/spec-language.md`, the two accepted canonical Specification records,
`schemas/spec.schema.json`, and the
[A1 research probe](../../research/shared-human-authoring-surface.md). The accepted A2
boundary is recorded in
[ADR 0016](../../decisions/0016-representation-neutral-authoring-boundary.md).

ExecPlan 0003 remains independently active for cold-human inspection. Its participant
observation is not authoring Evidence and this plan does not relabel it.

## Non-goals and constraints

- Do not select final syntax, file extension, parser framework, serialization, hosted
  logic, or proof assistant during A1.
- Do not infer local IDs, versions, imports, references, or defaults from spelling,
  order, file paths, or declaration categories.
- Do not convert hosted semantic strings into checked meaning without an explicit
  logic/checker boundary and Evidence mechanism.
- Do not mutate accepted canonical Stack/OrderedMap bytes or claim that authoring
  usability has passed without an eligible human observation.
- Preserve plural mathematics, exact identity, Claim/Evidence separation, and semantic
  versus realization compatibility.

## Specification changes

A0/A1 make no normative Specification change. They classify existing canonical fields
into explicit structural identity/references and presently hosted semantic payloads.
Any later elaboration contract must reproduce the same exact canonical records for the
two accepted domains or propose a separately reviewed migration; author convenience
cannot silently change product meaning.
Exact reproduction means canonical record-document equality, not preservation of JSON
formatting or source bytes. Deterministic serialization remains a separately tested
contract if a later option requires it.

## Revisioned work-dependency DAG

```text
A0 roadmap/source census
  -> A1 two-domain authoring falsifier
  -> A-R1 independent boundary review
  -> A-G1 problem-contract gate
  -> A2 reversible authoring-contract options and diagnostics
  -> A-R2 independent option review
  -> A-G2 contract choice or operator escalation
  -> A3 red two-domain round-trip and ambiguity controls
  -> A4 minimal elaborator
  -> A-R4 implementation review
  -> A5 author journey, documentation, and maintenance
  -> A-R5 independent end-to-end review
  -> A-G final convergence
```

| Node | Owner / exclusive boundary and integration point | Evidence packet, reviewer, gate, and escalation |
|---|---|---|
| A0 roadmap census | lead; read-only roadmap/governing docs; integrates into this plan | exact merged base and route ordering; lead verifies; A1; operator owns priority conflict |
| A1 boundary falsifier | lead/integrator; research note/test, plan, backlog/system-map links, checker requirements | exact digests, identity, per-family IDs, nested references, absent imports/surface, missing-ID and hosted-text controls; A-R1; escalate semantic contradiction to operator |
| A-R1 boundary review | uninvolved read-only reviewer; integrates concerns into lead-owned plan only | commands/results, counterexamples, omissions, solution-neutrality, PASS/BLOCK; A-G1; protected-boundary concern to operator |
| A-G1 problem gate | lead; plan-only disposition | retained review packet and full gate; releases A2 or successor A1; values choice remains unauthorized |
| A2 option probe | future owner; research notes/fixtures only; integrates into lead-owned option matrix | exact round-trip/ambiguity/diagnostic/recovery comparison; A-R2; escalate materially different author experiences without decisive evidence |
| A-R2 / A-G2 | independent reviewer then lead; review writes none, lead integrates plan/ADR proposal | option attacks and dispositions; choose smallest reversible contract or stop for operator; no parser release without PASS |
| A3 red contract | lead/test owner; exclusive authoring-contract fixtures/tests and proposed dependency-context ADR | Stack + OrderedMap exact-output relative to an explicit finite context; opaque-label nonauthority; invalid bytes/duplicate members/unsupported format; ambiguous/missing/wrong-kind ID/reference; hosted-payload and deterministic-diagnostic controls; independent contract review; A4 |
| A4 minimal elaborator | future implementation owner; exclusive new authoring module plus approved dependency metadata | frozen A3 controls, no canonical predecessor changes, focused/full gates; independent implementation review A-R4; toolchain/migration concern escalates |
| A-R4 | uninvolved read-only reviewer | parser containment, deterministic output/diagnostics, hidden-default and semantic-overclaim attacks; A5 or successor |
| A5 journey/maintenance | lead/integrator; author command/docs, user-journey controls, check integration, plan | exact two-domain author tasks, regression/sensitivity, recovery, limitations, one non-control human-facing adapter, and required operator-coordinated eligible uninvolved-author observation; A-R5 |
| A-R5 / A-G | uninvolved reviewer then lead; no reviewer writes, lead owns completion move | full lifecycle, negative controls, docs, full local/hosted gates, conventional squash handoff; operator owns unresolved product-direction fork |

## Implementation steps in dependency order

1. A0 reads the merged roadmap and governing authoring boundaries.
2. A1 freezes exact Stack surface, Stack/OrderedMap canonical record, and schema bytes.
3. A1 executes the smallest probes for shared mechanics, distinct domain shape, flat
   explicit IDs, absent OrderedMap surface, missing Stack canonical IDs, and opaque
   semantic payloads.
4. A-R1 independently attempts to falsify the resulting problem statement.
5. Only after A-G1 may A2 compare reversible authoring contracts. No parser code starts
   before A-G2.
6. A2 retains canonical-record input as the executable conformance control, rejects
   hidden-ID inference and an unneeded independent IR, and proposes one format-neutral
   outcome boundary for A-R2 challenge.

## Quality gates and evidence required

A1 runs:

```text
python3 -m unittest tests.research.test_shared_human_authoring_surface_probe -v
python3 scripts/check_repo.py
```

Expected A1 observation is five focused PASS results covering exact frozen bytes;
shared-but-distinct field shapes; exact identities, per-family declaration sets and
nested local/profile references with imports absent; canonical IDs missing from the
illustrative surface with no OrderedMap surface; and six hosted-text schema fields.
The full gate must report 32 research probes and preserve all predecessor summaries.

A-R1 must inspect exact inputs and probe sensitivity, distinguish lossless structural
elaboration from semantic checking, and confirm no solution is smuggled into the
problem statement. Every later node adds its exact commands and negative observations
before release.

A2 adds:

```text
python3 -m unittest tests.research.test_shared_human_authoring_options -v
```

Expected A2 observation is ten PASS results: two exact canonical controls are valid;
missing root identity, duplicate/dangling local IDs (including dependent-edge
cascades), unknown/wrong-kind inputs, and dangling profile members have exact paths;
blank hosted text retains the observed coarse root diagnostic; ordinary JSON collapses
duplicate members; invalid UTF-8/JSON remain host exceptions; existing diagnostics
replay deterministically; and array
reordering changes document equality without changing local addresses or graph validity.

A3 adds an intentionally red predecessor gate:

```text
python3 -m unittest tests.journeys.test_a3_shared_human_authoring_contract -v
```

Before A4 exists, the successor topology must be 19 tests: one exact-input and
dependency-gap control PASS, one intentional failure naming only the absent
`semantic_packages.authoring` module, and seventeen successor controls SKIP. The frozen
successor contract requires exact Stack and OrderedMap documents relative to explicit
finite profile contexts; no-default format and dependency inputs; provenance-only
labels; format/UTF-8/JSON/duplicate-member precedence; all-or-none outcomes; exact
identity/local-reference/hosted-text diagnostics; order preservation; deterministic
replay; schema/link phase barriers; used and validated dependency contents; wrong-kind
source rejection; stable raw detail; and isolated input/output snapshots. A4 must turn
this same suite green without weakening or deleting an assertion.

## Progress checklist

- [x] A0 roadmap and governing-source census
- [x] A1 candidate two-domain boundary falsifier
- [x] A-R1 independent boundary review
- [x] A-G1 problem-contract gate
- [x] A2 authoring-contract option probe
- [x] A-R2 independent option review
- [x] A-G2 contract choice or operator escalation
- [x] A3 red round-trip/ambiguity controls
- [ ] A4 minimal elaborator
- [ ] A-R4 implementation review
- [ ] A5 actor journey, documentation, and maintenance
- [ ] A-R5 end-to-end review
- [ ] A-G final convergence

## Discoveries and changed assumptions

- 2026-07-22: A0 confirms the merged roadmap names shared human authoring ahead of
  refinement or a third domain; this is an authored research route, not a new priority
  choice.
- 2026-07-22: A1 candidate finds a shared eight-family structural envelope plus one
  Stack-only derived-observation family, with 11 Stack and 18 OrderedMap declaration
  IDs. The current Stack sketch omits multiple canonical IDs and there is no OrderedMap
  sketch. Six semantic payload categories remain schema-valid nonempty strings. These
  facts reject immediate parser implementation but do not select a replacement.
- 2026-07-22: A-R1 BLOCK. Green focused/full gates did not make the claimed exact
  boundary sensitive: the first test version counted IDs without enumerating their
  per-family sets or nested carrier/profile/local references, and the note mentioned
  imported addresses although both inputs omit imports. The DAG also lacked explicit
  integration points, evidence packets, escalation owners, and expected observations
  for downstream packages. A1 successor enumerates those facts and expands ownership;
  no parser, syntax, IR, or canonical-format option is promoted by the correction.
- 2026-07-22: A-R1 successor PASS at exact commit `0e14b0a`. Independent replay
  confirms exact root identities, per-family declaration sets, global uniqueness,
  equivalence-carrier edges, performance operation families and exact profile/local
  references, plus explicit import absence. The note now separates observed facts from
  future import rules, and the DAG supplies integration, evidence, review, gate, and
  escalation ownership. Five focused and 32 total research controls pass; the complete
  repository gate preserves 221 actor journeys and every report/Evidence/proof lane.
  No material concern remains. A2/A3 must still decide and test whether declaration-
  array ordering belongs to output document equality even though addressing is order-
  independent.
- 2026-07-22: A-G1 PASS. The accepted result is the exact two-domain authoring problem
  and falsifier only. It releases reversible A2 option research but grants no authority
  to choose syntax, parser, authoring IR, canonical migration, hosted logic, implicit
  defaults, or a materially different author workflow.
- 2026-07-22: A2 candidate compares four routes. Direct canonical-record input is the
  only executable two-domain control and remains temporary rather than a final human
  surface. Hidden-ID inference is rejected. A separate authoring IR is rejected until
  a second frontend or non-identity transformation demonstrates need. An explicit
  lossless surface remains a candidate but cannot be selected before grammar and human
  evidence. Six controls expose exact identity/reference diagnostics, one actionable-
  diagnostic deficit for blank hosted text (`SCHEMA_INVALID` at `#`), and the distinction
  between document array order and address semantics. The proposed A3 boundary accepts
  explicit bytes/format/source identity and returns an exact canonical document or
  ordered source-local diagnostics without owning a grammar. A-R2 must challenge this
  comparison before A-G2 chooses any implementation contract.
- 2026-07-22: The first A2 focused run retained one oracle BLOCK: renaming `push` to
  duplicate `empty` produces both the expected duplicate-ID diagnostic and a truthful
  dependent dangling `operationFamily` diagnostic. The successor oracle requires both
  ordered results rather than suppressing the cascade; no checker behavior changes.
- 2026-07-22: A-R2 BLOCK. The candidate left `source identity` undefined, allowing a
  reading where provenance could fill or override canonical identity; it omitted raw
  duplicate-member, invalid-byte/JSON, wrong-kind, and deterministic replay controls;
  and the plan could close with JSON alone while human observation was optional. The
  successor renames this input to an opaque diagnostic label with a nonauthority
  metamorphic obligation, expands A2/A3 raw and semantic diagnostics, and requires a
  non-control human-facing adapter plus eligible uninvolved-author observation before
  final convergence. The coarse blank-payload diagnostic may remain a red A3
  predecessor; it does not block option research by itself. No operator values call has
  yet been reached.
- 2026-07-22: A-R2 successor PASS at exact commit `48333d2`. Ten focused controls and
  the full 42-research/221-journey repository gate pass. The reviewer confirms opaque
  labels have no authority, raw ambiguity and diagnostic deficits are sufficient A3
  predecessors, JSON cannot close the lifecycle, the IR rejection remains justified,
  and blank hosted text may remain an explicit red A3 case. Remaining A3 details are
  exact format dispatch, raw-parse precedence, all-or-none outcome/location shape, and
  deterministic source-to-array mapping. No operator values call exists at this gate.
- 2026-07-22: A-G2 PASS. ADR 0016 accepts the reviewed representation-neutral boundary
  with exact `canonical-spec-json-v1` control dispatch, provenance-only labels,
  all-or-none document/diagnostic outcomes, raw rejection before record validation,
  explicit identity, source-order preservation without position semantics, and no
  independent IR. This releases A3 red controls. It does not select final surface
  grammar or author workflow; unresolved later surface values still escalate.
- 2026-07-22: A3 candidate exposes one omitted mechanical input in ADR 0016: both
  retained Specifications reference separate profile records and each produces two
  exact dangling-reference diagnostics in isolation. Proposed ADR 0017 makes the
  dependency context finite, explicit, required, and discovery-free; record labels
  remain provenance-only and success is link-valid relative to that exact context.
  The focused predecessor has the required 17-test topology: one PASS, one intentional
  missing-module failure, and fifteen SKIP. This is a contract correction, not a choice
  of syntax, workflow, registry, or acquisition authority. Independent A3 review must
  attack the context and red oracles before A4 is released.
- 2026-07-22: The dispatcher-requested Fable 5 A-R3 attempt returned no output during
  its bounded interval and was terminated. This is retained as provider unavailability,
  not review evidence. A separately framed internal reviewer was assigned as the
  explicit fallback.
- 2026-07-22: A-R3 BLOCK at `12974b8`. The reviewer reproduced the 1 PASS / 1 FAIL /
  15 SKIP topology and showed that an empty module cannot pass vacuously, but found the
  dependency contents, validation phase, labels, input order, and duplicate addresses
  under-specified. A4 could have treated any nonempty tuple as permission to ignore its
  records. The suite also omitted a schema-valid wrong source kind, missing local
  identity/reference fields, opaque nonempty hosted-text preservation, and stable raw
  detail. The A3 successor adds those exact controls and reconciles ADR 0017's ordering;
  no syntax, workflow, registry, acquisition, or other operator values choice is made.
- 2026-07-22: A-R3 successor BLOCK at `3635e6c`. The prior gaps close and the revised
  1 PASS / 1 FAIL / 17 SKIP topology cannot pass through an empty or dependency-blind
  module, but the wrong-context and duplicate-address oracles did not also require an
  all-or-none failure. Invalid dependency checks asserted only path order and a code
  set, allowing truthful codes at false root pointers. The next successor requires
  `ok == false`, no document, and exact ordered `(code, path, pointer)` tuples. No
  product-direction decision is involved.
- 2026-07-22: A-R3 final PASS at exact clean commit `49a9923`. The reviewer reproduces
  the final 1 PASS / 1 intentional FAIL / 17 SKIP topology and confirms that mixed
  document-plus-diagnostic outcomes and false root pointers now fail. Exact dependency
  schema diagnostics follow caller input order, while wrong context, invalid context,
  and duplicate addresses all require `ok == false` and no document. ADR 0017 is
  accepted for A4. The complete repository gate runs all 240 actor journeys and every
  retained record, loader, adapter, candidate, research, governance, report, Evidence,
  and proof lane; its sole failure is the declared absent A4 module and the same 17
  successor controls skip. A3 remains an intentionally red checkpoint and must not
  merge until A4 turns the same suite green without weakening an assertion.
- 2026-07-22: A4 candidate `8caed67` turns all 19 frozen controls green. The complete
  repository gate passes 240 actor journeys, 42 research probes, and every retained
  record, loader, adapter, candidate, governance, report, Evidence, and proof lane.
- 2026-07-22: The dispatched Sonnet 5 A-R4 route resolved the requested model at high
  effort but STOPPED before product review: the strict child mounted the linked `/tmp`
  worktree without its parent `/srv/.../.git` metadata, so it could not establish the
  exact revision or clean state. This is tooling/provenance evidence only. A separately
  framed internal reviewer was assigned explicitly.
- 2026-07-22: A-R4 BLOCK at exact clean `8caed67`. Strict raw probes pass, but ordinary
  dependency boundary values escape the promised all-or-none observation: `None` as
  the container raises `TypeError`, non-dependency items raise `AttributeError`, and a
  `MappingProxyType` document raises during `deepcopy` despite the public `Mapping`
  annotation. The successor freezes container/item/label/document and recursive-value
  failures, retains `Mapping`, and must convert them into deterministic diagnostics
  before A-R4 can pass. No final surface or operator values decision is involved.
- 2026-07-22: A-R4 successor BLOCK at exact clean `5c3dee2`. All prior counterexamples
  close, 21 focused controls and the complete 242-journey repository gate pass, and
  mapping proxies, nested proxies, `UserDict`, and recursive context behave correctly.
  One conforming custom `Mapping` whose iterator raises `RuntimeError` still escapes
  because snapshot containment catches selected exception types. The next successor
  freezes throwing top-level/nested JSON containers and contains ordinary `Exception`,
  while leaving process-control exceptions untouched. No direction choice is involved.

## Decision log

| Question | Evidence and concerns | Decision / reopen observation |
|---|---|---|
| implement the illustrative `.pspec` grammar now | it cannot supply exact accepted Stack IDs without undocumented derivation, has no OrderedMap comparison, and cannot check hosted semantic strings | reject for A1; reopen only after an explicit contract passes exact two-domain round-trip and ambiguity controls |
| treat canonical JSON as the final author surface | JSON already preserves exact records but human ergonomics have not been observed; ADR 0003 calls it temporary | retain as one A2 comparison option, not a decision |
| choose one formal logic for semantic payloads | current accepted domains use plural observations/laws/resources and externally governed proof/conformance Evidence | prohibited absent a concrete scoped need; a hosted logic may be selected per aspect later |
| add a syntax-neutral authoring IR now | only one executable input exists and the current transformation is identity; a second structural model would create drift before it enables composition | reject until a second frontend or non-identity transformation demonstrates the need |
| preserve declaration-array order or canonicalize it | array positions do not address declarations, but record-document equality observes array order | require each adapter to preserve explicit source declaration order for exact output; do not infer semantic meaning from position; reopen if canonical record equality changes |
| accept the format-neutral boundary or escalate now | A-R2 confirms the contract closes authority/diagnostic/JSON-inertia gaps, remains reversible, and leaves final surface experience open | accept ADR 0016 and release A3; no operator decision exists until evidence cannot distinguish materially different surface workflows |
| validate external references without ambient discovery | both retained Specifications are invalid as isolated graphs because their profile references resolve only with separate dependency records | propose an explicit finite caller-supplied dependency context in ADR 0017; A3 review must pass before A4 may implement it |

## Result and remaining work

A0 through A3 are complete. The project now has an executable, independently
reviewed two-domain statement of the authoring deficit without committing to final
surface syntax. A2/A-R2/A-G2 accept the representation-neutral boundary and release A3
red controls; A-R3 accepts the exact red contract and releases A4. Parser implementation,
grammar, independent authoring IR, canonical format migration, semantic type checking,
non-control surface, and human usability remain unimplemented and unaccepted.

## Stop and escalation conditions

- stop if any proposal derives stable identity or exact references from hidden rules;
- stop if author convenience changes canonical meaning or erases unsupported aspects;
- stop if parsing hosted text is described as semantic checking;
- stop before a syntax or canonical-format migration without two-domain round-trip,
  diagnostic, recovery, and independent-review evidence;
- escalate if equally viable options encode materially different author workflows or
  require a hard-to-reverse universal foundation with no actor evidence.
