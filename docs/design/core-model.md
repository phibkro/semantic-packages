# Core model

## Specification

A versioned semantic artifact containing one or more aspects:

```text
identity
vocabulary
operations and observations
laws and invariants
behavior/protocol transitions
effect contract
resource contract
performance/empirical claims
imports and refinements
```

Aspects may be sparse. A pure algebraic specification need not declare protocols or performance.

## Realization

A mapping from a specification's vocabulary into executable artifacts, together with metadata about language, target, runtime, ABI, build, and limits.

A realization is not accepted merely because names and types align. It must be associated with claims and evidence.

## Claims and evidence

A claim records:

```text
subject
proposition
scope
assumptions
exclusions
status
```

Evidence records:

```text
mechanism
artifact/provenance
specification version
realization version
environment
result
freshness
```

## Policies

A consumer policy stratifies concerns:

```text
required | preferred | optional | ignored | forbidden
```

It may also state acceptable evidence mechanisms and minimum assurance per concern.

## Satisfaction

The system should initially support a family of conformance relations rather than pretending there is one universal boolean:

- schema/type conformance;
- exact law satisfaction;
- observational refinement;
- protocol simulation;
- test-suite threshold;
- benchmark/empirical threshold;
- human assertion.

The resolver reports the relation and evidence used.
