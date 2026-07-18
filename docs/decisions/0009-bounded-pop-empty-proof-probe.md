# ADR 0009: Bounded `pop-empty` proof probe

## Status

Accepted experimentally for ExecPlan 0001 only.

## Context

The tracer requires one named Specification law to be checked by a machine-invoked
proof checker with explicit inputs, assumptions, provenance, and review state. The
canonical Stack law `pop-empty` states that `pop(empty) == None`; it is universally
quantified and is not narrowed by the bounded conformance profile. The repository does
not select a universal proof assistant or a machine-readable proposition language.

A local preflight found Lean 4.30.0 already available and exposed two important traps:
`sorry` can otherwise leave a successful exit with a warning, and declared axioms can
pass elaboration. A diverse review supported the bounded model but required tighter
statement linkage, evidence wording, and fixture disposition. It also questioned the
proposed `--trust=0` flag; the lead verified directly that the installed Lean 4.30.0
binary documents and accepts `--trust=0`.

## Decision

Implement one replaceable, core-only Lean probe for exact declaration
`(specification, stack, 0.1.0)#pop-empty` and exact Claim
`(claim, stack-pop-empty-law, 0.1.0)`. Model the Specification's extensional observation
space as finite top-first sequences and prove, universally for `A : Type u`, that
observing `pop` on the empty sequence produces `Option.none`.

`List A` is a mathematical model of the already defined observation space, not a
required Realization representation. The result can support only this statement's
satisfaction in that model and the operation of the proof-evidence pipeline. It does
not establish Realization conformance, derivability from other laws, consistency or
completeness of the whole Specification, or global authority for Lean.

Keep Lean-specific material under one proof-local boundary. A manifest pins the exact
Specification, declaration, and Claim addresses; expected elaborated theorem statement
and theorem name; SHA-256 digests of the canonical Specification, Claim, Lean source,
and checker; the exact Lean version and commit; the real invocation including
`--trust=0`; and the expected empty axiom dependency set. The checker verifies linkage,
digests, version, statement, exit status, warning-free output, and the positive
no-axioms observation before reporting success.

The Lean source uses only core, places `set_option warningAsError true` before any
declaration, and contains no `sorry`, declared axiom, `unsafe` declaration, adapter, or
Realization code. Red-first controls must include a false theorem, `sorry`, an injected
axiom, a same-name wrong-but-true statement, a wrong declaration link, stale canonical
input and source digests, a checker-version mismatch, and attempted reuse of the Wave 2
fixture placeholder. Proof-attempt or provenance failures are errors, not Evidence
challenging the law.

Any resulting canonical Evidence is an additional specification-scoped record with no
Realization, adapter, or profile scope. Its method states model satisfaction and
pipeline checking rather than the broader phrase “the law is proved.” Machine success
does not grant acceptance; independent review owns `reviewState`. Translation fidelity,
element domains as Lean types, the Lean kernel/toolchain, and the provenance runner are
explicit assumptions.

The existing accepted `fixture-only` proof Evidence is a schema/link fixture, not
product proof evidence. W3-PG1 must disposition that live resolver hazard and
deliberately re-baseline fixture counts if it adds a ninth valid record; the new record
does not silently “supersede” it because the current schema has no supersedes edge or
selection rule.

## Alternatives and review corrections

- An abstract `StackSpec` carrying `pop_empty` as a field was rejected because using
  the field would assume the proposition rather than check it from independent model
  definitions.
- Bounded enumeration was rejected as proof because the profile scopes evidence runs
  but does not narrow the universal law.
- Producing and independently rechecking `.olean` files remains a possible successor,
  but adds artifact machinery without demonstrated value for this first definitional
  theorem.
- Installing another prover solely for model diversity was deferred; provider diversity
  challenged this design, but model identity never grants proof authority.
- Pinning only a theorem name was rejected because a same-name, wrong-but-true theorem
  would pass. The expected elaborated statement is part of the checked manifest.

## Consequences

- The first theorem is intentionally simple and nearly definitional; its tracer value
  is the falsifiable end-to-end proof/evidence pipeline, not mathematical novelty.
- The hand-reviewed mapping from prose/JSON to Lean remains an assumption because the
  canonical language has no formal proposition elaborator.
- `pop-empty` does not exercise element equivalence or Stack quotient reasoning.
  Translating `pop-push` or another law is a new design node, not a mechanical extension.
- The Lean model must never be reused as the conformance runner's or adapter's oracle.
- No Lean syntax or tool choice enters the schemas, adapter protocol, or ConsumerPolicy.

## Revisit conditions

Revisit before translating another law, deriving one law from others, selecting a
project-wide proof foundation, automating proposition elaboration, accepting proof
Evidence through a resolver, or relying on generated proof artifacts across machines.
