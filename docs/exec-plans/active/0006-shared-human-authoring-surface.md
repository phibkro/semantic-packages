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
illustrative until those tracers exposed authoring needs. The governing sources are
the constitution, `ARCHITECTURE.md`, `docs/design/core-model.md`,
`docs/design/spec-language.md`, the two accepted canonical Specification records,
`schemas/spec.schema.json`, and the
[A1 research probe](../../research/shared-human-authoring-surface.md).

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

| Node | Owner and exclusive boundary | Required evidence / downstream gate |
|---|---|---|
| A0 roadmap census | lead; read-only roadmap and governing docs | accepted next node and protected constraints; releases A1 |
| A1 boundary falsifier | lead/integrator; research note, research test, this plan, route links | exact input digests, two-domain declaration census, missing surface/ID controls, hosted-text boundary; A-R1 |
| A-R1 boundary review | uninvolved read-only reviewer | challenge whether facts justify withholding parser/syntax selection and whether any identity/semantic need is omitted; A-G1 |
| A-G1 problem gate | lead | accept/revise the authoring problem only; no solution authority |
| A2 option probe | future owner; research fixtures/notes only | compare canonical JSON authoring, explicit low-sugar surface, and syntax-neutral authoring contract against exact round trip and diagnostics |
| A-R2 / A-G2 | independent reviewer then lead or operator | reject hidden defaults/universal logic; escalate if product values, not evidence, decide materially different author experiences |
| A3--A5 | future plan revisions with exclusive implementation/test/docs scopes | refute-first round trip, minimal green elaboration, actor observation, regression and maintenance |

## Implementation steps in dependency order

1. A0 reads the merged roadmap and governing authoring boundaries.
2. A1 freezes exact Stack surface, Stack/OrderedMap canonical record, and schema bytes.
3. A1 executes the smallest probes for shared mechanics, distinct domain shape, flat
   explicit IDs, absent OrderedMap surface, missing Stack canonical IDs, and opaque
   semantic payloads.
4. A-R1 independently attempts to falsify the resulting problem statement.
5. Only after A-G1 may A2 compare reversible authoring contracts. No parser code starts
   before A-G2.

## Quality gates and evidence required

A1 runs:

```text
python3 -m unittest tests.research.test_shared_human_authoring_surface_probe -v
python3 scripts/check_repo.py
```

A-R1 must inspect exact inputs and probe sensitivity, distinguish lossless structural
elaboration from semantic checking, and confirm no solution is smuggled into the
problem statement. Every later node adds its exact commands and negative observations
before release.

## Progress checklist

- [x] A0 roadmap and governing-source census
- [x] A1 candidate two-domain boundary falsifier
- [ ] A-R1 independent boundary review
- [ ] A-G1 problem-contract gate
- [ ] A2 authoring-contract option probe
- [ ] A-R2 independent option review
- [ ] A-G2 contract choice or operator escalation
- [ ] A3 red round-trip/ambiguity controls
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

## Decision log

| Question | Evidence and concerns | Decision / reopen observation |
|---|---|---|
| implement the illustrative `.pspec` grammar now | it cannot supply exact accepted Stack IDs without undocumented derivation, has no OrderedMap comparison, and cannot check hosted semantic strings | reject for A1; reopen only after an explicit contract passes exact two-domain round-trip and ambiguity controls |
| treat canonical JSON as the final author surface | JSON already preserves exact records but human ergonomics have not been observed; ADR 0003 calls it temporary | retain as one A2 comparison option, not a decision |
| choose one formal logic for semantic payloads | current accepted domains use plural observations/laws/resources and externally governed proof/conformance Evidence | prohibited absent a concrete scoped need; a hosted logic may be selected per aspect later |

## Result and remaining work

A0 is complete and A1 is a review candidate. The project now has an executable,
two-domain statement of the authoring deficit without committing to its solution.
A-R1 and A-G1 remain before option research. Parser, grammar, authoring IR, canonical
format migration, semantic type checking, and human usability remain unimplemented and
unaccepted.

## Stop and escalation conditions

- stop if any proposal derives stable identity or exact references from hidden rules;
- stop if author convenience changes canonical meaning or erases unsupported aspects;
- stop if parsing hosted text is described as semantic checking;
- stop before a syntax or canonical-format migration without two-domain round-trip,
  diagnostic, recovery, and independent-review evidence;
- escalate if equally viable options encode materially different author workflows or
  require a hard-to-reverse universal foundation with no actor evidence.
