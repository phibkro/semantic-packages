# Research synthesis

## Repeated abstraction pattern

Computer architecture, networking, programming languages, databases, and protocols all stabilize around a contract that separates observable meaning from implementation:

```text
producer → stable semantic interface → engine/realization
```

An ISA is the specification of an abstract machine; physical and virtual engines are both realizations. SQL and Datalog demonstrate declarative meaning separated from planning and execution. Standards such as HTTP distribute shared semantics rather than a shared server implementation.

## Package-level hypothesis

A package can be modeled as:

```text
Specification + Realizations + Claims + Evidence + Profiles + Policies
```

The reusable object is a theory rather than a code archive.

## Mathematical foundations

- **Institution theory**: signatures, sentences, models, satisfaction, and
  logic-independent specification composition. Goguen and Burstall's
  [institution framework](https://publish.lfcs.inf.ed.ac.uk/reports/90/ECS-LFCS-90-106)
  is a candidate when imports or refinement must preserve satisfaction across logics,
  not a requirement for today's exact visible import edges.
- **Category theory and categorical logic**: composition, morphisms, refinement, and
  translations between semantic worlds. The Curry–Howard–Lambek correspondence and
  higher-order categorical logic explain how typed calculi and categorical semantics
  can structure a proof lane; they do not require the registry to choose one internal
  logic for every semantic concern.
- **Universal algebra**: operations and equations for compositional structures.
- **Coalgebra**: observable behavior, evolving systems, and behavioral equivalence/bisimulation.
- **Dependent type theory/proof assistants**: construction and checking of specifications and evidence.
- **Linear and quantitative systems**: user-definable resource usage and capability obligations.
- **Effect systems**: required, permitted, optional, and forbidden interactions with an environment.
- **Temporal/session/state-machine theories**: legal interaction protocols.
- **Cost and empirical semantics**: operational and statistically observable claims.

No single foundation should be forced to encode every concern. The system should host typed semantic aspects and explicit translations between them.

Proof relevance provides a useful interpretation of the existing data model without
becoming its foundation: Claims identify propositions and scope, while Evidence keeps
witness-level mechanism, provenance, result, assumptions, and exclusions. The analogy
explains why Evidence records for one Claim remain distinguishable, but it does not turn
tests, benchmarks, audits, or assertions into proof terms. Propositions-as-types is
therefore appropriate inside a selected proof mechanism such as Lean, not as a rewrite
of the six-role architecture: Specification, Realization, Claim, Evidence, Profile,
and Policy.

## Representation independence

Data declarations should express observations and laws rather than concrete memory layout. A `Person` may expose `name : Person -> String` and `age : Person -> Nat` without requiring an array-of-structs representation. A realization may choose AoS, SoA, columnar storage, computed fields, or remote queries if observations remain valid.

## Security implication

Distributing specifications rather than code reduces exposure to malicious installation and runtime behavior. Risk moves toward underspecification, misleading claims, unsound evidence, and incorrect local realization. This is a different and often more inspectable trust problem, not a complete elimination of risk.

## Engineering strategy

Use a vertical tracer bullet. The first implementation must connect authoring, validation, proof/test evidence, realization registration, browsing, and compatibility resolution before deepening any layer.

The adoption trigger for stronger categorical machinery is an observed product need:
OrderedMap authoring that strains the flat observation/law model, imports that need
meaning-preserving translation, or explicit refinement that needs simulation or
bisimulation. Until then, category theory validates the observation-first design but
does not add an implementation layer.

One possible cross-project seam is deliberately one-way: a BANG-compiled artifact may
be registered as a Realization and evidenced like any other, making this registry a
verification substrate without coupling either project's semantic core. No current
tracer depends on that integration.
